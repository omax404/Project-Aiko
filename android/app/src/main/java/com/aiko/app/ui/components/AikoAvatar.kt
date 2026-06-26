package com.aiko.app.ui.components

import android.util.Log
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.aiko.app.domain.EmotionState
import com.aiko.app.ui.theme.AikoColors

@Composable
fun AikoAvatar(
    emotionState: EmotionState,
    dominantEmotion: String,
    isTyping: Boolean,
    isSpeaking: Boolean,
    modifier: Modifier = Modifier,
    size: Dp = 160.dp
) {
    val context = LocalContext.current

    // Emotion Color Mapping
    val activeColor = when (dominantEmotion.lowercase()) {
        "happy" -> AikoColors.HappyGold
        "flustered" -> AikoColors.FlusteredPink
        "devoted" -> AikoColors.DevotedViolet
        "calm" -> AikoColors.CalmBlue
        "sad" -> AikoColors.SadGrey
        "worried" -> AikoColors.WorriedOrange
        "jealous" -> AikoColors.JealousGreen
        else -> AikoColors.Primary
    }

    val animatedGlowColor by animateColorAsState(
        targetValue = activeColor,
        animationSpec = tween(800),
        label = "avatarGlow"
    )

    // Pulsing core animation for procedural fallback and glow
    val infiniteTransition = rememberInfiniteTransition(label = "pulseRing")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.95f,
        targetValue = 1.08f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )

    val spinRotation by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(8000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "rotation"
    )

    Box(
        modifier = modifier.size(size),
        contentAlignment = Alignment.Center
    ) {
        // 1. Double Glowing Ambient Rings (Glass depth)
        Box(
            modifier = Modifier
                .fillMaxSize()
                .scale(pulseScale)
                .blur(radius = 16.dp)
                .clip(CircleShape)
                .background(animatedGlowColor.copy(alpha = 0.15f))
                .border(2.dp, animatedGlowColor.copy(alpha = 0.3f), CircleShape)
        )

        Box(
            modifier = Modifier
                .size(size - 16.dp)
                .blur(radius = 8.dp)
                .clip(CircleShape)
                .background(animatedGlowColor.copy(alpha = 0.10f))
        )

        // HIGH-FIDELITY FALLBACK: Glowing Frosted Glass Refraction Sphere Core
        AikoPersona(
            emotionTag = dominantEmotion,
            modifier = Modifier.size(size - 24.dp)
        )
    }
}
