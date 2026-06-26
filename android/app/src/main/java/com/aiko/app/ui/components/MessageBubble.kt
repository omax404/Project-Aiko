package com.aiko.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aiko.app.data.local.MessageEntity
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography
import kotlinx.coroutines.delay

@Composable
fun MessageBubble(
    message: MessageEntity,
    modifier: Modifier = Modifier,
    shouldStream: Boolean = false
) {
    val isUser = message.role == "user"
    val haptic = LocalHapticFeedback.current
    var displayedText by remember { mutableStateOf("") }

    // Character streaming for premium feel
    LaunchedEffect(message.content) {
        if (shouldStream && !isUser) {
            displayedText = ""
            message.content.forEach { char ->
                displayedText += char
                // Soft typewriter tactile haptics
                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                delay(16L)
            }
        } else {
            displayedText = message.content
        }
    }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        contentAlignment = if (isUser) Alignment.CenterEnd else Alignment.CenterStart
    ) {
        Row(
            verticalAlignment = Alignment.Bottom,
            modifier = Modifier.fillMaxWidth(0.85f)
        ) {
            if (isUser) {
                Spacer(modifier = Modifier.weight(1f))
            }

            Column(
                horizontalAlignment = if (isUser) Alignment.End else Alignment.Start
            ) {
                // Emotion Tag pill (Aiko only)
                if (!isUser && message.emotionTag != null) {
                    EmotionBadge(
                        emotion = message.emotionTag,
                        modifier = Modifier.padding(bottom = 4.dp)
                    )
                }

                // Bubble card
                Box(
                    modifier = Modifier
                        .clip(
                            RoundedCornerShape(
                                topStart = 20.dp,
                                topEnd = 20.dp,
                                bottomStart = if (isUser) 20.dp else 4.dp,
                                bottomEnd = if (isUser) 4.dp else 20.dp
                            )
                        )
                        .background(
                            if (isUser) AikoColors.SurfaceDark else Color.White
                        )
                        .border(
                            width = if (isUser) 0.dp else 2.dp,
                            color = if (isUser) Color.Transparent else AikoColors.SurfaceDark,
                            shape = RoundedCornerShape(
                                topStart = 20.dp,
                                topEnd = 20.dp,
                                bottomStart = if (isUser) 20.dp else 4.dp,
                                bottomEnd = if (isUser) 4.dp else 20.dp
                            )
                        )
                        .padding(horizontal = 16.dp, vertical = 12.dp)
                ) {
                    Text(
                        text = displayedText,
                        style = AikoTypography.bodyLarge.copy(
                            color = if (isUser) Color.White else AikoColors.TextPrimary,
                            fontSize = 15.sp,
                            fontWeight = FontWeight.Medium,
                            lineHeight = 22.sp
                        )
                    )
                }
            }

            if (!isUser) {
                Spacer(modifier = Modifier.weight(1f))
            }
        }
    }
}
