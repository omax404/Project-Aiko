package com.aiko.app.ui.screens.settings

import android.Manifest
import android.content.pm.PackageManager
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.aiko.app.data.local.AikoPrefs
import com.aiko.app.data.repository.ChatRepository
import com.aiko.app.ui.components.AbstractPosterCanvas
import com.aiko.app.ui.components.EditorialButton
import com.aiko.app.ui.components.EditorialCard
import com.aiko.app.ui.components.allWallpaperKeys
import com.aiko.app.ui.components.wallpaperLabel
import com.aiko.app.ui.components.wallpaperPreviewColor
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoFonts
import com.aiko.app.ui.theme.AikoTypography
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    chatRepository: ChatRepository,
    aikoPrefs: AikoPrefs,
    onBack: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    val scope = rememberCoroutineScope()
    val context = LocalContext.current

    // Bind preferences flows
    val userName by aikoPrefs.userNameFlow.collectAsState(initial = "")
    val apiKey by aikoPrefs.apiKeyFlow.collectAsState(initial = "")
    val voiceEnabled by aikoPrefs.voiceEnabledFlow.collectAsState(initial = false)
    val modelChoice by aikoPrefs.modelChoiceFlow.collectAsState(initial = "gemini-1.5-flash")
    val desktopConnected by aikoPrefs.desktopConnectedFlow.collectAsState(initial = false)
    val desktopUrl by aikoPrefs.desktopUrlFlow.collectAsState(initial = "http://10.0.2.2:8000")

    // Connection Mode & Theme
    val connectionMode by aikoPrefs.connectionModeFlow.collectAsState(initial = "Link to Desktop")
    val themeAccentColor by aikoPrefs.themeAccentColorFlow.collectAsState(initial = "#C9A8D9")
    val avatarMode by aikoPrefs.avatarModeFlow.collectAsState(initial = "WebView")
    val lastSyncTimestamp by aikoPrefs.lastSyncTimestampFlow.collectAsState(initial = 0L)

    // Appearance preferences
    val chatFont by aikoPrefs.chatFontFlow.collectAsState(initial = "system_sans")
    val chatWallpaper by aikoPrefs.chatWallpaperFlow.collectAsState(initial = "default")
    val chatBubbleStyle by aikoPrefs.chatBubbleStyleFlow.collectAsState(initial = "default")
    val chatTextSize by aikoPrefs.chatTextSizeFlow.collectAsState(initial = 1.0f)

    // Somatic intensity states
    val jitter by aikoPrefs.jitterIntensityFlow.collectAsState(initial = 0.4f)
    val tear by aikoPrefs.tearIntensityFlow.collectAsState(initial = 1.0f)
    val lean by aikoPrefs.leanIntensityFlow.collectAsState(initial = 1.0f)
    val blush by aikoPrefs.blushIntensityFlow.collectAsState(initial = 1.0f)
    val pout by aikoPrefs.poutIntensityFlow.collectAsState(initial = 1.0f)
    val boba by aikoPrefs.bobaIntensityFlow.collectAsState(initial = 1.0f)
    val oxytocin by aikoPrefs.oxytocinIntensityFlow.collectAsState(initial = 1.0f)
    val melatonin by aikoPrefs.melatoninIntensityFlow.collectAsState(initial = 1.0f)

    // Vocalization Settings states
    val ttsEngine by aikoPrefs.ttsEngineFlow.collectAsState(initial = "native")
    val ttsApiUrl by aikoPrefs.ttsApiUrlFlow.collectAsState(initial = "https://api.openai.com/v1/audio/speech")
    val ttsApiKey by aikoPrefs.ttsApiKeyFlow.collectAsState(initial = "")
    val ttsApiVoice by aikoPrefs.ttsApiVoiceFlow.collectAsState(initial = "alloy")
    val ttsApiModel by aikoPrefs.ttsApiModelFlow.collectAsState(initial = "tts-1")

    var syncInProgress by remember { mutableStateOf(false) }
    var qrScannerOpen by remember { mutableStateOf(false) }

    // Camera permission launcher
    val cameraPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            qrScannerOpen = true
        } else {
            Toast.makeText(context, "Camera permission required to scan QR code", Toast.LENGTH_LONG).show()
        }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(AikoColors.Background)
    ) {
        AbstractPosterCanvas(modifier = Modifier.fillMaxSize())

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 20.dp)
                .verticalScroll(rememberScrollState())
        ) {
            Spacer(modifier = Modifier.height(48.dp))

            // Navigation Header
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp)
            ) {
                IconButton(onClick = onBack, modifier = Modifier.size(48.dp)) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back", tint = AikoColors.TextPrimary)
                }
                Spacer(Modifier.width(8.dp))
                Column {
                    Text(
                        text = "Control Center",
                        style = AikoTypography.headlineLarge.copy(fontSize = 24.sp, fontWeight = FontWeight.Bold)
                    )
                    Text(
                        text = "Configure neural systems & sync preferences",
                        style = AikoTypography.bodyMedium
                    )
                }
            }

            Spacer(modifier = Modifier.height(18.dp))

            // 1. IDENTITY & PERSONA
            EditorialCard(modifier = Modifier.fillMaxWidth()) {
                Column {
                    CardHeader("IDENTITY DETAILS")
                    OutlinedTextField(
                        value = userName,
                        onValueChange = { scope.launch { aikoPrefs.setUserName(it) } },
                        label = { Text("Your Name") },
                        colors = outlinedTextFieldColors(),
                        shape = RoundedCornerShape(14.dp),
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 2. CONNECTION SYSTEM
            EditorialCard(modifier = Modifier.fillMaxWidth()) {
                Column {
                    CardHeader("CONNECTION INSTANCE")
                    
                    Text("Connection Mode", style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.SemiBold))
                    Spacer(Modifier.height(8.dp))
                    
                    listOf("Link to Desktop", "Local on Phone", "Remote Ollama Server").forEach { mode ->
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable {
                                    scope.launch {
                                        aikoPrefs.setConnectionMode(mode)
                                        aikoPrefs.setDesktopConnected(mode == "Link to Desktop")
                                    }
                                }
                                .padding(vertical = 6.dp)
                        ) {
                            RadioButton(
                                selected = connectionMode == mode,
                                onClick = {
                                    scope.launch {
                                        aikoPrefs.setConnectionMode(mode)
                                        aikoPrefs.setDesktopConnected(mode == "Link to Desktop")
                                    }
                                },
                                colors = RadioButtonDefaults.colors(selectedColor = AikoColors.Accent)
                            )
                            Spacer(Modifier.width(8.dp))
                            Text(mode, style = AikoTypography.bodyMedium)
                        }
                    }

                    if (connectionMode == "Link to Desktop") {
                        Spacer(modifier = Modifier.height(14.dp))
                        OutlinedTextField(
                            value = desktopUrl,
                            onValueChange = { scope.launch { aikoPrefs.setDesktopUrl(it) } },
                            label = { Text("Aiko Desktop Server URL") },
                            trailingIcon = {
                                IconButton(onClick = {
                                    val isGranted = ContextCompat.checkSelfPermission(
                                        context,
                                        Manifest.permission.CAMERA
                                    ) == PackageManager.PERMISSION_GRANTED
                                    if (isGranted) {
                                        qrScannerOpen = true
                                    } else {
                                        cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
                                    }
                                }) {
                                    Icon(Icons.Default.QrCodeScanner, "Scan QR Code", tint = AikoColors.Accent)
                                }
                            },
                            colors = outlinedTextFieldColors(),
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier.fillMaxWidth()
                        )
                    } else {
                        Spacer(modifier = Modifier.height(14.dp))
                        OutlinedTextField(
                            value = apiKey,
                            onValueChange = { scope.launch { aikoPrefs.setApiKey(it) } },
                            label = { Text("Local / Remote API Key") },
                            visualTransformation = PasswordVisualTransformation(),
                            colors = outlinedTextFieldColors(),
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier.fillMaxWidth()
                        )
                        Spacer(modifier = Modifier.height(14.dp))
                        OutlinedTextField(
                            value = modelChoice,
                            onValueChange = { scope.launch { aikoPrefs.setModelChoice(it) } },
                            label = { Text("LLM Model Name") },
                            colors = outlinedTextFieldColors(),
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 3. APPEARANCE & THEME
            EditorialCard(modifier = Modifier.fillMaxWidth()) {
                Column {
                    CardHeader("INTERFACE STYLING")

                    Text("Accent Theme Color", style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.SemiBold))
                    Spacer(Modifier.height(8.dp))
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        OutlinedTextField(
                            value = themeAccentColor,
                            onValueChange = { newValue ->
                                if (newValue.length <= 7) {
                                    scope.launch { aikoPrefs.setThemeAccentColor(newValue) }
                                }
                            },
                            label = { Text("Hex Color Code") },
                            colors = outlinedTextFieldColors(),
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier.weight(1f)
                        )
                        Spacer(Modifier.width(16.dp))
                        Box(
                            modifier = Modifier
                                .size(48.dp)
                                .clip(CircleShape)
                                .background(AikoColors.Accent)
                                .border(1.dp, AikoColors.TextSecondary, CircleShape)
                        )
                    }

                    Spacer(modifier = Modifier.height(18.dp))
                    Text("System Font Type", style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.SemiBold))
                    Spacer(modifier = Modifier.height(8.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        AikoFonts.allKeys.forEach { key ->
                            val selected = chatFont == key
                            Surface(
                                onClick = { scope.launch { aikoPrefs.setChatFont(key) } },
                                color = if (selected) AikoColors.Accent.copy(alpha = 0.15f) else AikoColors.Surface,
                                border = if (selected) BorderStroke(1.5.dp, AikoColors.Accent) else BorderStroke(1.dp, AikoColors.TextSecondary.copy(alpha = 0.3f)),
                                shape = RoundedCornerShape(12.dp)
                            ) {
                                Text(
                                    text = AikoFonts.labelFor(key),
                                    style = AikoTypography.bodyMedium.copy(
                                        color = if (selected) AikoColors.Accent else AikoColors.TextPrimary,
                                        fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal
                                    ),
                                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp)
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(18.dp))
                    Text("Interactive Avatar Mode", style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.SemiBold))
                    Spacer(modifier = Modifier.height(8.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        listOf("WebView" to "Live2D", "Static" to "Offline Card").forEach { (key, label) ->
                            val selected = avatarMode == key
                            Surface(
                                onClick = { scope.launch { aikoPrefs.setAvatarMode(key) } },
                                modifier = Modifier.weight(1f),
                                color = if (selected) AikoColors.Accent.copy(alpha = 0.15f) else AikoColors.Surface,
                                border = if (selected) BorderStroke(1.5.dp, AikoColors.Accent) else BorderStroke(1.dp, AikoColors.TextSecondary.copy(alpha = 0.3f)),
                                shape = RoundedCornerShape(12.dp)
                            ) {
                                Box(contentAlignment = Alignment.Center, modifier = Modifier.padding(vertical = 10.dp)) {
                                    Text(
                                        text = label,
                                        style = AikoTypography.bodyMedium.copy(
                                            color = if (selected) AikoColors.Accent else AikoColors.TextPrimary,
                                            fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal
                                        )
                                    )
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(18.dp))
                    Text("Chat Wallpaper", style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.SemiBold))
                    Spacer(modifier = Modifier.height(8.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        allWallpaperKeys.forEach { key ->
                            val selected = chatWallpaper == key
                            val color = wallpaperPreviewColor(key)
                            val label = wallpaperLabel(key)
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                modifier = Modifier.clickable { scope.launch { aikoPrefs.setChatWallpaper(key) } }
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(64.dp)
                                        .clip(RoundedCornerShape(10.dp))
                                        .background(color)
                                        .border(
                                            width = if (selected) 2.dp else 1.dp,
                                            color = if (selected) AikoColors.Accent else Color.Transparent,
                                            shape = RoundedCornerShape(10.dp)
                                        )
                                )
                                Spacer(Modifier.height(4.dp))
                                Text(
                                    text = label,
                                    style = AikoTypography.labelMedium.copy(fontSize = 10.sp),
                                    maxLines = 1
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(18.dp))
                    
                    // Local mutable state representation for the text size slider
                    var localTextSize by remember(chatTextSize) { mutableStateOf(chatTextSize) }
                    Text("Chat Text Scale: ${(localTextSize * 100).toInt()}%", style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.SemiBold))
                    Slider(
                        value = localTextSize,
                        onValueChange = { localTextSize = it },
                        onValueChangeFinished = { scope.launch { aikoPrefs.setChatTextSize(localTextSize) } },
                        valueRange = 0.8f..1.4f,
                        colors = SliderDefaults.colors(
                            thumbColor = AikoColors.Accent,
                            activeTrackColor = AikoColors.Accent,
                            inactiveTrackColor = AikoColors.AccentSoft
                        )
                    )

                    Spacer(modifier = Modifier.height(14.dp))
                    Text("Chat Bubble Style", style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.SemiBold))
                    Spacer(modifier = Modifier.height(8.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        listOf("default" to "Classic", "minimal" to "Minimal", "bordered" to "Bordered").forEach { (key, label) ->
                            val selected = chatBubbleStyle == key
                            Surface(
                                onClick = { scope.launch { aikoPrefs.setChatBubbleStyle(key) } },
                                modifier = Modifier.weight(1f),
                                color = if (selected) AikoColors.Accent.copy(alpha = 0.15f) else AikoColors.Surface,
                                border = if (selected) BorderStroke(1.5.dp, AikoColors.Accent) else BorderStroke(1.dp, AikoColors.TextSecondary.copy(alpha = 0.3f)),
                                shape = RoundedCornerShape(12.dp)
                            ) {
                                Box(contentAlignment = Alignment.Center, modifier = Modifier.padding(vertical = 10.dp)) {
                                    Text(
                                        text = label,
                                        style = AikoTypography.bodyMedium.copy(
                                            color = if (selected) AikoColors.Accent else AikoColors.TextPrimary,
                                            fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal
                                        )
                                    )
                                }
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 3b. SOMATIC ANIMATION INTENSITIES
            EditorialCard(modifier = Modifier.fillMaxWidth()) {
                Column {
                    CardHeader("SOMATIC INTENSITIES")
                    SomaticSlider("Jitter", jitter) { scope.launch { aikoPrefs.setJitterIntensity(it) } }
                    SomaticSlider("Tear Flow", tear) { scope.launch { aikoPrefs.setTearIntensity(it) } }
                    SomaticSlider("Forward Lean", lean) { scope.launch { aikoPrefs.setLeanIntensity(it) } }
                    SomaticSlider("Cheek Blush", blush) { scope.launch { aikoPrefs.setBlushIntensity(it) } }
                    SomaticSlider("Pout Overlay", pout) { scope.launch { aikoPrefs.setPoutIntensity(it) } }
                    SomaticSlider("Boba Wobble", boba) { scope.launch { aikoPrefs.setBobaIntensity(it) } }
                    SomaticSlider("Oxytocin", oxytocin) { scope.launch { aikoPrefs.setOxytocinIntensity(it) } }
                    SomaticSlider("Melatonin", melatonin) { scope.launch { aikoPrefs.setMelatoninIntensity(it) } }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 4. VOCALIZATION SETTINGS
            EditorialCard(modifier = Modifier.fillMaxWidth()) {
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text("Voice Output", style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.SemiBold))
                            Text("Enable text-to-speech feedback", style = AikoTypography.bodyMedium)
                        }
                        Switch(
                            checked = voiceEnabled,
                            onCheckedChange = { scope.launch { aikoPrefs.setVoiceEnabled(it) } },
                            colors = switchColors()
                        )
                    }

                    if (voiceEnabled) {
                        Spacer(modifier = Modifier.height(14.dp))
                        Text("TTS Engine Provider", style = AikoTypography.bodyMedium.copy(fontWeight = FontWeight.SemiBold))
                        Spacer(modifier = Modifier.height(6.dp))
                        
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            listOf("native" to "Native TTS", "custom_api" to "Custom API").forEach { (key, label) ->
                                val selected = ttsEngine == key
                                Surface(
                                    onClick = { scope.launch { aikoPrefs.setTtsEngine(key) } },
                                    modifier = Modifier.weight(1f),
                                    color = if (selected) AikoColors.Accent.copy(alpha = 0.15f) else AikoColors.Surface,
                                    border = if (selected) BorderStroke(1.5.dp, AikoColors.Accent) else BorderStroke(1.dp, AikoColors.TextSecondary.copy(alpha = 0.3f)),
                                    shape = RoundedCornerShape(12.dp)
                                ) {
                                    Box(contentAlignment = Alignment.Center, modifier = Modifier.padding(vertical = 10.dp)) {
                                        Text(
                                            text = label,
                                            style = AikoTypography.bodyMedium.copy(
                                                color = if (selected) AikoColors.Accent else AikoColors.TextPrimary,
                                                fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal
                                            )
                                        )
                                    }
                                }
                            }
                        }

                        if (ttsEngine == "custom_api") {
                            Spacer(modifier = Modifier.height(14.dp))
                            OutlinedTextField(
                                value = ttsApiUrl,
                                onValueChange = { scope.launch { aikoPrefs.setTtsApiUrl(it) } },
                                label = { Text("TTS API URL") },
                                colors = outlinedTextFieldColors(),
                                shape = RoundedCornerShape(14.dp),
                                modifier = Modifier.fillMaxWidth()
                            )
                            Spacer(modifier = Modifier.height(10.dp))
                            OutlinedTextField(
                                value = ttsApiKey,
                                onValueChange = { scope.launch { aikoPrefs.setTtsApiKey(it) } },
                                label = { Text("TTS API Key (Optional)") },
                                visualTransformation = PasswordVisualTransformation(),
                                colors = outlinedTextFieldColors(),
                                shape = RoundedCornerShape(14.dp),
                                modifier = Modifier.fillMaxWidth()
                            )
                            Spacer(modifier = Modifier.height(10.dp))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                OutlinedTextField(
                                    value = ttsApiVoice,
                                    onValueChange = { scope.launch { aikoPrefs.setTtsApiVoice(it) } },
                                    label = { Text("Voice ID / Name") },
                                    colors = outlinedTextFieldColors(),
                                    shape = RoundedCornerShape(14.dp),
                                    modifier = Modifier.weight(1f)
                                )
                                OutlinedTextField(
                                    value = ttsApiModel,
                                    onValueChange = { scope.launch { aikoPrefs.setTtsApiModel(it) } },
                                    label = { Text("Model ID") },
                                    colors = outlinedTextFieldColors(),
                                    shape = RoundedCornerShape(14.dp),
                                    modifier = Modifier.weight(1f)
                                )
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 5. NEURAL MEMORY SYNC
            EditorialCard(modifier = Modifier.fillMaxWidth()) {
                Column {
                    CardHeader("OFFLINE MEMORY SYNC")
                    
                    val dateStr = if (lastSyncTimestamp == 0L) {
                        "Never Synced"
                    } else {
                        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.ROOT)
                        sdf.format(Date(lastSyncTimestamp))
                    }
                    
                    Text("Last Synced: $dateStr", style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.SemiBold))
                    Text("Synchronizes offline memories with desktop hub ChromaDB.", style = AikoTypography.bodyMedium)
                    Spacer(Modifier.height(14.dp))
                    
                    Button(
                        onClick = {
                            if (syncInProgress) return@Button
                            syncInProgress = true
                            scope.launch {
                                val ok = chatRepository.syncMemories()
                                syncInProgress = false
                                val msg = if (ok) "Memory sync completed successfully!" else "Memory sync failed. Verify link."
                                Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
                            }
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = AikoColors.Accent, contentColor = AikoColors.Background),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        if (syncInProgress) {
                            CircularProgressIndicator(modifier = Modifier.size(20.dp), color = AikoColors.Background, strokeWidth = 2.dp)
                            Spacer(Modifier.width(8.dp))
                        }
                        Text("Consolidate Memories Now")
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 6. DANGER RESETS
            EditorialButton(
                text = "Erase Memories & Re-align",
                backgroundColor = AikoColors.Surface,
                onClick = {
                    scope.launch {
                        chatRepository.clearHistory()
                        Toast.makeText(context, "All memory logs cleared.", Toast.LENGTH_SHORT).show()
                    }
                }
            )
            Spacer(modifier = Modifier.height(96.dp))
        }

        if (qrScannerOpen) {
            QrCodeScannerView(
                onQrScanned = { result ->
                    qrScannerOpen = false
                    scope.launch {
                        aikoPrefs.setDesktopUrl(result)
                        aikoPrefs.setConnectionMode("Link to Desktop")
                        aikoPrefs.setDesktopConnected(true)
                        Toast.makeText(context, "Linked to $result!", Toast.LENGTH_SHORT).show()
                    }
                },
                onClose = { qrScannerOpen = false }
            )
        }
    }
}

@Composable
private fun CardHeader(title: String) {
    Text(
        text = title,
        style = AikoTypography.labelMedium.copy(
            fontWeight = FontWeight.Bold,
            color = AikoColors.TextSecondary,
            letterSpacing = 1.sp
        ),
        modifier = Modifier.padding(bottom = 12.dp)
    )
}

/**
 * A debounced custom slider wrapper that only saves state in data store on touch release
 */
@Composable
private fun SomaticSlider(
    name: String,
    value: Float,
    onFinished: (Float) -> Unit
) {
    var localValue by remember(value) { mutableStateOf(value) }
    Column {
        Text("$name: ${(localValue * 100).toInt()}%", style = AikoTypography.labelMedium)
        Slider(
            value = localValue,
            onValueChange = { localValue = it },
            onValueChangeFinished = { onFinished(localValue) },
            colors = SliderDefaults.colors(
                thumbColor = AikoColors.Accent,
                activeTrackColor = AikoColors.Accent,
                inactiveTrackColor = AikoColors.AccentSoft
            )
        )
        Spacer(modifier = Modifier.height(4.dp))
    }
}

@Composable
private fun outlinedTextFieldColors() = OutlinedTextFieldDefaults.colors(
    focusedBorderColor = AikoColors.Accent,
    unfocusedBorderColor = AikoColors.TextSecondary,
    focusedTextColor = AikoColors.TextPrimary,
    unfocusedTextColor = AikoColors.TextPrimary,
    focusedLabelColor = AikoColors.Accent,
    unfocusedLabelColor = AikoColors.TextSecondary
)

@Composable
private fun switchColors() = SwitchDefaults.colors(
    checkedThumbColor = Color.White,
    checkedTrackColor = AikoColors.Accent,
    uncheckedThumbColor = AikoColors.TextSecondary,
    uncheckedTrackColor = AikoColors.Surface
)
