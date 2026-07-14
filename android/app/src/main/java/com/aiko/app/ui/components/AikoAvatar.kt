package com.aiko.app.ui.components

import android.util.Log
import android.webkit.ConsoleMessage
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.aiko.app.domain.EmotionState
import com.aiko.app.ui.theme.AikoColors
import kotlinx.coroutines.delay

/**
 * JavaScript-to-Kotlin bridge class for Live2D model load status reporting.
 * Exposed to WebView JS as "AikoBridge" so the HTML page can signal
 * whether the model loaded successfully or failed (e.g. OOM on low-RAM devices).
 */
class AikoBridge(
    private val onLoaded: (Boolean) -> Unit
) {
    @JavascriptInterface
    fun onModelLoaded(success: Boolean) {
        Log.d("AikoBridge", "Model loaded: $success")
        onLoaded(success)
    }

    @JavascriptInterface
    fun onModelFailed(errorMessage: String) {
        Log.e("AikoBridge", "Model failed: $errorMessage")
        onLoaded(false)
    }
}

@Composable
fun AikoAvatar(
    emotionState: EmotionState,
    dominantEmotion: String,
    isTyping: Boolean,
    isSpeaking: Boolean,
    avatarMode: String = "WebView",
    modifier: Modifier = Modifier,
    size: Dp = 160.dp
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    // Emotion Color Mapping
    val activeColor = when (dominantEmotion.lowercase()) {
        "happy" -> AikoColors.HappyGold
        "flustered" -> AikoColors.FlusteredPink
        "devoted" -> AikoColors.DevotedViolet
        "calm" -> AikoColors.CalmBlue
        "sad" -> AikoColors.SadGrey
        "worried" -> AikoColors.WorriedOrange
        "jealous" -> AikoColors.JealousGreen
        else -> AikoColors.Primary
    }

    val animatedGlowColor by animateColorAsState(
        targetValue = activeColor,
        animationSpec = tween(800),
        label = "avatarGlow"
    )

    val infiniteTransition = rememberInfiniteTransition(label = "pulseRing")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.95f,
        targetValue = 1.08f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )

    Box(
        modifier = modifier.size(size),
        contentAlignment = Alignment.Center
    ) {
        // 1. Double Glowing Ambient Rings (Glass depth)
        Box(
            modifier = Modifier
                .fillMaxSize()
                .scale(pulseScale)
                .blur(radius = 16.dp)
                .clip(CircleShape)
                .background(animatedGlowColor.copy(alpha = 0.15f))
                .border(2.dp, animatedGlowColor.copy(alpha = 0.3f), CircleShape)
        )

        Box(
            modifier = Modifier
                .size(size - 16.dp)
                .blur(radius = 8.dp)
                .clip(CircleShape)
                .background(animatedGlowColor.copy(alpha = 0.10f))
        )

        if (avatarMode == "WebView") {
            // Track model load state: null = loading, true = success, false = failed
            val modelLoaded = remember { mutableStateOf<Boolean?>(null) }

            // Loading safety timeout: if model fails to report load state in 8s, fallback
            LaunchedEffect(Unit) {
                delay(8000)
                if (modelLoaded.value == null) {
                    Log.w("AikoAvatar", "Live2D load timeout after 8s. Falling back.")
                    modelLoaded.value = false
                }
            }

            // Create the JS bridge that receives callbacks from the HTML page
            val bridge = remember {
                AikoBridge { success ->
                    modelLoaded.value = success
                }
            }

            val webView = remember {
                android.webkit.WebView(context).apply {
                    settings.javaScriptEnabled = true
                    settings.allowFileAccess = true
                    settings.allowContentAccess = true
                    @Suppress("DEPRECATION")
                    settings.allowFileAccessFromFileURLs = true
                    @Suppress("DEPRECATION")
                    settings.allowUniversalAccessFromFileURLs = true
                    settings.domStorageEnabled = true
                    @Suppress("DEPRECATION")
                    settings.setRenderPriority(WebSettings.RenderPriority.HIGH)
                    setBackgroundColor(0) // Transparent background

                    // Add JS bridge for model load status reporting
                    addJavascriptInterface(bridge, "AikoBridge")

                    // Log JS console messages to logcat for debugging WebView issues
                    webChromeClient = object : WebChromeClient() {
                        override fun onConsoleMessage(consoleMessage: ConsoleMessage?): Boolean {
                            consoleMessage?.let {
                                val tag = "AikoWebView"
                                val msg = "${it.message()} [${it.sourceId()}:${it.lineNumber()}]"
                                when (it.messageLevel()) {
                                    ConsoleMessage.MessageLevel.ERROR -> Log.e(tag, msg)
                                    ConsoleMessage.MessageLevel.WARNING -> Log.w(tag, msg)
                                    else -> Log.d(tag, msg)
                                }
                            }
                            return true
                        }
                    }

                    webViewClient = object : android.webkit.WebViewClient() {
                        override fun onPageFinished(view: android.webkit.WebView?, url: String?) {
                            val js = "if (window.updateState) { window.updateState('$dominantEmotion', ${emotionState.dopamine}, ${emotionState.serotonin}, ${emotionState.cortisol}, ${emotionState.adrenaline}, $isSpeaking, ${if (isSpeaking) 0.6f else 0.0f}); }"
                            view?.evaluateJavascript(js, null)
                        }
                    }
                    loadUrl("file:///android_asset/live2d/live2d_avatar.html")
                }
            }

            // Push dynamic updates to the model
            LaunchedEffect(dominantEmotion, emotionState, isSpeaking) {
                val js = "if (window.updateState) { window.updateState('$dominantEmotion', ${emotionState.dopamine}, ${emotionState.serotonin}, ${emotionState.cortisol}, ${emotionState.adrenaline}, $isSpeaking, ${if (isSpeaking) 0.6f else 0.0f}); }"
                webView.evaluateJavascript(js, null)
            }

            // Pauses the WebGL ticker when backgrounded or disposed, resuming it on active display
            DisposableEffect(lifecycleOwner) {
                val observer = LifecycleEventObserver { _, event ->
                    when (event) {
                        Lifecycle.Event.ON_RESUME -> {
                            webView.evaluateJavascript("if (window.app && window.app.ticker) { window.app.ticker.start(); }", null)
                        }
                        Lifecycle.Event.ON_PAUSE -> {
                            webView.evaluateJavascript("if (window.app && window.app.ticker) { window.app.ticker.stop(); }", null)
                        }
                        else -> {}
                    }
                }
                lifecycleOwner.lifecycle.addObserver(observer)
                onDispose {
                    lifecycleOwner.lifecycle.removeObserver(observer)
                    webView.evaluateJavascript("if (window.app && window.app.ticker) { window.app.ticker.stop(); }", null)
                }
            }

            when (modelLoaded.value) {
                null -> {
                    // Model is still loading — show WebView (it may succeed) plus a loading indicator
                    AndroidView(
                        factory = { webView },
                        modifier = Modifier
                            .size(size - 24.dp)
                    )
                    // Overlay a subtle loading indicator
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        CircularProgressIndicator(
                            color = animatedGlowColor,
                            strokeWidth = 2.dp,
                            modifier = Modifier.size(24.dp)
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "Loading Aiko...",
                            color = animatedGlowColor.copy(alpha = 0.8f),
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
                true -> {
                    // Model loaded successfully — show full WebView without circular clip
                    AndroidView(
                        factory = { webView },
                        modifier = Modifier
                            .size(size - 24.dp)
                    )
                }
                false -> {
                    // Model failed to load (OOM etc.) — show beautiful fallback
                    AikoPersona(
                        emotionTag = dominantEmotion,
                        modifier = Modifier.size(size - 24.dp)
                    )
                }
            }
        } else {
            // HIGH-FIDELITY FALLBACK: Glowing Frosted Glass Refraction Sphere Core
            AikoPersona(
                emotionTag = dominantEmotion,
                modifier = Modifier.size(size - 24.dp)
            )
        }
    }
}
