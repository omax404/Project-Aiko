package com.aiko.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.aiko.app.data.repository.ChatRepository
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class AikoConnectionService : Service() {

    @Inject
    lateinit var chatRepository: ChatRepository

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    companion object {
        const val CHANNEL_ID = "aiko_connection_channel"
        const val NOTIFICATION_ID = 1001
        const val PUSH_NOTIFICATION_ID = 1002
        
        var isAppInForeground = false
    }

    override fun onCreate() {
        super.onCreate()
        Log.i("AikoConnectionService", "Service onCreate - starting foreground service")
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, createForegroundNotification())
        
        // Start collecting events to push notifications when in background
        serviceScope.launch {
            chatRepository.proactiveMessage.collectLatest { text ->
                if (text != null && text.isNotEmpty() && !isAppInForeground) {
                    Log.i("AikoConnectionService", "App is backgrounded, posting proactive notification")
                    showIncomingNotification("Aiko", text)
                    // Reset to avoid double triggers
                    chatRepository.proactiveMessage.value = null
                }
            }
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.i("AikoConnectionService", "Service onStartCommand - START_STICKY")
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    override fun onDestroy() {
        Log.i("AikoConnectionService", "Service onDestroy - cleaning up scope")
        super.onDestroy()
        serviceScope.cancel()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Aiko Connection Monitor",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Keeps WebSocket connection active to Aiko Hub in the background"
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    private fun createForegroundNotification(): Notification {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Aiko Link Active")
            .setContentText("Connected to Neural Hub in background")
            .setSmallIcon(android.R.drawable.stat_sys_data_bluetooth) // standard fallback icon
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private fun showIncomingNotification(title: String, content: String) {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(content)
            .setSmallIcon(android.R.drawable.stat_notify_chat)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setDefaults(Notification.DEFAULT_ALL)
            .build()

        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(PUSH_NOTIFICATION_ID, notification)
    }
}
