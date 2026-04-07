# Preferred Tech Stack & Implementation Rules

When generating code or UI components for this brand, you **MUST** strictly adhere to the following technology choices.

## Core Stack
* **Framework:** Python + Flet (Flutter based).
*   **Target:** Desktop Application (Windows).
*   **Styling Engine:** Flet Properties (Vanilla Python).
*   **Architecture:** Asyncio, Event Loop, Component Classes.

## Implementation Guidelines

### 1. Styling
*   Use the `  ` dict defined in `ui/components.py` (which mirrors `design-tokens.json`).
*   **Theme:** Dark Mode Only ("Obsidian Glass").
*   **Typography:** "Silkscreen" for all text elements.

### 2. Component Patterns
*   **Classes:** Extend `ft.Container` for complex UI elements.
*   **State:** Use `await page.update()` or specific control updates. Do not block the main thread.
*   **Assets:** Icons use `ft.Icons`. Images use `ft.Image`.

### 3. Forbidden Patterns
*   Do NOT use React, Tailwind, or Web Logic (unless explicitly creating a web dashboard separately).
*   Do NOT use blocking `time.sleep()` in main thread (use `asyncio.sleep`).
