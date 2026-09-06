package com.smsbridge.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.smsbridge.MainActivity
import com.smsbridge.call.CallMaker
import com.smsbridge.data.AppDatabase
import com.smsbridge.data.CallJobStatus
import com.smsbridge.data.JobStatus
import com.smsbridge.sms.SmsSender
import com.smsbridge.ws.BridgeServiceControl
import com.smsbridge.ws.PairingManager
import com.smsbridge.ws.WsServer
import com.smsbridge.ws.callStatusMessage
import com.smsbridge.ws.smsStatusMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull
import java.util.Calendar
import java.util.UUID

/** Foreground service owning the WebSocket server, mDNS advertisement, and
 * the SMS + Call dispatch loops. Runs the phone-side daily quota + rate
 * limiting — see campaign_engine.py's module docstring on the desktop for why. */
class BridgeService : Service() {
    private val scope = CoroutineScope(Dispatchers.IO + Job())
    private var wsServer: WsServer? = null
    private var nsdAdvertiser: NsdAdvertiser? = null
    private var paused = false
    private val smsWakeChannel = Channel<Unit>(Channel.CONFLATED)
    private val callWakeChannel = Channel<Unit>(Channel.CONFLATED)

    private lateinit var deviceId: String
    private lateinit var deviceName: String

    override fun onCreate() {
        super.onCreate()
        instance = this
        deviceId = getOrCreateDeviceId(this)
        deviceName = "${Build.MANUFACTURER} ${Build.MODEL}"

        startForeground(NOTIFICATION_ID, buildNotification("Starting..."))

        val server = WsServer(this)
        server.start()
        wsServer = server

        val advertiser = NsdAdvertiser(this)
        val code = PairingManager.generateCode()
        advertiser.start(deviceId, deviceName)
        nsdAdvertiser = advertiser

        BridgeServiceControl.onNewJob = { smsWakeChannel.trySend(Unit) }
        BridgeServiceControl.onNewCallJob = { callWakeChannel.trySend(Unit) }
        BridgeServiceControl.onPauseChanged = { paused = it }

        updateNotification("Pairing code: $code")
        scope.launch { smsDispatchLoop() }
        scope.launch { callDispatchLoop() }
    }

    override fun onDestroy() {
        wsServer?.shutdownServer()
        nsdAdvertiser?.stop()
        BridgeServiceControl.onNewJob = null
        BridgeServiceControl.onNewCallJob = null
        BridgeServiceControl.onPauseChanged = null
        scope.cancel()
        if (instance === this) instance = null
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_STICKY

    // ── SMS dispatch loop (unchanged logic) ──────────────────────────────
    private suspend fun smsDispatchLoop() {
        val jobDao = AppDatabase.get(this).jobDao()
        while (true) {
            if (paused) {
                withTimeoutOrNull(2000) { smsWakeChannel.receive() }
                continue
            }

            val job = jobDao.nextByStatus(JobStatus.PENDING)
            if (job == null) {
                withTimeoutOrNull(30_000) { smsWakeChannel.receive() }
                continue
            }

            val sentToday = jobDao.countSentSince(startOfTodayMillis())
            if (sentToday >= job.dailyLimit) {
                updateNotification("SMS daily limit reached (${job.dailyLimit}/day). Resuming tomorrow.")
                withTimeoutOrNull(5 * 60_000) { smsWakeChannel.receive() }
                continue
            }

            jobDao.updateStatus(job.messageId, JobStatus.SENDING, null)
            runCatching {
                SmsSender.send(this, job.messageId, job.phoneNumber, job.text, job.simSlot)
            }.onFailure { e ->
                jobDao.updateStatus(job.messageId, JobStatus.FAILED, e.message ?: "Could not send this message.")
                notifySmsStatusChanged(job.messageId)
            }

            val pending = jobDao.countByStatus(JobStatus.PENDING)
            val sent = jobDao.countByStatus(JobStatus.SENT)
            updateNotification("SMS — Sent: $sent    Pending: $pending")

            delay(job.rateLimitMs)
        }
    }

    // ── Call dispatch loop ────────────────────────────────────────────────
    private suspend fun callDispatchLoop() {
        val callJobDao = AppDatabase.get(this).callJobDao()
        while (true) {
            if (paused) {
                withTimeoutOrNull(2000) { callWakeChannel.receive() }
                continue
            }

            val job = callJobDao.nextByStatus(CallJobStatus.PENDING)
            if (job == null) {
                withTimeoutOrNull(30_000) { callWakeChannel.receive() }
                continue
            }

            val calledToday = callJobDao.countCalledSince(startOfTodayMillis())
            if (calledToday >= job.dailyLimit) {
                updateNotification("Call daily limit reached (${job.dailyLimit}/day). Resuming tomorrow.")
                withTimeoutOrNull(5 * 60_000) { callWakeChannel.receive() }
                continue
            }

            callJobDao.updateStatus(job.messageId, CallJobStatus.SENDING, null)

            val result = runCatching {
                CallMaker.placeCall(this, job.phoneNumber, job.ringDurationSec)
            }

            result.onSuccess { callResult ->
                when (callResult.status) {
                    "ANSWERED", "SENT", "NO_ANSWER" -> {
                        callJobDao.markCompleted(job.messageId, callResult.status, System.currentTimeMillis())
                    }
                    "FAILED" -> {
                        callJobDao.updateStatus(job.messageId, CallJobStatus.FAILED, callResult.error ?: "Call failed")
                    }
                    else -> {
                        callJobDao.markCompleted(job.messageId, CallJobStatus.SENT, System.currentTimeMillis())
                    }
                }
                notifyCallStatusChanged(job.messageId)
            }.onFailure { e ->
                callJobDao.updateStatus(job.messageId, CallJobStatus.FAILED, e.message ?: "Could not place call.")
                notifyCallStatusChanged(job.messageId)
            }

            val pending = callJobDao.countByStatus(CallJobStatus.PENDING)
            val sent = callJobDao.countByStatus(CallJobStatus.SENT) +
                       callJobDao.countByStatus(CallJobStatus.ANSWERED) +
                       callJobDao.countByStatus(CallJobStatus.NO_ANSWER)
            updateNotification("Calls — Completed: $sent    Queued: $pending")

            delay(job.rateLimitMs)
        }
    }

    // ── Status notification helpers ──────────────────────────────────────
    private fun notifySmsStatusChanged(messageId: String) {
        scope.launch {
            val jobDao = AppDatabase.get(this@BridgeService).jobDao()
            val job = jobDao.get(messageId) ?: return@launch
            val delivered = wsServer?.protocolHandler?.broadcast(smsStatusMessage(job)) ?: false
            if (delivered) {
                jobDao.markSynced(messageId)
            }
        }
    }

    private fun notifyCallStatusChanged(messageId: String) {
        scope.launch {
            val callJobDao = AppDatabase.get(this@BridgeService).callJobDao()
            val job = callJobDao.get(messageId) ?: return@launch
            val delivered = wsServer?.protocolHandler?.broadcast(callStatusMessage(job)) ?: false
            if (delivered) {
                callJobDao.markSynced(messageId)
            }
        }
    }

    private fun startOfTodayMillis(): Long {
        val cal = Calendar.getInstance()
        cal.set(Calendar.HOUR_OF_DAY, 0)
        cal.set(Calendar.MINUTE, 0)
        cal.set(Calendar.SECOND, 0)
        cal.set(Calendar.MILLISECOND, 0)
        return cal.timeInMillis
    }

    private fun ensureChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val nm = getSystemService(NotificationManager::class.java)
            if (nm.getNotificationChannel(CHANNEL_ID) == null) {
                nm.createNotificationChannel(
                    NotificationChannel(CHANNEL_ID, "SMS Bridge running", NotificationManager.IMPORTANCE_LOW)
                )
            }
        }
    }

    private fun buildNotification(text: String): android.app.Notification {
        ensureChannel()
        val openAppIntent = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or
                (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) PendingIntent.FLAG_IMMUTABLE else 0),
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .setContentTitle("SMS Bridge running")
            .setContentText(text)
            .setContentIntent(openAppIntent)
            .setOngoing(true)
            .build()
    }

    private fun updateNotification(text: String) {
        val nm = getSystemService(NotificationManager::class.java)
        nm.notify(NOTIFICATION_ID, buildNotification(text))
    }

    companion object {
        private const val CHANNEL_ID = "bridge_service"
        private const val NOTIFICATION_ID = 1
        private const val PREFS_NAME = "smsbridge_device"
        private const val KEY_DEVICE_ID = "device_id"

        @Volatile
        private var instance: BridgeService? = null

        fun isRunning(): Boolean = instance != null

        fun notifyStatusChanged(messageId: String) {
            instance?.notifySmsStatusChanged(messageId)
        }

        fun getOrCreateDeviceId(context: Context): String {
            val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            val existing = prefs.getString(KEY_DEVICE_ID, null)
            if (existing != null) return existing
            val newId = UUID.randomUUID().toString()
            prefs.edit().putString(KEY_DEVICE_ID, newId).apply()
            return newId
        }
    }
}
