package com.aiko.app.di

import android.content.Context
import com.aiko.app.data.local.AikoDatabase
import com.aiko.app.data.local.AikoPrefs
import com.aiko.app.data.local.BondDao
import com.aiko.app.data.local.EmotionLogDao
import com.aiko.app.data.local.MemoryDao
import com.aiko.app.data.local.MessageDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AikoDatabase {
        return AikoDatabase.getDatabase(context)
    }

    @Provides
    @Singleton
    fun provideMessageDao(database: AikoDatabase): MessageDao {
        return database.messageDao()
    }

    @Provides
    @Singleton
    fun provideMemoryDao(database: AikoDatabase): MemoryDao {
        return database.memoryDao()
    }

    @Provides
    @Singleton
    fun provideEmotionLogDao(database: AikoDatabase): EmotionLogDao {
        return database.emotionLogDao()
    }

    @Provides
    @Singleton
    fun provideBondDao(database: AikoDatabase): BondDao {
        return database.bondDao()
    }

    @Provides
    @Singleton
    fun provideAikoVocalizer(
        @ApplicationContext context: Context,
        aikoPrefs: AikoPrefs
    ): com.aiko.app.domain.AikoVocalizer {
        return com.aiko.app.domain.AikoVocalizer(context, aikoPrefs)
    }
}
