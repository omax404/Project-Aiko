package com.aiko.app.domain

import android.content.Context
import android.media.MediaPlayer
import android.speech.tts.TextToSpeech
import android.util.Log
import com.aiko.app.data.local.AikoPrefs
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AikoVocalizer @Inject constructor(
    @ApplicationContext private val context: Context,
    private val aikoPrefs: AikoPrefs
) : TextToSpeech.OnInitListener {

    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(10, java.util.concurrent.TimeUnit.SECONDS)
        .readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .build()

    private var nativeTts: TextToSpeech? = null
    private var isNativeTtsReady = false
    private var mediaPlayer: MediaPlayer? = null

    init {
        // Initialize native Android TTS in background
        try {
            nativeTts = TextToSpeech(context, this)
        } catch (e: Exception) {
            Log.e("AikoVocalizer", "Failed to initialize native TextToSpeech: ${e.message}")
        }
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            val result = nativeTts?.setLanguage(Locale.getDefault())
            if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                nativeTts?.setLanguage(Locale.US)
            }
            isNativeTtsReady = true
            Log.d("AikoVocalizer", "Native Android TTS initialized successfully.")
        } else {
            Log.e("AikoVocalizer", "Native Android TTS initialization failed.")
        }
    }

    /**
     * Synthesizes and speaks the given text based on current user preferences.
     */
    suspend fun speak(text: String) = withContext(Dispatchers.IO) {
        val voiceEnabled = aikoPrefs.voiceEnabledFlow.first()
        if (!voiceEnabled) return@withContext

        val engine = aikoPrefs.ttsEngineFlow.first()
        Log.d("AikoVocalizer", "Speaking text with engine '$engine': '$text'")

        // Stop any currently playing audio
        stop()

        when (engine) {
            "native" -> {
                speakNative(text)
            }
            "custom_api" -> {
                speakCustomApi(text)
            }
            else -> {
                Log.d("AikoVocalizer", "TTS Engine is disabled.")
            }
        }
    }

    /**
     * Stops any current playback or native speaking immediately.
     */
    fun stop() {
        try {
            if (nativeTts?.isSpeaking == true) {
                nativeTts?.stop()
            }
            mediaPlayer?.let { player ->
                if (player.isPlaying) {
                    player.stop()
                }
                player.release()
            }
            mediaPlayer = null
        } catch (e: Exception) {
            Log.e("AikoVocalizer", "Error stopping vocalizer playback: ${e.message}")
        }
    }

    private fun speakNative(text: String) {
        if (!isNativeTtsReady || nativeTts == null) {
            Log.w("AikoVocalizer", "Native TTS is not ready yet.")
            return
        }
        // Clean text slightly for better native pronunciation
        val cleanText = text.replace(Regex("[*_#`]"), "")
        nativeTts?.speak(cleanText, TextToSpeech.QUEUE_FLUSH, null, "aiko_utterance")
    }

    private suspend fun speakCustomApi(text: String) {
        val apiUrl = aikoPrefs.ttsApiUrlFlow.first()
        val apiKey = aikoPrefs.ttsApiKeyFlow.first()
        val voice = aikoPrefs.ttsApiVoiceFlow.first()
        val model = aikoPrefs.ttsApiModelFlow.first()

        if (apiUrl.isBlank()) {
            Log.w("AikoVocalizer", "Custom TTS API URL is blank.")
            return
        }

        try {
            // Build OpenAI-compatible speech request body
            val jsonPayload = JSONObject().apply {
                put("model", model)
                put("input", text)
                put("voice", voice)
            }
            val requestBody = jsonPayload.toString().toRequestBody("application/json".toMediaType())

            val requestBuilder = Request.Builder()
                .url(apiUrl)
                .post(requestBody)

            if (apiKey.isNotBlank()) {
                requestBuilder.addHeader("Authorization", "Bearer $apiKey")
            }

            val request = requestBuilder.build()
            val response = httpClient.newCall(request).execute()

            if (response.isSuccessful) {
                val audioBytes = response.body?.bytes() ?: throw Exception("Response body is null")
                
                // Save temporary audio file to app cache directory
                val tempFile = File(context.cacheDirs(), "aiko_temp_tts.mp3")
                FileOutputStream(tempFile).use { fos ->
                    fos.write(audioBytes)
                }

                // Play the temporary file using MediaPlayer
                withContext(Dispatchers.Main) {
                    mediaPlayer = MediaPlayer().apply {
                        setDataSource(tempFile.absolutePath)
                        prepare()
                        start()
                        setOnCompletionListener {
                            it.release()
                            if (mediaPlayer == it) {
                                mediaPlayer = null
                            }
                        }
                    }
                }
            } else {
                Log.e("AikoVocalizer", "Custom TTS API request failed: Code ${response.code}. Message: ${response.message}")
            }
        } catch (e: Exception) {
            Log.e("AikoVocalizer", "Error calling custom TTS API: ${e.message}", e)
        }
    }

    // Helper to safely fetch context cache dirs
    private fun Context.cacheDirs(): File {
        return this.cacheDir ?: File(this.filesDir, "cache").apply { mkdirs() }
    }

    /** Called when the application/Activity is destroyed to release resources. */
    fun release() {
        try {
            stop()
            nativeTts?.shutdown()
            nativeTts = null
        } catch (e: Exception) {
            Log.e("AikoVocalizer", "Error shutting down native TextToSpeech: ${e.message}")
        }
    }
}
