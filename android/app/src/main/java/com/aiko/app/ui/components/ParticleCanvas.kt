package com.aiko.app.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import com.aiko.app.ui.theme.AikoColors
import kotlin.random.Random

data class Particle(
    var x: Float,
    var y: Float,
    val size: Float,
    val speedX: Float,
    val speedY: Float,
    var alpha: Float,
    val alphaSpeed: Float
)

@Composable
fun ParticleCanvas(
    modifier: Modifier = Modifier,
    activeColor: Color = AikoColors.Primary
) {
    val animatedColor by animateColorAsState(
        targetValue = activeColor,
        animationSpec = tween(1000),
        label = "particleColor"
    )

    val particles = remember { mutableStateListOf<Particle>() }

    // Spawn initial particles
    LaunchedEffect(Unit) {
        repeat(30) {
            particles.add(
                Particle(
                    x = Random.nextFloat(),
                    y = Random.nextFloat(),
                    size = Random.nextFloat() * 12f + 4f,
                    speedX = (Random.nextFloat() - 0.5f) * 0.0005f,
                    speedY = -Random.nextFloat() * 0.001f - 0.0002f, // upward drift
                    alpha = Random.nextFloat() * 0.5f + 0.1f,
                    alphaSpeed = Random.nextFloat() * 0.005f + 0.002f
                )
            )
        }
    }

    // Animation Loop
    LaunchedEffect(Unit) {
        while (true) {
            withFrameNanos { _ ->
                particles.forEachIndexed { index, p ->
                    // Update positions
                    p.x += p.speedX
                    p.y += p.speedY
                    p.alpha -= p.alphaSpeed

                    // Reset if faded or out of bounds
                    if (p.alpha <= 0f || p.y < 0f || p.x < 0f || p.x > 1f) {
                        particles[index] = Particle(
                            x = Random.nextFloat(),
                            y = 1.0f, // start at bottom
                            size = Random.nextFloat() * 12f + 4f,
                            speedX = (Random.nextFloat() - 0.5f) * 0.0005f,
                            speedY = -Random.nextFloat() * 0.001f - 0.0002f,
                            alpha = Random.nextFloat() * 0.5f + 0.3f,
                            alphaSpeed = Random.nextFloat() * 0.005f + 0.002f
                        )
                    }
                }
            }
        }
    }

    Canvas(modifier = modifier.fillMaxSize()) {
        val width = size.width
        val height = size.height

        particles.forEach { p ->
            val drawX = p.x * width
            val drawY = p.y * height
            drawCircle(
                color = animatedColor.copy(alpha = p.alpha),
                radius = p.size,
                center = Offset(drawX, drawY)
            )
        }
    }
}
