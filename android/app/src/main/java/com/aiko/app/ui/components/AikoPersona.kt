package com.aiko.app.ui.components

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Log
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.cos
import kotlin.math.sin

/**
 * The high-fidelity fallback visual representation of Aiko.
 * Displays a beautiful glass card containing her character illustration matching
 * the current emotion, with floating physics and orbit particle systems.
 */
@Composable
fun AikoPersona(
    emotionTag: String,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current

    // Emotion Color Mapping
    val targetColor = when (emotionTag.lowercase()) {
        "flustered", "happy" -> Color(0xFFFF5293) // Warm Pink
        "calm", "devoted" -> Color(0xFF4C8CFF)    // Deep Blue
        "excited" -> Color(0xFFFFD043)            // Energetic Gold
        "sad", "worried" -> Color(0xFF7A8D9B)     // Muted Gray/Blue
        "jealous" -> Color(0xFFB33771)            // Sharp Violet
        else -> Color(0xFF4C8CFF)                 // Default Calm
    }

    val emotionLabel = when (emotionTag.lowercase()) {
        "happy" -> "Happy"
        "flustered" -> "Flustered"
        "calm" -> "Calm"
        "devoted" -> "Devoted"
        "excited" -> "Excited"
        "sad" -> "Sad"
        "worried" -> "Worried"
        "jealous" -> "Jealous"
        else -> "Aiko"
    }

    val emotionSizeMultiplier = when (emotionTag.lowercase()) {
        "excited" -> 1.15f
        "happy", "flustered" -> 1.08f
        "sad", "worried" -> 0.88f
        "jealous" -> 1.05f
        else -> 1.0f
    }

    val emotionGlowAlpha = when (emotionTag.lowercase()) {
        "excited" -> 0.95f
        "happy", "flustered" -> 0.85f
        "devoted" -> 0.80f
        "sad", "worried" -> 0.45f
        "jealous" -> 0.70f
        else -> 0.65f
    }

    val glowColor by animateColorAsState(
        targetValue = targetColor,
        animationSpec = tween(1200, easing = FastOutSlowInEasing),
        label = "emotion_color_shift"
    )

    val animatedSizeMultiplier by animateFloatAsState(
        targetValue = emotionSizeMultiplier,
        animationSpec = tween(800, easing = FastOutSlowInEasing),
        label = "emotion_size"
    )

    val animatedGlowAlpha by animateFloatAsState(
        targetValue = emotionGlowAlpha,
        animationSpec = tween(600, easing = FastOutSlowInEasing),
        label = "emotion_glow_alpha"
    )

    // Physics & Animation
    val infiniteTransition = rememberInfiniteTransition(label = "persona_physics")
    
    val floatY by infiniteTransition.animateFloat(
        initialValue = -12f,
        targetValue = 12f,
        animationSpec = infiniteRepeatable(
            animation = tween(2800, easing = EaseInOutSine),
            repeatMode = RepeatMode.Reverse
        ),
        label = "hover_y"
    )

    val coreIntensity by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 0.85f,
        animationSpec = infiniteRepeatable(
            animation = tween(1800, easing = EaseInOutSine),
            repeatMode = RepeatMode.Reverse
        ),
        label = "core_pulse"
    )

    val rotationAngle by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(20000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "internal_rotation"
    )

    val outerRotation by infiniteTransition.animateFloat(
        initialValue = 360f,
        targetValue = 0f,
        animationSpec = infiniteRepeatable(
            animation = tween(15000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "outer_rotation"
    )

    val twinkle by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(900, easing = EaseInOutSine),
            repeatMode = RepeatMode.Reverse
        ),
        label = "twinkle"
    )

    // Load bitmap matching dominant emotion
    val stickerPath = getStickerPath(emotionTag)
    val bitmap = rememberAssetBitmap(context, stickerPath)

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = modifier
    ) {
        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier
                .weight(1f)
                .offset { androidx.compose.ui.unit.IntOffset(0, floatY.dp.roundToPx()) }
                .graphicsLayer {
                    scaleX = animatedSizeMultiplier
                    scaleY = animatedSizeMultiplier
                    shadowElevation = 30.dp.toPx()
                    ambientShadowColor = glowColor
                    spotShadowColor = glowColor
                }
        ) {
            // Background Canvas: Glowing cores and orbiting rings
            Canvas(modifier = Modifier.fillMaxSize()) {
                val radius = size.width / 2.3f
                val center = Offset(size.width / 2, size.height / 2)

                // 1. Outer particle ring
                drawParticleRing(
                    center = center,
                    radius = radius * 1.35f,
                    particleCount = 10,
                    rotationDegrees = outerRotation,
                    color = glowColor,
                    alpha = twinkle * 0.5f * animatedGlowAlpha,
                    particleRadius = 2.5f
                )

                // 2. Inner particle ring
                drawParticleRing(
                    center = center,
                    radius = radius * 1.1f,
                    particleCount = 7,
                    rotationDegrees = rotationAngle * 1.3f,
                    color = Color.White,
                    alpha = (1f - twinkle) * 0.4f,
                    particleRadius = 1.5f
                )

                // 3. Ambient core aura glow
                drawCircle(
                    brush = Brush.radialGradient(
                        colors = listOf(
                            glowColor.copy(alpha = coreIntensity * 0.35f * animatedGlowAlpha),
                            glowColor.copy(alpha = 0.10f * animatedGlowAlpha),
                            Color.Transparent
                        ),
                        center = center,
                        radius = radius * 1.4f
                    ),
                    blendMode = BlendMode.Screen
                )
            }

            // Foreground: Frosted Glass Character Card
            if (bitmap != null) {
                Box(
                    modifier = Modifier
                        .size(130.dp)
                        .scale(0.92f)
                        .clip(RoundedCornerShape(28.dp))
                        .background(Color.White.copy(alpha = 0.07f))
                        .border(
                            1.5.dp,
                            Brush.verticalGradient(
                                listOf(
                                    Color.White.copy(alpha = 0.28f),
                                    Color.White.copy(alpha = 0.04f)
                                )
                            ),
                            RoundedCornerShape(28.dp)
                        )
                        .padding(14.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Image(
                        bitmap = bitmap.asImageBitmap(),
                        contentDescription = emotionLabel,
                        modifier = Modifier.fillMaxSize()
                    )
                }
            } else {
                // Secondary text fallback if image is missing
                Box(
                    modifier = Modifier
                        .size(130.dp)
                        .clip(RoundedCornerShape(28.dp))
                        .background(Color.White.copy(alpha = 0.1f)),
                    contentAlignment = Alignment.Center
                ) {
                    Text("❦", fontSize = 42.sp, color = glowColor)
                }
            }
        }

        // Emotion label below
        Spacer(modifier = Modifier.height(10.dp))
        Text(
            text = emotionLabel.uppercase(),
            color = glowColor.copy(alpha = 0.85f),
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            letterSpacing = 2.sp
        )
    }
}

/**
 * Maps dominant emotion strings to local asset sticker paths.
 */
private fun getStickerPath(emotion: String): String = when (emotion.lowercase()) {
    "happy" -> "stickers/01_Happy_Cheer.png"
    "flustered" -> "stickers/02_Shy_Blush.png"
    "calm" -> "stickers/07_Waving_Hello.png"
    "devoted" -> "stickers/09_Heart_Eyes_Rose.png"
    "excited" -> "stickers/13_Excited_Jump.png"
    "sad" -> "stickers/05_Crying_Comical.png"
    "worried" -> "stickers/03_Surprised_Gasp.png"
    "jealous" -> "stickers/10_Annoyed_Pout.png"
    else -> "stickers/07_Waving_Hello.png"
}

/**
 * Loads a bitmap from the assets folder safely with try-catch and closing the stream.
 */
@Composable
private fun rememberAssetBitmap(context: Context, path: String): Bitmap? {
    return remember(path) {
        try {
            context.assets.open(path).use { stream ->
                BitmapFactory.decodeStream(stream)
            }
        } catch (e: Exception) {
            Log.e("AikoPersona", "Failed to load fallback sticker asset $path", e)
            null
        }
    }
}

private fun DrawScope.drawParticleRing(
    center: Offset,
    radius: Float,
    particleCount: Int,
    rotationDegrees: Float,
    color: Color,
    alpha: Float,
    particleRadius: Float
) {
    for (i in 0 until particleCount) {
        val angle = rotationDegrees + (i * (360f / particleCount))
        val rad = Math.toRadians(angle.toDouble())
        val waveOffset = sin(rad * 3.0 + rotationDegrees * 0.02) * radius * 0.06f
        val px = center.x + (cos(rad) * (radius + waveOffset)).toFloat()
        val py = center.y + (sin(rad) * (radius + waveOffset)).toFloat()

        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    color.copy(alpha = alpha),
                    color.copy(alpha = alpha * 0.2f),
                    Color.Transparent
                ),
                center = Offset(px, py),
                radius = particleRadius * 3f
            )
        )
        drawCircle(
            color = Color.White.copy(alpha = alpha * 0.85f),
            radius = particleRadius,
            center = Offset(px, py)
        )
    }
}
