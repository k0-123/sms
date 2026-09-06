package com.smsbridge.data

import androidx.room.Entity
import androidx.room.PrimaryKey

/** Status vocabulary mirrors the desktop app's messages table exactly. */
object CallJobStatus {
    const val PENDING = "PENDING"
    const val SENDING = "SENDING"   // call in progress
    const val SENT = "SENT"         // call completed (rang or answered)
    const val ANSWERED = "ANSWERED"
    const val NO_ANSWER = "NO_ANSWER"
    const val FAILED = "FAILED"
}

@Entity(tableName = "call_jobs")
data class CallJobEntity(
    @PrimaryKey val messageId: String,
    val campaignId: String,
    val phoneNumber: String,
    val ringDurationSec: Int,
    val simSlot: Int,
    val rateLimitMs: Long,
    val dailyLimit: Int,
    val status: String,
    val error: String? = null,
    val endedAt: Long? = null,
    val syncedToDesktop: Boolean = false,
    val createdAt: Long = System.currentTimeMillis(),
)
