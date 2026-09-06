package com.smsbridge.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            """CREATE TABLE IF NOT EXISTS call_jobs (
                messageId TEXT NOT NULL PRIMARY KEY,
                campaignId TEXT NOT NULL,
                phoneNumber TEXT NOT NULL,
                ringDurationSec INTEGER NOT NULL,
                simSlot INTEGER NOT NULL,
                rateLimitMs INTEGER NOT NULL,
                dailyLimit INTEGER NOT NULL,
                status TEXT NOT NULL,
                error TEXT,
                endedAt INTEGER,
                syncedToDesktop INTEGER NOT NULL DEFAULT 0,
                createdAt INTEGER NOT NULL DEFAULT 0
            )"""
        )
    }
}

@Database(
    entities = [JobEntity::class, PairedDeviceEntity::class, CallJobEntity::class],
    version = 2,
    exportSchema = false,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun jobDao(): JobDao
    abstract fun pairedDeviceDao(): PairedDeviceDao
    abstract fun callJobDao(): CallJobDao

    companion object {
        @Volatile
        private var instance: AppDatabase? = null

        fun get(context: Context): AppDatabase =
            instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext, AppDatabase::class.java, "smsbridge.db"
                )
                    .addMigrations(MIGRATION_1_2)
                    .build().also { instance = it }
            }
    }
}
