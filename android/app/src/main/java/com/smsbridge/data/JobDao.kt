package com.smsbridge.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update

@Dao
interface JobDao {
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertIfAbsent(job: JobEntity): Long

    @Update
    suspend fun update(job: JobEntity)

    @Query("SELECT * FROM jobs WHERE messageId = :messageId")
    suspend fun get(messageId: String): JobEntity?

    @Query("SELECT * FROM jobs WHERE status = :status ORDER BY createdAt ASC LIMIT 1")
    suspend fun nextByStatus(status: String): JobEntity?

    @Query("SELECT * FROM jobs WHERE syncedToDesktop = 0 AND status IN ('SENT', 'DELIVERED', 'FAILED')")
    suspend fun unsynced(): List<JobEntity>

    @Query("SELECT COUNT(*) FROM jobs WHERE status = :status")
    suspend fun countByStatus(status: String): Int

    @Query(
        "SELECT COUNT(*) FROM jobs WHERE status = 'SENT' AND sentAt >= :startOfDayMillis"
    )
    suspend fun countSentSince(startOfDayMillis: Long): Int

    @Query("UPDATE jobs SET status = :status, error = :error WHERE messageId = :messageId")
    suspend fun updateStatus(messageId: String, status: String, error: String?)

    @Query("UPDATE jobs SET status = :status, sentAt = :sentAt, syncedToDesktop = 0 WHERE messageId = :messageId")
    suspend fun markSent(messageId: String, status: String, sentAt: Long)

    @Query("UPDATE jobs SET syncedToDesktop = 1 WHERE messageId = :messageId")
    suspend fun markSynced(messageId: String)

    @Query("SELECT * FROM jobs WHERE campaignId = :campaignId AND status = 'PENDING'")
    suspend fun pendingForCampaign(campaignId: String): List<JobEntity>

    @Query("DELETE FROM jobs WHERE campaignId = :campaignId AND status = 'PENDING'")
    suspend fun cancelPendingForCampaign(campaignId: String)
}
