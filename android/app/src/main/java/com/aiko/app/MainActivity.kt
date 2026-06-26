package com.aiko.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Analytics
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.aiko.app.data.local.AikoPrefs
import com.aiko.app.data.repository.ChatRepository
import com.aiko.app.domain.EmotionEngine
import com.aiko.app.ui.components.FloatingNavBar
import com.aiko.app.ui.screens.bond.BondScreen
import com.aiko.app.ui.screens.chat.ChatScreen
import com.aiko.app.ui.screens.home.HomeScreen
import com.aiko.app.ui.screens.memory.MemoryScreen
import com.aiko.app.ui.screens.onboarding.OnboardingScreen
import com.aiko.app.ui.screens.settings.SettingsScreen
import com.aiko.app.ui.theme.AikoTheme
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject
    lateinit var aikoPrefs: AikoPrefs

    @Inject
    lateinit var chatRepository: ChatRepository

    @Inject
    lateinit var emotionEngine: EmotionEngine

    override fun onCreate(savedInstanceState: Bundle?) {
        // Install instant splash screen
        installSplashScreen()
        super.onCreate(savedInstanceState)

        // Target SDK 36 edge-to-edge
        enableEdgeToEdge()

        setContent {
            AikoTheme {
                val onboardingDone by aikoPrefs.onboardingDoneFlow.collectAsState(initial = null)
                var currentScreen by remember { mutableStateOf("home") }

                if (onboardingDone == null) {
                    // Loading placeholder
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding()
                    )
                } else if (onboardingDone == false) {
                    OnboardingScreen(
                        aikoPrefs = aikoPrefs,
                        onOnboardingComplete = { /* Flow updates Preference flow */ }
                    )
                } else {
                    Scaffold(
                        modifier = Modifier.fillMaxSize(),
                        containerColor = Color.Transparent,
                        bottomBar = {
                            FloatingNavBar(
                                selectedRoute = currentScreen,
                                items = listOf(
                                    "home" to Icons.Default.Home,
                                    "chat" to Icons.Default.Chat,
                                    "bond" to Icons.Default.Analytics,
                                    "memory" to Icons.Default.Info,
                                    "settings" to Icons.Default.Settings
                                ),
                                onItemSelected = { currentScreen = it }
                            )
                        }
                    ) { innerPadding ->
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(innerPadding)
                        ) {
                            AnimatedContent(
                                targetState = currentScreen,
                                transitionSpec = {
                                    fadeIn(animationSpec = androidx.compose.animation.core.tween(300)) togetherWith
                                            fadeOut(animationSpec = androidx.compose.animation.core.tween(300))
                                },
                                label = "screenTransition"
                            ) { target ->
                                when (target) {
                                    "home" -> HomeScreen(
                                        chatRepository = chatRepository,
                                        aikoPrefs = aikoPrefs,
                                        emotionEngine = emotionEngine
                                    )
                                    "chat" -> ChatScreen(
                                        chatRepository = chatRepository,
                                        emotionEngine = emotionEngine
                                    )
                                    "bond" -> BondScreen(
                                        chatRepository = chatRepository
                                    )
                                    "memory" -> MemoryScreen(
                                        chatRepository = chatRepository
                                    )
                                    "settings" -> SettingsScreen(
                                        chatRepository = chatRepository,
                                        aikoPrefs = aikoPrefs
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
