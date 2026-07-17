package com.aiko.app.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography

/**
 * Editorial Flat Card Container
 */
@Composable
fun EditorialCard(
    modifier: Modifier = Modifier,
    cornerRadius: Dp = 24.dp,
    backgroundColor: Color = AikoColors.SurfaceDark,
    content: @Composable () -> Unit
) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(cornerRadius))
            .background(backgroundColor)
            .padding(16.dp)
    ) {
        content()
    }
}
/**
 * Animated statistics neurochemical visualizer with premium bouncy springs
 */
@Composable
fun NeuroBar(
    name: String,
    value: Float, // 0f - 1f
    color: Color,
    modifier: Modifier = Modifier
) {
    val animatedProgress by animateFloatAsState(
        targetValue = value,
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioMediumBouncy,
            stiffness = Spring.StiffnessLow
        ),
        label = "neuroSpring"
    )

    Column(modifier = modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = name,
                style = AikoTypography.bodyLarge.copy(
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 14.sp
                )
            )
            Spacer(modifier = Modifier.weight(1f))
            Text(
                text = "${(value * 100).toInt()}%",
                style = AikoTypography.labelMedium.copy(
                    color = color,
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp
                )
            )
        }
        Spacer(modifier = Modifier.height(6.dp))
        
        // Progress Track
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(4.dp)
                .clip(CircleShape)
                .background(Color(0xFFE0E0E0)) // Light gray track
        ) {
            // Foreground active track
            Box(
                modifier = Modifier
                    .fillMaxHeight()
                    .fillMaxWidth(fraction = animatedProgress)
                    .clip(CircleShape)
                    .background(color)
            )
        }
    }
}

/**
 * Editorial Flat Button
 */
@Composable
fun EditorialButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    backgroundColor: Color = AikoColors.PrimaryRed,
    textColor: Color = Color.White
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(56.dp)
            .clip(RoundedCornerShape(28.dp))
            .background(backgroundColor)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = text,
            style = AikoTypography.bodyLarge.copy(
                fontWeight = FontWeight.Bold,
                color = textColor,
                letterSpacing = 1.sp
            )
        )
    }
}
/**
 * Minimalist Outline Pill Badge
 */
@Composable
fun EmotionBadge(
    emotion: String,
    modifier: Modifier = Modifier
) {
    val color = when (emotion.lowercase()) {
        "happy", "playful" -> AikoColors.HappyGold
        "flustered" -> AikoColors.FlusteredPink
        "devoted" -> AikoColors.DevotedViolet
        "calm" -> AikoColors.CalmBlue
        "worried" -> AikoColors.WorriedOrange
        "jealous" -> AikoColors.JealousGreen
        else -> AikoColors.PrimaryRed
    }

    Box(
        modifier = modifier
            .clip(CircleShape)
            .border(1.dp, color, CircleShape)
            .padding(horizontal = 12.dp, vertical = 6.dp)
    ) {
        Text(
            text = emotion.uppercase(),
            style = AikoTypography.labelMedium.copy(
                color = color,
                fontWeight = FontWeight.Bold,
                fontSize = 10.sp,
                letterSpacing = 1.5.sp
            )
        )
    }
}
/**
 * High-contrast minimalist navigation bar
 */
@Composable
fun FloatingNavBar(
    selectedRoute: String,
    items: List<Pair<String, ImageVector>>,
    onItemSelected: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .padding(horizontal = 24.dp, vertical = 12.dp)
            .fillMaxWidth()
            .height(72.dp)
            .clip(RoundedCornerShape(36.dp))
            .background(Color.White)
            .border(2.dp, AikoColors.TextPrimary, RoundedCornerShape(36.dp)),
        contentAlignment = Alignment.Center
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            items.forEach { (route, icon) ->
                val isSelected = selectedRoute == route
                val tintColor by animateColorAsState(
                    targetValue = if (isSelected) AikoColors.PrimaryRed else AikoColors.TextSecondary,
                    animationSpec = tween(300),
                    label = "navTint"
                )

                Box(
                    modifier = Modifier
                        .weight(1f)
                        .clickable(onClick = { onItemSelected(route) }),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.padding(vertical = 8.dp)
                    ) {
                        Icon(
                            imageVector = icon,
                            contentDescription = route,
                            modifier = Modifier.size(26.dp),
                            tint = tintColor
                        )
                        if (isSelected) {
                            Spacer(modifier = Modifier.height(4.dp))
                            Box(
                                modifier = Modifier
                                    .size(width = 6.dp, height = 6.dp)
                                    .clip(CircleShape)
                                    .background(AikoColors.PrimaryRed)
                            )
                        }
                    }
                }
            }
        }
    }
}

/**
 * Geometric Abstract Poster Background Canvas
 */
@Composable
fun AbstractPosterCanvas(modifier: Modifier = Modifier) {
    val primaryRed = AikoColors.PrimaryRed
    val surfaceDark = AikoColors.SurfaceDark
    val textPrimary = AikoColors.TextPrimary

    androidx.compose.foundation.Canvas(modifier = modifier) {
        val width = size.width
        val height = size.height

        // Top left giant circle (Vibrant Red)
        drawCircle(
            color = primaryRed,
            radius = width * 0.45f,
            center = androidx.compose.ui.geometry.Offset(-width * 0.1f, -height * 0.05f)
        )

        // Bottom right semi-circle (Dark Charcoal)
        drawCircle(
            color = surfaceDark,
            radius = width * 0.6f,
            center = androidx.compose.ui.geometry.Offset(width * 1.1f, height * 1.1f)
        )
        
        // Soft vignette overlay for depth around avatar area
        drawRect(
            brush = androidx.compose.ui.graphics.Brush.radialGradient(
                colors = listOf(
                    androidx.compose.ui.graphics.Color.Transparent,
                    surfaceDark.copy(alpha = 0.15f)
                ),
                center = androidx.compose.ui.geometry.Offset(width * 0.5f, height * 0.45f),
                radius = width * 0.9f
            )
        )
    }
}
