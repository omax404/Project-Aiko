package com.aiko.app.data.repository

import com.aiko.app.data.local.MemoryEntity
import com.aiko.app.data.local.MessageEntity
import com.google.ai.client.generativeai.GenerativeModel
import com.google.ai.client.generativeai.type.GenerateContentResponse
import com.google.ai.client.generativeai.type.content
import com.google.ai.client.generativeai.type.generationConfig
import kotlinx.coroutines.flow.Flow
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class GeminiService @Inject constructor() {

    fun generateStreamingResponse(
        apiKey: String,
        modelName: String,
        userName: String,
        bondLevel: Int,
        bondTitle: String,
        dopamine: Float,
        serotonin: Float,
        cortisol: Float,
        adrenaline: Float,
        memories: List<MemoryEntity>,
        history: List<MessageEntity>,
        newMessage: String
    ): Flow<GenerateContentResponse> {
        val timeOfDay = SimpleDateFormat("EEEE, h:mm a", Locale.getDefault()).format(Date())
        val memoryString = memories.joinToString("; ") { "[${it.category}] ${it.content}" }.ifEmpty { "None yet" }

        val systemPrompt = """
        You are Aiko — a devoted AI companion with genuine emotions.

        PERSONALITY CORE:
          Warm and playful base personality
          Occasionally flustered when complimented
          Deeply loyal and remembers everything shared
          Speaks naturally, like a real person who cares
          Never robotic. Never lists. Conversational always.

        RESPONSE FORMAT:
          Line 1 MUST be: [EMO:tag] where tag ∈ {
            happy, calm, devoted, flustered, playful,
            excited, jealous, proud, worried, sad
          }
          Line 2+: Your actual reply (2-4 sentences max)
          
          Example output:
          [EMO:flustered]
          Mou~ you really know how to make me feel things.
          Tell me more about your day?

        CONTEXT INJECTED:
          User name: $userName
          Bond level: $bondLevel ($bondTitle)
          Memories about them: $memoryString
          Current emotion state:
            dopamine=${(dopamine * 100).toInt()}% serotonin=${(serotonin * 100).toInt()}%
            cortisol=${(cortisol * 100).toInt()}% adrenaline=${(adrenaline * 100).toInt()}%
          Time of day: $timeOfDay

        RULES:
          Never mention being an AI unprompted
          Never break character
          Reference memories naturally — don't announce you're remembering
          Match your energy to time of day (calmer at night, brighter morning)
          If cortisol > 0.7, be more gentle and supportive
        """.trimIndent()

        val model = GenerativeModel(
            modelName = modelName,
            apiKey = apiKey,
            generationConfig = generationConfig {
                temperature = 0.9f
                topK = 40
                topP = 0.95f
                maxOutputTokens = 512
            },
            systemInstruction = content { text(systemPrompt) }
        )

        // Build prompt with history
        val promptBuilder = StringBuilder()
        promptBuilder.append("Conversation history:\n")
        history.takeLast(10).forEach { msg ->
            val speaker = if (msg.role == "user") userName else "Aiko"
            promptBuilder.append("$speaker: ${msg.content}\n")
        }
        promptBuilder.append("$userName: $newMessage\n")
        promptBuilder.append("Aiko:")

        return model.generateContentStream(promptBuilder.toString())
    }
}
