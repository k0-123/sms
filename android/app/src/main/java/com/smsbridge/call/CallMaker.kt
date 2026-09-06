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

/**
 * Places phone calls using the device's native dialer and monitors call state.
 *
 * Flow: dial → wait for RINGING/OFFHOOK → auto-hangup after [ringDurationSec] →
 * detect IDLE → report result.
 *
 * Uses TelecomManager.endCall() on API 28+ for auto-hangup, with a reflection
 * fallback for older devices (ITelephony.endCall).
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
     * @param context        Application context
     * @param phoneNumber    E.164 formatted number
     * @param ringDurationSec Max seconds to let the call ring before auto-hangup
     * @return [CallResult] describing the outcome
     */
    @Suppress("MissingPermission")
    suspend fun placeCall(
        context: Context,
        phoneNumber: String,
        ringDurationSec: Int,
    ): CallResult = withContext(Dispatchers.Main) {
        val callCompleted = CompletableDeferred<CallResult>()
        val telephonyManager = context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager

        var wasRinging = false
        var wasOffhook = false

        // Register call state listener
        val callback: Any  // either TelephonyCallback or PhoneStateListener
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            // API 31+ uses TelephonyCallback
            val tcb = object : TelephonyCallback(), TelephonyCallback.CallStateListener {
                override fun onCallStateChanged(state: Int) {
                    when (state) {
                        TelephonyManager.CALL_STATE_RINGING -> wasRinging = true
                        TelephonyManager.CALL_STATE_OFFHOOK -> wasOffhook = true
                        TelephonyManager.CALL_STATE_IDLE -> {
                            if (wasOffhook) {
                                callCompleted.complete(CallResult("ANSWERED"))
                            } else if (wasRinging) {
                                callCompleted.complete(CallResult("SENT"))
                            } else {
                                callCompleted.complete(CallResult("SENT"))
                            }
                        }
                    }
                }
            }
            telephonyManager.registerTelephonyCallback(ContextCompat.getMainExecutor(context), tcb)
            callback = tcb
        } else {
            // Legacy PhoneStateListener for older APIs
            @Suppress("DEPRECATION")
            val listener = object : PhoneStateListener() {
                @Deprecated("Deprecated in Java")
                override fun onCallStateChanged(state: Int, incomingNumber: String?) {
                    when (state) {
                        TelephonyManager.CALL_STATE_RINGING -> wasRinging = true
                        TelephonyManager.CALL_STATE_OFFHOOK -> wasOffhook = true
                        TelephonyManager.CALL_STATE_IDLE -> {
                            if (wasOffhook) {
                                callCompleted.complete(CallResult("ANSWERED"))
                            } else if (wasRinging) {
                                callCompleted.complete(CallResult("SENT"))
                            } else {
                                callCompleted.complete(CallResult("SENT"))
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

        // Wait for call to complete or timeout
        val timeoutMs = (ringDurationSec + 10) * 1000L  // extra 10s buffer
        val result = withTimeoutOrNull(timeoutMs) {
            // After ringDurationSec, try to end the call
            delay(ringDurationSec * 1000L)
            endCall(context)
            // Wait a bit more for IDLE state
            withTimeoutOrNull(10_000L) { callCompleted.await() }
        }

        unregisterCallback(telephonyManager, callback)

        return@withContext result ?: CallResult("SENT")  // timed out = assume rang
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
