package com.aiko.app

import android.app.Application
import dagger.hilt.android.HiltAndroidApp
import android.util.Log

@HiltAndroidApp
class AikoApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        Log.d("AikoApplication", "Application started!")
    }
}
