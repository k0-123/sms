package com.smsbridge.ws

import android.content.Context
import com.smsbridge.data.AppDatabase
import com.smsbridge.data.JobEntity
import com.smsbridge.data.JobStatus
import org.java_websocket.WebSocket
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import java.util.UUID

private val ISO = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).apply {
    timeZone = TimeZone.getTimeZone("UTC")
}

fun nowIso(): String = ISO.format(Date())

fun envelope(type: String, payload: JSONObject): String =
    JSONObject()
        .put("type", type)
        .put("id", UUID.randomUUID().toString())
        .put("ts", nowIso())
        .put("payload", payload)
        .toString()

/** Parses incoming messages and drives pairing / auth / job intake. Runs on
 * a coroutine per connection; SMS dispatch itself happens in a separate
 * BridgeService worker loop that reads from the Room job queue this class
 * writes into (decoupling "accept the job" from "actually send it"). */
class ProtocolHandler(private val context: Context) {
    private val jobDao = AppDatabase.get(context).jobDao()
    private val tokenStore = TokenStore(context)
    private val authenticatedConnections = mutableSetOf<WebSocket>()

    fun isAuthenticated(conn: WebSocket): Boolean = conn in authenticatedConnections

    fun onClose(conn: WebSocket) {
        authenticatedConnections.remove(conn)
    }

    /** Pushes a message (e.g. sms_status) to every currently-authenticated
     * desktop. Returns whether any connection actually received it - if not
     * (desktop currently disconnected), the caller should leave the
     * underlying job's synced_to_desktop flag false so it gets re-sent by
     * pushUnsyncedStatuses() on the next reconnect. */
    fun broadcast(message: String): Boolean {
        var delivered = false
        authenticatedConnections.toList().forEach { conn ->
            runCatching { conn.send(message) }.onSuccess { delivered = true }
        }
        return delivered
    }

    /** Reconciliation: re-sends every not-yet-acknowledged status update to a
     * newly authenticated connection, so a desktop that was disconnected
     * mid-campaign catches up on what actually happened on the phone. */
    private suspend fun pushUnsyncedStatuses(conn: WebSocket) {
        jobDao.unsynced().forEach { job ->
            runCatching { conn.send(smsStatusMessage(job)) }
                .onSuccess { jobDao.markSynced(job.messageId) }
        }
    }

    suspend fun handle(raw: String, conn: WebSocket) {
        val env = JSONObject(raw)
        val type = env.getString("type")
        val payload = env.optJSONObject("payload") ?: JSONObject()

        when (type) {
            "pair_request" -> handlePairRequest(payload, conn)
            "auth" -> handleAuth(payload, conn)
            "heartbeat" -> handleHeartbeat(conn)
            "sms_job" -> handleSmsJob(payload, conn)
            "pause" -> BridgeServiceControl.setPaused(true)
            "resume" -> BridgeServiceControl.setPaused(false)
            "cancel_campaign" -> handleCancelCampaign(payload)
            "unpair" -> handleUnpair(payload)
        }
    }

    private suspend fun handlePairRequest(payload: JSONObject, conn: WebSocket) {
        val deviceId = payload.getString("device_id")
        val deviceName = payload.getString("device_name")
        val code = payload.getString("pairing_code")

        val result = PairingManager.requestPairing(context, deviceId, deviceName, code)
        val response = JSONObject().put("accepted", result.accepted)
        result.token?.let { response.put("pairing_token", it) }
        result.reason?.let { response.put("reason", it) }
        conn.send(envelope("pair_response", response))
    }

    private suspend fun handleAuth(payload: JSONObject, conn: WebSocket) {
        val deviceId = payload.getString("device_id")
        val token = payload.getString("pairing_token")
        val ok = tokenStore.isValid(deviceId, token)
        val response = JSONObject().put("accepted", ok)
        if (ok) {
            authenticatedConnections.add(conn)
            response.put("session_token", UUID.randomUUID().toString())
            response.put("phone_number", "")
        } else {
            response.put("reason", "This phone no longer recognizes that pairing. Please re-pair.")
        }
        conn.send(envelope("auth_ack", response))
        if (ok) {
            pushUnsyncedStatuses(conn)
        }
    }

    private fun handleHeartbeat(conn: WebSocket) {
        conn.send(envelope("heartbeat_ack", JSONObject().put("queue_depth", 0)))
    }

    private suspend fun handleSmsJob(payload: JSONObject, conn: WebSocket) {
        val messageId = payload.getString("message_id")
        val job = JobEntity(
            messageId = messageId,
            campaignId = payload.getString("campaign_id"),
            phoneNumber = payload.getString("phone_number"),
            text = payload.getString("text"),
            simSlot = payload.optInt("sim_slot", 0),
            rateLimitMs = payload.optLong("rate_limit_ms", 2000L),
            dailyLimit = payload.optInt("daily_limit", 100),
            status = JobStatus.PENDING,
        )
        jobDao.insertIfAbsent(job)
        conn.send(envelope("sms_job_ack", JSONObject().put("message_id", messageId).put("status", "QUEUED")))
        BridgeServiceControl.notifyNewJob()
    }

    private suspend fun handleCancelCampaign(payload: JSONObject) {
        jobDao.cancelPendingForCampaign(payload.getString("campaign_id"))
    }

    private fun handleUnpair(payload: JSONObject) {
        val deviceId = payload.getString("device_id")
        tokenStore.revoke(deviceId)
    }
}

fun smsStatusMessage(job: JobEntity): String {
    val payload = JSONObject()
        .put("message_id", job.messageId)
        .put("status", job.status)
        .put("error", job.error)
        .put("sent_at", job.sentAt?.let { ISO.format(Date(it)) })
    return envelope("sms_status", payload)
}

/** Thin control surface so ProtocolHandler (per-connection) can signal the
 * long-lived BridgeService worker loop without holding a service reference. */
object BridgeServiceControl {
    @Volatile
    var onNewJob: (() -> Unit)? = null

    @Volatile
    var onPauseChanged: ((Boolean) -> Unit)? = null

    fun notifyNewJob() {
        onNewJob?.invoke()
    }

    fun setPaused(paused: Boolean) {
        onPauseChanged?.invoke(paused)
    }
}
