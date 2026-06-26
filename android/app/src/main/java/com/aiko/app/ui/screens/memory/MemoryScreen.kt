package com.aiko.app.ui.screens.memory

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aiko.app.data.local.MemoryEntity
import com.aiko.app.data.repository.ChatRepository
import com.aiko.app.ui.components.EditorialCard
import com.aiko.app.ui.components.AbstractPosterCanvas
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography
import kotlinx.coroutines.launch

@Composable
fun MemoryScreen(
    chatRepository: ChatRepository,
    modifier: Modifier = Modifier
) {
    val memories by chatRepository.getMemories().collectAsState(initial = emptyList<MemoryEntity>())
    val scope = rememberCoroutineScope()
    val haptic = LocalHapticFeedback.current

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
        ) {
            Spacer(modifier = Modifier.height(40.dp))

            Text(
                text = "Memory Core",
                style = AikoTypography.headlineLarge.copy(fontSize = 24.sp, fontWeight = FontWeight.Bold)
            )
            Text(
                text = "Facts AIKO has remembered about you",
                style = AikoTypography.bodyMedium
            )

            Spacer(modifier = Modifier.height(24.dp))

            if (memories.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "Nothing here yet... talk to me more~ 🌸",
                        style = AikoTypography.bodyLarge.copy(
                            color = AikoColors.TextSecondary,
                            fontSize = 15.sp,
                            textAlign = TextAlign.Center
                        )
                    )
                }
            } else {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f)
                ) {
                    // Group memories by category
                    val grouped = memories.groupBy { it.category }

                    grouped.forEach { (category, list) ->
                        item {
                            Text(
                                text = category.uppercase(),
                                style = AikoTypography.labelMedium.copy(
                                    fontWeight = FontWeight.Bold,
                                    color = AikoColors.Primary,
                                    letterSpacing = 1.sp
                                ),
                                modifier = Modifier.padding(top = 16.dp, bottom = 8.dp)
                            )
                        }

                        items(list, key = { it.id }) { memory ->
                            MemoryRow(
                                memory = memory,
                                onDelete = {
                                    scope.launch {
                                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                        chatRepository.memoryDao.deleteMemory(memory.id)
                                    }
                                }
                            )
                            Spacer(modifier = Modifier.height(10.dp))
                        }
                    }
                    item { Spacer(modifier = Modifier.height(80.dp)) }
                }
            }
        }
    }
}

@Composable
fun MemoryRow(
    memory: MemoryEntity,
    onDelete: () -> Unit,
    modifier: Modifier = Modifier
) {
    EditorialCard(
        modifier = modifier.fillMaxWidth()
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                text = memory.content,
                style = AikoTypography.bodyLarge.copy(
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Medium
                ),
                modifier = Modifier.weight(1f)
            )
            Spacer(modifier = Modifier.width(12.dp))
            IconButton(
                onClick = onDelete,
                modifier = Modifier.clip(RoundedCornerShape(8.dp))
            ) {
                Icon(
                    imageVector = Icons.Default.Delete,
                    contentDescription = "Delete Memory",
                    tint = AikoColors.TextSecondary
                )
            }
        }
    }
}
