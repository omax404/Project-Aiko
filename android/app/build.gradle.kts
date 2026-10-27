plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.hilt)
    alias(libs.plugins.ksp)
    alias(libs.plugins.kotlin.serialization)
}

// Fail-closed release signing: the release signing config exists only when a keystore is
// supplied via env (ANDROID_KEYSTORE_*) or gradle.properties (RELEASE_*). There is
// deliberately NO debug-keystore fallback: a release artifact signed with the public
// androiddebugkey is forgeable by anyone who holds that well-known key.
val releaseKeystorePath: String? =
    System.getenv("ANDROID_KEYSTORE_PATH") ?: project.findProperty("RELEASE_STORE_FILE") as? String

android {
    namespace = "com.aiko.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.aiko.app"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        if (releaseKeystorePath != null) {
            create("release") {
                storeFile = file(releaseKeystorePath)
                storePassword = System.getenv("ANDROID_KEYSTORE_PASSWORD") ?: project.findProperty("RELEASE_STORE_PASSWORD") as? String ?: ""
                keyAlias = System.getenv("ANDROID_KEY_ALIAS") ?: project.findProperty("RELEASE_KEY_ALIAS") as? String ?: ""
                keyPassword = System.getenv("ANDROID_KEY_PASSWORD") ?: project.findProperty("RELEASE_KEY_PASSWORD") as? String ?: ""
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            // null when no keystore was provided; the guard below then fails the release build.
            signingConfig = signingConfigs.findByName("release")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
        freeCompilerArgs += listOf(
            "-opt-in=androidx.compose.material3.ExperimentalMaterial3Api",
            "-opt-in=androidx.compose.animation.ExperimentalSharedTransitionApi",
            "-opt-in=kotlinx.coroutines.ExperimentalCoroutinesApi",
            "-opt-in=androidx.compose.ui.ExperimentalComposeUiApi"
        )
    }

    buildFeatures {
        compose = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

// AGP would otherwise emit an *unsigned* release APK without failing. Keeping the failure in
// a task action (instead of a configuration-time throw) is configuration-cache safe and leaves
// debug builds, `./gradlew tasks` and IDE sync untouched.
if (releaseKeystorePath == null) {
    tasks.matching { it.name == "assembleRelease" || it.name == "bundleRelease" }.configureEach {
        doFirst {
            throw GradleException(
                "Refusing to build a release artifact without a signing key. Set " +
                    "ANDROID_KEYSTORE_PATH, ANDROID_KEYSTORE_PASSWORD, ANDROID_KEY_ALIAS and " +
                    "ANDROID_KEY_PASSWORD (or RELEASE_STORE_FILE/RELEASE_STORE_PASSWORD/" +
                    "RELEASE_KEY_ALIAS/RELEASE_KEY_PASSWORD in gradle.properties). " +
                    "Debug builds are unaffected."
            )
        }
    }
}

dependencies {
    // Core Android & Lifecycle
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)

    // Jetpack Compose
    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.graphics)
    implementation(libs.compose.ui.tooling)
    implementation(libs.compose.material3)
    implementation("androidx.compose.material:material-icons-extended")
    implementation(libs.compose.googlefonts)
    implementation(libs.compose.animation)
    implementation(libs.compose.foundation)

    // Navigation
    implementation(libs.navigation.compose)

    // Room Database
    implementation(libs.room.runtime)
    implementation(libs.room.ktx)
    ksp(libs.room.compiler)

    // Dependency Injection (Hilt)
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
    implementation(libs.hilt.navigation)

    // Networking
    implementation(libs.retrofit)
    implementation(libs.retrofit.gson)
    implementation(libs.okhttp.logging)

    // Media and Animations
    implementation(libs.coil)
    implementation(libs.lottie)

    // AI Integrations
    implementation(libs.gemini)
    implementation(libs.mediapipe.llm)

    // Misc Preferences & Layout
    implementation(libs.datastore)
    implementation(libs.splashscreen)
    implementation(libs.window)

    // Kotlinx Serialization JSON
    implementation(libs.kotlinx.serialization.json)

    // CameraX
    implementation(libs.camerax.core)
    implementation(libs.camerax.camera2)
    implementation(libs.camerax.lifecycle)
    implementation(libs.camerax.view)

    // ML Kit Barcode Scanning for QR linking
    implementation(libs.mlkit.barcode)

    // WebRTC client dependency for P2P connection (Modern community fork)
    implementation(libs.stream.webrtc)
}
