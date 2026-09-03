package com.smsbridge.sms

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.telephony.SmsManager
import android.telephony.SubscriptionManager

const val EXTRA_MESSAGE_ID = "message_id"

/** Wraps SmsManager: multipart splitting, per-SIM selection, and SENT/DELIVERED
 * PendingIntents correlated back to a message_id so BridgeService's worker
 * loop can await the real send outcome instead of assuming success. */
object SmsSender {

    fun send(context: Context, messageId: String, phoneNumber: String, text: String, simSlot: Int) {
        val smsManager = resolveSmsManager(context, simSlot)
        val parts = smsManager.divideMessage(text)

        val sentIntents = ArrayList<PendingIntent>()
        val deliveredIntents = ArrayList<PendingIntent>()
        for (i in parts.indices) {
            sentIntents.add(pendingIntentFor(context, SentStatusReceiver::class.java, messageId, i))
            deliveredIntents.add(pendingIntentFor(context, DeliveredStatusReceiver::class.java, messageId, i))
        }

        if (parts.size <= 1) {
            smsManager.sendTextMessage(phoneNumber, null, text, sentIntents.firstOrNull(), deliveredIntents.firstOrNull())
        } else {
            smsManager.sendMultipartTextMessage(phoneNumber, null, parts, sentIntents, deliveredIntents)
        }
    }

    private fun pendingIntentFor(
        context: Context, receiverClass: Class<*>, messageId: String, partIndex: Int
    ): PendingIntent {
        // Explicit component (rather than a plain action string) so delivery
        // doesn't depend on implicit-broadcast manifest matching.
        val intent = Intent(context, receiverClass).apply {
            putExtra(EXTRA_MESSAGE_ID, messageId)
        }
        val flags = PendingIntent.FLAG_UPDATE_CURRENT or
            (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) PendingIntent.FLAG_IMMUTABLE else 0)
        // requestCode combines messageId + part so each part's PendingIntent is distinct.
        val requestCode = (messageId + partIndex).hashCode()
        return PendingIntent.getBroadcast(context, requestCode, intent, flags)
    }

    private fun resolveSmsManager(context: Context, simSlot: Int): SmsManager {
        if (simSlot <= 0) return defaultSmsManager()
        return runCatching {
            val subManager = context.getSystemService(Context.TELEPHONY_SUBSCRIPTION_SERVICE) as SubscriptionManager
            val info = subManager.getActiveSubscriptionInfoForSimSlotIndex(simSlot)
            if (info != null) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    context.getSystemService(SmsManager::class.java).createForSubscriptionId(info.subscriptionId)
                } else {
                    @Suppress("DEPRECATION")
                    SmsManager.getSmsManagerForSubscriptionId(info.subscriptionId)
                }
            } else {
                defaultSmsManager()
            }
        }.getOrElse { defaultSmsManager() }
    }

    @Suppress("DEPRECATION")
    private fun defaultSmsManager(): SmsManager = SmsManager.getDefault()
}
