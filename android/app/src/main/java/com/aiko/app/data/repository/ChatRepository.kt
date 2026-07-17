package com.aiko.app.data.repository

import android.content.Context
import android.util.Log
import com.aiko.app.data.local.AikoPrefs
import com.aiko.app.data.local.AikoDatabase
import androidx.room.withTransaction
import com.aiko.app.data.local.BondDao
import com.aiko.app.data.local.BondEntity
import com.aiko.app.data.local.EmotionLogDao
import com.aiko.app.data.local.EmotionLogEntity
import com.aiko.app.data.local.MemoryDao
import com.aiko.app.data.local.MemoryEntity
import com.aiko.app.data.local.MessageDao
import com.aiko.app.data.local.MessageEntity
import com.aiko.app.domain.EmotionEngine
import com.aiko.app.domain.EmotionState
import com.aiko.app.domain.MemoryExtractor
import com.aiko.app.domain.AikoVocalizer
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import org.json.JSONObject
import org.json.JSONArray
import org.webrtc.PeerConnection
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ChatRepository @Inject constructor(
    @ApplicationContext private val context: Context,
    private val messageDao: MessageDao,
    val memoryDao: MemoryDao,
    val emotionLogDao: EmotionLogDao,
    private val bondDao: BondDao,
    private val aikoPrefs: AikoPrefs,
    private val emotionEngine: EmotionEngine,
    private val memoryExtractor: MemoryExtractor,
    private val geminiService: GeminiService,
    private val vocalizer: AikoVocalizer,
    private val aikoDatabase: AikoDatabase
) {
    private val repositoryScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private val _currentEmotion = MutableStateFlow(EmotionState())
    val currentEmotion: StateFlow<EmotionState> = _currentEmotion.asStateFlow()

    private val _currentAmplitude = MutableStateFlow(0f)
    val currentAmplitude: StateFlow<Float> = _currentAmplitude.asStateFlow()

    // Shared streaming states for UI coordination
    val streamingText = MutableStateFlow("")
    val isThinking = MutableStateFlow(false)
    val proactiveMessage = MutableStateFlow<String?>(null)

    // WebSocket state variables
    private var webSocket: okhttp3.WebSocket? = null
    private var isConnecting = false
    private var reconnectDelay = 1000L
    private val wsClient = OkHttpClient.Builder()
        .pingInterval(15, java.util.concurrent.TimeUnit.SECONDS)
        .build()
    private var activeChatChannel: kotlinx.coroutines.channels.Channel<String>? = null

    // WebRTC client state variables
    private var webRtcClient: WebRtcClient? = null

    init {
        // Hydrate initial emotion state from DB
        repositoryScope.launch {
            val latestLog = emotionLogDao.getLatestLog()
            if (latestLog != null) {
                _currentEmotion.value = EmotionState(
                    dopamine = latestLog.dopamine,
                    serotonin = latestLog.serotonin,
                    cortisol = latestLog.cortisol,
                    adrenaline = latestLog.adrenaline
                )
            } else {
                // Seed a default log
                saveEmotionLog(_currentEmotion.value)
            }

            // Seed a default bond if none exists
            if (bondDao.getBond() == null) {
                bondDao.insertOrUpdateBond(BondEntity())
            }
        }
        
        // Start WebSocket Connection Monitor
        startWebSocketConnection()
    }

    fun getMessages(conversationId: String): Flow<List<MessageEntity>> {
        return messageDao.getMessagesForConversation(conversationId)
    }

    fun getMemories(): Flow<List<MemoryEntity>> {
        return memoryDao.getAllMemoriesFlow()
    }

    fun getBond(): Flow<BondEntity> {
        return bondDao.getBondFlow().map { it ?: BondEntity() }
    }

    suspend fun clearHistory() {
        messageDao.clearAll()
        memoryDao.clearAll()
        emotionLogDao.clearAll()
        bondDao.clearAll()
        _currentEmotion.value = EmotionState()
        saveEmotionLog(_currentEmotion.value)
        bondDao.insertOrUpdateBond(BondEntity())
        vocalizer.stop()
    }

    suspend fun saveEmotionLog(state: EmotionState) {
        val dominant = emotionEngine.determineDominantEmotion(state)
        emotionLogDao.insertLog(
            EmotionLogEntity(
                dopamine = state.dopamine,
                serotonin = state.serotonin,
                cortisol = state.cortisol,
                adrenaline = state.adrenaline,
                dominantEmotion = dominant
            )
        )
    }

    /**
     * Converts an HTTP URL to its WebSocket equivalent.
     */
    private fun getWebSocketUrl(httpUrl: String): String {
        val clean = httpUrl.trim()
        val noProto = when {
            clean.startsWith("http://") -> clean.substring(7)
            clean.startsWith("https://") -> clean.substring(8)
            else -> clean
        }
        val proto = if (clean.startsWith("https://")) "wss://" else "ws://"
        val base = if (noProto.endsWith("/")) noProto.dropLast(1) else noProto
        return "$proto$base/ws"
    }

    /**
     * Reconnect monitor loop.
     */
    private fun startWebSocketConnection() {
        repositoryScope.launch {
            aikoPrefs.desktopConnectedFlow.collect { isConnected ->
                if (isConnected) {
                    val url = aikoPrefs.desktopUrlFlow.first()
                    connectWs(url)

                    // Also initialize WebRTC pipeline
                    try {
                        webRtcClient?.close()
                        webRtcClient = WebRtcClient(
                            context = context,
                            serverUrl = url,
                            onMessageReceived = { msg ->
                                handleIncomingWebRtcMessage(msg)
                            }
                        ).apply {
                            startConnection()
                        }
                    } catch (e: Exception) {
                        Log.e("ChatRepository", "WebRTC init failed: ${e.message}")
                    }
                } else {
                    disconnectWs()
                    webRtcClient?.close()
                    webRtcClient = null
                }
            }
        }
    }

    private fun connectWs(serverUrl: String) {
        if (webSocket != null || isConnecting) return
        isConnecting = true
        try {
            val wsUrl = getWebSocketUrl(serverUrl)
            val request = Request.Builder().url(wsUrl).build()

            webSocket = wsClient.newWebSocket(request, object : okhttp3.WebSocketListener() {
                override fun onOpen(webSocket: okhttp3.WebSocket, response: okhttp3.Response) {
                    Log.i("ChatRepository", "WebSocket Connected to $wsUrl")
                    isConnecting = false
                    reconnectDelay = 1000L
                }

                override fun onMessage(webSocket: okhttp3.WebSocket, text: String) {
                    try {
                        val json = JSONObject(text)
                        val type = json.optString("type")

                        when (type) {
                            "chat_token" -> {
                                val token = json.optString("token")
                                activeChatChannel?.trySend(token)
                                val emotion = json.optString("emotion")
                                if (emotion.isNotEmpty() && emotion != "null") {
                                    updateEmotionState(emotion)
                                }
                            }
                            "tts_amplitude" -> {
                                val amp = json.optDouble("amplitude", 0.0).toFloat()
                                _currentAmplitude.value = amp
                            }
                            "chat_end" -> {
                                val emotion = json.optString("emotion")
                                if (emotion.isNotEmpty() && emotion != "null") {
                                    updateEmotionState(emotion)
                                }
                                activeChatChannel?.close()

                                val isProactive = json.optBoolean("proactive", false)
                                val proactiveText = json.optString("text").ifEmpty { json.optString("content") }
                                if (isProactive && proactiveText.isNotEmpty()) {
                                    repositoryScope.launch {
                                        messageDao.insertMessage(
                                            MessageEntity(
                                                conversationId = "default",
                                                role = "aiko",
                                                content = proactiveText,
                                                emotionTag = if (emotion.isNotEmpty() && emotion != "null") emotion else null
                                            )
                                        )
                                        proactiveMessage.value = proactiveText
                                    }
                                }
                            }
                        }
                    } catch (e: Exception) {
                        Log.e("ChatRepository", "Error parsing WS message: ${e.message}")
                    }
                }

                override fun onClosed(webSocket: okhttp3.WebSocket, code: Int, reason: String) {
                    Log.i("ChatRepository", "WebSocket Closed: $reason")
                    scheduleReconnect(serverUrl)
                }

                override fun onFailure(webSocket: okhttp3.WebSocket, t: Throwable, response: okhttp3.Response?) {
                    Log.e("ChatRepository", "WebSocket Failure: ${t.message}")
                    scheduleReconnect(serverUrl)
                }
            })
        } catch (e: Exception) {
            Log.e("ChatRepository", "Error creating WebSocket: ${e.message}")
            isConnecting = false
        }
    }

    private fun scheduleReconnect(serverUrl: String) {
        webSocket = null
        isConnecting = false
        repositoryScope.launch {
            delay(reconnectDelay)
            reconnectDelay = (reconnectDelay * 2).coerceAtMost(15000L)
            if (aikoPrefs.desktopConnectedFlow.first()) {
                connectWs(serverUrl)
            }
        }
    }

    private fun disconnectWs() {
        webSocket?.close(1000, "Disconnected by user")
        webSocket = null
        isConnecting = false
    }

    private fun handleIncomingWebRtcMessage(text: String) {
        try {
            val raw = JSONObject(text)
            val type = raw.optString("type")
            val payload = if (raw.has("payload")) raw.getJSONObject("payload") else raw

            when (type) {
                "chat_token" -> {
                    val token = payload.optString("token")
                    activeChatChannel?.trySend(token)
                    val emotion = payload.optString("emotion")
                    if (emotion.isNotEmpty() && emotion != "null") {
                        updateEmotionState(emotion)
                    }
                }
                "tts_amplitude" -> {
                    val amp = payload.optDouble("amplitude", 0.0).toFloat()
                    _currentAmplitude.value = amp
                }
                "chat_end" -> {
                    val emotion = payload.optString("emotion")
                    if (emotion.isNotEmpty() && emotion != "null") {
                        updateEmotionState(emotion)
                    }
                    activeChatChannel?.close()

                    val isProactive = payload.optBoolean("proactive", false)
                    val proactiveText = payload.optString("text").ifEmpty { payload.optString("content") }
                    if (isProactive && proactiveText.isNotEmpty()) {
                        repositoryScope.launch {
                            messageDao.insertMessage(
                                MessageEntity(
                                    conversationId = "default",
                                    role = "aiko",
                                    content = proactiveText,
                                    emotionTag = if (emotion.isNotEmpty() && emotion != "null") emotion else null
                                )
                            )
                            proactiveMessage.value = proactiveText
                        }
                    }
                }
                "biological_sync" -> {
                    val chemicals = payload.optJSONObject("chemicals")
                    if (chemicals != null) {
                        // Server sends values in 0.0–1.0 range (NOT 0–100)
                        val state = EmotionState(
                            dopamine = chemicals.optDouble("dopamine", 0.5).toFloat().coerceIn(0f, 1f),
                            serotonin = chemicals.optDouble("serotonin", 0.5).toFloat().coerceIn(0f, 1f),
                            cortisol = chemicals.optDouble("cortisol", 0.2).toFloat().coerceIn(0f, 1f),
                            adrenaline = chemicals.optDouble("adrenaline", 0.1).toFloat().coerceIn(0f, 1f),
                            oxytocin = chemicals.optDouble("oxytocin", 0.3).toFloat().coerceIn(0f, 1f),
                            melatonin = chemicals.optDouble("melatonin", 0.1).toFloat().coerceIn(0f, 1f)
                        )
                        _currentEmotion.value = state
                        repositoryScope.launch {
                            saveEmotionLog(state)
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e("ChatRepository", "Error parsing WebRTC data message: ${e.message}")
        }
    }

    private fun updateEmotionState(emotion: String) {
        val state = when (emotion) {
            "happy" -> EmotionState(dopamine = 0.8f, serotonin = 0.8f, cortisol = 0.1f, adrenaline = 0.4f)
            "flustered" -> EmotionState(dopamine = 0.9f, serotonin = 0.6f, cortisol = 0.3f, adrenaline = 0.7f)
            "devoted" -> EmotionState(dopamine = 0.7f, serotonin = 0.9f, cortisol = 0.1f, adrenaline = 0.3f)
            "calm" -> EmotionState(dopamine = 0.5f, serotonin = 0.8f, cortisol = 0.1f, adrenaline = 0.2f)
            "sad" -> EmotionState(dopamine = 0.2f, serotonin = 0.3f, cortisol = 0.6f, adrenaline = 0.2f)
            "worried" -> EmotionState(dopamine = 0.3f, serotonin = 0.4f, cortisol = 0.8f, adrenaline = 0.5f)
            "jealous" -> EmotionState(dopamine = 0.4f, serotonin = 0.5f, cortisol = 0.4f, adrenaline = 0.6f)
            else -> EmotionState()
        }
        _currentEmotion.value = state
        repositoryScope.launch {
            saveEmotionLog(state)
        }
    }

    /**
     * Incremental memory synchronization.
     */
    suspend fun syncMemories(): Boolean = withContext(Dispatchers.IO) {
        val isConnected = aikoPrefs.desktopConnectedFlow.first()
        if (!isConnected) return@withContext false

        val baseUrl = aikoPrefs.desktopUrlFlow.first()
        val since = aikoPrefs.lastSyncTimestampFlow.first()
        val url = if (baseUrl.endsWith("/")) {
            "${baseUrl}api/memory/export?since=${since / 1000.0}"
        } else {
            "${baseUrl}/api/memory/export?since=${since / 1000.0}"
        }

        val request = Request.Builder().url(url).build()

        return@withContext try {
            val response = wsClient.newCall(request).execute()
            response.use { resp ->
                if (resp.isSuccessful) {
                    val body = resp.body?.string() ?: ""
                    val json = JSONObject(body)
                    val memories = json.optJSONArray("memories")
                    if (memories != null) {
                        var maxTimestamp = since
                        for (i in 0 until memories.length()) {
                            val obj = memories.getJSONObject(i)
                            val id = obj.optString("id")
                            val content = obj.optString("content")
                            val category = obj.optString("category")
                            val confidence = obj.optDouble("confidence", 1.0).toFloat()
                            val timestamp = obj.optLong("timestamp", System.currentTimeMillis())

                            memoryDao.insertMemory(
                                MemoryEntity(
                                    id = id,
                                    category = category,
                                    content = content,
                                    confidence = confidence,
                                    createdAt = timestamp,
                                    lastAccessed = System.currentTimeMillis()
                                )
                            )
                            maxTimestamp = maxOf(maxTimestamp, timestamp)
                        }
                        aikoPrefs.setLastSyncTimestamp(maxTimestamp)
                        true
                    } else false
                } else false
            }
        } catch (e: Exception) {
            Log.e("ChatRepository", "Memory sync error: ${e.message}")
            false
        }
    }

    /**
     * Sends the message and returns a real-time stream flow.
     */
    suspend fun streamAikoResponse(
        conversationId: String,
        newMessage: String,
        base64Image: String? = null
    ): Flow<String> {
        val isDesktopConnected = aikoPrefs.desktopConnectedFlow.first()
        val desktopUrl = aikoPrefs.desktopUrlFlow.first()

        // 1. Local logging of user message
        messageDao.insertMessage(
            MessageEntity(
                conversationId = conversationId,
                role = "user",
                content = newMessage,
                emotionTag = null
            )
        )

        if (isDesktopConnected) {
            val channel = kotlinx.coroutines.channels.Channel<String>(kotlinx.coroutines.channels.Channel.UNLIMITED)
            activeChatChannel = channel

            val payload = JSONObject().apply {
                put("type", "chat")
                put("text", newMessage)
                put("session_id", conversationId)
                val attachmentsArray = JSONArray()
                if (base64Image != null) {
                    attachmentsArray.put(base64Image)
                }
                put("attachments", attachmentsArray)
            }

            // Route over active WebRTC peer-to-peer data channel if connected
            val isRtcConnected = webRtcClient?.connectionState?.value == PeerConnection.PeerConnectionState.CONNECTED
            var sent = false
            if (isRtcConnected) {
                sent = webRtcClient?.sendMessage(payload.toString()) ?: false
                if (sent) {
                    Log.i("ChatRepository", "Message routed over WebRTC P2P DataChannel")
                }
            }

            // Fallback to local network WebSocket
            if (!sent) {
                if (webSocket == null) {
                    connectWs(desktopUrl)
                    delay(300)
                }
                val ws = webSocket
                if (ws != null) {
                    ws.send(payload.toString())
                    Log.i("ChatRepository", "Message routed over local WebSocket link")
                } else {
                    channel.trySend("Error: Neural Hub not connected. Re-checking link...")
                    channel.close()
                }
            }

            return flow {
                for (token in channel) {
                    emit(token)
                }
            }
        }

        // 2. Local fallback inference mode
        _currentEmotion.update { current ->
            val userImpactedEmotion = emotionEngine.processMessage(newMessage, current)
            repositoryScope.launch { saveEmotionLog(userImpactedEmotion) }
            userImpactedEmotion
        }

        val apiKey = aikoPrefs.apiKeyFlow.first()
        val modelName = aikoPrefs.modelChoiceFlow.first()
        val userName = aikoPrefs.userNameFlow.first()
        val bond = bondDao.getBond() ?: BondEntity()
        val recentMessages = messageDao.getRecentMessages(12)
        val memories = memoryDao.getAllMemories()

        return geminiService.generateStreamingResponse(
            apiKey = apiKey,
            modelName = modelName,
            userName = userName,
            bondLevel = bond.level,
            bondTitle = bond.relationshipTitle,
            dopamine = _currentEmotion.value.dopamine,
            serotonin = _currentEmotion.value.serotonin,
            cortisol = _currentEmotion.value.cortisol,
            adrenaline = _currentEmotion.value.adrenaline,
            memories = memories,
            history = recentMessages,
            newMessage = newMessage
        ).map { it.text ?: "" }
         .catch { err ->
             emit("Connection sync issues: ${err.message ?: "Failed to generate response. Check API key settings."}")
         }
    }

    /**
     * Sends a raw JSON string to the active link channel.
     */
    fun sendRawMessage(msg: String): Boolean {
        val isRtcConnected = webRtcClient?.connectionState?.value == org.webrtc.PeerConnection.PeerConnectionState.CONNECTED
        if (isRtcConnected) {
            val sent = webRtcClient?.sendMessage(msg) ?: false
            if (sent) {
                Log.i("ChatRepository", "Raw message sent over WebRTC")
                return true
            }
        }
        val ws = webSocket
        if (ws != null) {
            val sent = ws.send(msg)
            if (sent) {
                Log.i("ChatRepository", "Raw message sent over WebSocket")
                return true
            }
        }
        return false
    }

    /**
     * Triggers speech vocalization for the given text.
     */
    suspend fun speakText(text: String) {
        vocalizer.speak(text)
    }

    /**
     * Finalizes the message logging once stream finishes.
     */
    suspend fun finalizeAikoResponse(
        conversationId: String,
        fullReply: String
    ) {
        val isDesktopConnected = aikoPrefs.desktopConnectedFlow.first()
        val (cleanText, tag) = emotionEngine.parseResponseEmotion(fullReply)

        aikoDatabase.withTransaction {
            if (isDesktopConnected) {
                messageDao.insertMessage(
                    MessageEntity(
                        conversationId = conversationId,
                        role = "aiko",
                        content = cleanText,
                        emotionTag = tag
                    )
                )
                return@withTransaction
            }

            // Auto-vocalize response in Local Fallback mode if voice output is enabled
            if (aikoPrefs.voiceEnabledFlow.first()) {
                repositoryScope.launch {
                    vocalizer.speak(cleanText)
                }
            }

            val current = _currentEmotion.value
            val finalEmotion = emotionEngine.applyTagImpact(tag, current)
            _currentEmotion.value = finalEmotion
            saveEmotionLog(finalEmotion)

            messageDao.insertMessage(
                MessageEntity(
                    conversationId = conversationId,
                    role = "aiko",
                    content = cleanText,
                    emotionTag = tag
                )
            )

            // XP/Level mapping
            val oldBond = bondDao.getBond() ?: BondEntity()
            val xpGain = 10 + (finalEmotion.dopamine * 5).toInt()
            var newXp = oldBond.xp + xpGain
            var newLevel = oldBond.level
            val xpNeeded = 100 * newLevel
            if (newXp >= xpNeeded) {
                newLevel += 1
                newXp -= xpNeeded
            }

            val relationshipTitle = when (newLevel) {
                in 1..3 -> "Stranger"
                in 4..7 -> "Companion"
                in 8..12 -> "Devoted Friend"
                in 13..17 -> "Soulbound"
                else -> "Eternal Partner"
            }

            bondDao.insertOrUpdateBond(
                oldBond.copy(
                    level = newLevel,
                    xp = newXp,
                    totalMessages = oldBond.totalMessages + 2,
                    lastInteraction = System.currentTimeMillis(),
                    relationshipTitle = relationshipTitle
                )
            )
        }

        // Memory consolidation triggers (outside transaction to avoid holding DB lock for long operations)
        val oldBond = bondDao.getBond() ?: BondEntity()
        if ((oldBond.totalMessages + 2) % 5 == 0) {
            repositoryScope.launch {
                try {
                    val apiKey = aikoPrefs.apiKeyFlow.first()
                    val modelName = aikoPrefs.modelChoiceFlow.first()
                    val messages = messageDao.getRecentMessages(6).map { "${it.role}: ${it.content}" }
                    val existingMemories = memoryDao.getAllMemories()
                    memoryExtractor.extractAndSaveMemories(
                        apiKey = apiKey,
                        modelName = modelName,
                        lastMessages = messages,
                        existingMemories = existingMemories
                    )
                } catch (e: Exception) {
                    Log.e("ChatRepository", "Async memory extraction failed", e)
                }
            }
        }
    }
}
