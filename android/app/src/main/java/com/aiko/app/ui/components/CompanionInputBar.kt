package com.aiko.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography

@Composable
fun CompanionInputBar(
    onSend: (String) -> Unit,
    onMicTap: () -> Unit,
    modifier: Modifier = Modifier
) {
    var text by remember { mutableStateOf("") }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(24.dp))
            .background(Color(0xFF241829).copy(alpha = 0.8f))
            .border(1.dp, Color(0x0FFFFFFF), RoundedCornerShape(24.dp))
            .padding(horizontal = 16.dp, vertical = 8.dp)
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.fillMaxWidth()
        ) {
            IconButton(
                onClick = onMicTap,
                modifier = Modifier.size(36.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Mic,
                    contentDescription = "Voice Input",
                    tint = AikoColors.Accent,
                    modifier = Modifier.size(20.dp)
                )
            }
            
            Spacer(modifier = Modifier.width(8.dp))
            
            BasicTextField(
                value = text,
                onValueChange = { text = it },
                singleLine = true,
                cursorBrush = SolidColor(AikoColors.Accent),
                textStyle = AikoTypography.bodyLarge.copy(
                    fontSize = 14.sp,
                    color = AikoColors.TextPrimary
                ),
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                keyboardActions = KeyboardActions(
                    onSend = {
                        if (text.trim().isNotEmpty()) {
                            onSend(text.trim())
                            text = ""
                        }
                    }
                ),
                decorationBox = { innerTextField ->
                    if (text.isEmpty()) {
                        Text(
                            text = "Say something...",
                            style = AikoTypography.bodyLarge.copy(
                                fontSize = 14.sp,
                                color = AikoColors.TextSecondary
                            )
                        )
                    }
                    innerTextField()
                },
                modifier = Modifier.weight(1f)
            )

            if (text.trim().isNotEmpty()) {
                IconButton(
                    onClick = {
                        onSend(text.trim())
                        text = ""
                    },
                    modifier = Modifier.size(36.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Send,
                        contentDescription = "Send",
                        tint = AikoColors.Accent,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }
        }
    }
}
