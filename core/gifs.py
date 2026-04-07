"""
AIKO'S EMOTIONAL GIF LIBRARY v2.0
Expanded emotional range with Smart Detection, Priority System, and Relationship Gating.
Makes Aiko feel truly alive by responding to contextual keywords intelligently.
"""

import random
import re

# ═══════════════════════════════════════════════════════════════
#                    EXPANDED GIF LIBRARY
# ═══════════════════════════════════════════════════════════════

AIKO_GIFS = {
    # --- Positive / Love ---
    'love': [
        "https://media.tenor.com/UEFGoNHQg2wAAAAC/fullmetal-alchemist-roy-mustang.gif",
        "https://media.tenor.com/Nos-wttNWeIAAAAC/chihaya-anon-anon-chihaya.gif",
        "https://media.tenor.com/b7KyU2wDv04AAAAC/kiss-anime.gif",
        "https://media.tenor.com/5E98UTF-L_YAAAAC/happy-love.gif",
        "https://media.tenor.com/2l3q2Wc2Z4kAAAAC/anime-love-heart.gif",
        "https://media.tenor.com/J3iE2x-4a7UAAAAC/love-anime.gif",
        "https://media.tenor.com/z2QlOqXwJ9AAAAAC/anime-love.gif",
    ],
    'happy': [
        "https://media.tenor.com/VRW3rpzMnYIAAAAC/kaoruko-waguri-the-fragrant-flower-blooms-with-dignity.gif",
        "https://media.tenor.com/_X5Kn5MWhRMAAAAC/yay-yeah.gif",
    ],
    'excited': [  
        "https://tenor.com/fr/view/anime-woo-bounce-fast-jump-gif-16252995",
        "https://tenor.com/fr/view/oshi-no-ko-onk-oshi-no-ko-season-2-episode-11-anime-gif-9124778409799054596"
         ],
    
    # --- Bored / Done ---
    'bored': [
        "https://tenor.com/fr/view/anime-frieren-tasty-eating-eat-gif-8951409568795430521",
     
    ],
    
    # --- Shocked / Surprised ---
    'shocked': [
        "https://media.tenor.com/reP8M82-c_gAAAAC/anime-shocked.gif",
        "https://media.tenor.com/8v8S_fN-p_4AAAAC/surprised-anime-face.gif",
        "https://media.tenor.com/p_C0G7MIsU0AAAAC/shocked-expression.gif",
        "https://media.tenor.com/BBCQZcLFD_0AAAAC/anime-shocked-oresuki.gif",
    ],
    
    # --- Tired / Sleepy ---
    'tired': [
        "https://media.tenor.com/W2q2s2x4k2x4AAAAC/anime-sleep.gif",
        "https://media.tenor.com/IMRLmefJ6MsAAAAAC/tired-anime.gif",
        "https://media.tenor.com/6X7pS8X8L8YAAAAC/sleepy-anime-girl.gif",
        "https://media.tenor.com/XExNWqF5VTEAAAAC/anime-sleepy.gif",
    ],
    
    # --- Negative / Sad ---
    'sad': [
        "https://media.tenor.com/DiFQ_Rl3dCQAAAAAC/anime-cry-crying.gif",
        "https://media.tenor.com/35S_M89zT3sAAAAAC/horimiya-anime.gif",
        "https://media.tenor.com/DifoWwjRvOcAAAAAC/tohru-honda-tohru.gif",
        "https://media.tenor.com/jczQB19mnk0AAAAAC/chibi-anime-boy.gif",
        "https://media.tenor.com/5l3q2Wc2Z4kAAAAC/anime-sad.gif",
    ],
    'cry': [
        "https://media.tenor.com/DiFQ_Rl3dCQAAAAAC/anime-cry-crying.gif",
        "https://media.tenor.com/35S_M89zT3sAAAAAC/horimiya-anime.gif",
        "https://media.tenor.com/DifoWwjRvOcAAAAAC/tohru-honda-tohru.gif",
        "https://media.tenor.com/P4w8w-1q1wAAAAAC/anime-tears.gif",
    ],
    'angry': [
        "https://media.tenor.com/FHTOu1fN6DcAAAAC/angry-anime.gif",
        "https://media.tenor.com/xDWLUFUVii8AAAAC/anime-pout.gif",
        "https://media.tenor.com/1q2w3e4r5t6yAAAAAC/anime-mad.gif",
        "https://media.tenor.com/W_1s_6CPJOAAAAAC/anime-angry.gif",
    ],
    'pout': [
        "https://media.tenor.com/FHTOu1fN6DcAAAAC/angry-anime.gif",
        "https://media.tenor.com/xDWLUFUVii8AAAAC/anime-pout.gif",
        "https://media.tenor.com/YseiXI4o5bsAAAAC/sad-pout.gif",
        "https://media.tenor.com/i--qyYG3cJMAAAAC/anime-pout.gif",
        "https://media.tenor.com/9v8S_fN-p_4AAAAC/miku-pout.gif",
    ],

    # --- NEW: Disgust ---
    'disgust': [
        "https://media.tenor.com/T096XAn8_8EAAAAC/anime-gross.gif",
        "https://media.tenor.com/FHTOu1fN6DcAAAAC/disgust-anime.gif",
        "https://media.tenor.com/xDWLUFUVii8AAAAC/ewe-anime.gif",
    ],
    
    # --- NEW: Panic ---
    'panic': [
        "https://media.tenor.com/reP8M82-c_gAAAAC/anime-panic.gif",
        "https://media.tenor.com/Qy7K8v-2T2AAAAAC/anya-panic.gif",
        "https://media.tenor.com/WvDHCwXvSgMAAAAC/scared-anime.gif",
    ],
    
    # --- NEW: Victory ---
    'victory': [
        "https://media.tenor.com/6a6Atg2FjQ4AAAAC/anime-victory.gif",
        "https://media.tenor.com/_X5Kn5MWhRMAAAAC/anime-cheer.gif",
        "https://media.tenor.com/IMRLmefJ6MsAAAAAC/peace-sign-anime.gif",
    ],

    # --- Actions ---
    'hug': [
        "https://media.tenor.com/TYvVBj3Fi5AAAAAC/hug.gif",
        "https://media.tenor.com/7f9CqFtd4SsAAAAC/hug.gif",
        "https://media.tenor.com/IpGw3LOZi2wAAAAC/hugtrip.gif",
        "https://media.tenor.com/BFmsQg9J1ZMAAAAC/chikako-hugging-otohime-for-the-first-and-she-confused.gif",
    ],
    'kiss': [
        "https://media.tenor.com/b7KyU2wDv04AAAAC/kiss-anime.gif",
        "https://media.tenor.com/5E98UTF-L_YAAAAC/happy-love.gif",
    ],
    'blush': [
        "https://media.tenor.com/YcjMpOSyz2AAAAAC/marin-kitagawa-blush.gif",
        "https://media.tenor.com/GiOGySHeERMAAAAC/anime-blush.gif",
        "https://media.tenor.com/DLir-ShS_BsAAAAC/marin-marin-kitagawa.gif",
        "https://media.tenor.com/ia9ZGb4SMWcAAAAC/anime-blush-blush.gif",
    ],
    'pat': [
        "https://media.tenor.com/Y7BZc7W1i8AAAAAC/anime-head-pat.gif",
        "https://media.tenor.com/wLqFGYigNcAAAAAC/kaede-azusagawa-kaede.gif",
        "https://media.tenor.com/E6fMgW18e6AAAAAC/pat-head.gif",
        "https://media.tenor.com/kS-f_A7XG98AAAAC/headpat-anime.gif",
    ],
    'smug': [
        "https://media.tenor.com/Qy7K8v-2T2AAAAAC/anya-smug.gif",
        "https://media.tenor.com/79S_A3-2X-EAAAAC/smug-anime.gif",
    ],
    'bonk': [
        "https://media.tenor.com/9P_G_vS5WzUAAAAC/anime-bonk.gif",
        "https://media.tenor.com/v8S_fN-p_4YAAAAC/anime-hammer.gif",
        "https://media.tenor.com/DHYvIdj_RIEAAAAC/bonk-anime.gif",
    ],
    'lick': [
        "https://media.tenor.com/5w2e3r4t5y6uAAAAAC/anime-lick.gif",
    ],
    
    # --- Yandere / Protective ---
    'yandere': [
        "https://media.tenor.com/w2wqNH8jFywAAAAAC/yandere-mine.gif",
        "https://media.tenor.com/KLUHpOURlWAAAAAC/yandere-anime.gif",
        "https://media.tenor.com/QaBuatKOCZwAAAAAC/princess-connect-re-dive-anime.gif",
        "https://media.tenor.com/QCMSAySva2wAAAAAC/eriko-princess-connect-re-dive.gif",
    ],
    
    # --- Casual ---
    'confused': [
        "https://media.tenor.com/BFmsQg9J1ZMAAAAC/chikako-hugging-otohime-for-the-first-and-she-confused.gif",
        "https://media.tenor.com/y6NN6z0lKPAAAAAC/what-confused.gif",
    ],
    'wave': [
        "https://media.tenor.com/aXl7XVXB55IAAAAC/anime-wave.gif",
        "https://media.tenor.com/aKMsM9ybIY4AAAAC/wave-waving.gif",
    ],
    'thinking': [
        "https://media.tenor.com/Lb-sTaI3MLUAAAAC/anime-think.gif",
        "https://media.tenor.com/3KCh8xL6TLMAAAAC/curious-question-mark.gif", 
        "https://tenor.com/fr/view/the-fragrant-flower-blooms-with-dignity-kaoruko-waguri-kaoru-hana-wa-rin-to-saku-waguri-kaoruko-gif-13996586934910010189",
    ],
}


# ═══════════════════════════════════════════════════════════════
#                    EMOTION TRIGGER KEYWORDS
# ═══════════════════════════════════════════════════════════════

EMOTION_TRIGGERS = {
    # Intense emotions (checked first via priority)
    'yandere': ['mine', 'only mine', 'other girls', 'who is she', 'jealous', 'possessive', 'stay away'],
    'bonk': ['horny', 'lewd', 'sus', 'degenerate', 'perv', 'naughty', 'dirty minded', '😏'],
    'angry': ['angry', 'mad', 'furious', 'pissed', 'hate', 'rage', '😡', 'grr'],
    'sad': ['sad', 'depressed', 'lonely', 'miss you', 'crying', '😢', '😭', 'heartbroken'],
    'panic': ['help', 'panic', 'scared', 'screaming', 'aaaaa', 'worry', 'oh no'],
    'shocked': ['what', 'nani', 'omg', 'holy', 'wow', 'real?', 'seriously', 'no way', '!?', 'wtf', 'wth'],
    'disgust': ['gross', 'eww', 'stinky', 'ugly', 'disgusting', 'yuck', 'nasty'],
    
    # Positive emotions (checked after intense)
    'love': ['love', 'ily', 'i love you', 'heart', 'sweetie', 'darling', 'mwah', '❤', '💕', '💖', 'xoxo', 'baby'],
    'blush': ['cute', 'beautiful', 'gorgeous', 'pretty', 'adorable', 'flatter', 'charming', '///', 'kawaii'],
    'excited': ['excited', 'omggg', 'cant wait', "let's go", 'hyped', 'pumped', 'wooo'],
    'victory': ['win', 'won', 'victory', 'yes!', 'gg', 'ez clap', 'celebrate', 'we did it'],
    'happy': ['yay', 'happy', 'awesome', 'great', 'nice', 'hype', 'amazing', 'perfect', 'fantastic', 'wonderful', '🎉', '✨'],
    
    # Action emotions
    'hug': ['hug', 'cuddle', 'hold me', 'comfort', 'embrace', '🤗'],
    'pat': ['headpat', 'pat pat', 'good girl', 'good job', 'well done', 'petpet'],
    'smug': ['lol', 'lmao', 'too easy', 'rekt', 'pathetic', 'gotcha', 'owned'],
    'pout': ['mean', 'unfair', 'unhappy', 'meanie', 'hmph', 'not fair'],
    
    # Passive emotions (checked last)
    'tired': ['sleepy', 'night', 'tired', 'exhausted', 'bed', 'goodnight', 'gn', 'zzz', '😴', 'yawn'],
    'bored': ['boring', 'meh', 'whatever', 'slow', 'im bored', 'nothing to do', 'bland'],
    'thinking': ['hmm', 'wonder', 'maybe', 'perhaps', 'consider', 'pondering'],
    'confused': ['huh', 'what?', 'confused', "don't understand", 'weird', '???', 'explain'],
    'wave': ['hello', 'hey', 'yo', 'sup', 'morning', 'afternoon', 'evening', 'greetings'],
}

# Priority order: intense emotions > positive > action > passive
# This ensures Aiko's "intensity" isn't missed
EMOTION_PRIORITY = [
    # Intense (check first)
    'yandere', 'bonk', 'angry', 'sad', 'panic', 'shocked', 'disgust',
    # Positive
    'love', 'blush', 'excited', 'victory', 'happy',
    # Action
    'hug', 'pat', 'smug', 'pout',
    # Passive (check last)
    'tired', 'bored', 'thinking', 'confused', 'wave'
]

# Relationship-gated emotions (require affection level)
RELATIONSHIP_GATED = {
    'love': 50,      # Need 50+ affection for love GIFs
    'kiss': 70,      # Need 70+ affection for kiss GIFs
    'yandere': 60,   # Need 60+ affection for yandere mode
    'blush': 30,     # Low threshold for blush
}


# ═══════════════════════════════════════════════════════════════
#                    SMART DETECTION LOGIC v2.0
# ═══════════════════════════════════════════════════════════════

def detect_aiko_emotion(message_text: str, affection_level: int = 100) -> str | None:
    """
    Scans the text for keywords and returns a matching GIF URL.
    Uses regex for whole-word matching and priority system.
    
    Args:
        message_text: The user's message to scan
        affection_level: User's affection level (0-100) for relationship gating
    
    Returns:
        GIF URL or None if no match found
    
    Usage:
        gif_url = detect_aiko_emotion("I love you so much!", affection_level=80)
        if gif_url:
            await channel.send(gif_url)
    """
    content = message_text.lower()
    
    for category in EMOTION_PRIORITY:
        if category not in EMOTION_TRIGGERS:
            continue
            
        # Check relationship gate
        if category in RELATIONSHIP_GATED:
            required_affection = RELATIONSHIP_GATED[category]
            if affection_level < required_affection:
                continue  # Skip this emotion - not enough affection
        
        keywords = EMOTION_TRIGGERS[category]
        for word in keywords:
            # Use regex for whole-word matching (avoids 'hi' in 'thinking')
            # But allow emoji/symbol triggers to match anywhere
            if word.isalpha():
                pattern = r'\b' + re.escape(word) + r'\b'
                if re.search(pattern, content):
                    if category in AIKO_GIFS and AIKO_GIFS[category]:
                        return random.choice(AIKO_GIFS[category])
            else:
                # Non-alpha (emoji, symbols) - direct match
                if word in content:
                    if category in AIKO_GIFS and AIKO_GIFS[category]:
                        return random.choice(AIKO_GIFS[category])
    
    return None


def get_emotion_category(message_text: str, affection_level: int = 100) -> str | None:
    """
    Returns the emotion category name instead of a GIF.
    Useful for setting VTS expressions or other emotion-based logic.
    
    Usage:
        emotion = get_emotion_category("I love you!")
        print(emotion)  # Output: 'love'
    """
    content = message_text.lower()
    
    for category in EMOTION_PRIORITY:
        if category not in EMOTION_TRIGGERS:
            continue
            
        # Check relationship gate
        if category in RELATIONSHIP_GATED:
            if affection_level < RELATIONSHIP_GATED[category]:
                continue
        
        keywords = EMOTION_TRIGGERS[category]
        for word in keywords:
            if word.isalpha():
                pattern = r'\b' + re.escape(word) + r'\b'
                if re.search(pattern, content):
                    return category
            else:
                if word in content:
                    return category
    
    return None


def get_random_gif(category: str) -> str | None:
    """
    Get a random GIF from a specific category.
    Returns None if category doesn't exist.
    """
    if category in AIKO_GIFS and AIKO_GIFS[category]:
        return random.choice(AIKO_GIFS[category])
    return None


def get_all_categories() -> list:
    """Returns a list of all available emotion categories."""
    return list(AIKO_GIFS.keys())


def should_send_gif(chance: float = 0.5) -> bool:
    """
    Returns True with the given probability.
    Use this to add cooldown/chance to GIF sending.
    
    Usage:
        if should_send_gif(0.5):  # 50% chance
            gif = detect_aiko_emotion(message)
            if gif:
                await channel.send(gif)
    """
    return random.random() < chance
