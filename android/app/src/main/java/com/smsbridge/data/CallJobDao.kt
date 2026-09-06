package com.smsbridge.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface CallJobDao {
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertIfAbsent(job: CallJobEntity): Long

    @Query("SELECT * FROM call_jobs WHERE messageId = :messageId")
    suspend fun get(messageId: String): CallJobEntity?

    @Query("SELECT * FROM call_jobs WHERE status = :status ORDER BY createdAt ASC LIMIT 1")
    suspend fun nextByStatus(status: String): CallJobEntity?

    @Query("SELECT * FROM call_jobs WHERE syncedToDesktop = 0 AND status IN ('SENT', 'ANSWERED', 'NO_ANSWER', 'FAILED')")
    suspend fun unsynced(): List<CallJobEntity>

    @Query("SELECT COUNT(*) FROM call_jobs WHERE status = :status")
    suspend fun countByStatus(status: String): Int

    @Query("SELECT COUNT(*) FROM call_jobs WHERE status IN ('SENT', 'ANSWERED', 'NO_ANSWER') AND endedAt >= :startOfDayMillis")
    suspend fun countCalledSince(startOfDayMillis: Long): Int

    @Query("UPDATE call_jobs SET status = :status, error = :error WHERE messageId = :messageId")
    suspend fun updateStatus(messageId: String, status: String, error: String?)

    @Query("UPDATE call_jobs SET status = :status, endedAt = :endedAt, syncedToDesktop = 0 WHERE messageId = :messageId")
    suspend fun markCompleted(messageId: String, status: String, endedAt: Long)

    @Query("UPDATE call_jobs SET syncedToDesktop = 1 WHERE messageId = :messageId")
    suspend fun markSynced(messageId: String)

    @Query("SELECT * FROM call_jobs WHERE campaignId = :campaignId AND status = 'PENDING'")
    suspend fun pendingForCampaign(campaignId: String): List<CallJobEntity>

    @Query("DELETE FROM call_jobs WHERE campaignId = :campaignId AND status = 'PENDING'")
    suspend fun cancelPendingForCampaign(campaignId: String)
}
