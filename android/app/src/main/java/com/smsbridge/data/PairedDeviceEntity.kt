package com.smsbridge.data

import androidx.room.Entity
import androidx.room.PrimaryKey

/** Display/bookkeeping record for a paired desktop. The actual secret pairing
 * token lives only in TokenStore's EncryptedSharedPreferences, never here. */
@Entity(tableName = "paired_devices")
data class PairedDeviceEntity(
    @PrimaryKey val deviceId: String,
    val deviceName: String,
    val lastConnectedAt: Long = System.currentTimeMillis(),
)
