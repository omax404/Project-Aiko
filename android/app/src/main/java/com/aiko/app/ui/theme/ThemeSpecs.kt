package com.aiko.app.ui.theme

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// Editorial Poster Color Tokens
object AikoColors {
    val BackgroundLight = Color(0xFFEBE6DD) // Creamy beige
    val SurfaceDark = Color(0xFF2B2A2A) // Dark Charcoal
    val PrimaryRed = Color(0xFFE54545) // Vibrant Red Accent
    
    // Emotion Colors (Adjusted for light theme)
    val FlusteredPink = Color(0xFFE8437E)
    val HappyGold = Color(0xFFD6A000)
    val CalmBlue = Color(0xFF3270E0)
    val DevotedViolet = Color(0xFF6B3BC2)
    val SadGrey = Color(0xFF6A7985)
    val WorriedOrange = Color(0xFFE66442)
    val JealousGreen = Color(0xFF29B373)

    // Standard Theme Colors
    val Primary = PrimaryRed
    val Secondary = SurfaceDark
    val Accent = PrimaryRed
    val TextPrimary = Color(0xFF1A1A1A) // Near black
    val TextSecondary = Color(0xFF595959) // Gray
    val TextOnDark = Color(0xFFF7F5F0) // Off white for dark cards
}

val EditorialColorScheme = lightColorScheme(
    primary = AikoColors.Primary,
    secondary = AikoColors.Secondary,
    background = AikoColors.BackgroundLight,
    surface = AikoColors.SurfaceDark,
    onPrimary = Color.White,
    onSecondary = AikoColors.TextOnDark,
    onBackground = AikoColors.TextPrimary,
    onSurface = AikoColors.TextOnDark
)

val EditorialSerif = FontFamily.Serif
val EditorialSans = FontFamily.SansSerif

val AikoTypography = Typography(
    headlineLarge = TextStyle(
        fontFamily = EditorialSerif,
        fontWeight = FontWeight.Bold,
        fontSize = 36.sp,
        lineHeight = 44.sp,
        letterSpacing = (-0.5).sp,
        color = AikoColors.TextPrimary
    ),
    titleLarge = TextStyle(
        fontFamily = EditorialSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 24.sp,
        lineHeight = 32.sp,
        letterSpacing = 0.sp,
        color = AikoColors.TextPrimary
    ),
    bodyLarge = TextStyle(
        fontFamily = EditorialSans,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.5.sp,
        color = AikoColors.TextPrimary
    ),
    bodyMedium = TextStyle(
        fontFamily = EditorialSans,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.25.sp,
        color = AikoColors.TextSecondary
    ),
    labelMedium = TextStyle(
        fontFamily = EditorialSans,
        fontWeight = FontWeight.Medium,
        fontSize = 12.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.5.sp,
        color = AikoColors.TextSecondary
    )
)

@Composable
fun AikoTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = EditorialColorScheme,
        typography = AikoTypography,
        content = content
    )
}

/**
 * Editorial Flat Modifier
 */
fun Modifier.editorialCard(
    cornerRadius: Dp = 16.dp,
    backgroundColor: Color = AikoColors.SurfaceDark
): Modifier = this
    .clip(RoundedCornerShape(cornerRadius))
    .background(backgroundColor)

