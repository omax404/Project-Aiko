package com.aiko.app.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography

@Composable
fun AmbientBubble(
    text: String,
    modifier: Modifier = Modifier
) {
    AnimatedVisibility(
        visible = text.isNotEmpty(),
        enter = fadeIn() + expandVertically(),
        exit = fadeOut() + shrinkVertically(),
        modifier = modifier
    ) {
        Box(
            modifier = Modifier
                .widthIn(max = 240.dp)
                .clip(RoundedCornerShape(14.dp, 14.dp, 14.dp, 4.dp))
                .background(Color(0xFF1E1B16).copy(alpha = 0.92f))
                .border(1.dp, Color(0xFFFFFFFF).copy(alpha = 0.08f), RoundedCornerShape(14.dp, 14.dp, 14.dp, 4.dp))
                .padding(horizontal = 14.dp, vertical = 10.dp)
        ) {
            Text(
                text = text,
                style = AikoTypography.bodyMedium.copy(
                    fontSize = 13.sp,
                    lineHeight = 18.sp,
                    color = AikoColors.TextPrimary
                )
            )
        }
    }
}
