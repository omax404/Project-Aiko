package com.aiko.app.data.local

import android.content.Context
import androidx.room.Dao
import androidx.room.Database
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Room
import androidx.room.RoomDatabase
import kotlinx.coroutines.flow.Flow

@Dao
interface MessageDao {
    @Query("SELECT * FROM messages WHERE conversationId = :conversationId ORDER BY timestamp ASC")
    fun getMessagesForConversation(conversationId: String): Flow<List<MessageEntity>>

    @Query("SELECT * FROM messages ORDER BY timestamp DESC LIMIT :limit")
    suspend fun getRecentMessages(limit: Int): List<MessageEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMessage(message: MessageEntity)

    @Query("DELETE FROM messages WHERE conversationId = :conversationId")
    suspend fun deleteConversation(conversationId: String)

    @Query("DELETE FROM messages")
    suspend fun clearAll()
}

@Dao
interface MemoryDao {
    @Query("SELECT * FROM memories ORDER BY createdAt DESC")
    fun getAllMemoriesFlow(): Flow<List<MemoryEntity>>

    @Query("SELECT * FROM memories ORDER BY createdAt DESC")
    suspend fun getAllMemories(): List<MemoryEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMemory(memory: MemoryEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMemories(memories: List<MemoryEntity>)

    @Query("DELETE FROM memories WHERE id = :id")
    suspend fun deleteMemory(id: String)

    @Query("DELETE FROM memories")
    suspend fun clearAll()
}

@Dao
interface EmotionLogDao {
    @Query("SELECT * FROM emotion_logs ORDER BY timestamp DESC LIMIT 1")
    fun getLatestLogFlow(): Flow<EmotionLogEntity?>

    @Query("SELECT * FROM emotion_logs ORDER BY timestamp DESC LIMIT 1")
    suspend fun getLatestLog(): EmotionLogEntity?

    @Query("SELECT * FROM emotion_logs ORDER BY timestamp DESC LIMIT :limit")
    fun getLogsFlow(limit: Int): Flow<List<EmotionLogEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertLog(log: EmotionLogEntity)

    @Query("DELETE FROM emotion_logs")
    suspend fun clearAll()
}

@Dao
interface BondDao {
    @Query("SELECT * FROM bonds WHERE id = 'singleton_bond' LIMIT 1")
    fun getBondFlow(): Flow<BondEntity?>

    @Query("SELECT * FROM bonds WHERE id = 'singleton_bond' LIMIT 1")
    suspend fun getBond(): BondEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrUpdateBond(bond: BondEntity)

    @Query("DELETE FROM bonds")
    suspend fun clearAll()
}

@Database(
    entities = [
        MessageEntity::class,
        MemoryEntity::class,
        EmotionLogEntity::class,
        BondEntity::class
    ],
    version = 4,
    exportSchema = false
)
abstract class AikoDatabase : RoomDatabase() {
    abstract fun messageDao(): MessageDao
    abstract fun memoryDao(): MemoryDao
    abstract fun emotionLogDao(): EmotionLogDao
    abstract fun bondDao(): BondDao

    companion object {
        @Volatile
        private var INSTANCE: AikoDatabase? = null

        fun getDatabase(context: Context): AikoDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AikoDatabase::class.java,
                    "aiko_database"
                )
                .fallbackToDestructiveMigration() // Dev and version 4 migration fallback
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
