# Aiko Desktop - Mobile & Cross-Platform Support

Aiko Desktop is built using Tauri v2, meaning it natively supports **Windows, macOS, Linux, Android, and iOS**.

## Linux & macOS
The `tauri.conf.json` is already configured with `"targets": "all"`.
- If you run `npm run tauri build` on a Mac, it will produce `.dmg` and `.app` bundles.
- If you run it on Linux, it will produce `.deb` and `.AppImage` files.

## Android Support

To compile Aiko for Android:

### 1. Requirements
You must have the following installed on your machine:
- **Android Studio**
- **Android SDK** and **NDK**
- **Java Development Kit (JDK)**

### 2. Initialization
Run the Tauri mobile initialization command:
```bash
npm run tauri android init
```
This will generate the `src-tauri/gen/android` folder.

### 3. Development
To run Aiko on a connected Android device or emulator:
```bash
npm run tauri android dev
```

### 4. Build
To compile the `.apk` and `.aab` (Android App Bundle):
```bash
npm run tauri android build
```

> **Note:** The Live2D model rendering (pixi.js) and React chat interface are fully responsive and will automatically adapt to mobile screen sizes (handled in `MobileApp.tsx`).
