package com.smsbridge.data

import androidx.room.Entity
import androidx.room.PrimaryKey

/** Status vocabulary mirrors the desktop app's messages table exactly. */
object JobStatus {
    const val PENDING = "PENDING"
    const val SENDING = "SENDING"
    const val SENT = "SENT"
    const val DELIVERED = "DELIVERED"
    const val FAILED = "FAILED"
}

@Entity(tableName = "jobs")
data class JobEntity(
    @PrimaryKey val messageId: String,
    val campaignId: String,
    val phoneNumber: String,
    val text: String,
    val simSlot: Int,
    val rateLimitMs: Long,
    val dailyLimit: Int,
    val status: String,
    val error: String? = null,
    val sentAt: Long? = null,
    val syncedToDesktop: Boolean = false,
    val createdAt: Long = System.currentTimeMillis(),
)
