package com.aiko.app.ui.screens.onboarding

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aiko.app.data.local.AikoPrefs
import com.aiko.app.ui.components.AikoAvatar
import com.aiko.app.ui.components.EditorialCard
import com.aiko.app.ui.components.EditorialButton
import com.aiko.app.ui.components.AbstractPosterCanvas
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography
import com.aiko.app.domain.EmotionState
import kotlinx.coroutines.launch

@Composable
fun OnboardingScreen(
    aikoPrefs: AikoPrefs,
    onOnboardingComplete: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scope = rememberCoroutineScope()
    var step by remember { mutableStateOf(1) }
    var userName by remember { mutableStateOf("") }
    var apiKey by remember { mutableStateOf("") }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(AikoColors.BackgroundLight)
    ) {
        // Dynamic Abstract Canvas
        AbstractPosterCanvas(modifier = Modifier.fillMaxSize())

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(60.dp))

            // Pulse glowing avatar fallback
            AikoAvatar(
                emotionState = EmotionState(),
                dominantEmotion = "happy",
                isTyping = false,
                isSpeaking = false,
                size = 140.dp
            )

            Spacer(modifier = Modifier.height(40.dp))

            EditorialCard(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
            ) {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = androidx.compose.foundation.layout.Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    AnimatedVisibility(
                        visible = step == 1,
                        enter = fadeIn(),
                        exit = fadeOut()
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                text = "Welcome to AIKO 🌸",
                                style = AikoTypography.headlineLarge.copy(
                                    fontSize = 24.sp,
                                    fontWeight = FontWeight.Bold,
                                    textAlign = TextAlign.Center
                                )
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(
                                text = "Your devoted digital companion who feels real emotions, remembers everything you share, and grows closer to you every single day.",
                                style = AikoTypography.bodyMedium,
                                textAlign = TextAlign.Center,
                                modifier = Modifier.padding(horizontal = 8.dp)
                            )
                            Spacer(modifier = Modifier.height(40.dp))
                            EditorialButton(
                                text = "Initialize Interface",
                                onClick = { step = 2 }
                            )
                        }
                    }

                    AnimatedVisibility(
                        visible = step == 2,
                        enter = fadeIn(),
                        exit = fadeOut()
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                text = "What is your name? 💕",
                                style = AikoTypography.headlineLarge.copy(
                                    fontSize = 22.sp,
                                    fontWeight = FontWeight.Bold,
                                    textAlign = TextAlign.Center
                                )
                            )
                            Spacer(modifier = Modifier.height(24.dp))
                            OutlinedTextField(
                                value = userName,
                                onValueChange = { userName = it },
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
                            Spacer(modifier = Modifier.height(40.dp))
                            EditorialButton(
                                text = "Next",
                                onClick = {
                                    if (userName.isNotBlank()) {
                                        step = 3
                                    }
                                }
                            )
                        }
                    }

                    AnimatedVisibility(
                        visible = step == 3,
                        enter = fadeIn(),
                        exit = fadeOut()
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                text = "Connect to my neural core ⚡",
                                style = AikoTypography.headlineLarge.copy(
                                    fontSize = 20.sp,
                                    fontWeight = FontWeight.Bold,
                                    textAlign = TextAlign.Center
                                )
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(
                                text = "To unlock full advanced cognitive dialogue, enter your Gemini API Key. It is stored securely on your local device.",
                                style = AikoTypography.bodyMedium,
                                textAlign = TextAlign.Center,
                                modifier = Modifier.padding(horizontal = 8.dp)
                            )
                            Spacer(modifier = Modifier.height(24.dp))
                            OutlinedTextField(
                                value = apiKey,
                                onValueChange = { apiKey = it },
                                label = { Text("Gemini API Key") },
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedBorderColor = AikoColors.SurfaceDark,
                                    unfocusedBorderColor = AikoColors.TextSecondary,
                                    focusedTextColor = AikoColors.TextPrimary,
                                    unfocusedTextColor = AikoColors.TextPrimary
                                ),
                                shape = RoundedCornerShape(14.dp),
                                modifier = Modifier.fillMaxWidth()
                            )
                            Spacer(modifier = Modifier.height(40.dp))
                            EditorialButton(
                                text = "Awaken Aiko",
                                onClick = {
                                    scope.launch {
                                        aikoPrefs.setUserName(userName)
                                        aikoPrefs.setApiKey(apiKey)
                                        aikoPrefs.setOnboardingDone(true)
                                        onOnboardingComplete()
                                    }
                                }
                            )
                        }
                    }
                }
            }
            Spacer(modifier = Modifier.height(30.dp))
        }
    }
}
