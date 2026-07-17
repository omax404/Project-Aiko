package com.aiko.app.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.map
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "aiko_preferences")

@Singleton
class AikoPrefs @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val dataStore = context.dataStore

    private object PreferencesKeys {
        val API_KEY = stringPreferencesKey("api_key")
        val PERSONALITY_MODE = stringPreferencesKey("personality_mode")
        val USER_NAME = stringPreferencesKey("user_name")
        val THEME = stringPreferencesKey("theme")
        val VOICE_ENABLED = booleanPreferencesKey("voice_enabled")
        val MODEL_CHOICE = stringPreferencesKey("model_choice")
        val ONBOARDING_DONE = booleanPreferencesKey("onboarding_done")
        val DESKTOP_CONNECTED = booleanPreferencesKey("desktop_connected")
        val DESKTOP_URL = stringPreferencesKey("desktop_url")

        // Connection & Appearance
        val CONNECTION_MODE = stringPreferencesKey("connection_mode")
        val THEME_ACCENT_COLOR = stringPreferencesKey("theme_accent_color")
        val AVATAR_MODE = stringPreferencesKey("avatar_mode")
        val LAST_SYNC_TIMESTAMP = longPreferencesKey("last_sync_timestamp")
        
        val JITTER_INTENSITY = floatPreferencesKey("jitter_intensity")
        val TEAR_INTENSITY = floatPreferencesKey("tear_intensity")
        val LEAN_INTENSITY = floatPreferencesKey("lean_intensity")
        val BLUSH_INTENSITY = floatPreferencesKey("blush_intensity")
        val POUT_INTENSITY = floatPreferencesKey("pout_intensity")
        val BOBA_INTENSITY = floatPreferencesKey("boba_intensity")
        val OXYTOCIN_INTENSITY = floatPreferencesKey("oxytocin_intensity")
        val MELATONIN_INTENSITY = floatPreferencesKey("melatonin_intensity")

        val CHAT_FONT = stringPreferencesKey("chat_font")
        val CHAT_WALLPAPER = stringPreferencesKey("chat_wallpaper")
        val CHAT_WALLPAPER_URI = stringPreferencesKey("chat_wallpaper_uri")
        val CHAT_BUBBLE_STYLE = stringPreferencesKey("chat_bubble_style")
        val CHAT_TEXT_SIZE = floatPreferencesKey("chat_text_size")

        // Vocalization Settings
        val TTS_ENGINE = stringPreferencesKey("tts_engine")
        val TTS_API_URL = stringPreferencesKey("tts_api_url")
        val TTS_API_KEY = stringPreferencesKey("tts_api_key")
        val TTS_API_VOICE = stringPreferencesKey("tts_api_voice")
        val TTS_API_MODEL = stringPreferencesKey("tts_api_model")
    }

    /** Helper to map DataStore keys to safe, catch-protected Flow streams */
    private fun <T> safeFlow(key: Preferences.Key<T>, defaultValue: T): Flow<T> {
        return dataStore.data
            .catch { exception ->
                if (exception is IOException) {
                    emit(emptyPreferences())
                } else {
                    throw exception
                }
            }
            .map { preferences ->
                preferences[key] ?: defaultValue
            }
    }

    val apiKeyFlow: Flow<String> = safeFlow(PreferencesKeys.API_KEY, "")
    val personalityModeFlow: Flow<String> = safeFlow(PreferencesKeys.PERSONALITY_MODE, "Warm")
    val userNameFlow: Flow<String> = safeFlow(PreferencesKeys.USER_NAME, "User")
    val themeFlow: Flow<String> = safeFlow(PreferencesKeys.THEME, "GlassDark")
    val voiceEnabledFlow: Flow<Boolean> = safeFlow(PreferencesKeys.VOICE_ENABLED, false)
    val modelChoiceFlow: Flow<String> = safeFlow(PreferencesKeys.MODEL_CHOICE, "gemini-1.5-flash")
    val onboardingDoneFlow: Flow<Boolean> = safeFlow(PreferencesKeys.ONBOARDING_DONE, false)
    val desktopConnectedFlow: Flow<Boolean> = safeFlow(PreferencesKeys.DESKTOP_CONNECTED, false)
    val desktopUrlFlow: Flow<String> = safeFlow(PreferencesKeys.DESKTOP_URL, "http://10.0.2.2:8000")

    val connectionModeFlow: Flow<String> = safeFlow(PreferencesKeys.CONNECTION_MODE, "Link to Desktop")
    val themeAccentColorFlow: Flow<String> = safeFlow(PreferencesKeys.THEME_ACCENT_COLOR, "#C9A8D9")
    val avatarModeFlow: Flow<String> = safeFlow(PreferencesKeys.AVATAR_MODE, "WebView")
    val lastSyncTimestampFlow: Flow<Long> = safeFlow(PreferencesKeys.LAST_SYNC_TIMESTAMP, 0L)

    val jitterIntensityFlow: Flow<Float> = safeFlow(PreferencesKeys.JITTER_INTENSITY, 0.4f)
    val tearIntensityFlow: Flow<Float> = safeFlow(PreferencesKeys.TEAR_INTENSITY, 1.0f)
    val leanIntensityFlow: Flow<Float> = safeFlow(PreferencesKeys.LEAN_INTENSITY, 1.0f)
    val blushIntensityFlow: Flow<Float> = safeFlow(PreferencesKeys.BLUSH_INTENSITY, 1.0f)
    val poutIntensityFlow: Flow<Float> = safeFlow(PreferencesKeys.POUT_INTENSITY, 1.0f)
    val bobaIntensityFlow: Flow<Float> = safeFlow(PreferencesKeys.BOBA_INTENSITY, 1.0f)
    val oxytocinIntensityFlow: Flow<Float> = safeFlow(PreferencesKeys.OXYTOCIN_INTENSITY, 1.0f)
    val melatoninIntensityFlow: Flow<Float> = safeFlow(PreferencesKeys.MELATONIN_INTENSITY, 1.0f)

    val chatFontFlow: Flow<String> = safeFlow(PreferencesKeys.CHAT_FONT, "system_sans")
    val chatWallpaperFlow: Flow<String> = safeFlow(PreferencesKeys.CHAT_WALLPAPER, "default")
    val chatWallpaperUriFlow: Flow<String> = safeFlow(PreferencesKeys.CHAT_WALLPAPER_URI, "")
    val chatBubbleStyleFlow: Flow<String> = safeFlow(PreferencesKeys.CHAT_BUBBLE_STYLE, "default")
    val chatTextSizeFlow: Flow<Float> = safeFlow(PreferencesKeys.CHAT_TEXT_SIZE, 1.0f)

    // Vocalization Settings flows
    val ttsEngineFlow: Flow<String> = safeFlow(PreferencesKeys.TTS_ENGINE, "native")
    val ttsApiUrlFlow: Flow<String> = safeFlow(PreferencesKeys.TTS_API_URL, "https://api.openai.com/v1/audio/speech")
    val ttsApiKeyFlow: Flow<String> = safeFlow(PreferencesKeys.TTS_API_KEY, "")
    val ttsApiVoiceFlow: Flow<String> = safeFlow(PreferencesKeys.TTS_API_VOICE, "alloy")
    val ttsApiModelFlow: Flow<String> = safeFlow(PreferencesKeys.TTS_API_MODEL, "tts-1")

    suspend fun setApiKey(apiKey: String) = dataStore.edit { it[PreferencesKeys.API_KEY] = apiKey }
    suspend fun setPersonalityMode(mode: String) = dataStore.edit { it[PreferencesKeys.PERSONALITY_MODE] = mode }
    suspend fun setUserName(name: String) = dataStore.edit { it[PreferencesKeys.USER_NAME] = name }
    suspend fun setTheme(theme: String) = dataStore.edit { it[PreferencesKeys.THEME] = theme }
    suspend fun setVoiceEnabled(enabled: Boolean) = dataStore.edit { it[PreferencesKeys.VOICE_ENABLED] = enabled }
    suspend fun setModelChoice(model: String) = dataStore.edit { it[PreferencesKeys.MODEL_CHOICE] = model }
    suspend fun setOnboardingDone(done: Boolean) = dataStore.edit { it[PreferencesKeys.ONBOARDING_DONE] = done }
    suspend fun setDesktopConnected(connected: Boolean) = dataStore.edit { it[PreferencesKeys.DESKTOP_CONNECTED] = connected }
    suspend fun setDesktopUrl(url: String) = dataStore.edit { it[PreferencesKeys.DESKTOP_URL] = url }

    suspend fun setConnectionMode(mode: String) = dataStore.edit { it[PreferencesKeys.CONNECTION_MODE] = mode }
    suspend fun setThemeAccentColor(color: String) = dataStore.edit { it[PreferencesKeys.THEME_ACCENT_COLOR] = color }
    suspend fun setAvatarMode(mode: String) = dataStore.edit { it[PreferencesKeys.AVATAR_MODE] = mode }
    suspend fun setLastSyncTimestamp(timestamp: Long) = dataStore.edit { it[PreferencesKeys.LAST_SYNC_TIMESTAMP] = timestamp }

    suspend fun setJitterIntensity(v: Float) = dataStore.edit { it[PreferencesKeys.JITTER_INTENSITY] = v }
    suspend fun setTearIntensity(v: Float) = dataStore.edit { it[PreferencesKeys.TEAR_INTENSITY] = v }
    suspend fun setLeanIntensity(v: Float) = dataStore.edit { it[PreferencesKeys.LEAN_INTENSITY] = v }
    suspend fun setBlushIntensity(v: Float) = dataStore.edit { it[PreferencesKeys.BLUSH_INTENSITY] = v }
    suspend fun setPoutIntensity(v: Float) = dataStore.edit { it[PreferencesKeys.POUT_INTENSITY] = v }
    suspend fun setBobaIntensity(v: Float) = dataStore.edit { it[PreferencesKeys.BOBA_INTENSITY] = v }
    suspend fun setOxytocinIntensity(v: Float) = dataStore.edit { it[PreferencesKeys.OXYTOCIN_INTENSITY] = v }
    suspend fun setMelatoninIntensity(v: Float) = dataStore.edit { it[PreferencesKeys.MELATONIN_INTENSITY] = v }

    suspend fun setChatFont(font: String) = dataStore.edit { it[PreferencesKeys.CHAT_FONT] = font }
    suspend fun setChatWallpaper(wallpaper: String) = dataStore.edit { it[PreferencesKeys.CHAT_WALLPAPER] = wallpaper }
    suspend fun setChatWallpaperUri(uri: String) = dataStore.edit { it[PreferencesKeys.CHAT_WALLPAPER_URI] = uri }
    suspend fun setChatBubbleStyle(style: String) = dataStore.edit { it[PreferencesKeys.CHAT_BUBBLE_STYLE] = style }
    suspend fun setChatTextSize(size: Float) = dataStore.edit { it[PreferencesKeys.CHAT_TEXT_SIZE] = size }

    // Vocalization Settings setters
    suspend fun setTtsEngine(engine: String) = dataStore.edit { it[PreferencesKeys.TTS_ENGINE] = engine }
    suspend fun setTtsApiUrl(url: String) = dataStore.edit { it[PreferencesKeys.TTS_API_URL] = url }
    suspend fun setTtsApiKey(key: String) = dataStore.edit { it[PreferencesKeys.TTS_API_KEY] = key }
    suspend fun setTtsApiVoice(voice: String) = dataStore.edit { it[PreferencesKeys.TTS_API_VOICE] = voice }
    suspend fun setTtsApiModel(model: String) = dataStore.edit { it[PreferencesKeys.TTS_API_MODEL] = model }
}
