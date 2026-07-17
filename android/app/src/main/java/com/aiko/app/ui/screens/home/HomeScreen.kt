package com.aiko.app.ui.screens.home

import android.util.Log
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.aiko.app.data.local.AikoPrefs
import com.aiko.app.data.local.MessageEntity
import com.aiko.app.data.repository.ChatRepository
import com.aiko.app.domain.EmotionEngine
import com.aiko.app.ui.components.AbstractPosterCanvas
import com.aiko.app.ui.components.AikoAvatar
import com.aiko.app.ui.components.AmbientBubble
import com.aiko.app.ui.components.CompanionInputBar
import com.aiko.app.ui.components.CompanionTopCard
import com.aiko.app.ui.components.NeurochemPanel
import com.aiko.app.ui.components.SubtitleBar
import com.aiko.app.ui.theme.AikoColors
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

// Clean XML tags and system tool codes for subtitle bar presentation
private val tagCleanerRegex = Regex("""<(think|emotion|thought|relevant_memory_context|current_visual_awareness)>.*?</\1>|<.*?>|\[(?:SCAN|MCP|TASK|BIO_REGISTER|GAME|OPEN|TYPE|CLICK|PRESS|WAIT|WALLPAPER|WEATHER|MUSIC|LETTER|VTS_BG|IMAGE|RECALL|LATEX|REFLECTIVE_STATE|GIF)[^\]]*?\]""", RegexOption.IGNORE_CASE)

private fun cleanText(value: String): String {
    return value.replace(tagCleanerRegex, "").trim()
}

@Composable
fun HomeScreen(
    chatRepository: ChatRepository,
    aikoPrefs: AikoPrefs,
    emotionEngine: EmotionEngine,
    onOpenSettings: () -> Unit,
    onSwipeUp: () -> Unit,
    modifier: Modifier = Modifier
) {
    val currentEmotion by chatRepository.currentEmotion.collectAsState()
    val currentAmplitude by chatRepository.currentAmplitude.collectAsState()
    val avatarMode by aikoPrefs.avatarModeFlow.collectAsState(initial = "WebView")
    val messages by chatRepository.getMessages("default").collectAsState(initial = emptyList())
    
    val streaming by chatRepository.streamingText.collectAsState()
    val thinking by chatRepository.isThinking.collectAsState()
    val proactiveMessage by chatRepository.proactiveMessage.collectAsState(initial = null)

    LaunchedEffect(proactiveMessage) {
        if (proactiveMessage != null) {
            delay(8000)
            chatRepository.proactiveMessage.value = null
        }
    }

    val scope = rememberCoroutineScope()
    val dominantEmotion = emotionEngine.determineDominantEmotion(currentEmotion)

    // Dynamic weather caching and loading directly via wttr.in
    var weatherText by remember { mutableStateOf("") }
    LaunchedEffect(Unit) {
        while (true) {
            withContext(Dispatchers.IO) {
                try {
                    val client = okhttp3.OkHttpClient()
                    val request = okhttp3.Request.Builder()
                        .url("https://wttr.in/?format=3")
                        .header("User-Agent", "curl/7.64.1")
                        .build()
                    client.newCall(request).execute().use { response ->
                        if (response.isSuccessful) {
                            val result = response.body?.string() ?: ""
                            weatherText = if (result.contains(":")) {
                                result.substringAfter(":").trim()
                            } else {
                                result.trim()
                            }
                        }
                    }
                } catch (e: Exception) {
                    Log.e("HomeScreen", "Weather fetch error: ${e.message}")
                    if (weatherText.isEmpty()) {
                        weatherText = "Clear · 68°F" // Fallback
                    }
                }
            }
            delay(1800000) // update every 30 minutes
        }
    }

    // Dialogue calculation
    val lastAikoMessage = remember(messages) {
        messages.lastOrNull { it.role == "aiko" }?.content?.let { cleanText(it) } ?: ""
    }
    val activeLine = if (streaming.isNotEmpty()) streaming else lastAikoMessage

    // Activity state
    val currentActivity = when {
        thinking -> "thinking..."
        currentAmplitude > 0.05f -> "speaking..."
        else -> "observing screen"
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .pointerInput(Unit) {
                detectVerticalDragGestures { change, dragAmount ->
                    // Trigger swipe up to transition into full chat log view
                    if (dragAmount < -25f) {
                        onSwipeUp()
                    }
                }
            }
    ) {
        // Layer 1: Abstract Poster Canvas background
        AbstractPosterCanvas(modifier = Modifier.fillMaxSize())

        // Layer 2: Live2D Avatar / Fallback Core (Full bleed, bottom-right offset)
        AikoAvatar(
            emotionState = currentEmotion,
            dominantEmotion = dominantEmotion,
            isTyping = thinking,
            isSpeaking = currentAmplitude > 0.05f,
            amplitude = currentAmplitude,
            avatarMode = avatarMode,
            size = Dp.Unspecified,
            modifier = Modifier.fillMaxSize()
        )

        // Proactive Ambient Bubble callout next to the avatar
        proactiveMessage?.let { text ->
            AmbientBubble(
                text = text,
                modifier = Modifier
                    .align(Alignment.Center)
                    .offset(y = (-80).dp)
            )
        }

        // Layer 3: Top-left Status Overlay (Time, Weather, Mood, Activity)
        CompanionTopCard(
            dominantEmotion = dominantEmotion,
            weatherText = weatherText,
            currentActivity = currentActivity,
            modifier = Modifier
                .align(Alignment.TopStart)
                .padding(start = 16.dp, top = 48.dp)
        )

        // Layer 4: Top-right Telemetry Overlay (6 neurochemical bars)
        NeurochemPanel(
            emotionState = currentEmotion,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(end = 16.dp, top = 48.dp)
        )

        // Layer 5: Settings Gear floating action circle
        IconButton(
            onClick = onOpenSettings,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(end = 16.dp, top = 400.dp) // Offset below neuro bars
                .size(40.dp)
                .clip(CircleShape)
                .background(Color(0xFF35223D).copy(alpha = 0.5f))
                .border(1.dp, Color(0x0FFFFFFF), CircleShape)
        ) {
            Icon(
                imageVector = Icons.Default.Settings,
                contentDescription = "Settings",
                tint = AikoColors.Accent,
                modifier = Modifier.size(20.dp)
            )
        }

        // Layer 6: Subtitle Dialogue Box (glassmorphic, typwriter, skip action)
        SubtitleBar(
            speaker = "Aiko",
            text = activeLine,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(horizontal = 16.dp)
                .padding(bottom = 100.dp)
        )

        // Layer 7: Minimal input dock
        CompanionInputBar(
            onSend = { prompt ->
                if (prompt.isEmpty() || thinking) return@CompanionInputBar
                chatRepository.isThinking.value = true
                chatRepository.streamingText.value = ""
                scope.launch {
                    var full = ""
                    runCatching {
                        chatRepository.streamAikoResponse("default", prompt, null).collect { token ->
                            full += token
                            chatRepository.streamingText.value = cleanText(full)
                        }
                    }.onFailure { err ->
                        full = "Connection sync issues. Let's try linked network setup again."
                        chatRepository.streamingText.value = full
                    }
                    chatRepository.finalizeAikoResponse("default", full)
                    chatRepository.streamingText.value = ""
                    chatRepository.isThinking.value = false
                }
            },
            onMicTap = {
                // STT WebSocket trigger link
                scope.launch {
                    val desktopConnected = aikoPrefs.desktopConnectedFlow.first()
                    if (desktopConnected) {
                        // Notify server to start speech listening loop
                        val payload = org.json.JSONObject().apply {
                            put("type", "listen")
                        }
                        chatRepository.sendRawMessage(payload.toString())
                    }
                }
            },
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(horizontal = 16.dp)
                .padding(bottom = 24.dp)
        )
    }
}
