package com.aiko.app.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.emptyPreferences
import androidx.datastore.preferences.core.stringPreferencesKey
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
    }

    val apiKeyFlow: Flow<String> = dataStore.data
        .catch { exception ->
            if (exception is IOException) {
                emit(emptyPreferences())
            } else {
                throw exception
            }
        }.map { preferences ->
            preferences[PreferencesKeys.API_KEY] ?: ""
        }

    val personalityModeFlow: Flow<String> = dataStore.data
        .map { preferences ->
            preferences[PreferencesKeys.PERSONALITY_MODE] ?: "Warm"
        }

    val userNameFlow: Flow<String> = dataStore.data
        .map { preferences ->
            preferences[PreferencesKeys.USER_NAME] ?: "User"
        }

    val themeFlow: Flow<String> = dataStore.data
        .map { preferences ->
            preferences[PreferencesKeys.THEME] ?: "GlassDark"
        }

    val voiceEnabledFlow: Flow<Boolean> = dataStore.data
        .map { preferences ->
            preferences[PreferencesKeys.VOICE_ENABLED] ?: false
        }

    val modelChoiceFlow: Flow<String> = dataStore.data
        .map { preferences ->
            preferences[PreferencesKeys.MODEL_CHOICE] ?: "gemini-1.5-flash"
        }

    val onboardingDoneFlow: Flow<Boolean> = dataStore.data
        .map { preferences ->
            preferences[PreferencesKeys.ONBOARDING_DONE] ?: false
        }

    val desktopConnectedFlow: Flow<Boolean> = dataStore.data
        .map { preferences ->
            preferences[PreferencesKeys.DESKTOP_CONNECTED] ?: false
        }

    val desktopUrlFlow: Flow<String> = dataStore.data
        .map { preferences ->
            preferences[PreferencesKeys.DESKTOP_URL] ?: "http://10.0.2.2:8000"
        }

    suspend fun setApiKey(apiKey: String) {
        dataStore.edit { preferences ->
            preferences[PreferencesKeys.API_KEY] = apiKey
        }
    }

    suspend fun setPersonalityMode(mode: String) {
        dataStore.edit { preferences ->
            preferences[PreferencesKeys.PERSONALITY_MODE] = mode
        }
    }

    suspend fun setUserName(name: String) {
        dataStore.edit { preferences ->
            preferences[PreferencesKeys.USER_NAME] = name
        }
    }

    suspend fun setTheme(theme: String) {
        dataStore.edit { preferences ->
            preferences[PreferencesKeys.THEME] = theme
        }
    }

    suspend fun setVoiceEnabled(enabled: Boolean) {
        dataStore.edit { preferences ->
            preferences[PreferencesKeys.VOICE_ENABLED] = enabled
        }
    }

    suspend fun setModelChoice(model: String) {
        dataStore.edit { preferences ->
            preferences[PreferencesKeys.MODEL_CHOICE] = model
        }
    }

    suspend fun setOnboardingDone(done: Boolean) {
        dataStore.edit { preferences ->
            preferences[PreferencesKeys.ONBOARDING_DONE] = done
        }
    }

    suspend fun setDesktopConnected(connected: Boolean) {
        dataStore.edit { preferences ->
            preferences[PreferencesKeys.DESKTOP_CONNECTED] = connected
        }
    }

    suspend fun setDesktopUrl(url: String) {
        dataStore.edit { preferences ->
            preferences[PreferencesKeys.DESKTOP_URL] = url
        }
    }
}
