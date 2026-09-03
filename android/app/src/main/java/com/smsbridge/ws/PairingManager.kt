package com.smsbridge.ws

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import com.smsbridge.data.AppDatabase
import com.smsbridge.data.PairedDeviceEntity
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.withTimeoutOrNull
import java.util.UUID
import kotlin.random.Random

data class PairResult(val accepted: Boolean, val token: String? = null, val reason: String? = null)

/** Validates pairing codes, prompts the user via a notification with
 * Allow/Deny actions (no foreground activity required), and issues tokens. */
object PairingManager {
    private const val CHANNEL_ID = "pairing"
    private const val ACTION_RESPOND = "com.smsbridge.PAIR_RESPOND"
    const val EXTRA_REQUEST_ID = "request_id"
    const val EXTRA_ACCEPTED = "accepted"

    private var activeCode: String? = null
    private var activeCodeExpiresAt: Long = 0
    private val pending = mutableMapOf<String, CompletableDeferred<Boolean>>()

    fun generateCode(): String {
        val code = (100000 + Random.nextInt(900000)).toString()
        activeCode = code
        activeCodeExpiresAt = System.currentTimeMillis() + 2 * 60 * 1000
        return code
    }

    fun currentCode(): String? =
        if (activeCode != null && System.currentTimeMillis() < activeCodeExpiresAt) activeCode else null

    suspend fun requestPairing(
        context: Context,
        deviceId: String,
        deviceName: String,
        submittedCode: String,
    ): PairResult {
        val code = currentCode()
        if (code == null || code != submittedCode) {
            return PairResult(accepted = false, reason = "Invalid or expired pairing code.")
        }

        ensureChannel(context)
        val requestId = UUID.randomUUID().toString()
        val deferred = CompletableDeferred<Boolean>()
        pending[requestId] = deferred

        showConfirmationNotification(context, requestId, deviceName)

        val accepted = withTimeoutOrNull(60_000) { deferred.await() } ?: false
        pending.remove(requestId)

        if (!accepted) {
            return PairResult(accepted = false, reason = "Pairing was declined on the phone. Please try again.")
        }

        val tokenStore = TokenStore(context)
        val token = tokenStore.generateToken()
        tokenStore.store(deviceId, token)
        AppDatabase.get(context).pairedDeviceDao().upsert(PairedDeviceEntity(deviceId, deviceName))
        return PairResult(accepted = true, token = token)
    }

    fun resolve(requestId: String, accepted: Boolean) {
        pending[requestId]?.complete(accepted)
    }

    private fun ensureChannel(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val nm = context.getSystemService(NotificationManager::class.java)
            if (nm.getNotificationChannel(CHANNEL_ID) == null) {
                nm.createNotificationChannel(
                    NotificationChannel(CHANNEL_ID, "Pairing requests", NotificationManager.IMPORTANCE_HIGH)
                )
            }
        }
    }

    private fun showConfirmationNotification(context: Context, requestId: String, deviceName: String) {
        fun actionIntent(accepted: Boolean): PendingIntent {
            val intent = Intent(context, PairingResponseReceiver::class.java).apply {
                action = ACTION_RESPOND
                putExtra(EXTRA_REQUEST_ID, requestId)
                putExtra(EXTRA_ACCEPTED, accepted)
            }
            val flags = PendingIntent.FLAG_UPDATE_CURRENT or
                (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) PendingIntent.FLAG_IMMUTABLE else 0)
            return PendingIntent.getBroadcast(context, requestId.hashCode(), intent, flags)
        }

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_sys_download_done)
            .setContentTitle("Allow SMS Broadcaster?")
            .setContentText("$deviceName wants to send SMS through this phone.")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .addAction(0, "Allow", actionIntent(true))
            .addAction(0, "Deny", actionIntent(false))
            .build()

        val nm = context.getSystemService(NotificationManager::class.java)
        nm.notify(requestId.hashCode(), notification)
    }
}

class PairingResponseReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val requestId = intent.getStringExtra(PairingManager.EXTRA_REQUEST_ID) ?: return
        val accepted = intent.getBooleanExtra(PairingManager.EXTRA_ACCEPTED, false)
        PairingManager.resolve(requestId, accepted)
        val nm = context.getSystemService(NotificationManager::class.java)
        nm.cancel(requestId.hashCode())
    }
}
