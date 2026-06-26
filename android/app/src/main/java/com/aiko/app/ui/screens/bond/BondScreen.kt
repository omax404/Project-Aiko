package com.aiko.app.ui.screens.bond

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.layout.size
import androidx.compose.ui.unit.sp
import com.aiko.app.data.local.BondEntity
import com.aiko.app.data.local.EmotionLogEntity
import com.aiko.app.data.repository.ChatRepository
import com.aiko.app.ui.components.EditorialCard
import com.aiko.app.ui.components.AbstractPosterCanvas
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun BondScreen(
    chatRepository: ChatRepository,
    modifier: Modifier = Modifier
) {
    val bondState by chatRepository.getBond().collectAsState(initial = BondEntity())
    // Observe latest 10 logs of neuro status
    val logs by chatRepository.emotionLogDao.getLogsFlow(10).collectAsState(initial = emptyList())

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(AikoColors.BackgroundLight)
    ) {
        AbstractPosterCanvas(modifier = Modifier.fillMaxSize())

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(40.dp))

            Text(
                text = "Bond Telemetry",
                style = AikoTypography.headlineLarge.copy(fontSize = 24.sp, fontWeight = FontWeight.Bold)
            )
            Text(
                text = "Neuro-chemical analytics & bond parameters",
                style = AikoTypography.bodyMedium
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Milestone indicators
            EditorialCard(modifier = Modifier.fillMaxWidth()) {
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column {
                            Text(
                                text = "Relationship Milestone",
                                style = AikoTypography.labelMedium.copy(fontWeight = FontWeight.Bold)
                            )
                            Text(
                                text = bondState.relationshipTitle,
                                style = AikoTypography.titleLarge.copy(
                                    color = AikoColors.Primary,
                                    fontWeight = FontWeight.Bold
                                )
                            )
                        }
                        Spacer(modifier = Modifier.weight(1f))
                        Box(modifier = Modifier.padding(8.dp)) {
                            Text(
                                text = "Lvl ${bondState.level}",
                                style = AikoTypography.headlineLarge.copy(
                                    fontSize = 28.sp,
                                    color = AikoColors.Secondary,
                                    fontWeight = FontWeight.Black
                                )
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Stats details
                    Row(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(text = "Total Conversations", style = AikoTypography.labelMedium)
                            Text(
                                text = "${bondState.totalMessages / 2} sessions",
                                style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.SemiBold)
                            )
                        }
                        Column(modifier = Modifier.weight(1f)) {
                            Text(text = "First Met On", style = AikoTypography.labelMedium)
                            val dateString = SimpleDateFormat("MMM d, yyyy", Locale.getDefault()).format(Date(bondState.firstMet))
                            Text(
                                text = dateString,
                                style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.SemiBold)
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Premium custom Canvas chart representing emotional shifts
            EditorialCard(modifier = Modifier.fillMaxWidth()) {
                Column {
                    Text(
                        text = "EMOTIONAL DYNAMICS",
                        style = AikoTypography.labelMedium.copy(
                            fontWeight = FontWeight.Bold,
                            color = AikoColors.TextSecondary,
                            letterSpacing = 1.sp
                        ),
                        modifier = Modifier.padding(bottom = 12.dp)
                    )

                    if (logs.size < 2) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(160.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "Telemetry logging updates after conversations 🌸",
                                style = AikoTypography.bodyMedium,
                                textAlign = TextAlign.Center
                            )
                        }
                    } else {
                        // Drawing custom lines representing chemistry indexes
                        val reversedLogs = logs.reversed()
                        Canvas(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(160.dp)
                        ) {
                            val canvasWidth = size.width
                            val canvasHeight = size.height
                            val spacing = canvasWidth / (reversedLogs.size - 1)

                            // Helper function to draw dynamic flow lines
                            fun drawLogLine(
                                selector: (EmotionLogEntity) -> Float,
                                color: Color
                            ) {
                                val path = Path()
                                reversedLogs.forEachIndexed { index, log ->
                                    val x = index * spacing
                                    val valPct = selector(log)
                                    val y = canvasHeight - (valPct * canvasHeight)
                                    if (index == 0) {
                                        path.moveTo(x, y)
                                    } else {
                                        path.lineTo(x, y)
                                    }
                                }
                                drawPath(
                                    path = path,
                                    color = color,
                                    style = Stroke(width = 4f)
                                )
                            }

                            // Render Dopamine logs line (Pink)
                            drawLogLine({ it.dopamine }, AikoColors.FlusteredPink)
                            // Render Serotonin logs line (Violet)
                            drawLogLine({ it.serotonin }, AikoColors.DevotedViolet)
                            // Render Cortisol logs line (Orange)
                            drawLogLine({ it.cortisol }, AikoColors.WorriedOrange)
                        }

                        Spacer(modifier = Modifier.height(12.dp))

                        // Custom Legend Indicators
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Box(modifier = Modifier.size(8.dp).background(AikoColors.FlusteredPink))
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(text = "Dopamine", style = AikoTypography.labelMedium)
                            }
                            Spacer(modifier = Modifier.width(16.dp))
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Box(modifier = Modifier.size(8.dp).background(AikoColors.DevotedViolet))
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(text = "Serotonin", style = AikoTypography.labelMedium)
                            }
                            Spacer(modifier = Modifier.width(16.dp))
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Box(modifier = Modifier.size(8.dp).background(AikoColors.WorriedOrange))
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(text = "Cortisol", style = AikoTypography.labelMedium)
                            }
                        }
                    }
                }
            }
            Spacer(modifier = Modifier.height(90.dp)) // Floating nav padding
        }
    }
}
