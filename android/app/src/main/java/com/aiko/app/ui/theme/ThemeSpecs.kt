package com.aiko.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.Typography
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import androidx.compose.ui.text.googlefonts.GoogleFont
import androidx.compose.ui.text.googlefonts.Font
import com.aiko.app.R

val fontProvider = GoogleFont.Provider(
    providerAuthority = "com.google.android.gms.fonts",
    providerPackage = "com.google.android.gms",
    certificates = R.array.com_google_android_gms_fonts_certs
)

val CormorantGaramond = FontFamily(
    Font(googleFont = GoogleFont("Cormorant Garamond"), fontProvider = fontProvider)
)
val DMSans = FontFamily(
    Font(googleFont = GoogleFont("DM Sans"), fontProvider = fontProvider)
)
val Inter = FontFamily(
    Font(googleFont = GoogleFont("Inter"), fontProvider = fontProvider)
)
val JetBrainsMono = FontFamily(
    Font(googleFont = GoogleFont("JetBrains Mono"), fontProvider = fontProvider)
)

/**
 * Dynamic color palette that can be customized at runtime via user preferences.
 * All color fields can be overridden by passing a custom accent color hex string.
 */
@Immutable
data class AikoDynamicColors(
    val Background: Color = Color(0xFF1C1320),
    val Surface: Color = Color(0xFF2A1B30),
    val Accent: Color = Color(0xFFC9A8D9),
    val TextPrimary: Color = Color(0xFFf0ebe3),
    val TextSecondary: Color = Color(0xFF9a8f7e),
    val Error: Color = Color(0xFFf87171),
    val AccentSoft: Color = Accent.copy(alpha = 0.15f),
    val Card: Color = Color(0xFF35223D),
    val InputBg: Color = Color(0xFF241829),
    val Border: Color = Color(0x0FFFFFFF),
    val SuccessGreen: Color = Color(0xFF4ade80),
    val ErrorRed: Color = Color(0xFFf87171),
    
    // Neurochemical Bar Colors (Matching Tailwind classes)
    val DopamineBar: Color = Color(0xFFEAB308),
    val SerotoninBar: Color = Color(0xFF22C55E),
    val CortisolBar: Color = Color(0xFFEF4444),
    val AdrenalineBar: Color = Color(0xFF3B82F6),
    val OxytocinBar: Color = Color(0xFFEC4899),
    val MelatoninBar: Color = Color(0xFF8B5CF6),

    // Compatibility aliases
    val BackgroundLight: Color = Background,
    val SurfaceDark: Color = Surface,
    val PrimaryRed: Color = Accent,
    val Primary: Color = Accent,
    val Secondary: Color = Surface,
    val TextOnDark: Color = TextPrimary,
    val FlusteredPink: Color = Color(0xFFFF5293),
    val HappyGold: Color = Color(0xFFFFD043),
    val CalmBlue: Color = Color(0xFF4C8CFF),
    val DevotedViolet: Color = Color(0xFF9B51E0),
    val SadGrey: Color = Color(0xFF7A8D9B),
    val WorriedOrange: Color = Color(0xFFFF9F43),
    val JealousGreen: Color = Color(0xFF1DD1A1)
)

val LocalAikoColors = staticCompositionLocalOf { AikoDynamicColors() }

/**
 * Accessor object providing backward-compatible access to the current dynamic colors.
 * All existing code referencing AikoColors.Accent, AikoColors.Background, etc. continues to work.
 */
object AikoColors {
    val Background: Color @Composable get() = LocalAikoColors.current.Background
    val Surface: Color @Composable get() = LocalAikoColors.current.Surface
    val Accent: Color @Composable get() = LocalAikoColors.current.Accent
    val TextPrimary: Color @Composable get() = LocalAikoColors.current.TextPrimary
    val TextSecondary: Color @Composable get() = LocalAikoColors.current.TextSecondary
    val Error: Color @Composable get() = LocalAikoColors.current.Error
    val AccentSoft: Color @Composable get() = LocalAikoColors.current.AccentSoft
    val Card: Color @Composable get() = LocalAikoColors.current.Card
    val InputBg: Color @Composable get() = LocalAikoColors.current.InputBg
    val Border: Color @Composable get() = LocalAikoColors.current.Border
    val SuccessGreen: Color @Composable get() = LocalAikoColors.current.SuccessGreen
    val ErrorRed: Color @Composable get() = LocalAikoColors.current.ErrorRed

    // Chemical bar getters
    val DopamineBar: Color @Composable get() = LocalAikoColors.current.DopamineBar
    val SerotoninBar: Color @Composable get() = LocalAikoColors.current.SerotoninBar
    val CortisolBar: Color @Composable get() = LocalAikoColors.current.CortisolBar
    val AdrenalineBar: Color @Composable get() = LocalAikoColors.current.AdrenalineBar
    val OxytocinBar: Color @Composable get() = LocalAikoColors.current.OxytocinBar
    val MelatoninBar: Color @Composable get() = LocalAikoColors.current.MelatoninBar

    val BackgroundLight: Color @Composable get() = LocalAikoColors.current.BackgroundLight
    val SurfaceDark: Color @Composable get() = LocalAikoColors.current.SurfaceDark
    val PrimaryRed: Color @Composable get() = LocalAikoColors.current.PrimaryRed
    val Primary: Color @Composable get() = LocalAikoColors.current.Primary
    val Secondary: Color @Composable get() = LocalAikoColors.current.Secondary
    val TextOnDark: Color @Composable get() = LocalAikoColors.current.TextOnDark
    val FlusteredPink: Color @Composable get() = LocalAikoColors.current.FlusteredPink
    val HappyGold: Color @Composable get() = LocalAikoColors.current.HappyGold
    val CalmBlue: Color @Composable get() = LocalAikoColors.current.CalmBlue
    val DevotedViolet: Color @Composable get() = LocalAikoColors.current.DevotedViolet
    val SadGrey: Color @Composable get() = LocalAikoColors.current.SadGrey
    val WorriedOrange: Color @Composable get() = LocalAikoColors.current.WorriedOrange
    val JealousGreen: Color @Composable get() = LocalAikoColors.current.JealousGreen
}

/** Font family selection for the app, stored as a preference key string. */
object AikoFonts {
    val SansSerif = Inter
    val Serif = CormorantGaramond
    val Monospace = JetBrainsMono
    val Cursive = FontFamily.Cursive

    fun fromKey(key: String): FontFamily = when (key) {
        "system_serif", "cormorant" -> Serif
        "monospace", "jetbrains" -> Monospace
        "dm_sans" -> DMSans
        "inter" -> Inter
        "cursive" -> Cursive
        else -> SansSerif
    }

    fun labelFor(key: String): String = when (key) {
        "system_serif", "cormorant" -> "Cormorant Garamond"
        "monospace", "jetbrains" -> "JetBrains Mono"
        "dm_sans" -> "DM Sans"
        "inter" -> "Inter"
        "cursive" -> "Handwritten"
        else -> "Inter"
    }

    val allKeys = listOf("inter", "dm_sans", "cormorant", "jetbrains", "cursive")
}

val LocalAikoFontFamily = staticCompositionLocalOf<FontFamily> { Inter }
val LocalAikoTextScale = staticCompositionLocalOf { 1.0f }

/** Builds a Material3 Typography with the given font families and text scale. */
fun buildAikoTypography(
    headingFamily: FontFamily = CormorantGaramond,
    bodyFamily: FontFamily = Inter,
    scale: Float = 1.0f
): Typography = Typography(
    headlineLarge = TextStyle(fontFamily = headingFamily, fontWeight = FontWeight.SemiBold, fontSize = (34 * scale).sp, lineHeight = (40 * scale).sp, color = Color(0xFFf0ebe3)),
    titleLarge = TextStyle(fontFamily = headingFamily, fontWeight = FontWeight.Medium, fontSize = (22 * scale).sp, lineHeight = (28 * scale).sp, color = Color(0xFFf0ebe3)),
    bodyLarge = TextStyle(fontFamily = bodyFamily, fontWeight = FontWeight.Normal, fontSize = (16 * scale).sp, lineHeight = (23 * scale).sp, color = Color(0xFFf0ebe3)),
    bodyMedium = TextStyle(fontFamily = bodyFamily, fontWeight = FontWeight.Normal, fontSize = (14 * scale).sp, lineHeight = (20 * scale).sp, color = Color(0xFF9a8f7e)),
    labelMedium = TextStyle(fontFamily = bodyFamily, fontWeight = FontWeight.Medium, fontSize = (12 * scale).sp, lineHeight = (16 * scale).sp, letterSpacing = 0.4.sp, color = Color(0xFF9a8f7e))
)

/**
 * Static fallback typography for non-composable contexts.
 * Prefer using MaterialTheme.typography inside @Composable functions.
 */
val AikoTypography = buildAikoTypography()

/** Parses a hex color string like "#C9A8D9" or "C9A8D9" into a Color, with fallback. */
fun parseHexColor(hex: String, fallback: Color = Color(0xFFC9A8D9)): Color {
    return try {
        val cleaned = hex.removePrefix("#").trim()
        if (cleaned.length == 6) {
            Color(android.graphics.Color.parseColor("#$cleaned"))
        } else if (cleaned.length == 8) {
            Color(android.graphics.Color.parseColor("#$cleaned"))
        } else {
            fallback
        }
    } catch (_: Exception) {
        fallback
    }
}

@Composable
fun AikoTheme(
    accentColorHex: String = "#C9A8D9",
    fontKey: String = "inter",
    textScale: Float = 1.0f,
    content: @Composable () -> Unit
) {
    val accent = parseHexColor(accentColorHex)
    val dynamicColors = AikoDynamicColors(
        Accent = accent,
        AccentSoft = accent.copy(alpha = 0.15f),
        PrimaryRed = accent,
        Primary = accent,
        FlusteredPink = accent,
        HappyGold = accent,
        CalmBlue = accent,
        DevotedViolet = accent,
        WorriedOrange = accent,
        JealousGreen = accent
    )

    val bodyFamily = AikoFonts.fromKey(fontKey)
    val headingFamily = if (fontKey == "inter" || fontKey == "system_sans") CormorantGaramond else bodyFamily
    val typography = buildAikoTypography(headingFamily, bodyFamily, textScale)

    val colorScheme = darkColorScheme(
        primary = dynamicColors.Accent,
        secondary = dynamicColors.Accent,
        background = dynamicColors.Background,
        surface = dynamicColors.Surface,
        onPrimary = dynamicColors.Background,
        onBackground = dynamicColors.TextPrimary,
        onSurface = dynamicColors.TextPrimary,
        error = dynamicColors.Error
    )

    CompositionLocalProvider(
        LocalAikoColors provides dynamicColors,
        LocalAikoFontFamily provides bodyFamily,
        LocalAikoTextScale provides textScale
    ) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = typography,
            content = content
        )
    }
}
