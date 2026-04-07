# SOP: Screen Analysis

## Goal
Periodically observe the user's screen to provide context-aware support and reactive emotions.

## Inputs
- `timestamp`: Current time.
- `active_window`: Title of the focused application.

## Process
1. Run `execution/capture_screen.py`.
2. Analyze the resulting image using the Vision Engine.
3. Classify the user activity (Gaming, Coding, Browsing, Working).
4. Update Aiko's emotion state based on the activity.
5. If something highly relevant is found (error, achievement, interesting content), generate a proactive message.

## Outputs
- `activity_type`: String (e.g., "coding").
- `description`: LLM-generated description of the screen.
- `suggested_emotion`: Mapping based on keywords.
