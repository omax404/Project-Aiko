package com.aiko.app.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay
import kotlin.math.cos
import kotlin.math.sin
import kotlin.random.Random

/**
 * The primary visual representation of the Aiko AI.
 * Handles continuous floating physics, emotion-driven color shifting, and 3D glass rendering.
 */
@Composable
fun AikoPersona(
    emotionTag: String,
    modifier: Modifier = Modifier
) {
    // 1. Emotion to Color Mapping Engine
    val targetColor = when (emotionTag.lowercase()) {
        "flustered", "happy" -> Color(0xFFFF5293) // Warm Pink
        "calm", "devoted" -> Color(0xFF4C8CFF)    // Deep Blue
        "excited" -> Color(0xFFFFD043)            // Energetic Gold
        "sad", "worried" -> Color(0xFF7A8D9B)     // Muted Gray/Blue
        "jealous" -> Color(0xFFB33771)            // Sharp Violet
        else -> Color(0xFF4C8CFF)                 // Default Calm
    }

    // Smooth emotion transitions (matches human emotional shifting speeds)
    val glowColor by animateColorAsState(
        targetValue = targetColor,
        animationSpec = tween(1200, easing = FastOutSlowInEasing),
        label = "emotion_color_shift"
    )

    // 2. Physics & Animation Engine
    val infiniteTransition = rememberInfiniteTransition(label = "persona_physics")
    
    // Vertical floating (mimics breathing/hovering)
    val floatY by infiniteTransition.animateFloat(
        initialValue = -15f,
        targetValue = 15f,
        animationSpec = infiniteRepeatable(
            animation = tween(2800, easing = EaseInOutSine),
            repeatMode = RepeatMode.Reverse
        ),
        label = "hover_y"
    )

    // Core energy pulsing
    val coreIntensity by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 0.85f,
        animationSpec = infiniteRepeatable(
            animation = tween(1800, easing = EaseInOutSine),
            repeatMode = RepeatMode.Reverse
        ),
        label = "core_pulse"
    )

    // Rotation for inner particles
    val rotationAngle by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(20000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "internal_rotation"
    )

    Box(
        modifier = modifier
            .offset(y = floatY.dp)
            .graphicsLayer {
                // Outer ambient glow casting onto the UI
                shadowElevation = 40.dp.toPx()
                ambientShadowColor = glowColor
                spotShadowColor = glowColor
            }
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val radius = size.width / 2f
            val center = Offset(size.width / 2, size.height / 2)

            // Layer 1: Ambient Core Energy (The Emotion Source)
            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(
                        glowColor.copy(alpha = coreIntensity),
                        glowColor.copy(alpha = 0.1f),
                        Color.Transparent
                    ),
                    center = center,
                    radius = radius * 1.2f
                ),
                blendMode = BlendMode.Screen
            )

            // Layer 2: The Frosted Glass Sphere Body
            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(
                        Color.White.copy(alpha = 0.3f),  // Top-left ambient light
                        Color.Transparent,               // Clear center for depth
                        glowColor.copy(alpha = 0.4f),    // Bottom-right emotion reflection
                        Color.Black.copy(alpha = 0.6f)   // Deep edge shadow
                    ),
                    center = Offset(size.width * 0.35f, size.height * 0.35f),
                    radius = radius
                )
            )

            // Layer 3: Sharp Specular Highlight (The "Glass" Reflection)
            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(
                        Color.White.copy(alpha = 0.9f),
                        Color.White.copy(alpha = 0.0f)
                    ),
                    center = Offset(size.width * 0.25f, size.height * 0.25f),
                    radius = radius * 0.4f
                )
            )

            // Layer 4: Crisp Rim Lighting
            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(
                        Color.Transparent,
                        Color.White.copy(alpha = 0.1f),
                        Color.White.copy(alpha = 0.5f)
                    ),
                    center = center,
                    radius = radius
                ),
                style = androidx.compose.ui.graphics.drawscope.Stroke(width = 1.5.dp.toPx())
            )

            // Layer 5: Internal Energy Filaments (Rotates)
            val filamentCount = 5
            for (i in 0 until filamentCount) {
                val angle = rotationAngle + (i * (360f / filamentCount))
                val rad = Math.toRadians(angle.toDouble())
                
                // Calculate sweeping curve points inside the sphere
                val startX = center.x + (cos(rad) * radius * 0.8).toFloat()
                val startY = center.y + (sin(rad) * radius * 0.8).toFloat()
                
                val endX = center.x - (cos(rad + 1.5) * radius * 0.8).toFloat()
                val endY = center.y - (sin(rad + 1.5) * radius * 0.8).toFloat()

                drawLine(
                    brush = Brush.linearGradient(
                        colors = listOf(Color.Transparent, Color.White.copy(alpha = 0.4f), Color.Transparent),
                        start = Offset(startX, startY),
                        end = Offset(endX, endY)
                    ),
                    start = Offset(startX, startY),
                    end = Offset(endX, endY),
                    strokeWidth = 2.dp.toPx(),
                    blendMode = BlendMode.Overlay
                )
            }
        }
    }
}
