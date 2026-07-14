package com.aiko.app.ui.screens.chat

import android.Manifest
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.util.Base64
import android.util.Log
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.text.AnnotatedString
import com.aiko.app.ui.components.ChatWallpaper
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.aiko.app.data.local.AikoPrefs
import kotlinx.coroutines.delay
import com.aiko.app.data.local.MessageEntity
import com.aiko.app.data.repository.ChatRepository
import com.aiko.app.domain.EmotionEngine
import com.aiko.app.domain.EmotionState
import com.aiko.app.ui.components.AikoAvatar
import com.aiko.app.ui.theme.AikoColors
import com.aiko.app.ui.theme.AikoTypography
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream

// Strips XML tags (think, emotion, thought, etc.) and system tool codes
private val tagCleanerRegex = Regex("""<(think|emotion|thought|relevant_memory_context|current_visual_awareness)>.*?</\1>|<.*?>|\[(?:SCAN|MCP|TASK|BIO_REGISTER|GAME|OPEN|TYPE|CLICK|PRESS|WAIT|WALLPAPER|WEATHER|MUSIC|LETTER|VTS_BG|IMAGE|RECALL|LATEX|REFLECTIVE_STATE|GIF)[^\]]*?\]""", RegexOption.IGNORE_CASE)

private fun cleanText(value: String): String {
    return value.replace(tagCleanerRegex, "").trim()
}

@Composable
fun loadAssetImage(context: Context, path: String): Bitmap? {
    return remember(path) {
        try {
            context.assets.open(path).use { stream ->
                BitmapFactory.decodeStream(stream)
            }
        } catch (e: Exception) {
            null
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    chatRepository: ChatRepository,
    emotionEngine: EmotionEngine,
    aikoPrefs: AikoPrefs,
    onOpenSettings: () -> Unit,
    modifier: Modifier = Modifier
) {
    val messages by chatRepository.getMessages("default").collectAsState(initial = emptyList())
    val chemistry by chatRepository.currentEmotion.collectAsState()
    val amplitude by chatRepository.currentAmplitude.collectAsState()
    val connectionMode by aikoPrefs.connectionModeFlow.collectAsState("Link to Desktop")
    val avatarMode by aikoPrefs.avatarModeFlow.collectAsState("WebView")
    val chatWallpaper by aikoPrefs.chatWallpaperFlow.collectAsState("default")
    val chatBubbleStyle by aikoPrefs.chatBubbleStyleFlow.collectAsState("default")

    val haptic = LocalHapticFeedback.current

    val scope = rememberCoroutineScope()
    val listState = rememberLazyListState()

    var draft by rememberSaveable { mutableStateOf("") }
    var streaming by remember { mutableStateOf("") }
    var thinking by remember { mutableStateOf(false) }
    var drawerOpen by remember { mutableStateOf(false) }
    var moodOpen by remember { mutableStateOf(false) }
    var voiceListening by remember { mutableStateOf(false) }

    var avatarExpanded by remember { mutableStateOf(true) }
    var stickerPickerOpen by remember { mutableStateOf(false) }
    var cameraOpen by remember { mutableStateOf(false) }
    var attachedImage by remember { mutableStateOf<Bitmap?>(null) }
    var showMemorySyncBanner by remember { mutableStateOf(false) }
    var syncSuccess by remember { mutableStateOf(false) }

    // Scroll to bottom on new message
    LaunchedEffect(messages.size, streaming.length) {
        val finalIndex = if (streaming.isNotEmpty()) messages.size else messages.lastIndex
        if (finalIndex >= 0) listState.animateScrollToItem(finalIndex)
    }

    // Camera permission launcher
    val cameraPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            cameraOpen = true
        } else {
            Log.e("ChatScreen", "Camera permission denied")
        }
    }

    if (moodOpen) {
        MoodSheet(chemistry, emotionEngine.determineDominantEmotion(chemistry), { moodOpen = false })
    }

    if (stickerPickerOpen) {
        StickerPickerSheet(
            onStickerSelected = { stickerName ->
                stickerPickerOpen = false
                scope.launch {
                    val stickerCode = "[STICKER:$stickerName]"
                    chatRepository.finalizeAikoResponse("default", stickerCode)
                }
            },
            onDismiss = { stickerPickerOpen = false }
        )
    }

    Box(modifier.fillMaxSize()) {
        ChatWallpaper(wallpaperKey = chatWallpaper, modifier = Modifier.fillMaxSize())
        Column(Modifier.fillMaxSize().navigationBarsPadding()) {
            AikoTopBar(
                connectionMode = connectionMode,
                avatarExpanded = avatarExpanded,
                onToggleAvatar = { avatarExpanded = !avatarExpanded },
                onMenu = { drawerOpen = true },
                onSettings = onOpenSettings
            )
            
            MoodStrip(
                state = chemistry,
                mood = emotionEngine.determineDominantEmotion(chemistry),
                modifier = Modifier.clickable { moodOpen = true }
            )

            // Dynamic live-updating sync banner
            AnimatedVisibility(showMemorySyncBanner) {
                Surface(
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 6.dp),
                    color = if (syncSuccess) AikoColors.Surface else AikoColors.Surface,
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = if (syncSuccess) Icons.Default.CloudDone else Icons.Default.CloudSync,
                            contentDescription = "Sync",
                            tint = AikoColors.Accent
                        )
                        Spacer(Modifier.width(10.dp))
                        Text(
                            text = if (syncSuccess) "Memories consolidated with Desktop!" else "Synchronizing memories...",
                            style = AikoTypography.bodyMedium
                        )
                    }
                }
            }

            // Expandable Live2D / 3D Avatar Area
            AnimatedVisibility(
                visible = avatarExpanded,
                enter = fadeIn(),
                exit = fadeOut()
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(230.dp)
                        .background(AikoColors.Background),
                    contentAlignment = Alignment.Center
                ) {
                    AikoAvatar(
                        emotionState = chemistry,
                        dominantEmotion = emotionEngine.determineDominantEmotion(chemistry),
                        isTyping = thinking,
                        isSpeaking = amplitude > 0.05f,
                        avatarMode = avatarMode,
                        size = 210.dp
                    )
                }
            }

            if (messages.isEmpty() && streaming.isEmpty()) {
                EmptyChat(Modifier.weight(1f), onStart = {})
            } else {
                LazyColumn(
                    state = listState,
                    modifier = Modifier.weight(1f).fillMaxWidth(),
                    contentPadding = PaddingValues(horizontal = 20.dp, vertical = 18.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(messages, key = { it.id }) { AnimatedMessageCard(it, chatBubbleStyle) }
                    if (streaming.isNotEmpty()) {
                        item {
                            MessageCard(
                                MessageEntity(
                                    conversationId = "default",
                                    role = "aiko",
                                    content = streaming,
                                    emotionTag = null
                                ),
                                bubbleStyle = chatBubbleStyle
                            )
                        }
                    }
                    if (thinking && streaming.isEmpty()) {
                        item { ThinkingRow() }
                    }
                }
            }

            // Preview of attached image
            attachedImage?.let { img ->
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 20.dp, vertical = 4.dp),
                    contentAlignment = Alignment.TopStart
                ) {
                    Box(
                        modifier = Modifier
                            .size(80.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .border(1.5.dp, AikoColors.Accent, RoundedCornerShape(12.dp))
                    ) {
                        Image(
                            bitmap = img.asImageBitmap(),
                            contentDescription = "Attachment preview",
                            modifier = Modifier.fillMaxSize()
                        )
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .background(Color.Black.copy(alpha = 0.3f))
                                .clickable { attachedImage = null },
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(Icons.Default.Delete, "Remove", tint = Color.White)
                        }
                    }
                }
            }

            Composer(
                text = draft,
                onTextChange = { draft = it },
                listening = voiceListening,
                onVoice = { voiceListening = !voiceListening },
                onAttach = { stickerPickerOpen = true },
                onCamera = {
                    cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
                },
                onSend = {
                    val prompt = draft.trim()
                    if ((prompt.isEmpty() && attachedImage == null) || thinking) return@Composer
                    
                    // Trigger haptic feedback
                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                    
                    draft = ""
                    thinking = true
                    streaming = ""
                    
                    val imageToAttach = attachedImage
                    attachedImage = null
                    
                    scope.launch {
                        var base64Str: String? = null
                        if (imageToAttach != null) {
                            val outputStream = ByteArrayOutputStream()
                            imageToAttach.compress(Bitmap.CompressFormat.JPEG, 85, outputStream)
                            base64Str = Base64.encodeToString(outputStream.toByteArray(), Base64.DEFAULT)
                        }
                        
                        var full = ""
                        runCatching {
                            chatRepository.streamAikoResponse("default", prompt, base64Str).collect { token ->
                                full += token
                                streaming = cleanText(full)
                            }
                        }.onFailure { err ->
                            full = "Connection sync issues. Let's try linked network setup again."
                            streaming = full
                        }
                        
                        chatRepository.finalizeAikoResponse("default", full)
                        streaming = ""
                        thinking = false
                    }
                }
            )
        }

        ConversationDrawer(
            open = drawerOpen,
            messages = messages,
            onDismiss = { drawerOpen = false },
            onSyncMemory = {
                drawerOpen = false
                showMemorySyncBanner = true
                syncSuccess = false
                scope.launch {
                    val ok = chatRepository.syncMemories()
                    syncSuccess = ok
                    delay(3000)
                    showMemorySyncBanner = false
                }
            }
        )

        if (cameraOpen) {
            CameraCaptureView(
                onImageCaptured = { bitmap ->
                    attachedImage = bitmap
                    cameraOpen = false
                },
                onClose = { cameraOpen = false }
            )
        }
    }
}

@Composable
private fun AikoTopBar(
    connectionMode: String,
    avatarExpanded: Boolean,
    onToggleAvatar: () -> Unit,
    onMenu: () -> Unit,
    onSettings: () -> Unit
) = Surface(
    color = AikoColors.Background.copy(alpha = 0.92f),
    modifier = Modifier.fillMaxWidth()
) {
    Row(
        Modifier.fillMaxWidth().statusBarsPadding().height(64.dp).padding(horizontal = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        IconButton(onMenu, Modifier.size(48.dp)) {
            Icon(Icons.Default.Menu, "Conversations", tint = AikoColors.TextPrimary)
        }
        Column(modifier = Modifier.weight(1f)) {
            Text("Aiko", style = AikoTypography.titleLarge)
            Text(
                text = connectionMode,
                style = AikoTypography.labelMedium.copy(fontSize = 10.sp, color = AikoColors.Accent)
            )
        }
        IconButton(onToggleAvatar, Modifier.size(48.dp)) {
            Icon(
                imageVector = if (avatarExpanded) Icons.Default.Visibility else Icons.Default.VisibilityOff,
                contentDescription = "Toggle avatar view",
                tint = AikoColors.TextPrimary
            )
        }
        IconButton(onSettings, Modifier.size(48.dp)) {
            Icon(Icons.Default.Settings, "Settings", tint = AikoColors.TextPrimary)
        }
    }
}

@Composable
private fun MoodStrip(state: EmotionState, mood: String, modifier: Modifier) = Row(
    modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 4.dp).clip(RoundedCornerShape(18.dp)).background(AikoColors.Surface).padding(10.dp),
    verticalAlignment = Alignment.CenterVertically
) {
    Box(Modifier.size(30.dp).clip(CircleShape).background(AikoColors.AccentSoft), contentAlignment = Alignment.Center) {
        Text("A", style = AikoTypography.bodyMedium.copy(color = AikoColors.Accent, fontWeight = FontWeight.Bold))
    }
    Spacer(Modifier.width(10.dp))
    Column(Modifier.weight(1f)) {
        Text("Aiko feels ${mood.replaceFirstChar { it.uppercase() }}", style = AikoTypography.bodyMedium.copy(color = AikoColors.TextPrimary))
        Text("Tap to review current states", style = AikoTypography.labelMedium)
    }
    Icon(Icons.Default.KeyboardArrowUp, null, tint = AikoColors.TextSecondary)
}

@Composable
private fun EmptyChat(modifier: Modifier, onStart: () -> Unit) = Box(
    modifier = modifier.fillMaxSize(),
    contentAlignment = Alignment.Center
) {
    Surface(
        color = AikoColors.Surface.copy(alpha = 0.4f),
        border = androidx.compose.foundation.BorderStroke(1.dp, AikoColors.Accent.copy(alpha = 0.12f)),
        shape = RoundedCornerShape(24.dp),
        modifier = Modifier.padding(24.dp).fillMaxWidth(0.9f)
    ) {
        Column(
            modifier = Modifier.padding(28.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text("❦", style = AikoTypography.headlineLarge.copy(color = AikoColors.Accent, fontSize = 44.sp))
            Spacer(Modifier.height(16.dp))
            Text("A quiet place to begin.", style = AikoTypography.titleLarge)
            Spacer(Modifier.height(10.dp))
            Text(
                text = "Aiko remembers what matters, syncing persistently over your devices.",
                style = AikoTypography.bodyMedium,
                textAlign = TextAlign.Center
            )
        }
    }
}

@Composable
private fun AnimatedMessageCard(message: MessageEntity, bubbleStyle: String) {
    var visible by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        visible = true
    }
    androidx.compose.animation.AnimatedVisibility(
        visible = visible,
        enter = androidx.compose.animation.fadeIn(animationSpec = tween(400)) + 
                androidx.compose.animation.slideInVertically(
                    initialOffsetY = { it / 3 },
                    animationSpec = tween(400, easing = FastOutSlowInEasing)
                )
    ) {
        MessageCard(message = message, bubbleStyle = bubbleStyle)
    }
}

private fun formatTime(timestamp: Long): String {
    val sdf = java.text.SimpleDateFormat("HH:mm", java.util.Locale.getDefault())
    return sdf.format(java.util.Date(timestamp))
}

@Composable
private fun MessageCard(message: MessageEntity, bubbleStyle: String = "default") {
    val user = message.role == "user"
    var actions by remember { mutableStateOf(false) }
    val context = LocalContext.current
    val clipboardManager = LocalClipboardManager.current

    val shape = RoundedCornerShape(20.dp, 20.dp, if (user) 4.dp else 20.dp, if (user) 20.dp else 4.dp)
    
    val bubbleBrush = if (user) {
        Brush.linearGradient(
            colors = listOf(
                AikoColors.Accent.copy(alpha = 0.24f),
                AikoColors.Accent.copy(alpha = 0.08f)
            )
        )
    } else {
        Brush.linearGradient(
            colors = listOf(
                AikoColors.Surface,
                AikoColors.Surface.copy(alpha = 0.75f)
            )
        )
    }

    val border = when (bubbleStyle) {
        "bordered" -> androidx.compose.foundation.BorderStroke(1.dp, if (user) AikoColors.Accent else AikoColors.TextSecondary.copy(alpha = 0.5f))
        else -> null
    }

    Column(Modifier.fillMaxWidth(), horizontalAlignment = if (user) Alignment.End else Alignment.Start) {
        Surface(
            color = if (bubbleStyle == "minimal") Color.Transparent else Color.Transparent,
            border = border,
            shape = shape,
            modifier = Modifier
                .fillMaxWidth(.86f)
                .then(
                    if (bubbleStyle != "minimal") {
                        Modifier.background(brush = bubbleBrush, shape = shape)
                    } else {
                        Modifier
                    }
                )
                .clickable { actions = !actions }
        ) {
            val content = message.content
            if (content.startsWith("[STICKER:") && content.endsWith("]")) {
                val stickerName = content.removePrefix("[STICKER:").removeSuffix("]")
                val bitmap = loadAssetImage(context, "stickers/$stickerName")
                if (bitmap != null) {
                    Image(
                        bitmap = bitmap.asImageBitmap(),
                        contentDescription = "Sticker asset",
                        modifier = Modifier.size(120.dp).padding(10.dp)
                    )
                } else {
                    Text("[Sticker: $stickerName]", style = AikoTypography.bodyLarge, modifier = Modifier.padding(16.dp))
                }
            } else {
                Text(cleanText(content), style = AikoTypography.bodyLarge, modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp))
            }
        }
        
        Text(
            text = formatTime(message.timestamp),
            style = AikoTypography.labelMedium.copy(fontSize = 10.sp),
            modifier = Modifier.padding(top = 2.dp, start = if (user) 0.dp else 6.dp, end = if (user) 6.dp else 0.dp)
        )

        AnimatedVisibility(actions, enter = fadeIn(), exit = fadeOut()) {
            Row(Modifier.padding(top = 4.dp)) {
                TextButton({ 
                    clipboardManager.setText(AnnotatedString(cleanText(message.content)))
                    actions = false 
                }) {
                    Text("Copy", style = AikoTypography.labelMedium.copy(color = AikoColors.Accent))
                }
                if (!user) {
                    val speakScope = rememberCoroutineScope()
                    TextButton({
                        actions = false
                        speakScope.launch {
                            chatRepository.speakText(message.content)
                        }
                    }) {
                        Text("Speak", style = AikoTypography.labelMedium.copy(color = AikoColors.Accent))
                    }
                }
            }
        }
    }
}

@Composable
private fun ThinkingRow() = Row(
    Modifier.padding(12.dp),
    verticalAlignment = Alignment.CenterVertically
) {
    CircularProgressIndicator(Modifier.size(16.dp), strokeWidth = 2.dp, color = AikoColors.Accent)
    Spacer(Modifier.width(10.dp))
    Text("Aiko is thinking", style = AikoTypography.bodyMedium)
}

@Composable
private fun Composer(
    text: String,
    onTextChange: (String) -> Unit,
    listening: Boolean,
    onVoice: () -> Unit,
    onAttach: () -> Unit,
    onCamera: () -> Unit,
    onSend: () -> Unit
) = Surface(
    Modifier.fillMaxWidth().imePadding().padding(12.dp),
    color = AikoColors.Surface.copy(alpha = 0.85f),
    border = androidx.compose.foundation.BorderStroke(1.dp, AikoColors.TextSecondary.copy(alpha = 0.15f)),
    shape = RoundedCornerShape(28.dp)
) {
    Row(
        Modifier.padding(start = 6.dp, end = 6.dp, top = 4.dp, bottom = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        IconButton(onAttach, Modifier.size(40.dp)) {
            Icon(Icons.Default.StickyNote2, "Stickers", tint = AikoColors.TextSecondary)
        }
        IconButton(onCamera, Modifier.size(40.dp)) {
            Icon(Icons.Default.PhotoCamera, "Camera", tint = AikoColors.TextSecondary)
        }
        TextField(
            value = text,
            onValueChange = onTextChange,
            modifier = Modifier.weight(1f).heightIn(max = 130.dp),
            placeholder = { Text("Speak your mind…", style = AikoTypography.bodyMedium) },
            textStyle = AikoTypography.bodyLarge,
            colors = TextFieldDefaults.colors(
                focusedContainerColor = Color.Transparent,
                unfocusedContainerColor = Color.Transparent,
                focusedIndicatorColor = Color.Transparent,
                unfocusedIndicatorColor = Color.Transparent
            )
        )
        IconButton(onVoice, Modifier.size(40.dp)) {
            Icon(
                imageVector = if (listening) Icons.Default.GraphicEq else Icons.Default.Mic,
                contentDescription = "Voice Input",
                tint = if (listening) AikoColors.Accent else AikoColors.TextSecondary
            )
        }
        IconButton(
            onClick = onSend,
            modifier = Modifier.size(40.dp).clip(CircleShape).background(AikoColors.Accent)
        ) {
            Icon(Icons.AutoMirrored.Filled.Send, "Send", tint = AikoColors.Background)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MoodSheet(state: EmotionState, mood: String, dismiss: () -> Unit) = ModalBottomSheet(
    onDismissRequest = dismiss,
    containerColor = AikoColors.Surface,
    contentColor = AikoColors.TextPrimary
) {
    Column(Modifier.padding(horizontal = 24.dp).padding(bottom = 32.dp)) {
        Text("Aiko feels ${mood.replaceFirstChar { it.uppercase() }}", style = AikoTypography.titleLarge)
        Spacer(Modifier.height(8.dp))
        Text("A live reflection from her neural state.", style = AikoTypography.bodyMedium)
        Spacer(Modifier.height(22.dp))
        listOf(
            "Dopamine" to state.dopamine,
            "Serotonin" to state.serotonin,
            "Cortisol" to state.cortisol,
            "Adrenaline" to state.adrenaline
        ).forEach { (name, value) ->
            Text(name, style = AikoTypography.labelMedium.copy(color = AikoColors.TextPrimary))
            Spacer(Modifier.height(6.dp))
            LinearProgressIndicator(
                progress = { value },
                modifier = Modifier.fillMaxWidth().height(6.dp).clip(CircleShape),
                color = AikoColors.Accent.copy(alpha = .35f + value * .65f),
                trackColor = AikoColors.AccentSoft
            )
            Spacer(Modifier.height(16.dp))
        }
    }
}

@Composable
private fun ConversationDrawer(
    open: Boolean,
    messages: List<MessageEntity>,
    onDismiss: () -> Unit,
    onSyncMemory: () -> Unit
) = AnimatedVisibility(
    visible = open,
    enter = fadeIn() + slideInHorizontally { -it },
    exit = fadeOut() + slideOutHorizontally { -it }
) {
    Surface(Modifier.fillMaxHeight().fillMaxWidth(.88f), color = AikoColors.Surface) {
        Column(Modifier.statusBarsPadding().padding(20.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Conversations", style = AikoTypography.titleLarge, modifier = Modifier.weight(1f))
                IconButton(onDismiss) {
                    Icon(Icons.Default.Close, "Close", tint = AikoColors.TextPrimary)
                }
            }
            Spacer(Modifier.height(20.dp))
            
            // Memory Sync Trigger Row
            Surface(
                modifier = Modifier.fillMaxWidth().clickable { onSyncMemory() },
                color = AikoColors.AccentSoft,
                shape = RoundedCornerShape(14.dp)
            ) {
                Row(
                    modifier = Modifier.padding(14.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(Icons.Default.CloudSync, null, tint = AikoColors.Accent)
                    Spacer(Modifier.width(12.dp))
                    Column {
                        Text("Consolidate Memories", style = AikoTypography.bodyLarge.copy(fontWeight = FontWeight.Bold))
                        Text("Sync latest details from Desktop", style = AikoTypography.bodyMedium)
                    }
                }
            }
            
            Spacer(Modifier.height(20.dp))
            Text("Today", style = AikoTypography.labelMedium.copy(color = AikoColors.Accent))
            Spacer(Modifier.height(8.dp))
            Surface(Modifier.fillMaxWidth(), color = AikoColors.Surface, shape = RoundedCornerShape(16.dp)) {
                Column(Modifier.padding(14.dp)) {
                    Text(if (messages.isEmpty()) "New conversation" else cleanText(messages.first().content).take(28), style = AikoTypography.bodyLarge)
                    Text(
                        text = messages.lastOrNull()?.let { cleanText(it.content).take(55) } ?: "Start a conversation with Aiko",
                        style = AikoTypography.bodyMedium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
            Spacer(Modifier.weight(1f))
            Button(
                onClick = onDismiss,
                colors = ButtonDefaults.buttonColors(containerColor = AikoColors.Accent, contentColor = AikoColors.Background),
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Default.Add, null)
                Spacer(Modifier.width(6.dp))
                Text("New conversation")
            }
        }
    }
}

@Composable
fun StickerPickerSheet(
    onStickerSelected: (String) -> Unit,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val stickersList = remember {
        listOf(
            "01_Happy_Cheer.png", "02_Shy_Blush.png", "03_Surprised_Gasp.png",
            "04_Sleepy_Yawn.png", "05_Crying_Tears.png", "06_Confident_Smile.png",
            "07_Waving_Hello.png", "08_Thinking_Hmm.png", "09_Heart_Eyes.png",
            "10_Annoyed_Sigh.png", "11_Laughing_Giggle.png", "12_Sad_Pout.png",
            "13_Excited_Sparkle.png", "14_Winking_Tease.png", "15_Sick_Dizzy.png",
            "16_Determined_Focus.png", "17_Sipping_Tea.png", "18_Confident_Smirk_Left.png"
        )
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Choose a Sticker", style = AikoTypography.titleLarge) },
        text = {
            LazyVerticalGrid(
                columns = GridCells.Fixed(3),
                modifier = Modifier.height(280.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(stickersList) { stickerPath ->
                    val bitmap = loadAssetImage(context, "stickers/$stickerPath")
                    if (bitmap != null) {
                        Image(
                            bitmap = bitmap.asImageBitmap(),
                            contentDescription = stickerPath,
                            modifier = Modifier
                                .size(72.dp)
                                .clip(RoundedCornerShape(8.dp))
                                .background(AikoColors.Surface)
                                .clickable { onStickerSelected(stickerPath) }
                                .padding(6.dp)
                        )
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) { Text("Close", color = AikoColors.Accent) }
        },
        containerColor = AikoColors.Surface
    )
}

@Composable
fun CameraCaptureView(
    onImageCaptured: (Bitmap) -> Unit,
    onClose: () -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val cameraProviderFuture = remember { ProcessCameraProvider.getInstance(context) }
    val imageCapture = remember { ImageCapture.Builder().build() }

    Box(Modifier.fillMaxSize().background(Color.Black)) {
        AndroidView(
            factory = { ctx ->
                val previewView = PreviewView(ctx)
                cameraProviderFuture.addListener({
                    val cameraProvider = cameraProviderFuture.get()
                    val preview = Preview.Builder().build().also {
                        it.setSurfaceProvider(previewView.surfaceProvider)
                    }
                    try {
                        cameraProvider.unbindAll()
                        cameraProvider.bindToLifecycle(
                            lifecycleOwner,
                            CameraSelector.DEFAULT_BACK_CAMERA,
                            preview,
                            imageCapture
                        )
                    } catch (e: Exception) {
                        Log.e("CameraCaptureView", "Camera binding failed: ${e.message}")
                    }
                }, ContextCompat.getMainExecutor(ctx))
                previewView
            },
            modifier = Modifier.fillMaxSize()
        )

        // Capture overlays
        Box(
            modifier = Modifier.fillMaxSize().padding(bottom = 48.dp),
            contentAlignment = Alignment.BottomCenter
        ) {
            Row(
                modifier = Modifier.fillMaxWidth().padding(horizontal = 32.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(
                    onClick = onClose,
                    modifier = Modifier.size(56.dp).background(Color.DarkGray.copy(alpha = 0.5f), CircleShape)
                ) {
                    Icon(Icons.Default.Close, "Close", tint = Color.White)
                }

                Box(
                    modifier = Modifier
                        .size(72.dp)
                        .clip(CircleShape)
                        .background(Color.White)
                        .clickable {
                            val executor = ContextCompat.getMainExecutor(context)
                            imageCapture.takePicture(
                                executor,
                                object : ImageCapture.OnImageCapturedCallback() {
                                    override fun onCaptureSuccess(image: ImageProxy) {
                                        val buffer = image.planes[0].buffer
                                        val bytes = ByteArray(buffer.remaining())
                                        buffer.get(bytes)
                                        val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)

                                        val rotationDegrees = image.imageInfo.rotationDegrees
                                        val finalBitmap = if (rotationDegrees != 0) {
                                            val matrix = Matrix().apply { postRotate(rotationDegrees.toFloat()) }
                                            Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
                                        } else {
                                            bitmap
                                        }

                                        onImageCaptured(finalBitmap)
                                        image.close()
                                    }

                                    override fun onError(exception: ImageCaptureException) {
                                        Log.e("CameraCapture", "Capture failed: ${exception.message}")
                                    }
                                }
                            )
                        },
                    contentAlignment = Alignment.Center
                ) {
                    Box(Modifier.size(60.dp).clip(CircleShape).border(4.dp, Color.Black, CircleShape))
                }

                Spacer(Modifier.size(56.dp)) // UI Alignment spacer
            }
        }
    }
}
