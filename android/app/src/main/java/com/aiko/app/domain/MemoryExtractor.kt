package com.aiko.app.domain

import android.util.Log
import com.aiko.app.data.local.MemoryDao
import com.aiko.app.data.local.MemoryEntity
import com.google.ai.client.generativeai.GenerativeModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MemoryExtractor @Inject constructor(
    private val memoryDao: MemoryDao
) {

    suspend fun extractAndSaveMemories(
        apiKey: String,
        modelName: String,
        lastMessages: List<String>,
        existingMemories: List<MemoryEntity>
    ): List<MemoryEntity> = withContext(Dispatchers.IO) {
        if (apiKey.isBlank() || lastMessages.isEmpty()) return@withContext emptyList()

        try {
            val existingString = existingMemories.joinToString("\n") { "- [${it.category}] ${it.content}" }
            val conversationString = lastMessages.joinToString("\n") { it }

            val prompt = """
            From this conversation extract facts about the user.
            Return ONLY valid JSON, no markdown, no explanation:
            [
              {"category":"preference","content":"likes black coffee"},
              {"category":"personal","content":"has a sister named Sara"}
            ]
            Categories: preference, personal, event, emotion, goal
            Max 3 items. Only NEW information not previously known.
            
            Previously known:
            $existingString
            
            Conversation:
            $conversationString
            """.trimIndent()

            val model = GenerativeModel(
                modelName = modelName,
                apiKey = apiKey
            )

            val response = model.generateContent(prompt)
            val jsonText = response.text?.trim() ?: return@withContext emptyList()

            // Safe parsing of JSON: extract everything between the first '[' and the last ']'
            val arrayRegex = Regex("\\[[\\s\\S]*\\]")
            val cleanJson = arrayRegex.find(jsonText)?.value?.trim() ?: jsonText

            Log.d("MemoryExtractor", "Extracted raw json: $cleanJson")

            val jsonArray = JSONArray(cleanJson)
            val newMemories = mutableListOf<MemoryEntity>()

            for (i in 0 until jsonArray.length()) {
                val obj = jsonArray.getJSONObject(i)
                val cat = obj.optString("category", "preference").lowercase()
                val content = obj.optString("content", "").trim()

                if (content.isNotEmpty()) {
                    // Check if we already have it in local db, to prevent duplicate semantic insertion
                    val isDuplicate = existingMemories.any { 
                        it.content.lowercase().contains(content.lowercase()) || 
                        content.lowercase().contains(it.content.lowercase()) 
                    }
                    if (!isDuplicate) {
                        val memory = MemoryEntity(
                            id = UUID.randomUUID().toString(),
                            category = cat,
                            content = content,
                            confidence = 0.9f
                        )
                        newMemories.add(memory)
                        memoryDao.insertMemory(memory)
                        Log.d("MemoryExtractor", "Saved memory: $content in category $cat")
                    }
                }
            }
            return@withContext newMemories
        } catch (e: Exception) {
            Log.e("MemoryExtractor", "Error extracting memories from chat", e)
            return@withContext emptyList()
        }
    }
}
