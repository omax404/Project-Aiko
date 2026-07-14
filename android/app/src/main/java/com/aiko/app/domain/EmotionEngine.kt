package com.aiko.app.domain

import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.max
import kotlin.math.min

data class EmotionState(
    val dopamine: Float = 0.5f,    // 0f-1f — pleasure, reward
    val serotonin: Float = 0.5f,   // 0f-1f — mood, stability
    val cortisol: Float = 0.2f,    // 0f-1f — stress, fear
    val adrenaline: Float = 0.3f   // 0f-1f — excitement, urgency
)

@Singleton
class EmotionEngine @Inject constructor() {

    fun processMessage(msg: String, currentState: EmotionState): EmotionState {
        val text = msg.lowercase()
        var d = currentState.dopamine
        var s = currentState.serotonin
        var c = currentState.cortisol
        var a = currentState.adrenaline

        // 1. Dopamine Adjustments (Pleasure, Compliments, Rewards)
        if (text.contains("cute") || text.contains("love") || text.contains("pretty") ||
            text.contains("beautiful") || text.contains("good job") || text.contains("sweet") ||
            text.contains("compliment") || text.contains("like you") || text.contains("smart")
        ) {
            d = min(1.0f, d + 0.25f)
            a = min(1.0f, a + 0.15f) // Spikes excitement too!
            c = max(0.0f, c - 0.15f)
        } else if (text.contains("yes") || text.contains("great") || text.contains("awesome") ||
            text.contains("happy") || text.contains("fun") || text.contains("smile")
        ) {
            d = min(1.0f, d + 0.15f)
            s = min(1.0f, s + 0.10f)
        }

        // 2. Serotonin Adjustments (Peace, Mood, Stability vs Sadness)
        if (text.contains("sad") || text.contains("cry") || text.contains("depressed") ||
            text.contains("lonely") || text.contains("hurt") || text.contains("pain") ||
            text.contains("died") || text.contains("sick") || text.contains("bad")
        ) {
            s = max(0.0f, s - 0.20f)
            c = min(1.0f, c + 0.25f) // Triggers worried/sad Aiko
        } else if (text.contains("relax") || text.contains("calm") || text.contains("peace") ||
            text.contains("safe") || text.contains("sleep") || text.contains("meditate")
        ) {
            s = min(1.0f, s + 0.20f)
            c = max(0.0f, c - 0.20f)
            a = max(0.0f, a - 0.15f)
        }

        // 3. Cortisol Adjustments (Stress, Anxiety, Anger)
        if (text.contains("angry") || text.contains("hate") || text.contains("mad") ||
            text.contains("scared") || text.contains("worry") || text.contains("panic") ||
            text.contains("stress") || text.contains("stop") || text.contains("annoying")
        ) {
            c = min(1.0f, c + 0.25f)
            d = max(0.0f, d - 0.15f)
            a = min(1.0f, a + 0.10f)
        }

        // 4. Adrenaline Adjustments (Excitement, Urgency, Questions)
        if (text.contains("?") || text.contains("what") || text.contains("how") ||
            text.contains("why") || text.contains("quick") || text.contains("fast") ||
            text.contains("hurry") || text.contains("!" )
        ) {
            a = min(1.0f, a + 0.10f)
        }

        // Natural baseline decay (slowly drifts back towards central stability of 0.5f over time/messages)
        d = d * 0.95f + 0.5f * 0.05f
        s = s * 0.95f + 0.5f * 0.05f
        c = c * 0.95f + 0.2f * 0.05f
        a = a * 0.95f + 0.3f * 0.05f

        return EmotionState(d, s, c, a)
    }

    /**
     * Parses the response from Gemini to extract Aiko's declared emotional tag.
     * Returns a pair of the parsed response (without the tag) and the matching dominant tag.
     */
    fun parseResponseEmotion(response: String): Pair<String, String> {
        val legacyRegex = "\\[EMO:(\\w+)\\]".toRegex(RegexOption.IGNORE_CASE)
        val markupRegex = "<emotion>\\s*(\\w+)\\s*</emotion>".toRegex(RegexOption.IGNORE_CASE)
        val tag = (markupRegex.find(response) ?: legacyRegex.find(response))?.groupValues?.get(1)?.lowercase() ?: "calm"
        // Never persist protocol metadata into a user-visible message.
        val cleanText = response.replace(legacyRegex, "").replace(markupRegex, "").trim()
        return Pair(cleanText, tag)
    }

    /**
     * Modifies the emotional state based directly on Aiko's parsed response emotion tag.
     */
    fun applyTagImpact(tag: String, state: EmotionState): EmotionState {
        var d = state.dopamine
        var s = state.serotonin
        var c = state.cortisol
        var a = state.adrenaline

        when (tag) {
            "happy", "excited" -> {
                d = min(1.0f, d + 0.20f)
                s = min(1.0f, s + 0.10f)
                c = max(0.0f, c - 0.10f)
                if (tag == "excited") a = min(1.0f, a + 0.20f)
            }
            "flustered" -> {
                d = min(1.0f, d + 0.30f) // Spikes dopamine!
                a = min(1.0f, a + 0.25f) // Adrenaline rushes
                c = max(0.0f, c - 0.05f)
            }
            "devoted" -> {
                s = min(1.0f, s + 0.25f)
                d = min(1.0f, d + 0.15f)
                c = max(0.0f, c - 0.15f)
            }
            "playful" -> {
                d = min(1.0f, d + 0.15f)
                a = min(1.0f, a + 0.15f)
            }
            "jealous", "worried" -> {
                c = min(1.0f, c + 0.20f)
                d = max(0.0f, d - 0.10f)
                if (tag == "jealous") a = min(1.0f, a + 0.15f)
            }
            "sad" -> {
                s = max(0.0f, s - 0.25f)
                c = min(1.0f, c + 0.15f)
                d = max(0.0f, d - 0.15f)
            }
            "calm" -> {
                s = min(1.0f, s + 0.10f)
                c = max(0.0f, c - 0.10f)
                a = max(0.0f, a - 0.10f)
            }
            "proud" -> {
                d = min(1.0f, d + 0.20f)
                s = min(1.0f, s + 0.15f)
                a = min(1.0f, a + 0.10f)
            }
        }

        return EmotionState(d, s, c, a)
    }

    /**
     * Determines the dominant emotion name using values.
     */
    fun determineDominantEmotion(state: EmotionState): String {
        return when {
            state.cortisol > 0.6f -> if (state.adrenaline > 0.5f) "jealous" else "worried"
            state.dopamine > 0.75f && state.adrenaline > 0.6f -> "flustered"
            state.dopamine > 0.7f -> "happy"
            state.serotonin > 0.75f && state.adrenaline > 0.4f -> "proud"
            state.serotonin > 0.7f && state.dopamine > 0.5f -> "devoted"
            state.adrenaline > 0.6f -> "excited"
            state.cortisol > 0.4f -> "sad"
            state.dopamine > 0.55f -> "playful"
            else -> "calm"
        }
    }
}
