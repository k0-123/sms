package com.smsbridge.sms

import android.app.Activity
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.telephony.SmsManager
import com.smsbridge.data.AppDatabase
import com.smsbridge.data.JobStatus
import com.smsbridge.service.BridgeService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

fun describeSmsError(resultCode: Int): String = when (resultCode) {
    Activity.RESULT_OK -> "Sent"
    SmsManager.RESULT_ERROR_NO_SERVICE -> "No signal - the phone has no cellular service right now."
    SmsManager.RESULT_ERROR_RADIO_OFF -> "Airplane mode is on, or the radio is off."
    SmsManager.RESULT_ERROR_NULL_PDU -> "The phone could not build this message."
    SmsManager.RESULT_ERROR_GENERIC_FAILURE -> "The phone's SIM/carrier rejected this message."
    else -> "The phone reported an unknown error (code $resultCode)."
}

/** Fires once per SMS part after the SIM/carrier accepts or rejects it. */
class SentStatusReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val messageId = intent.getStringExtra(EXTRA_MESSAGE_ID) ?: return
        val resultCode = resultCode
        val pending = goAsync()
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val jobDao = AppDatabase.get(context).jobDao()
                val job = jobDao.get(messageId)
                if (job != null && job.status != JobStatus.FAILED) {
                    if (resultCode == Activity.RESULT_OK) {
                        jobDao.markSent(messageId, JobStatus.SENT, System.currentTimeMillis())
                    } else {
                        jobDao.updateStatus(messageId, JobStatus.FAILED, describeSmsError(resultCode))
                    }
                    BridgeService.notifyStatusChanged(messageId)
                }
            } finally {
                pending.finish()
            }
        }
    }
}
