package com.smsbridge.data

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface PairedDeviceDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(device: PairedDeviceEntity)

    @Query("SELECT * FROM paired_devices ORDER BY lastConnectedAt DESC")
    suspend fun listAll(): List<PairedDeviceEntity>

    @Query("SELECT * FROM paired_devices WHERE deviceId = :deviceId")
    suspend fun get(deviceId: String): PairedDeviceEntity?

    @Query("DELETE FROM paired_devices WHERE deviceId = :deviceId")
    suspend fun delete(deviceId: String)
}
