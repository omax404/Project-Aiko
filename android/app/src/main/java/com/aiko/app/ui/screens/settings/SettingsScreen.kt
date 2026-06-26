package com.aiko.app.ui.screens.settings

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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aiko.app.data.local.AikoPrefs
import com.aiko.app.data.repository.ChatRepository
import com.aiko.app.ui.components.EditorialCard
import com.aiko.app.ui.components.EditorialButton
import com.aiko.app.ui.components.AbstractPosterCanvas
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography
import kotlinx.coroutines.launch

@Composable
fun SettingsScreen(
    chatRepository: ChatRepository,
    aikoPrefs: AikoPrefs,
    modifier: Modifier = Modifier
) {
    val scope = rememberCoroutineScope()

    val userName by aikoPrefs.userNameFlow.collectAsState(initial = "")
    val apiKey by aikoPrefs.apiKeyFlow.collectAsState(initial = "")
    val voiceEnabled by aikoPrefs.voiceEnabledFlow.collectAsState(initial = false)
    val modelChoice by aikoPrefs.modelChoiceFlow.collectAsState(initial = "gemini-1.5-flash")
    val desktopConnected by aikoPrefs.desktopConnectedFlow.collectAsState(initial = false)
    val desktopUrl by aikoPrefs.desktopUrlFlow.collectAsState(initial = "http://10.0.2.2:8000")

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
                .verticalScroll(rememberScrollState())
        ) {
            Spacer(modifier = Modifier.height(40.dp))

            Text(
                text = "Control Center",
                style = AikoTypography.headlineLarge.copy(fontSize = 24.sp, fontWeight = FontWeight.Bold)
            )
            Text(
                text = "Configure neural systems & options",
                style = AikoTypography.bodyMedium
            )

            Spacer(modifier = Modifier.height(24.dp))

            // User configuration card
            EditorialCard(modifier = Modifier.fillMaxWidth()) {
                Column {
                    Text(
                        text = "IDENTITY DETAILS",
                        style = AikoTypography.labelMedium.copy(
                            fontWeight = FontWeight.Bold,
                            color = AikoColors.TextSecondary,
                            letterSpacing = 1.sp
                        ),
                        modifier = Modifier.padding(bottom = 12.dp)
                    )

                    OutlinedTextField(
                        value = userName,
                        onValueChange = { scope.launch { aikoPrefs.setUserName(it) } },
                        label = { Text("Your Name") },
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = AikoColors.SurfaceDark,
                            unfocusedBorderColor = AikoColors.TextSecondary,
                            focusedTextColor = AikoColors.TextPrimary,
                            unfocusedTextColor = AikoColors.TextPrimary
                        ),
                        shape = RoundedCornerShape(14.dp),
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Neural Core card
            EditorialCard(modifier = Modifier.fillMaxWidth()) {
                Column {
                    Text(
                        text = "NEURAL COGNITION",
                        style = AikoTypography.labelMedium.copy(
                            fontWeight = FontWeight.Bold,
                            color = AikoColors.TextSecondary,
                            letterSpacing = 1.sp
                        ),
                        modifier = Modifier.padding(bottom = 12.dp)
                    )

                    OutlinedTextField(
                        value = apiKey,
                        onValueChange = { scope.launch { aikoPrefs.setApiKey(it) } },
                        label = { Text("Gemini API Key") },
                        visualTransformation = PasswordVisualTransformation(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = AikoColors.SurfaceDark,
                            unfocusedBorderColor = AikoColors.TextSecondary,
                            focusedTextColor = AikoColors.TextPrimary,
                            unfocusedTextColor = AikoColors.TextPrimary
                        ),
                        shape = RoundedCornerShape(14.dp),
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(14.dp))

                    OutlinedTextField(
                        value = modelChoice,
                        onValueChange = { scope.launch { aikoPrefs.setModelChoice(it) } },
                        label = { Text("LLM Model Name") },
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = AikoColors.SurfaceDark,
                            unfocusedBorderColor = AikoColors.TextSecondary,
                            focusedTextColor = AikoColors.TextPrimary,
                            unfocusedTextColor = AikoColors.TextPrimary
                        ),
                        shape = RoundedCornerShape(14.dp),
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Desktop server link configuration card
            EditorialCard(modifier = Modifier.fillMaxWidth()) {
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "Desktop Link Mode",
                                style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.SemiBold)
                            )
                            Text(
                                text = "Sync memory and camera with Aiko Desktop",
                                style = AikoTypography.bodyMedium
                            )
                        }
                        Switch(
                            checked = desktopConnected,
                            onCheckedChange = { scope.launch { aikoPrefs.setDesktopConnected(it) } },
                            colors = SwitchDefaults.colors(
                                checkedThumbColor = Color.White,
                                checkedTrackColor = AikoColors.Primary
                            )
                        )
                    }

                    if (desktopConnected) {
                        Spacer(modifier = Modifier.height(14.dp))
                        OutlinedTextField(
                            value = desktopUrl,
                            onValueChange = { scope.launch { aikoPrefs.setDesktopUrl(it) } },
                            label = { Text("Aiko Desktop Server URL") },
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = AikoColors.SurfaceDark,
                                unfocusedBorderColor = AikoColors.TextSecondary,
                                focusedTextColor = AikoColors.TextPrimary,
                                unfocusedTextColor = AikoColors.TextPrimary
                            ),
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Preferences Toggles
            EditorialCard(modifier = Modifier.fillMaxWidth()) {
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "Tactile Vocalization",
                                style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.SemiBold)
                            )
                            Text(
                                text = "Aiko reads messages using speech synthesis fallback",
                                style = AikoTypography.bodyMedium
                            )
                        }
                        Switch(
                            checked = voiceEnabled,
                            onCheckedChange = { scope.launch { aikoPrefs.setVoiceEnabled(it) } },
                            colors = SwitchDefaults.colors(
                                checkedThumbColor = Color.White,
                                checkedTrackColor = AikoColors.Primary
                            )
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Danger resets
            EditorialButton(
                text = "Erase Memories & Re-align",
                backgroundColor = AikoColors.SurfaceDark,
                onClick = {
                    scope.launch {
                        chatRepository.clearHistory()
                    }
                }
            )
            Spacer(modifier = Modifier.height(90.dp))
        }
    }
}
