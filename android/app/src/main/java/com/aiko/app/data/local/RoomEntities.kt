package com.aiko.app.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.util.UUID

@Entity(tableName = "messages")
data class MessageEntity(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val conversationId: String,
    val role: String, // "user" or "aiko"
    val content: String,
    val emotionTag: String?, // happy, flustered, devoted, sad, etc.
    val timestamp: Long = System.currentTimeMillis()
)

@Entity(tableName = "memories")
data class MemoryEntity(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val category: String, // preference, personal, event, emotion, goal
    val content: String,
    val confidence: Float,
    val createdAt: Long = System.currentTimeMillis(),
    val lastAccessed: Long = System.currentTimeMillis()
)

@Entity(tableName = "emotion_logs")
data class EmotionLogEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0L,
    val dopamine: Float,
    val serotonin: Float,
    val cortisol: Float,
    val adrenaline: Float,
    val timestamp: Long = System.currentTimeMillis(),
    val dominantEmotion: String
)

@Entity(tableName = "bonds")
data class BondEntity(
    @PrimaryKey val id: String = "singleton_bond",
    val level: Int = 1,
    val xp: Int = 0,
    val totalMessages: Int = 0,
    val firstMet: Long = System.currentTimeMillis(),
    val lastInteraction: Long = System.currentTimeMillis(),
    val relationshipTitle: String = "Stranger"
)
