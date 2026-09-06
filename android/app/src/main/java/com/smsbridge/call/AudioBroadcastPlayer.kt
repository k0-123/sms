package com.smsbridge.call

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioManager
import android.media.MediaPlayer
import android.net.Uri
import android.util.Log
import java.io.File

/**
 * Handles audio playback during a phone call using speakerphone mode.
 *
 * When the call state transitions to OFFHOOK (the recipient answers), this
 * activates the device speakerphone, adjusts stream volume, and plays the
 * campaign's MP3 file so the microphone clearly transmits the announcement
 * to the caller.
 */
object AudioBroadcastPlayer {
    private const val TAG = "AudioBroadcastPlayer"
    private var mediaPlayer: MediaPlayer? = null
    private var originalAudioMode: Int = AudioManager.MODE_NORMAL
    private var originalSpeakerphone: Boolean = false

    /**
     * Play an audio file through speakerphone during an active call.
     *
     * @param context Application context
     * @param audioFile The campaign MP3/WAV file stored locally on the phone
     * @param onComplete Invoked when playback completes or fails, so the call can end
     */
    @Synchronized
    fun playInCall(
        context: Context,
        audioFile: File,
        onComplete: () -> Unit,
    ) {
        stop() // ensure any previous instance is cleaned up

        if (!audioFile.exists() || audioFile.length() == 0L) {
            Log.w(TAG, "Audio file does not exist or is empty: ${audioFile.absolutePath}")
            onComplete()
            return
        }

        try {
            val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
            originalAudioMode = audioManager.mode
            originalSpeakerphone = audioManager.isSpeakerphoneOn

            // Route audio to speakerphone
            audioManager.mode = AudioManager.MODE_IN_CALL
            audioManager.isSpeakerphoneOn = true

            // Set call volume to a loud, clear level
            val maxCallVol = audioManager.getStreamMaxVolume(AudioManager.STREAM_VOICE_CALL)
            audioManager.setStreamVolume(AudioManager.STREAM_VOICE_CALL, maxCallVol, 0)

            val maxMusicVol = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC)
            audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, (maxMusicVol * 0.9).toInt(), 0)

            val player = MediaPlayer().apply {
                setAudioAttributes(
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_VOICE_COMMUNICATION)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build()
                )
                setDataSource(context, Uri.fromFile(audioFile))
                setOnCompletionListener {
                    Log.i(TAG, "Audio broadcast finished playing.")
                    cleanup(context)
                    onComplete()
                }
                setOnErrorListener { _, what, extra ->
                    Log.e(TAG, "MediaPlayer error: what=$what extra=$extra")
                    cleanup(context)
                    onComplete()
                    true
                }
                prepare()
                start()
            }
            mediaPlayer = player
            Log.i(TAG, "Started playing in-call audio: ${audioFile.name}")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start in-call audio playback", e)
            cleanup(context)
            onComplete()
        }
    }

    /** Stop playback and restore device audio settings. */
    @Synchronized
    fun stop(context: Context? = null) {
        try {
            mediaPlayer?.let {
                if (it.isPlaying) it.stop()
                it.release()
            }
        } catch (e: Exception) {
            Log.w(TAG, "Error releasing MediaPlayer", e)
        } finally {
            mediaPlayer = null
            context?.let { cleanup(it) }
        }
    }

    private fun cleanup(context: Context) {
        try {
            val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
            audioManager.isSpeakerphoneOn = originalSpeakerphone
            audioManager.mode = originalAudioMode
        } catch (e: Exception) {
            Log.w(TAG, "Error restoring audio settings", e)
        }
    }
}
