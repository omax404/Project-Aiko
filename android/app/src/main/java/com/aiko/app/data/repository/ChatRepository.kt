package com.aiko.app.data.repository

import android.util.Log
import com.aiko.app.data.local.AikoPrefs
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
import com.google.ai.client.generativeai.type.GenerateContentResponse
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import org.json.JSONObject
import org.json.JSONArray
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ChatRepository @Inject constructor(
    private val messageDao: MessageDao,
    val memoryDao: MemoryDao,
    val emotionLogDao: EmotionLogDao,
    private val bondDao: BondDao,
    private val aikoPrefs: AikoPrefs,
    private val emotionEngine: EmotionEngine,
    private val memoryExtractor: MemoryExtractor,
    private val geminiService: GeminiService
) {
    private val repositoryScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private val _currentEmotion = MutableStateFlow(EmotionState())
    val currentEmotion: StateFlow<EmotionState> = _currentEmotion.asStateFlow()

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
     * Sends the message to Gemini or Desktop Server and returns a character stream.
     */
    suspend fun streamAikoResponse(
        conversationId: String,
        newMessage: String,
        base64Image: String? = null
    ): Flow<String> {
        // 1. Process sentiment of user's incoming text locally (if not connecting to desktop)
        val isDesktopConnected = aikoPrefs.desktopConnectedFlow.first()
        val desktopUrl = aikoPrefs.desktopUrlFlow.first()

        if (!isDesktopConnected) {
            val current = _currentEmotion.value
            val userImpactedEmotion = emotionEngine.processMessage(newMessage, current)
            _currentEmotion.value = userImpactedEmotion
            saveEmotionLog(userImpactedEmotion)
        }

        // 2. Insert user message in database
        messageDao.insertMessage(
            MessageEntity(
                conversationId = conversationId,
                role = "user",
                content = newMessage,
                emotionTag = null
            )
        )

        if (isDesktopConnected) {
            return streamFromDesktop(desktopUrl, newMessage, base64Image)
        }

        // 3. Fetch configs from DataStore for local execution
        val apiKey = aikoPrefs.apiKeyFlow.first()
        val modelName = aikoPrefs.modelChoiceFlow.first()
        val userName = aikoPrefs.userNameFlow.first()

        // 4. Fetch state dependencies from database
        val bond = bondDao.getBond() ?: BondEntity()
        val recentMessages = messageDao.getRecentMessages(12)
        val memories = memoryDao.getAllMemories()

        // 5. Generate and return the API response stream flow mapped to String
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
    }

    private fun streamFromDesktop(
        serverUrl: String,
        message: String,
        base64Image: String?
    ): Flow<String> = flow {
        val client = OkHttpClient.Builder()
            .connectTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
            .build()

        val jsonPayload = JSONObject().apply {
            put("message", message)
            put("user_id", "android_client")
            val attachmentsArray = JSONArray()
            if (base64Image != null) {
                attachmentsArray.put(base64Image)
            }
            put("attachments", attachmentsArray)
        }

        val mediaType = "application/json; charset=utf-8".toMediaTypeOrNull()
        val requestBody = jsonPayload.toString().toRequestBody(mediaType)

        val requestUrl = if (serverUrl.endsWith("/")) "${serverUrl}api/chat" else "$serverUrl/api/chat"
        val request = Request.Builder()
            .url(requestUrl)
            .post(requestBody)
            .build()

        try {
            val response = client.newCall(request).execute()
            if (response.isSuccessful) {
                val bodyString = response.body?.string() ?: ""
                val responseJson = JSONObject(bodyString)
                val replyText = responseJson.optString("response", "")

                // Sync desktop's emotion back to the phone to render state on mobile avatar
                val desktopEmotion = responseJson.optString("emotion", "neutral")
                val state = when (desktopEmotion) {
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
                saveEmotionLog(state)

                // Simulate smooth typing flow token-by-token
                for (char in replyText) {
                    emit(char.toString())
                    kotlinx.coroutines.delay(12L) // 12ms typing simulation per character
                }
            } else {
                emit("Error: Server returned code ${response.code}")
            }
        } catch (e: Exception) {
            emit("Error: Could not connect to Aiko Desktop at $serverUrl. Make sure they are on the same Wi-Fi!")
        }
    }

    /**
     * Finalizes the message logging once stream finishes.
     */
    suspend fun finalizeAikoResponse(
        conversationId: String,
        fullReply: String
    ) {
        val isDesktopConnected = aikoPrefs.desktopConnectedFlow.first()
        if (isDesktopConnected) {
            // For desktop sync: just log the clean message in database so it displays in chat history
            val (cleanText, tag) = emotionEngine.parseResponseEmotion(fullReply)
            messageDao.insertMessage(
                MessageEntity(
                    conversationId = conversationId,
                    role = "aiko",
                    content = cleanText,
                    emotionTag = tag
                )
            )
            return
        }

        // 1. Parse emotion code
        val (cleanText, tag) = emotionEngine.parseResponseEmotion(fullReply)

        // 2. Calculate chemistry response
        val current = _currentEmotion.value
        val finalEmotion = emotionEngine.applyTagImpact(tag, current)
        _currentEmotion.value = finalEmotion
        saveEmotionLog(finalEmotion)

        // 3. Save Aiko response in database
        messageDao.insertMessage(
            MessageEntity(
                conversationId = conversationId,
                role = "aiko",
                content = cleanText,
                emotionTag = tag
            )
        )

        // 4. Update xp bond status
        val oldBond = bondDao.getBond() ?: BondEntity()
        val xpGain = 10 + (finalEmotion.dopamine * 5).toInt() // Dopamine boosts XP!
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

        // 5. Check memory consolidation (run every 5 messages asynchronously)
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
