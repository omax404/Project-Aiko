"""
AIKO'S EMOTIONAL GIF LIBRARY v2.0
Expanded emotional range with Smart Detection, Priority System, and Relationship Gating.
Makes Aiko feel truly alive by responding to contextual keywords intelligently.
"""

import random
import re
import aiohttp
import os
import logging

logger = logging.getLogger("GIFEngine")

# Public fallback API keys
TENOR_PUBLIC_KEY = "LIVDSRZULEQX"
GIPHY_PUBLIC_KEY = "dc6zaTOxFJmzC"

# ═══════════════════════════════════════════════════════════════
#                    EXPANDED GIF LIBRARY
# ═══════════════════════════════════════════════════════════════

AIKO_GIFS = {
    # --- Positive / Love ---
    'love': [
        "/stickers/09_Heart_Eyes_Rose.png"
    ],
    'happy': [
        "/stickers/01_Happy_Cheer.png",
        "/stickers/11_Laughing.png"
    ],
    'excited': [  
        "/stickers/13_Excited_Jump.png"
    ],
    
    # --- Bored / Done ---
    'bored': [
        "/stickers/17_Teacup_Sip.png"
    ],
    
    # --- Shocked / Surprised ---
    'shocked': [
        "/stickers/03_Surprised_Gasp.png"
    ],
    
    # --- Tired / Sleepy ---
    'tired': [
        "/stickers/04_Sleepy_Yawn.png"
    ],
    
    # --- Negative / Sad ---
    'sad': [
        "/stickers/12_Sad_Wilted_Rose.png"
    ],
    'cry': [
        "/stickers/05_Crying_Comical.png"
    ],
    'angry': [
        "/stickers/10_Annoyed_Pout.png"
    ],
    'pout': [
        "/stickers/10_Annoyed_Pout.png"
    ],

    # --- NEW: Disgust ---
    'disgust': [
        "/stickers/15_Sick_Dizzy.png"
    ],
    
    # --- NEW: Panic ---
    'panic': [
        "/stickers/03_Surprised_Gasp.png"
    ],
    
    # --- NEW: Victory ---
    'victory': [
        "/stickers/14_Winking_Peace.png"
    ],

    # --- Actions ---
    'hug': [
        "/stickers/07_Waving_Hello.png"
    ],
    'kiss': [
        "/stickers/09_Heart_Eyes_Rose.png"
    ],
    'blush': [
        "/stickers/02_Shy_Blush.png"
    ],
    'pat': [
        "/stickers/08_Thinking_Pose.png"
    ],
    'smug': [
        "/stickers/06_Confident_Smirk_Right.png",
        "/stickers/18_Confident_Smirk_Left.png"
    ],
    'bonk': [
        "/stickers/16_Determined_Fist.png"
    ],
    'lick': [
        "/stickers/14_Winking_Peace.png"
    ],
    
    # --- Yandere / Protective ---
    'yandere': [
        "/stickers/16_Determined_Fist.png"
    ],
    
    # --- Casual ---
    'confused': [
        "/stickers/15_Sick_Dizzy.png"
    ],
    'wave': [
        "/stickers/07_Waving_Hello.png"
    ],
    'thinking': [
        "/stickers/08_Thinking_Pose.png"
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




async def search_gif(query: str, provider: str = None) -> str | None:
    """
    Search Tenor and/or Giphy dynamically for a GIF.
    If provider is not specified, tries Tenor first (better for anime), then Giphy.
    Uses custom API keys if present, otherwise falls back to public beta keys.
    If connection fails or results are empty, falls back to local static categories.
    """
    if not query:
        return None

    # Ensure search remains themed (cute anime style)
    search_query = query
    if "anime" not in query.lower():
        search_query = f"{query} anime"

    tenor_key = os.getenv("TENOR_API_KEY", TENOR_PUBLIC_KEY)
    giphy_key = os.getenv("GIPHY_API_KEY", GIPHY_PUBLIC_KEY)

    # List of search tasks to attempt
    providers_to_try = []
    if provider == "giphy":
        providers_to_try = [("giphy", giphy_key)]
    elif provider == "tenor":
        providers_to_try = [("tenor", tenor_key)]
    else:
        # Default: try Tenor first, then Giphy
        providers_to_try = [("tenor", tenor_key), ("giphy", giphy_key)]

    async with aiohttp.ClientSession() as session:
        for name, key in providers_to_try:
            try:
                if name == "tenor":
                    if len(key) == 12:  # legacy public v1 key
                        url = "https://api.tenor.com/v1/search"
                        params = {
                            "q": search_query,
                            "key": key,
                            "limit": 8,
                            "media_filter": "minimal"
                        }
                    else:
                        url = "https://tenor.googleapis.com/v2/search"
                        params = {
                            "q": search_query,
                            "key": key,
                            "client_key": "aiko_desktop",
                            "limit": 8,
                            "media_filter": "gif"
                        }
                    async with session.get(url, params=params, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            results = data.get("results", [])
                            if results:
                                # Choose randomly from top results to feel fresh and dynamic
                                chosen = random.choice(results)
                                media_formats = chosen.get("media_formats", {})
                                if not media_formats:
                                    media_list = chosen.get("media", [])
                                    if media_list:
                                        media_formats = media_list[0]
                                gif_url = media_formats.get("gif", {}).get("url")
                                if gif_url:
                                    logger.info(f"Successfully retrieved GIF from Tenor for: {query}")
                                    return gif_url
                        else:
                            logger.warning(f"Tenor API returned status {resp.status}")
                elif name == "giphy":
                    url = "https://api.giphy.com/v1/gifs/search"
                    params = {
                        "api_key": key,
                        "q": search_query,
                        "limit": 8
                    }
                    async with session.get(url, params=params, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            results = data.get("data", [])
                            if results:
                                chosen = random.choice(results)
                                gif_url = chosen.get("images", {}).get("original", {}).get("url")
                                if gif_url:
                                    logger.info(f"Successfully retrieved GIF from Giphy for: {query}")
                                    return gif_url
                        else:
                            logger.warning(f"Giphy API returned status {resp.status}")
            except Exception as e:
                logger.error(f"Error querying {name} for GIF: {e!r}")

    # --- Robust Fallback ---
    # Scan the query/prompt using get_emotion_category
    detected_emotion = get_emotion_category(query)
    if not detected_emotion:
        # Fall back to a general positive emotion or happy category if nothing detected
        detected_emotion = "happy"
        
    local_gif = get_random_gif(detected_emotion)
    if local_gif:
        logger.info(f"GIF API failed/empty. Graceful fallback to local static category '{detected_emotion}'")
        return local_gif

    return None
