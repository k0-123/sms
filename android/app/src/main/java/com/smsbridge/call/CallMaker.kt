package com.smsbridge.call

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.telecom.TelecomManager
import android.telephony.PhoneStateListener
import android.telephony.TelephonyCallback
import android.telephony.TelephonyManager
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import java.io.File

/**
 * Places phone calls using the device's native dialer and monitors call state.
 *
 * Flow:
 * 1. Dial recipient via Intent.ACTION_CALL.
 * 2. If recipient does NOT answer within [ringDurationSec], auto-hangup -> NO_ANSWER.
 * 3. If recipient answers (CALL_STATE_OFFHOOK):
 *    - If [audioFile] is provided, activates speakerphone and plays the MP3 announcement.
 *    - On audio completion, auto-hangup -> ANSWERED.
 * 4. Detect IDLE -> report result.
 */
object CallMaker {

    /** Result of a single call attempt. */
    data class CallResult(
        val status: String,  // SENT, ANSWERED, NO_ANSWER, FAILED
        val error: String? = null,
    )

    /**
     * Place a call and wait until it completes (or times out).
     *
     * @param context         Application context
     * @param phoneNumber     E.164 formatted number
     * @param ringDurationSec Max seconds to let the call ring before auto-hangup if unanswered
     * @param audioFile       Optional campaign MP3 file to play via speakerphone on answer
     * @return [CallResult] describing the outcome
     */
    @Suppress("MissingPermission")
    suspend fun placeCall(
        context: Context,
        phoneNumber: String,
        ringDurationSec: Int,
        audioFile: File? = null,
    ): CallResult = withContext(Dispatchers.Main) {
        val callCompleted = CompletableDeferred<CallResult>()
        val telephonyManager = context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager

        var wasRinging = false
        var wasOffhook = false

        fun onAnswered() {
            if (audioFile != null && audioFile.exists()) {
                AudioBroadcastPlayer.playInCall(context, audioFile) {
                    endCall(context)
                    if (!callCompleted.isCompleted) {
                        callCompleted.complete(CallResult("ANSWERED"))
                    }
                }
            }
        }

        // Register call state listener
        val callback: Any  // either TelephonyCallback or PhoneStateListener
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val tcb = object : TelephonyCallback(), TelephonyCallback.CallStateListener {
                override fun onCallStateChanged(state: Int) {
                    when (state) {
                        TelephonyManager.CALL_STATE_RINGING -> wasRinging = true
                        TelephonyManager.CALL_STATE_OFFHOOK -> {
                            wasOffhook = true
                            onAnswered()
                        }
                        TelephonyManager.CALL_STATE_IDLE -> {
                            AudioBroadcastPlayer.stop(context)
                            if (!callCompleted.isCompleted) {
                                if (wasOffhook) {
                                    callCompleted.complete(CallResult("ANSWERED"))
                                } else if (wasRinging) {
                                    callCompleted.complete(CallResult("NO_ANSWER"))
                                } else {
                                    callCompleted.complete(CallResult("SENT"))
                                }
                            }
                        }
                    }
                }
            }
            telephonyManager.registerTelephonyCallback(ContextCompat.getMainExecutor(context), tcb)
            callback = tcb
        } else {
            @Suppress("DEPRECATION")
            val listener = object : PhoneStateListener() {
                @Deprecated("Deprecated in Java")
                override fun onCallStateChanged(state: Int, incomingNumber: String?) {
                    when (state) {
                        TelephonyManager.CALL_STATE_RINGING -> wasRinging = true
                        TelephonyManager.CALL_STATE_OFFHOOK -> {
                            wasOffhook = true
                            onAnswered()
                        }
                        TelephonyManager.CALL_STATE_IDLE -> {
                            AudioBroadcastPlayer.stop(context)
                            if (!callCompleted.isCompleted) {
                                if (wasOffhook) {
                                    callCompleted.complete(CallResult("ANSWERED"))
                                } else if (wasRinging) {
                                    callCompleted.complete(CallResult("NO_ANSWER"))
                                } else {
                                    callCompleted.complete(CallResult("SENT"))
                                }
                            }
                        }
                    }
                }
            }
            @Suppress("DEPRECATION")
            telephonyManager.listen(listener, PhoneStateListener.LISTEN_CALL_STATE)
            callback = listener
        }

        // Place the call
        try {
            val callIntent = Intent(Intent.ACTION_CALL).apply {
                data = Uri.parse("tel:${phoneNumber}")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(callIntent)
        } catch (e: Exception) {
            unregisterCallback(telephonyManager, callback)
            return@withContext CallResult("FAILED", e.message ?: "Could not initiate call")
        }

        // Wait for call to complete or ring timeout
        // If an audio file is playing, allow up to 120s total; otherwise ringDurationSec + 10s
        val maxTotalTimeoutMs = if (audioFile != null && audioFile.exists()) 120_000L else (ringDurationSec + 10) * 1000L

        val result = withTimeoutOrNull(maxTotalTimeoutMs) {
            // First wait for ring duration
            val ringIntervalMs = 500L
            var elapsed = 0L
            while (elapsed < ringDurationSec * 1000L) {
                if (wasOffhook) break // Recipient answered! Let audio play
                delay(ringIntervalMs)
                elapsed += ringIntervalMs
            }

            if (!wasOffhook) {
                // Not answered within ringDurationSec -> hang up
                endCall(context)
                // Wait briefly for IDLE state confirmation
                withTimeoutOrNull(5_000L) { callCompleted.await() }
            } else {
                // Answered -> wait for audio to finish playing and call to finish
                callCompleted.await()
            }
        }

        AudioBroadcastPlayer.stop(context)
        unregisterCallback(telephonyManager, callback)

        return@withContext result ?: CallResult(if (wasOffhook) "ANSWERED" else "NO_ANSWER")
    }

    /** End the current call using TelecomManager (API 28+) or reflection fallback. */
    @Suppress("MissingPermission")
    private fun endCall(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            val telecomManager = context.getSystemService(Context.TELECOM_SERVICE) as TelecomManager
            try {
                @Suppress("DEPRECATION")
                telecomManager.endCall()
            } catch (e: Exception) {
                endCallViaReflection(context)
            }
        } else {
            endCallViaReflection(context)
        }
    }

    /** Reflection fallback for ending calls on older Android versions. */
    private fun endCallViaReflection(context: Context) {
        try {
            val telephonyManager = context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
            val clazz = Class.forName(telephonyManager.javaClass.name)
            val method = clazz.getDeclaredMethod("getITelephony")
            method.isAccessible = true
            val telephonyService = method.invoke(telephonyManager)
            val endCallMethod = telephonyService.javaClass.getDeclaredMethod("endCall")
            endCallMethod.invoke(telephonyService)
        } catch (e: Exception) {
            // Best-effort; call will end naturally if this fails
        }
    }

    private fun unregisterCallback(telephonyManager: TelephonyManager, callback: Any) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && callback is TelephonyCallback) {
            telephonyManager.unregisterTelephonyCallback(callback)
        } else if (callback is PhoneStateListener) {
            @Suppress("DEPRECATION")
            telephonyManager.listen(callback, PhoneStateListener.LISTEN_NONE)
        }
    }
}
