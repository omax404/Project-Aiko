# SOP: Language Learning & Cultural Practice

## Goal
Improve Aiko's fluency in Darija (Moroccan Arabic) and culturally connect with Master omax.

## Inputs
- `vocabulary`: `knowledge/darija.json`
- `last_learned`: `knowledge/learned_words.json`

## Process
1. Load a random word or expression from `darija.json`.
2. check if it's already "learned" recently to avoid repetition.
3. Use the Brain to generate a short, cute sentence or scenario using that word.
4. Surprise Master by speaking it in chat or including it in autonomous reflections.
5. Log the interaction to `learned_words.json`.

## Outputs
- `word`: The Darija word targeted.
- `usage_example`: The sentence generated.
- `reaction`: Master's response (if available).
