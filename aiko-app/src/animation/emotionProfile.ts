/** One semantic mood mapping shared by Aiko's expression and reply reaction. */
export interface EmotionProfile {
  expression: 'neutral' | 'happy' | 'shy' | 'sad' | 'pouty' | 'surprised' | 'sleepy';
  gesture?: 'greet' | 'handToFace' | 'nod' | 'surprisedJolt' | 'goodnight';
}

const PROFILES: Array<[RegExp, EmotionProfile]> = [
  [/\b(happy|joy|joyful|excited|playful|amused|delighted|cheerful)\b/, { expression: 'happy', gesture: 'greet' }],
  [/\b(shy|embarrass\w*|affection\w*|romantic|flirt\w*|warm)\b/, { expression: 'shy', gesture: 'handToFace' }],
  [/\b(sad|lonely|disappoint\w*|grief|hurt|down)\b/, { expression: 'sad' }],
  [/\b(angry|anger|frustrat\w*|annoy\w*|sarcastic|pout\w*)\b/, { expression: 'pouty' }],
  [/\b(surpris\w*|shock\w*|astonish\w*)\b/, { expression: 'surprised', gesture: 'surprisedJolt' }],
  [/\b(anxious|worried|scared|afraid|nervous)\b/, { expression: 'surprised' }],
  [/\b(sleep\w*|tired|bored)\b/, { expression: 'sleepy', gesture: 'goodnight' }],
  [/\b(curious|interest\w*|thoughtful|agree\w*|supportive|understand\w*)\b/, { expression: 'neutral', gesture: 'nod' }],
];

export function resolveEmotionProfile(emotion: string | null | undefined): EmotionProfile {
  const normalized = (emotion || '').toLowerCase().replace(/[_-]+/g, ' ');
  for (const [pattern, profile] of PROFILES) {
    if (pattern.test(normalized)) return profile;
  }
  return { expression: 'neutral' };
}

export function resolveReplyEmotion(text: string, explicitEmotion?: unknown): string {
  const match = text.match(/<emotion>\s*([^<]+?)\s*<\/emotion>|\[mood:\s*([^\]]+?)\s*\]/i);
  const taggedEmotion = (match?.[1] || match?.[2] || '').trim();
  if (taggedEmotion) return taggedEmotion.toLowerCase();
  return typeof explicitEmotion === 'string' && explicitEmotion.trim()
    ? explicitEmotion.trim().toLowerCase()
    : 'neutral';
}
