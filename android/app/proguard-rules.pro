# Room rules
-keep class * extends androidx.room.RoomDatabase
-keepclassmembers class * extends androidx.room.RoomDatabase {
    <init>(...);
}
-keep class * extends androidx.room.RoomOpenHelper

# Hilt rules
-keep class dagger.hilt.** { *; }
-keep class *__HiltComponents* { *; }
-keep interface *__HiltComponents* { *; }
-keep class * extends dagger.hilt.internal.GeneratedComponent
-keep class * extends dagger.hilt.internal.GeneratedComponentManager
-keep class * extends dagger.hilt.internal.UncheckedCasts

# WebRTC rules
-keep class org.webrtc.** { *; }

# Serialization and entities rules
-keep class com.aiko.app.data.local.** { *; }
-keep class com.aiko.app.domain.** { *; }
