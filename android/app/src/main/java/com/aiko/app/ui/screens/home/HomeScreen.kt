package com.aiko.app.ui.screens.home

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.graphics.Color
import com.aiko.app.data.local.AikoPrefs
import com.aiko.app.data.repository.ChatRepository
import com.aiko.app.domain.EmotionEngine
import com.aiko.app.ui.components.AbstractPosterCanvas
import com.aiko.app.ui.components.AikoAvatar
import com.aiko.app.ui.components.EditorialCard
import com.aiko.app.ui.components.NeuroBar
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography
import java.util.Calendar

@Composable
fun HomeScreen(
    chatRepository: ChatRepository,
    aikoPrefs: AikoPrefs,
    emotionEngine: EmotionEngine,
    modifier: Modifier = Modifier
) {
    val currentEmotion by chatRepository.currentEmotion.collectAsState()
    val bondState by chatRepository.getBond().collectAsState(initial = com.aiko.app.data.local.BondEntity())
    val userName by aikoPrefs.userNameFlow.collectAsState(initial = "User")

    val dominantEmotion = emotionEngine.determineDominantEmotion(currentEmotion)
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

    val greeting = when (Calendar.getInstance().get(Calendar.HOUR_OF_DAY)) {
        in 0..11 -> "Good morning"
        in 12..16 -> "Good afternoon"
        else -> "Good evening"
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(AikoColors.BackgroundLight)
    ) {
        AbstractPosterCanvas(modifier = Modifier.fillMaxSize())

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 32.dp)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(40.dp))

            // Greeting card
            Text(
                text = "$greeting,\n$userName.",
                style = AikoTypography.headlineLarge.copy(
                    fontSize = 48.sp,
                    lineHeight = 56.sp,
                    textAlign = TextAlign.Start
                ),
                modifier = Modifier.fillMaxWidth()
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Aiko is feeling ${dominantEmotion.uppercase()}",
                style = AikoTypography.bodyLarge.copy(
                    color = activeColor,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.5.sp
                ),
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(40.dp))

            // Aiko Reacting Live
            AikoAvatar(
                emotionState = currentEmotion,
                dominantEmotion = dominantEmotion,
                isTyping = false,
                isSpeaking = false,
                size = 200.dp
            )

            Spacer(modifier = Modifier.height(50.dp))

            // Chemistry telemetry
            EditorialCard(modifier = Modifier.fillMaxWidth()) {
                Column {
                    Text(
                        text = "NEUROCHEMICALS",
                        style = AikoTypography.titleLarge.copy(
                            fontSize = 18.sp,
                            color = AikoColors.TextOnDark
                        ),
                        modifier = Modifier.padding(bottom = 24.dp)
                    )
                    NeuroBar(name = "Dopamine", value = currentEmotion.dopamine, color = AikoColors.FlusteredPink)
                    Spacer(modifier = Modifier.height(16.dp))
                    NeuroBar(name = "Serotonin", value = currentEmotion.serotonin, color = AikoColors.DevotedViolet)
                    Spacer(modifier = Modifier.height(16.dp))
                    NeuroBar(name = "Cortisol", value = currentEmotion.cortisol, color = AikoColors.WorriedOrange)
                    Spacer(modifier = Modifier.height(16.dp))
                    NeuroBar(name = "Adrenaline", value = currentEmotion.adrenaline, color = AikoColors.HappyGold)
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Bond xp summary
            EditorialCard(modifier = Modifier.fillMaxWidth(), backgroundColor = AikoColors.PrimaryRed) {
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.Bottom
                    ) {
                        Column {
                            Text(
                                text = "BOND LEVEL",
                                style = AikoTypography.labelMedium.copy(color = Color.White.copy(alpha = 0.8f))
                            )
                            Text(
                                text = "${bondState.level}",
                                style = AikoTypography.headlineLarge.copy(
                                    color = Color.White,
                                    fontSize = 56.sp,
                                    lineHeight = 56.sp
                                )
                            )
                        }
                        Spacer(modifier = Modifier.weight(1f))
                        Column(horizontalAlignment = Alignment.End) {
                            Text(
                                text = bondState.relationshipTitle,
                                style = AikoTypography.titleLarge.copy(color = Color.White, fontSize = 18.sp)
                            )
                            Text(
                                text = "${bondState.xp} / ${100 * bondState.level} XP",
                                style = AikoTypography.bodyMedium.copy(color = Color.White.copy(alpha = 0.8f))
                            )
                        }
                    }
                }
            }
            Spacer(modifier = Modifier.height(120.dp)) // Floating Nav cushion
        }
    }
}
