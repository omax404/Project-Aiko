package com.aiko.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.aiko.app.data.repository.ChatRepository
import com.aiko.app.domain.EmotionEngine
import com.aiko.app.ui.screens.chat.ChatScreen
import com.aiko.app.ui.screens.settings.SettingsScreen
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTheme
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    @Inject lateinit var chatRepository: ChatRepository
    @Inject lateinit var emotionEngine: EmotionEngine
    @Inject lateinit var prefs: com.aiko.app.data.local.AikoPrefs

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen().setKeepOnScreenCondition { false }
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            var settingsOpen by rememberSaveable { mutableStateOf(false) }
            val themeAccentColor by prefs.themeAccentColorFlow.collectAsState(initial = "#C9A8D9")
            val chatFont by prefs.chatFontFlow.collectAsState(initial = "system_sans")
            val chatTextSize by prefs.chatTextSizeFlow.collectAsState(initial = 1.0f)

            AikoTheme(
                accentColorHex = themeAccentColor,
                fontKey = chatFont,
                textScale = chatTextSize
            ) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = AikoColors.Background
                ) {
                    if (settingsOpen) {
                        SettingsScreen(chatRepository, prefs, onBack = { settingsOpen = false })
                    } else {
                        ChatScreen(chatRepository, emotionEngine, prefs, onOpenSettings = { settingsOpen = true })
                    }
                }
            }
        }
    }
}
