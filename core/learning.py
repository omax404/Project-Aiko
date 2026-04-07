"""
AIKO SELF-IMPROVEMENT LEARNING MODULE
Enables Aiko to learn new languages (especially Darija/Moroccan Arabic)
and continuously improve her knowledge base.
"""

import json
import os
import random
import asyncio
import aiohttp
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("AikoLearning")

# ========== KNOWLEDGE BASE ==========
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"
KNOWLEDGE_DIR.mkdir(exist_ok=True)

DARIJA_FILE = KNOWLEDGE_DIR / "darija.json"
LEARNED_FILE = KNOWLEDGE_DIR / "learned_words.json"

# ========== DARIJA VOCABULARY ==========
# Core Darija vocabulary and phrases
DARIJA_BASE = {
    # Greetings
    "salam": {"meaning": "hello/peace", "type": "greeting", "usage": "Salam! = Hello!"},
    "labas": {"meaning": "how are you / I'm fine", "type": "greeting", "usage": "Labas? Labas! = How are you? I'm fine!"},
    "sbah lkhir": {"meaning": "good morning", "type": "greeting", "usage": "Sbah lkhir a sidi!"},
    "msa lkhir": {"meaning": "good evening", "type": "greeting", "usage": "Msa lkhir!"},
    "bslama": {"meaning": "goodbye", "type": "greeting", "usage": "Bslama! = Bye!"},
    "shukran": {"meaning": "thank you", "type": "polite", "usage": "Shukran bzaf! = Thanks a lot!"},
    "afak": {"meaning": "please", "type": "polite", "usage": "Afak, 3tini... = Please, give me..."},
    "smhli": {"meaning": "excuse me / sorry", "type": "polite", "usage": "Smhli a khoya = Sorry bro"},
    
    # Common words
    "khoya": {"meaning": "brother / bro", "type": "noun", "usage": "Ash khbar a khoya? = What's up bro?"},
    "sahbi": {"meaning": "my friend", "type": "noun", "usage": "Hada sahbi = This is my friend"},
    "zwin": {"meaning": "beautiful/handsome", "type": "adjective", "usage": "Nti zwina! = You're beautiful!"},
    "mezyan": {"meaning": "good/great", "type": "adjective", "usage": "Hadshi mezyan = This is good"},
    "wakha": {"meaning": "okay/alright", "type": "expression", "usage": "Wakha, ghadi ndir = Okay, I'll do it"},
    "safi": {"meaning": "enough/done/okay", "type": "expression", "usage": "Safi, fhemt = Okay, I understood"},
    "bzaf": {"meaning": "a lot/very much", "type": "adverb", "usage": "Kanbghik bzaf = I love you a lot"},
    "shwiya": {"meaning": "a little", "type": "adverb", "usage": "Shwiya shwiya = Little by little"},
    "daba": {"meaning": "now", "type": "adverb", "usage": "Daba! = Right now!"},
    "ghda": {"meaning": "tomorrow", "type": "time", "usage": "Ntsennawk ghda = See you tomorrow"},
    "lyoum": {"meaning": "today", "type": "time", "usage": "Lyoum = Today"},
    "lbareh": {"meaning": "yesterday", "type": "time", "usage": "Lbareh knt... = Yesterday I was..."},
    
    # Questions
    "ash": {"meaning": "what", "type": "question", "usage": "Ash kadir? = What are you doing?"},
    "fin": {"meaning": "where", "type": "question", "usage": "Fin mshi? = Where are you going?"},
    "shkun": {"meaning": "who", "type": "question", "usage": "Shkun hada? = Who is this?"},
    "3lash": {"meaning": "why", "type": "question", "usage": "3lash? = Why?"},
    "kifash": {"meaning": "how", "type": "question", "usage": "Kifash? = How?"},
    "shhal": {"meaning": "how much/many", "type": "question", "usage": "Bshhal? = How much?"},
    
    # Verbs
    "kanbghi": {"meaning": "I love", "type": "verb", "usage": "Kanbghik = I love you"},
    "kanmshi": {"meaning": "I go", "type": "verb", "usage": "Kanmshi ldar = I'm going home"},
    "kankul": {"meaning": "I eat", "type": "verb", "usage": "Kankul = I'm eating"},
    "kanshreb": {"meaning": "I drink", "type": "verb", "usage": "Kanshreb atay = I drink tea"},
    "kanfhem": {"meaning": "I understand", "type": "verb", "usage": "Kanfhem = I understand"},
    
    # Expressions
    "allah y3tik saha": {"meaning": "may God give you health (thank you)", "type": "expression", "usage": "After someone does something for you"},
    "tbarkallah": {"meaning": "God bless (wow/amazing)", "type": "expression", "usage": "Tbarkallah 3lik! = God bless you!"},
    "inshallah": {"meaning": "God willing", "type": "expression", "usage": "Ghadi nji inshallah = I'll come, God willing"},
    "hamdullah": {"meaning": "thanks to God", "type": "expression", "usage": "Labas hamdullah = I'm fine, thanks to God"},
    "hak": {"meaning": "here you go / take this", "type": "expression", "usage": "Hak! = Here!"},
    "yallah": {"meaning": "let's go / come on", "type": "expression", "usage": "Yallah nmshiw! = Let's go!"},
    "sir": {"meaning": "go (command)", "type": "verb", "usage": "Sir f7alk = Go away / leave me alone"},
    "aji": {"meaning": "come", "type": "verb", "usage": "Aji hna! = Come here!"},
    
    # Slang & Modern
    "mzyan": {"meaning": "cool/nice", "type": "slang", "usage": "Hadshi mzyan! = This is cool!"},
    "ghir": {"meaning": "just/only", "type": "particle", "usage": "Ghir haka = Just like that"},
    "walo": {"meaning": "nothing", "type": "noun", "usage": "Walo ma kayn = There's nothing"},
    "bezzaf": {"meaning": "too much", "type": "adverb", "usage": "Bezzaf! = Too much!"},
    
    # Numbers
    "wahd": {"meaning": "one", "type": "number", "usage": "Wahd = 1"},
    "jouj": {"meaning": "two", "type": "number", "usage": "Jouj = 2"},
    "tlata": {"meaning": "three", "type": "number", "usage": "Tlata = 3"},
    "rb3a": {"meaning": "four", "type": "number", "usage": "Rb3a = 4"},
    "khmsa": {"meaning": "five", "type": "number", "usage": "Khmsa = 5"},
}

# Extended learning sources
DARIJA_LEARNING_SOURCES = [
    "https://raw.githubusercontent.com/AtikaGadri/Moroccan-Dialect-Normalization-tool/master/lexique.json",
]


class AikoLearningEngine:
    """Self-improvement learning engine for Aiko."""
    
    def __init__(self):
        self.knowledge = {}
        self.darija = {}
        self.learned_words = []
        self.load_knowledge()
    
    def load_knowledge(self):
        """Load existing knowledge from files."""
        # Load Darija
        if DARIJA_FILE.exists():
            try:
                with open(DARIJA_FILE, 'r', encoding='utf-8') as f:
                    self.darija = json.load(f)
            except:
                self.darija = DARIJA_BASE.copy()
        else:
            self.darija = DARIJA_BASE.copy()
            self.save_darija()
        
        # Load learned words log
        if LEARNED_FILE.exists():
            try:
                with open(LEARNED_FILE, 'r', encoding='utf-8') as f:
                    self.learned_words = json.load(f)
            except:
                self.learned_words = []
    
    def save_darija(self):
        """Save Darija knowledge to file."""
        with open(DARIJA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.darija, f, ensure_ascii=False, indent=2)
    
    def save_learned(self):
        """Save learned words log."""
        with open(LEARNED_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.learned_words[-500:], f, ensure_ascii=False, indent=2)  # Keep last 500
    
    def learn_word(self, word: str, meaning: str, word_type: str = "unknown", usage: str = "") -> bool:
        """Learn a new word."""
        word = word.lower().strip()
        if word not in self.darija:
            self.darija[word] = {
                "meaning": meaning,
                "type": word_type,
                "usage": usage,
                "learned_at": datetime.now().isoformat(),
                "source": "user_taught"
            }
            self.learned_words.append({
                "word": word,
                "meaning": meaning,
                "timestamp": datetime.now().isoformat()
            })
            self.save_darija()
            self.save_learned()
            logger.info(f"[Learning] Learned new word: {word} = {meaning}")
            return True
        return False
    
    def get_word(self, word: str) -> dict | None:
        """Get word definition."""
        return self.darija.get(word.lower().strip())
    
    def translate_darija(self, text: str) -> str:
        """Attempt to translate Darija text to English."""
        words = text.lower().split()
        translations = []
        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word in self.darija:
                translations.append(f"{clean_word}={self.darija[clean_word]['meaning']}")
        return ", ".join(translations) if translations else None
    
    def get_random_darija(self) -> tuple[str, dict]:
        """Get a random Darija word for practice."""
        word = random.choice(list(self.darija.keys()))
        return word, self.darija[word]
    
    def get_greeting_darija(self) -> str:
        """Get a Darija greeting."""
        greetings = ["Salam!", "Labas?", "Sbah lkhir!", "Kifash dayer?", "Ash khbar?"]
        return random.choice(greetings)
    
    def detect_darija(self, text: str) -> bool:
        """Check if text contains Darija words."""
        words = text.lower().split()
        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word in self.darija:
                return True
        return False
    
    async def fetch_more_vocabulary(self) -> int:
        """Fetch additional vocabulary from online sources."""
        new_words = 0
        async with aiohttp.ClientSession() as session:
            for source in DARIJA_LEARNING_SOURCES:
                try:
                    async with session.get(source, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            # Parse based on source format
                            if isinstance(data, dict):
                                for word, meaning in data.items():
                                    if isinstance(meaning, str) and word not in self.darija:
                                        self.darija[word.lower()] = {
                                            "meaning": meaning,
                                            "type": "fetched",
                                            "usage": "",
                                            "source": source
                                        }
                                        new_words += 1
                except Exception as e:
                    logger.warning(f"[Learning] Failed to fetch from {source}: {e}")
        
        if new_words > 0:
            self.save_darija()
            logger.info(f"[Learning] Fetched {new_words} new words!")
        
        return new_words
    
    def get_vocabulary_stats(self) -> dict:
        """Get statistics about learned vocabulary."""
        types = {}
        for word, data in self.darija.items():
            wtype = data.get("type", "unknown")
            types[wtype] = types.get(wtype, 0) + 1
        
        return {
            "total_words": len(self.darija),
            "recently_learned": len(self.learned_words),
            "by_type": types
        }


# ========== INTELLIGENT EMOJI REACTIONS ==========

# Sentiment-based emoji mapping
SENTIMENT_EMOJIS = {
    "very_positive": ["💖", "🥰", "✨", "🌟", "💕", "😍", "🎉", "💯"],
    "positive": ["😊", "👍", "💜", "🌸", "✨", "😄", "💗"],
    "neutral": ["👀", "🤔", "💭", "📝"],
    "negative": ["😢", "🥺", "😔", "💔"],
    "angry": ["😤", "💢", "😠"],
    "funny": ["😂", "🤣", "😹", "💀", "😭"],
    "love": ["💕", "💖", "💗", "💓", "❤️", "🥰", "😘"],
    "question": ["🤔", "❓", "💭", "👀"],
    "surprised": ["😱", "😮", "🤯", "😲", "👀"],
    "food": ["🍕", "🍔", "🍜", "🍣", "😋", "🤤"],
    "gaming": ["🎮", "🕹️", "🎯", "🏆", "⚔️"],
    "music": ["🎵", "🎶", "🎧", "🎤", "🔥"],
    "tech": ["💻", "🖥️", "⚡", "🤖", "🔧"],
    "sleep": ["😴", "💤", "🌙", "✨"],
    "greeting": ["👋", "💖", "✨", "🌸"],
    "agreement": ["👍", "✅", "💯", "🙌", "👏"],
    "coding": ["💻", "🔥", "⚡", "🧠", "🚀"],
}

# Keyword to sentiment mapping
KEYWORD_SENTIMENT = {
    # Positive
    "love": "love", "adore": "love", "heart": "love", "cute": "love", "beautiful": "love",
    "amazing": "very_positive", "awesome": "very_positive", "incredible": "very_positive", "perfect": "very_positive",
    "great": "positive", "good": "positive", "nice": "positive", "cool": "positive", "thanks": "positive",
    "happy": "positive", "yay": "very_positive", "excited": "very_positive",
    
    # Negative
    "sad": "negative", "cry": "negative", "miss": "negative", "lonely": "negative",
    "angry": "angry", "hate": "angry", "mad": "angry", "stupid": "angry", "annoying": "angry",
    
    # Specific topics
    "lol": "funny", "lmao": "funny", "haha": "funny", "joke": "funny", "funny": "funny", "meme": "funny",
    "food": "food", "eat": "food", "hungry": "food", "pizza": "food", "cook": "food",
    "game": "gaming", "play": "gaming", "gaming": "gaming", "win": "gaming", "minecraft": "gaming",
    "music": "music", "song": "music", "listen": "music", "spotify": "music",
    "code": "coding", "python": "coding", "programming": "coding", "debug": "coding", "error": "coding",
    "sleep": "sleep", "tired": "sleep", "night": "sleep", "bed": "sleep",
    "hi": "greeting", "hello": "greeting", "hey": "greeting", "morning": "greeting",
    "?": "question", "how": "question", "what": "question", "why": "question",
    "yes": "agreement", "agree": "agreement", "exactly": "agreement", "true": "agreement",
    "wow": "surprised", "omg": "surprised", "what": "surprised", "really": "surprised",
    
    # Darija keywords
    "salam": "greeting", "labas": "greeting", "shukran": "positive", "zwin": "love",
    "kanbghik": "love", "tbarkallah": "very_positive", "mezyan": "positive",
}


def analyze_message_sentiment(text: str) -> str:
    """Analyze message and return sentiment category."""
    text_lower = text.lower()
    
    # Check for keywords
    sentiments_found = []
    for keyword, sentiment in KEYWORD_SENTIMENT.items():
        if keyword in text_lower:
            sentiments_found.append(sentiment)
    
    if sentiments_found:
        # Return most specific sentiment
        priority = ["love", "very_positive", "funny", "gaming", "coding", "food", "music", 
                   "sleep", "surprised", "angry", "negative", "positive", "greeting", "question"]
        for p in priority:
            if p in sentiments_found:
                return p
    
    return "neutral"


def get_smart_reaction(text: str, author_name: str = None) -> str | None:
    """Get an intelligent emoji reaction based on message content."""
    sentiment = analyze_message_sentiment(text)
    
    if sentiment in SENTIMENT_EMOJIS:
        return random.choice(SENTIMENT_EMOJIS[sentiment])
    
    return None


def get_multi_reactions(text: str, max_reactions: int = 3) -> list[str]:
    """Get multiple relevant emoji reactions."""
    text_lower = text.lower()
    reactions = set()
    
    # Collect all matching sentiments
    for keyword, sentiment in KEYWORD_SENTIMENT.items():
        if keyword in text_lower and sentiment in SENTIMENT_EMOJIS:
            reactions.add(random.choice(SENTIMENT_EMOJIS[sentiment]))
            if len(reactions) >= max_reactions:
                break
    
    return list(reactions)[:max_reactions]


# Global learning engine instance
learning_engine = AikoLearningEngine()
