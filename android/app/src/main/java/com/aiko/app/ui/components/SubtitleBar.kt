package com.aiko.app.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography
import kotlinx.coroutines.delay

@Composable
fun SubtitleBar(
    speaker: String,
    text: String,
    modifier: Modifier = Modifier
) {
    var displayedText by remember { mutableStateOf("") }
    var isFinished by remember { mutableStateOf(false) }

    // Reset when text changes and run typewriter effect
    LaunchedEffect(text) {
        displayedText = ""
        isFinished = false
        if (text.isNotEmpty()) {
            for (i in 1..text.length) {
                if (isFinished) break
                displayedText = text.substring(0, i)
                delay(28)
            }
            isFinished = true
        }
    }

    AnimatedVisibility(
        visible = text.isNotEmpty() && displayedText.isNotEmpty(),
        enter = fadeIn() + slideInVertically(initialOffsetY = { it / 2 }),
        exit = fadeOut() + slideOutVertically(targetOffsetY = { it / 2 }),
        modifier = modifier.fillMaxWidth()
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(16.dp))
                .background(Color(0xFF1C1320).copy(alpha = 0.85f))
                .border(1.dp, Color(0x19FFFFFF), RoundedCornerShape(16.dp))
                .clickable {
                    // Tap to skip typewriter and show full text immediately
                    isFinished = true
                    displayedText = text
                }
                .padding(16.dp)
        ) {
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(4.dp))
                            .background(AikoColors.Accent)
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = speaker,
                            style = AikoTypography.labelMedium.copy(
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF1C1320)
                            )
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text(
                    text = displayedText,
                    style = AikoTypography.bodyLarge.copy(
                        fontSize = 15.sp,
                        lineHeight = 22.sp,
                        color = AikoColors.TextPrimary
                    )
                )
            }
        }
    }
}
