package com.aiko.app

import android.os.Bundle
import android.content.Intent
import android.util.Log
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
import com.aiko.app.ui.screens.home.HomeScreen
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
            var currentScreen by rememberSaveable { mutableStateOf("home") }
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
                    when (currentScreen) {
                        "settings" -> {
                            SettingsScreen(chatRepository, prefs, onBack = { currentScreen = "home" })
                        }
                        "chat" -> {
                            ChatScreen(
                                chatRepository = chatRepository,
                                emotionEngine = emotionEngine,
                                aikoPrefs = prefs,
                                onOpenSettings = { currentScreen = "settings" }
                            )
                            androidx.activity.compose.BackHandler {
                                currentScreen = "home"
                            }
                        }
                        else -> {
                            HomeScreen(
                                chatRepository = chatRepository,
                                aikoPrefs = prefs,
                                emotionEngine = emotionEngine,
                                onOpenSettings = { currentScreen = "settings" },
                                onSwipeUp = { currentScreen = "chat" }
                            )
                        }
                    }
                }
            }
        }
        
        // Phase 5: Request push notifications permission on Android 13+
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.TIRAMISU) {
            requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 101)
        }
    }

    override fun onStart() {
        super.onStart()
        AikoConnectionService.isAppInForeground = true
        try {
            val intent = Intent(this, AikoConnectionService::class.java)
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                startForegroundService(intent)
            } else {
                startService(intent)
            }
        } catch (e: Exception) {
            Log.e("MainActivity", "Failed to start AikoConnectionService: ${e.message}")
        }
    }

    override fun onStop() {
        super.onStop()
        AikoConnectionService.isAppInForeground = false
    }
}
