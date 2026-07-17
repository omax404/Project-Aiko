package com.aiko.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Cloud
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale
import kotlinx.coroutines.delay

@Composable
fun GlassCard(
    modifier: Modifier = Modifier,
    cornerRadius: Dp = 16.dp,
    content: @Composable () -> Unit
) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(cornerRadius))
            .background(Color(0xFF35223D).copy(alpha = 0.5f))
            .border(1.dp, Color(0x0FFFFFFF), RoundedCornerShape(cornerRadius))
            .padding(16.dp)
    ) {
        content()
    }
}

@Composable
fun CompanionTopCard(
    dominantEmotion: String,
    weatherText: String,
    currentActivity: String,
    modifier: Modifier = Modifier
) {
    var currentTime by remember { mutableStateOf("") }
    
    LaunchedEffect(Unit) {
        while (true) {
            val cal = Calendar.getInstance()
            val sdf = SimpleDateFormat("HH:mm", Locale.getDefault())
            currentTime = sdf.format(cal.time)
            delay(10000) // update every 10 seconds
        }
    }

    GlassCard(modifier = modifier) {
        Column {
            // HH:MM clock
            Text(
                text = currentTime,
                style = AikoTypography.headlineLarge.copy(
                    fontSize = 38.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Serif
                )
            )
            
            // Weather line
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Default.Cloud,
                    contentDescription = "Weather",
                    tint = AikoColors.Accent,
                    modifier = Modifier.size(14.dp)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = weatherText.ifEmpty { "Loading weather..." },
                    style = AikoTypography.bodyMedium.copy(
                        fontSize = 13.sp,
                        color = AikoColors.TextSecondary
                    )
                )
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // Bullets
            Column {
                BulletRow(label = "Mood", value = dominantEmotion.uppercase(), color = AikoColors.Accent)
                Spacer(modifier = Modifier.height(6.dp))
                BulletRow(label = "Activity", value = currentActivity, color = AikoColors.Accent)
            }
        }
    }
}

@Composable
fun BulletRow(
    label: String,
    value: String,
    color: Color
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            modifier = Modifier
                .size(6.dp)
                .clip(CircleShape)
                .background(color)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = "$label: ",
            style = AikoTypography.bodyMedium.copy(
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                color = AikoColors.TextSecondary
            )
        )
        Text(
            text = value,
            style = AikoTypography.bodyMedium.copy(
                fontSize = 12.sp,
                color = AikoColors.TextPrimary
            )
        )
    }
}
