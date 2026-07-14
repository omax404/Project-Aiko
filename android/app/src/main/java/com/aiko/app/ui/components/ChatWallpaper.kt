package com.aiko.app.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.aiko.app.ui.theme.AikoColors

/**
 * Renders the chat background based on the user's selected wallpaper preference.
 * Supports: default dark, animated gradient presets, and solid color themes.
 */
@Composable
fun ChatWallpaper(
    wallpaperKey: String,
    modifier: Modifier = Modifier
) {
    when (wallpaperKey) {
        "gradient_sunset" -> AnimatedGradientWallpaper(
            colors = listOf(
                Color(0xFF1C1320),
                Color(0xFF4A1942),
                Color(0xFF8B2252),
                Color(0xFFD4456C)
            ),
            modifier = modifier
        )
        "gradient_ocean" -> AnimatedGradientWallpaper(
            colors = listOf(
                Color(0xFF0A1628),
                Color(0xFF0D2847),
                Color(0xFF144272),
                Color(0xFF205295)
            ),
            modifier = modifier
        )
        "gradient_aurora" -> AnimatedGradientWallpaper(
            colors = listOf(
                Color(0xFF0F0C29),
                Color(0xFF1B2838),
                Color(0xFF1A4040),
                Color(0xFF2D6A4F)
            ),
            modifier = modifier
        )
        "gradient_sakura" -> AnimatedGradientWallpaper(
            colors = listOf(
                Color(0xFF1C1320),
                Color(0xFF2D1B35),
                Color(0xFF5C3A5C),
                Color(0xFFC9A8D9)
            ),
            modifier = modifier
        )
        "gradient_midnight" -> AnimatedGradientWallpaper(
            colors = listOf(
                Color(0xFF0D0D0D),
                Color(0xFF141414),
                Color(0xFF1A1A2E),
                Color(0xFF16213E)
            ),
            modifier = modifier
        )
        "solid_charcoal" -> Box(
            modifier.fillMaxSize().background(Color(0xFF1A1A1A))
        )
        "solid_navy" -> Box(
            modifier.fillMaxSize().background(Color(0xFF0D1B2A))
        )
        "solid_wine" -> Box(
            modifier.fillMaxSize().background(Color(0xFF2D0A1E))
        )
        "solid_forest" -> Box(
            modifier.fillMaxSize().background(Color(0xFF0A1F0A))
        )
        else -> {
            // Default — use the theme background color
            Box(modifier.fillMaxSize().background(AikoColors.Background))
        }
    }
}

/**
 * A subtly animated vertical gradient that slowly shifts between color stops.
 * Creates a living, breathing background feel.
 */
@Composable
private fun AnimatedGradientWallpaper(
    colors: List<Color>,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "wallpaper_anim")

    val shift = infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(12000, easing = EaseInOutSine),
            repeatMode = RepeatMode.Reverse
        ),
        label = "gradient_shift"
    )

    Box(
        modifier
            .fillMaxSize()
            .drawBehind {
                val currentShift = shift.value
                val topOffset = currentShift * 0.15f
                val brush = Brush.verticalGradient(
                    colors = colors,
                    startY = topOffset * 200f,
                    endY = Float.POSITIVE_INFINITY
                )
                drawRect(brush = brush)
            }
    )
}

/** Returns a human-readable label for a wallpaper key. */
fun wallpaperLabel(key: String): String = when (key) {
    "gradient_sunset" -> "🌅 Sunset"
    "gradient_ocean" -> "🌊 Ocean"
    "gradient_aurora" -> "🌌 Aurora"
    "gradient_sakura" -> "🌸 Sakura"
    "gradient_midnight" -> "🌙 Midnight"
    "solid_charcoal" -> "⬛ Charcoal"
    "solid_navy" -> "🔷 Navy"
    "solid_wine" -> "🍷 Wine"
    "solid_forest" -> "🌲 Forest"
    else -> "✨ Default"
}

/** All available wallpaper keys for the settings gallery. */
val allWallpaperKeys = listOf(
    "default",
    "gradient_sunset",
    "gradient_ocean",
    "gradient_aurora",
    "gradient_sakura",
    "gradient_midnight",
    "solid_charcoal",
    "solid_navy",
    "solid_wine",
    "solid_forest"
)

/** Returns the primary representative color for a wallpaper preset (used in settings thumbnails). */
fun wallpaperPreviewColor(key: String): Color = when (key) {
    "gradient_sunset" -> Color(0xFF8B2252)
    "gradient_ocean" -> Color(0xFF144272)
    "gradient_aurora" -> Color(0xFF1A4040)
    "gradient_sakura" -> Color(0xFF5C3A5C)
    "gradient_midnight" -> Color(0xFF1A1A2E)
    "solid_charcoal" -> Color(0xFF1A1A1A)
    "solid_navy" -> Color(0xFF0D1B2A)
    "solid_wine" -> Color(0xFF2D0A1E)
    "solid_forest" -> Color(0xFF0A1F0A)
    else -> Color(0xFF1C1320)
}
