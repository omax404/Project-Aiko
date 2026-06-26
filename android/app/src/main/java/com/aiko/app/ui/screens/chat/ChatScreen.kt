package com.aiko.app.ui.screens.chat

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aiko.app.data.local.MessageEntity
import com.aiko.app.data.repository.ChatRepository
import com.aiko.app.domain.EmotionEngine
import com.aiko.app.ui.components.AbstractPosterCanvas
import com.aiko.app.ui.components.AikoAvatar
import com.aiko.app.ui.components.MessageBubble
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.flow.onCompletion
import kotlinx.coroutines.launch
import kotlin.random.Random

@Composable
fun ChatScreen(
    chatRepository: ChatRepository,
    emotionEngine: EmotionEngine,
    modifier: Modifier = Modifier
) {
    val scope = rememberCoroutineScope()
    val haptic = LocalHapticFeedback.current
    val listState = rememberLazyListState()

    val messages by chatRepository.getMessages("default").collectAsState(initial = emptyList())
    val currentEmotion by chatRepository.currentEmotion.collectAsState()
    val dominantEmotion = emotionEngine.determineDominantEmotion(currentEmotion)

    var textInput by remember { mutableStateOf("") }
    var isAikoTyping by remember { mutableStateOf(false) }
    var streamingMessageText by remember { mutableStateOf("") }
    
    // Auto-scroll list when message count changes
    LaunchedEffect(messages.size, streamingMessageText) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(messages.size - 1)
        }
    }

    val activeColor = when (dominantEmotion) {
        "happy" -> AikoColors.HappyGold
        "flustered" -> AikoColors.FlusteredPink
        "devoted" -> AikoColors.DevotedViolet
        "calm" -> AikoColors.CalmBlue
        "sad" -> AikoColors.SadGrey
        "worried" -> AikoColors.WorriedOrange
        "jealous" -> AikoColors.JealousGreen
        else -> AikoColors.Primary
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(AikoColors.BackgroundLight)
    ) {
        AbstractPosterCanvas(modifier = Modifier.fillMaxSize())

        Column(modifier = Modifier.fillMaxSize()) {
            
            // Top Conversation Header
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color.White)
                    .border(2.dp, AikoColors.SurfaceDark)
                    .padding(top = 40.dp, bottom = 12.dp, start = 20.dp, end = 20.dp),
                contentAlignment = Alignment.CenterStart
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    AikoAvatar(
                        emotionState = currentEmotion,
                        dominantEmotion = dominantEmotion,
                        isTyping = isAikoTyping,
                        isSpeaking = false,
                        size = 56.dp
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Column {
                        Text(
                            text = "AIKO",
                            style = AikoTypography.titleLarge.copy(
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                        )
                        Text(
                            text = if (isAikoTyping) "typing thoughts..." else dominantEmotion.uppercase(),
                            style = AikoTypography.labelMedium.copy(
                                color = activeColor,
                                fontWeight = FontWeight.Bold,
                                fontSize = 11.sp
                            )
                        )
                    }
                }
            }

            // Chat Messages Room
            LazyColumn(
                state = listState,
                modifier = Modifier
                    .weight(1f)
                    .padding(horizontal = 16.dp)
            ) {
                if (messages.isEmpty() && streamingMessageText.isEmpty()) {
                    item {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(top = 100.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "Say something, I've been waiting 💕",
                                style = AikoTypography.bodyLarge.copy(
                                    color = AikoColors.TextSecondary,
                                    fontSize = 15.sp,
                                    textAlign = TextAlign.Center
                                )
                            )
                        }
                    }
                }

                itemsIndexed(messages) { index, msg ->
                    // Stream ONLY the last message if it was generated now
                    val shouldStream = index == messages.size - 1 && msg.role == "aiko"
                    MessageBubble(
                        message = msg,
                        shouldStream = shouldStream
                    )
                }

                // Streaming temporary card
                if (streamingMessageText.isNotEmpty()) {
                    item {
                        MessageBubble(
                            message = MessageEntity(
                                conversationId = "default",
                                role = "aiko",
                                content = streamingMessageText,
                                emotionTag = dominantEmotion
                            ),
                            shouldStream = false
                        )
                    }
                }

                // Standard clean Typing Dots
                if (isAikoTyping && streamingMessageText.isEmpty()) {
                    item {
                        Row(
                            modifier = Modifier
                                .padding(vertical = 8.dp)
                                .clip(RoundedCornerShape(12.dp))
                                .background(Color.White)
                                .border(2.dp, AikoColors.SurfaceDark, RoundedCornerShape(12.dp))
                                .padding(horizontal = 14.dp, vertical = 8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "Aiko is thinking...",
                                style = AikoTypography.labelMedium.copy(color = AikoColors.TextPrimary)
                            )
                        }
                    }
                }

                item { Spacer(modifier = Modifier.height(80.dp)) } // navigation padding
            }

            // Input Bar
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color.White)
                    .border(2.dp, AikoColors.SurfaceDark)
                    .padding(horizontal = 16.dp, vertical = 12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    OutlinedTextField(
                        value = textInput,
                        onValueChange = { textInput = it },
                        placeholder = { Text("Write me a compliment... 💕") },
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = AikoColors.SurfaceDark,
                            unfocusedBorderColor = AikoColors.SurfaceDark,
                            focusedTextColor = AikoColors.TextPrimary,
                            unfocusedTextColor = AikoColors.TextPrimary
                        ),
                        shape = RoundedCornerShape(24.dp),
                        modifier = Modifier.weight(1f)
                    )
                    Spacer(modifier = Modifier.width(10.dp))
                    
                    // Glassmorphic neon send button
                    IconButton(
                        onClick = {
                            val prompt = textInput.trim()
                            if (prompt.isNotEmpty()) {
                                textInput = ""
                                isAikoTyping = true
                                haptic.performHapticFeedback(HapticFeedbackType.LongPress)

                                scope.launch {
                                    try {
                                        val stream = chatRepository.streamAikoResponse("default", prompt)
                                        var fullAikoResponse = ""
                                        
                                        // Introduce soft visual lag for natural pacing
                                        kotlinx.coroutines.delay(400L + Random.nextLong(0, 300L))
                                        isAikoTyping = false

                                        stream.onCompletion {
                                            scope.launch {
                                                chatRepository.finalizeAikoResponse("default", fullAikoResponse)
                                                streamingMessageText = ""
                                            }
                                        }.collect { chunk ->
                                            val textPart = chunk.text ?: ""
                                            fullAikoResponse += textPart
                                            streamingMessageText = fullAikoResponse
                                        }
                                    } catch (e: Exception) {
                                        isAikoTyping = false
                                        streamingMessageText = ""
                                        // Save elegant character error
                                        chatRepository.finalizeAikoResponse(
                                            "default",
                                            "[EMO:worried]\nSomething feels off... I can't seem to connect right now."
                                        )
                                    }
                                }
                            }
                        },
                        colors = IconButtonDefaults.iconButtonColors(
                            containerColor = AikoColors.PrimaryRed
                        ),
                        modifier = Modifier
                            .size(52.dp)
                            .clip(CircleShape)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Send,
                            contentDescription = "Send",
                            tint = Color.White
                        )
                    }
                }
                Spacer(modifier = Modifier.height(10.dp))
            }
        }
    }
}
