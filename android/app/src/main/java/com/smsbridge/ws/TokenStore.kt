package com.smsbridge.ws

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import java.security.SecureRandom
import java.util.Base64

/** Encrypted-at-rest storage for paired desktops' long-lived pairing tokens. */
class TokenStore(context: Context) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val prefs = EncryptedSharedPreferences.create(
        context,
        "smsbridge_tokens",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )

    fun generateToken(): String {
        val bytes = ByteArray(32)
        SecureRandom().nextBytes(bytes)
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes)
    }

    fun store(deviceId: String, token: String) {
        prefs.edit().putString(deviceId, token).apply()
    }

    fun get(deviceId: String): String? = prefs.getString(deviceId, null)

    fun isValid(deviceId: String, token: String): Boolean = get(deviceId) == token

    fun revoke(deviceId: String) {
        prefs.edit().remove(deviceId).apply()
    }
}
