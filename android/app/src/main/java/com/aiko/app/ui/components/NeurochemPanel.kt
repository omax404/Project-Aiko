package com.aiko.app.ui.components

import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aiko.app.domain.EmotionState
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography

@Composable
fun NeurochemPanel(
    emotionState: EmotionState,
    modifier: Modifier = Modifier
) {
    GlassCard(
        modifier = modifier.width(110.dp)
    ) {
        Column {
            Text(
                text = "NEURO",
                style = AikoTypography.labelMedium.copy(
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp,
                    color = AikoColors.TextSecondary
                ),
                modifier = Modifier.padding(bottom = 8.dp)
            )
            
            Column {
                MiniNeuroBar(name = "DOP", value = emotionState.dopamine, color = AikoColors.DopamineBar)
                Spacer(modifier = Modifier.height(6.dp))
                MiniNeuroBar(name = "SER", value = emotionState.serotonin, color = AikoColors.SerotoninBar)
                Spacer(modifier = Modifier.height(6.dp))
                MiniNeuroBar(name = "COR", value = emotionState.cortisol, color = AikoColors.CortisolBar)
                Spacer(modifier = Modifier.height(6.dp))
                MiniNeuroBar(name = "ADR", value = emotionState.adrenaline, color = AikoColors.AdrenalineBar)
                Spacer(modifier = Modifier.height(6.dp))
                MiniNeuroBar(name = "OXY", value = emotionState.oxytocin, color = AikoColors.OxytocinBar)
                Spacer(modifier = Modifier.height(6.dp))
                MiniNeuroBar(name = "MEL", value = emotionState.melatonin, color = AikoColors.MelatoninBar)
            }
        }
    }
}

@Composable
fun MiniNeuroBar(
    name: String,
    value: Float,
    color: Color
) {
    val animatedProgress by animateFloatAsState(
        targetValue = value.coerceIn(0f, 1f),
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioNoBouncy,
            stiffness = Spring.StiffnessLow
        ),
        label = "miniNeuroSpring"
    )

    Column(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = name,
                style = AikoTypography.labelMedium.copy(
                    fontSize = 9.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = AikoColors.TextSecondary
                )
            )
            Spacer(modifier = Modifier.weight(1f))
            Text(
                text = "${(value * 100).toInt()}%",
                style = AikoTypography.labelMedium.copy(
                    fontSize = 8.sp,
                    fontWeight = FontWeight.Bold,
                    color = color
                )
            )
        }
        Spacer(modifier = Modifier.height(2.dp))
        // Progress track & fill
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(4.dp)
                .clip(RoundedCornerShape(2.dp))
                .background(Color.White.copy(alpha = 0.05f))
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(animatedProgress)
                    .height(4.dp)
                    .clip(RoundedCornerShape(2.dp))
                    .background(color)
            )
        }
    }
}
