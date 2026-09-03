package com.smsbridge.sms

import android.app.Activity
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.smsbridge.data.AppDatabase
import com.smsbridge.data.JobStatus
import com.smsbridge.service.BridgeService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/** Delivery reports are best-effort - many carriers never send them. When one
 * does arrive it upgrades an already-SENT job's status marker to DELIVERED;
 * absence of this broadcast is not treated as a failure. */
class DeliveredStatusReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val messageId = intent.getStringExtra(EXTRA_MESSAGE_ID) ?: return
        if (resultCode != Activity.RESULT_OK) return
        val pending = goAsync()
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val jobDao = AppDatabase.get(context).jobDao()
                val job = jobDao.get(messageId)
                if (job != null && job.status == JobStatus.SENT) {
                    jobDao.markSent(messageId, JobStatus.DELIVERED, job.sentAt ?: System.currentTimeMillis())
                    BridgeService.notifyStatusChanged(messageId)
                }
            } finally {
                pending.finish()
            }
        }
    }
}
