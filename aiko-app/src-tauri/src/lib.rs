// Aiko Desktop — Tauri Core v7 (window controls + proactive + TTS fix)
// ════════════════════════════════════════════════════════════
// Manages the entire Aiko ecosystem from Rust for 7x faster startup

mod process_manager;

use tauri::{Manager, Listener, WebviewUrl, WebviewWindowBuilder};
use serde_json;
use tauri::menu::{Menu, MenuItem};
use tauri::tray::TrayIconBuilder;
use tauri_plugin_global_shortcut::ShortcutState;
use std::path::PathBuf;
use std::sync::Arc;

use process_manager::ProcessManager;

/// Lazily creates or retrieves the transparent Mascot overlay window so that
/// startup does not contend on dual WebView2 controller initialization.
fn ensure_mascot_window(app: &tauri::AppHandle) -> Option<tauri::WebviewWindow> {
    if let Some(existing) = app.get_webview_window("mascot") {
        return Some(existing);
    }
    match WebviewWindowBuilder::new(app, "mascot", WebviewUrl::App("/?mascot".into()))
        .title("Aiko Mascot")
        .inner_size(300.0, 420.0)
        .resizable(false)
        .transparent(true)
        .decorations(false)
        .always_on_top(true)
        .skip_taskbar(true)
        .shadow(false)
        .visible(true)
        .build()
    {
        Ok(win) => Some(win),
        Err(e) => {
            eprintln!("[Aiko/Rust] Failed to build mascot window: {e}");
            None
        }
    }
}

// ── Tauri Commands ─────────────────────────────────────────────

#[tauri::command]
fn minimize_window(app: tauri::AppHandle) {
    if let Some(win) = app.get_webview_window("main") {
        let _ = win.minimize();
    }
}

#[tauri::command]
fn maximize_window(app: tauri::AppHandle) {
    if let Some(win) = app.get_webview_window("main") {
        if win.is_maximized().unwrap_or(false) {
            let _ = win.unmaximize();
        } else {
            let _ = win.maximize();
        }
    }
}

#[tauri::command]
fn close_window(app: tauri::AppHandle) {
    if let Some(win) = app.get_webview_window("main") {
        // Keep the native window object alive so the tray can restore it and
        // the Neural Hub does not become an invisible, unreachable process.
        let _ = win.hide();
    }
}

#[tauri::command]
fn switch_to_mascot(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(mascot) = ensure_mascot_window(&app) {
        let _ = mascot.show();
        let _ = mascot.set_focus();
        if let Some(main) = app.get_webview_window("main") {
            let _ = main.hide();
        }
        Ok(())
    } else {
        Err("Failed to create mascot window".to_string())
    }
}

#[tauri::command]
fn restore_from_mascot(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(main) = app.get_webview_window("main") {
        let _ = main.unminimize();
        let _ = main.show();
        let _ = main.set_focus();
    }
    if let Some(mascot) = app.get_webview_window("mascot") {
        let _ = mascot.hide();
    }
    Ok(())
}

#[tauri::command]
fn log_error(app: tauri::AppHandle, message: String, stack: String) {
    if let Ok(path) = app.path().app_log_dir() {
        std::fs::create_dir_all(&path).ok();
        let log_path = path.join("error.log");
        let content = format!("{}\n{}\n\n", message, stack);
        use std::io::Write;
        if let Ok(mut file) = std::fs::OpenOptions::new()
            .create(true).append(true).open(log_path) {
            file.write_all(content.as_bytes()).ok();
        }
    }
}

/// Called by frontend to check if the Neural Hub is alive
#[tauri::command]
async fn check_hub_status() -> Result<bool, String> {
    Ok(process_manager::check_hub_health("127.0.0.1", 8000).await)
}

/// Called by frontend to get startup progress
#[tauri::command]
async fn get_startup_status() -> Result<String, String> {
    if process_manager::check_hub_health("127.0.0.1", 8000).await {
        Ok("online".to_string())
    } else {
        Ok("starting".to_string())
    }
}

/// Get status of all managed processes
#[tauri::command]
async fn get_process_status(pm: tauri::State<'_, Arc<ProcessManager>>) -> Result<Vec<process_manager::ProcessStatusDto>, String> {
    Ok(pm.get_process_status())
}

// ── User Settings Commands ───────────────────────────────────────

#[tauri::command]
async fn get_user_settings() -> Result<String, String> {
    if let Some(root) = find_project_root() {
        let path = root.join("user_settings.json");
        if path.exists() {
            if let Ok(content) = std::fs::read_to_string(&path) {
                return Ok(content);
            }
        }
    }
    Ok("{}".to_string())
}

/// Read the desktop-only owner token through Tauri IPC. Browser clients receive
/// a limited token from /token and cannot ask the hub to disclose this secret.
#[tauri::command]
fn get_local_auth_token() -> Result<String, String> {
    let root = find_project_root().ok_or_else(|| "Aiko data directory was not found".to_string())?;
    std::fs::read_to_string(root.join("data").join("local_token.txt"))
        .map(|token| token.trim().to_string())
        .map_err(|e| format!("Could not read desktop token: {e}"))
}

#[tauri::command]
async fn save_user_settings(settings: String) -> Result<(), String> {
    if settings.len() > 100 * 1024 {
        return Err("Settings size exceeds 100KB limit".to_string());
    }

    let parsed: serde_json::Value = match serde_json::from_str(&settings) {
        Ok(v) => v,
        Err(e) => return Err(format!("Invalid JSON format: {}", e)),
    };

    if !parsed.is_object() {
        return Err("Settings must be a JSON object".to_string());
    }

    if let Some(root) = find_project_root() {
        let path = root.join("user_settings.json");
        if let Err(e) = std::fs::write(&path, settings) {
            return Err(format!("Failed to save settings: {}", e));
        }
        Ok(())
    } else {
        Err("Project root not found".to_string())
    }
}

// ── Resolve the Aiko project root ──────────────────────────────

fn find_project_root() -> Option<PathBuf> {
    if let Ok(cwd) = std::env::current_dir() {
        let mut dir = Some(cwd);
        for _ in 0..4 {
            if let Some(ref d) = dir {
                if d.join("core").join("neural_hub.py").exists() {
                    return Some(d.clone());
                }
                dir = d.parent().map(|p| p.to_path_buf());
            }
        }
    }

    if let Ok(exe) = std::env::current_exe() {
        let mut dir = exe.parent().map(|p| p.to_path_buf());
        for _ in 0..6 {
            if let Some(ref d) = dir {
                if d.join("core").join("neural_hub.py").exists() {
                    return Some(d.clone());
                }
                dir = d.parent().map(|p| p.to_path_buf());
            }
        }
    }

    None
}

// ── Main Entry Point ───────────────────────────────────────────

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_autostart::init(tauri_plugin_autostart::MacosLauncher::LaunchAgent, Some(vec!["--start-hidden"])))
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_deep_link::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            log_error, minimize_window, maximize_window, close_window,
            switch_to_mascot, restore_from_mascot,
            check_hub_status, get_startup_status, get_process_status,
            get_user_settings, save_user_settings, get_local_auth_token
        ])
        .setup(|app| {
            // ═════════════════════════════════════════════════════════════════
            //  RUST PROCESS MANAGER — Full ecosystem startup
            // ════════════════════════════════════════════════════════════════════
            if let Some(project_root) = find_project_root() {
                println!("[Aiko/Rust] Project root: {:?}", project_root);

                let pm = Arc::new(ProcessManager::new(project_root));
                app.manage(pm.clone());

                let pm_bg = pm.clone();
                std::thread::spawn(move || {
                    let rt = tokio::runtime::Runtime::new().unwrap();
                    rt.block_on(async {
                        let hub_already_alive = process_manager::check_hub_health("127.0.0.1", 8000).await;

                        if hub_already_alive {
                            println!("[Aiko/Rust] Neural Hub already online — skipping process startup");
                            println!("[Aiko/Rust] ALL SYSTEMS GO (external launcher mode)");
                        } else {
                            println!("[Aiko/Rust] Cleaning stale processes...");
                            pm_bg.cleanup_stale_processes();

                            println!("[Aiko/Rust] Starting Ollama...");
                            pm_bg.start_ollama();

                            println!("[Aiko/Rust] Starting Neural Hub...");
                            match pm_bg.start_hub() {
                                Ok(_) => println!("[Aiko/Rust] Neural Hub spawned"),
                                Err(e) => eprintln!("[Aiko/Rust] Hub error: {}", e),
                            }

                            println!("[Aiko/Rust] Waiting for Neural Hub health...");
                            let ready = process_manager::wait_for_hub("127.0.0.1", 8000, 150).await;
                            if ready {
                                println!("[Aiko/Rust] Neural Hub ONLINE — starting satellites");
                                tokio::time::sleep(std::time::Duration::from_millis(500)).await;
                                pm_bg.start_bots();
                                println!("[Aiko/Rust] ALL SYSTEMS GO");

                                let pm_monitor = pm_bg.clone();
                                tokio::spawn(async move {
                                    pm_monitor.start_monitoring().await;
                                });
                            } else {
                                eprintln!("[Aiko/Rust] CRITICAL: Hub failed to start after 30s");
                            }
                        }
                    });
                });
            } else {
                eprintln!("[Aiko/Rust] WARNING: Could not find project root!");
            }

            // ════════════════════════════════════════════════════════════════════════
            //  TRAY + SHORTCUTS + VISUAL EFFECTS
            // ═══════════════════════════════════════════════════════════════════════════════════
            let show_i = MenuItem::with_id(app, "show", "Show Aiko Dashboard", true, None::<&str>)?;
            let mascot_i = MenuItem::with_id(app, "mascot", "Switch to Mascot Mode", true, None::<&str>)?;
            let quit_i = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_i, &mascot_i, &quit_i])?;

            let _tray = TrayIconBuilder::new()
                .icon(tauri::image::Image::from_bytes(include_bytes!("../icons/tray-icon.png")).unwrap())
                .icon_as_template(true)
                .menu(&menu)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => {
                        if let Some(win) = app.get_webview_window("main") {
                            let _ = win.unminimize();
                            let _ = win.show();
                            let _ = win.set_focus();
                        }
                    }
                    "mascot" => {
                        if let Some(mascot) = ensure_mascot_window(app) {
                            let _ = mascot.show();
                            let _ = mascot.set_focus();
                            if let Some(main) = app.get_webview_window("main") {
                                let _ = main.hide();
                            }
                        }
                    }
                    "quit" => {
                        if let Some(pm) = app.try_state::<Arc<ProcessManager>>() {
                            println!("[Aiko/Rust] Tray Quit triggered. Shutting down all processes...");
                            pm.shutdown();
                        }
                        app.exit(0);
                    }
                    _ => {}
                })
                .build(app)?;

            // Global Shortcut: Ctrl+Alt+A to toggle visibility
            let shortcut_builder = tauri_plugin_global_shortcut::Builder::new()
                .with_shortcut("ctrl+alt+a");
            match shortcut_builder {
                Ok(builder) => {
                    let plugin = builder
                        .with_handler(|app, _shortcut, event| {
                            if event.state == ShortcutState::Pressed {
                                if let Some(win) = app.get_webview_window("main") {
                                    if win.is_visible().unwrap_or(false) {
                                        let _ = win.hide();
                                    } else {
                                        let _ = win.unminimize();
                                        let _ = win.show();
                                        let _ = win.set_focus();
                                    }
                                }
                            }
                        })
                        .build();
                    if let Err(error) = app.handle().plugin(plugin) {
                        eprintln!("[Aiko/Rust] Global shortcut unavailable: {error}");
                    }
                }
                Err(error) => eprintln!("[Aiko/Rust] Global shortcut configuration failed: {error}"),
            }

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let tauri::RunEvent::Ready = event {
                if let Some(window) = app_handle.get_webview_window("main") {
                    let _ = window.unminimize();
                    let _ = window.show();
                    let _ = window.set_focus();

                    let win_clone = window.clone();
                    app_handle.listen("app-ready", move |_| {
                        let _ = win_clone.unminimize();
                        let _ = win_clone.show();
                        let _ = win_clone.set_focus();
                    });

                    // Non-blocking delayed focus check on a background thread that dispatches
                    // back onto the Win32 main thread without stalling the message pump.
                    let handle_for_retry = app_handle.clone();
                    std::thread::spawn(move || {
                        for delay_ms in [150u64, 450, 900] {
                            std::thread::sleep(std::time::Duration::from_millis(delay_ms));
                            let h = handle_for_retry.clone();
                            let _ = handle_for_retry.run_on_main_thread(move || {
                                if let Some(win) = h.get_webview_window("main") {
                                    let _ = win.unminimize();
                                    let _ = win.show();
                                }
                            });
                        }
                    });
                } else {
                    eprintln!("[Aiko/Rust] RunEvent::Ready — main window missing");
                }
            } else if let tauri::RunEvent::Exit = event {
                if let Some(pm) = app_handle.try_state::<Arc<ProcessManager>>() {
                    println!("[Aiko/Rust] RunEvent::Exit triggered. Shutting down all processes...");
                    pm.shutdown();
                }
            } else if let tauri::RunEvent::ExitRequested { api, .. } = event {
                api.prevent_exit();
            }
        });
}
