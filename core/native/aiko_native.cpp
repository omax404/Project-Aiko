/*
 * Aiko Native Helper v2.0 — Deep Win32 Integration
 * ──────────────────────────────────────────────────
 * Events emitted as JSON lines to stdout (Python reads via pipe):
 *
 *   {"event":"stats",      "cpu":..., "ram_used":..., "ram_total":...,
 *                          "ram_percent":..., "gpu":..., "gpu_vram":...,
 * "gpu_ok":...}
 *   {"event":"hotkey",     "action":"wake"|"mute"|"screenshot"|"emoji"}
 *   {"event":"window",     "title":"...", "exe":"...", "hwnd":...}
 *   {"event":"clipboard",  "text":"...", "len":...}
 *   {"event":"process",    "action":"start"|"stop", "name":"...", "pid":...}
 *   {"event":"touchpad",   "gesture":"tap"|"swipe"|"pinch"|"hold",
 *                          "dx":..., "dy":..., "fingers":..., "scale":...}
 *   {"event":"mouse",      "action":"lclick"|"rclick"|"dblclick"|"wheel",
 *                          "x":..., "y":..., "delta":...}
 *   {"event":"idle",       "idle_ms":...}
 *
 * Build (MinGW):
 *   g++ -std=c++17 -O2 -o aiko_native.exe aiko_native.cpp -lpdh -lwtsapi32
 */

#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0601 // Windows 7+
#include <atomic>
#include <math.h>
#include <mutex>
#include <pdh.h>
#include <psapi.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <string>
#include <thread>
#include <tlhelp32.h> // Process snapshots
#include <unordered_map>
#include <vector>
#include <windows.h> // MUST be first
#include <wtsapi32.h>

// HID usage page/usage constants (mingw may not ship hidusage.h)
#ifndef HID_USAGE_PAGE_GENERIC
#define HID_USAGE_PAGE_GENERIC ((USHORT)0x01)
#endif
#ifndef HID_USAGE_GENERIC_MOUSE
#define HID_USAGE_GENERIC_MOUSE ((USHORT)0x02)
#endif
#define HID_USAGE_PAGE_DIGITIZER ((USHORT)0x0D)
#define HID_USAGE_DIGITIZER_TOUCH ((USHORT)0x05)

#pragma comment(lib, "pdh.lib")
#pragma comment(lib, "wtsapi32.lib")

// ── Globals ──────────────────────────────────────────────────────
std::atomic<bool> g_running(true);
std::mutex g_print_mutex;

// Thread-safe JSON emit
static void emit(const char *json) {
  std::lock_guard<std::mutex> lk(g_print_mutex);
  puts(json);
  fflush(stdout);
}
static void emitf(const char *fmt, ...) {
  char buf[2048];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(buf, sizeof(buf), fmt, ap);
  va_end(ap);
  emit(buf);
}

// Escape a string for JSON (handles quotes, backslashes, control chars)
static std::string json_escape(const char *s) {
  std::string out;
  out.reserve(strlen(s) + 8);
  for (const char *p = s; *p; ++p) {
    switch (*p) {
    case '"':
      out += "\\\"";
      break;
    case '\\':
      out += "\\\\";
      break;
    case '\n':
      out += "\\n";
      break;
    case '\r':
      out += "\\r";
      break;
    case '\t':
      out += "\\t";
      break;
    default:
      if ((unsigned char)*p < 0x20) {
        char esc[8];
        snprintf(esc, 8, "\\u%04x", (unsigned char)*p);
        out += esc;
      } else
        out += *p;
    }
  }
  return out;
}

// ══════════════════════════════════════════════════════════════════
//  1. SYSTEM STATS  (CPU/RAM/GPU)
// ══════════════════════════════════════════════════════════════════
static PDH_HQUERY g_cpuQuery = NULL;
static PDH_HCOUNTER g_cpuCounter = NULL;

bool init_cpu_query() {
  if (PdhOpenQuery(NULL, 0, &g_cpuQuery) != ERROR_SUCCESS)
    return false;
  return PdhAddEnglishCounterA(g_cpuQuery,
                               "\\Processor(_Total)\\% Processor Time", 0,
                               &g_cpuCounter) == ERROR_SUCCESS;
}
double get_cpu_percent() {
  if (!g_cpuQuery)
    return 0.0;
  PdhCollectQueryData(g_cpuQuery);
  PDH_FMT_COUNTERVALUE val;
  return (PdhGetFormattedCounterValue(g_cpuCounter, PDH_FMT_DOUBLE, NULL,
                                      &val) == ERROR_SUCCESS)
             ? val.doubleValue
             : 0.0;
}
struct RamStats {
  double used_gb, total_gb, percent;
};
RamStats get_ram() {
  MEMORYSTATUSEX ms;
  ms.dwLength = sizeof(ms);
  GlobalMemoryStatusEx(&ms);
  double tot = (double)ms.ullTotalPhys / (1 << 30);
  double used = tot - (double)ms.ullAvailPhys / (1 << 30);
  return {used, tot, (used / tot) * 100.0};
}
struct GpuStats {
  double load, vram_gb;
  bool ok;
};
GpuStats get_gpu() {
  FILE *p = _popen("nvidia-smi --query-gpu=utilization.gpu,memory.used "
                   "--format=csv,noheader,nounits 2>NUL",
                   "r");
  if (!p)
    return {0, 0, false};
  char buf[128] = {};
  double l = 0, v = 0;
  bool ok = fgets(buf, sizeof(buf), p) && sscanf(buf, "%lf, %lf", &l, &v) == 2;
  _pclose(p);
  return {l, v / 1024.0, ok};
}

void stats_thread_fn() {
  bool cpu_ok = init_cpu_query();
  if (cpu_ok) {
    PdhCollectQueryData(g_cpuQuery);
    Sleep(300);
  }
  int gpu_tick = 0;
  GpuStats gpu = {0, 0, false};
  while (g_running) {
    double cpu = cpu_ok ? get_cpu_percent() : 0.0;
    RamStats ram = get_ram();
    if (gpu_tick == 0)
      gpu = get_gpu();
    gpu_tick = (gpu_tick + 1) % 8; // GPU every 4s
    emitf("{\"event\":\"stats\","
          "\"cpu\":%.1f,"
          "\"ram_used\":%.2f,\"ram_total\":%.2f,\"ram_percent\":%.1f,"
          "\"gpu\":%.1f,\"gpu_vram\":%.2f,\"gpu_ok\":%s}",
          cpu, ram.used_gb, ram.total_gb, ram.percent, gpu.load, gpu.vram_gb,
          gpu.ok ? "true" : "false");
    Sleep(500);
  }
}

// ══════════════════════════════════════════════════════════════════
//  2. HOTKEYS  (CTRL+SPACE, CTRL+M, CTRL+SHIFT+S, CTRL+SHIFT+E)
// ══════════════════════════════════════════════════════════════════
#define HK_WAKE 1
#define HK_MUTE 2
#define HK_SCREENSHOT 3
#define HK_EMOJI 4

void hotkey_thread_fn() {
  RegisterHotKey(NULL, HK_WAKE, MOD_CONTROL | MOD_NOREPEAT, VK_SPACE);
  RegisterHotKey(NULL, HK_MUTE, MOD_CONTROL | MOD_NOREPEAT, 'M');
  RegisterHotKey(NULL, HK_SCREENSHOT, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT,
                 'S');
  RegisterHotKey(NULL, HK_EMOJI, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, 'E');
  MSG msg;
  while (g_running) {
    if (PeekMessage(&msg, NULL, WM_HOTKEY, WM_HOTKEY, PM_REMOVE) &&
        msg.message == WM_HOTKEY) {
      const char *action = msg.wParam == HK_WAKE         ? "wake"
                           : msg.wParam == HK_MUTE       ? "mute"
                           : msg.wParam == HK_SCREENSHOT ? "screenshot"
                                                         : "emoji";
      emitf("{\"event\":\"hotkey\",\"action\":\"%s\"}", action);
    }
    Sleep(10);
  }
  for (int i = 1; i <= 4; i++)
    UnregisterHotKey(NULL, i);
}

// ══════════════════════════════════════════════════════════════════
//  3. FOREGROUND WINDOW TRACKER
//     Fires when the user switches to a different application.
// ══════════════════════════════════════════════════════════════════
static std::string g_last_win_title;

static std::string get_exe_name(DWORD pid) {
  char buf[MAX_PATH] = {};
  HANDLE h = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
  if (h) {
    GetModuleFileNameExA(h, NULL, buf, MAX_PATH);
    CloseHandle(h);
  }
  // basename
  const char *last = strrchr(buf, '\\');
  return last ? (last + 1) : buf;
}

void window_watcher_thread_fn() {
  while (g_running) {
    HWND hw = GetForegroundWindow();
    if (hw) {
      char title[512] = {};
      GetWindowTextA(hw, title, sizeof(title));
      std::string ttl(title);
      if (ttl != g_last_win_title) {
        g_last_win_title = ttl;
        DWORD pid = 0;
        GetWindowThreadProcessId(hw, &pid);
        std::string exe = get_exe_name(pid);
        emitf("{\"event\":\"window\","
              "\"title\":\"%s\",\"exe\":\"%s\",\"hwnd\":%lu}",
              json_escape(title).c_str(), json_escape(exe.c_str()).c_str(),
              (ULONG_PTR)hw);
      }
    }
    Sleep(400);
  }
}

// ══════════════════════════════════════════════════════════════════
//  4. CLIPBOARD MONITOR
//     Detects text copies globally.
// ══════════════════════════════════════════════════════════════════
HWND g_clip_hwnd = NULL;

LRESULT CALLBACK clip_wnd_proc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
  if (msg == WM_CLIPBOARDUPDATE) {
    if (IsClipboardFormatAvailable(CF_UNICODETEXT) && OpenClipboard(hwnd)) {
      HANDLE hd = GetClipboardData(CF_UNICODETEXT);
      if (hd) {
        wchar_t *wp2 = (wchar_t *)GlobalLock(hd);
        if (wp2) {
          // Convert to UTF-8
          char utf8[1024] = {};
          WideCharToMultiByte(CP_UTF8, 0, wp2, -1, utf8, sizeof(utf8) - 1, NULL,
                              NULL);
          GlobalUnlock(hd);
          emitf("{\"event\":\"clipboard\",\"text\":\"%s\",\"len\":%d}",
                json_escape(utf8).c_str(), (int)wcslen(wp2));
        }
      }
      CloseClipboard();
    }
  }
  return DefWindowProcA(hwnd, msg, wp, lp);
}

void clipboard_thread_fn() {
  // Create a hidden message-only window for clipboard listener
  WNDCLASSA wc = {};
  wc.lpfnWndProc = clip_wnd_proc;
  wc.hInstance = GetModuleHandle(NULL);
  wc.lpszClassName = "AikoClipWnd";
  RegisterClassA(&wc);
  g_clip_hwnd = CreateWindowExA(0, "AikoClipWnd", "", 0, 0, 0, 0, 0,
                                HWND_MESSAGE, NULL, NULL, NULL);
  if (!g_clip_hwnd)
    return;
  AddClipboardFormatListener(g_clip_hwnd);
  MSG msg;
  while (g_running && GetMessage(&msg, g_clip_hwnd, 0, 0) > 0) {
    TranslateMessage(&msg);
    DispatchMessage(&msg);
  }
  RemoveClipboardFormatListener(g_clip_hwnd);
  DestroyWindow(g_clip_hwnd);
}

// ══════════════════════════════════════════════════════════════════
//  5. PROCESS WATCHER
//     Detects new/exited processes (games, apps, etc.)
//     Uses snapshot diffing every 2s — lightweight.
// ══════════════════════════════════════════════════════════════════
static std::unordered_map<DWORD, std::string> g_procs;

static std::unordered_map<DWORD, std::string> snapshot_procs() {
  std::unordered_map<DWORD, std::string> out;
  HANDLE h = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
  if (h == INVALID_HANDLE_VALUE)
    return out;
  PROCESSENTRY32 pe;
  pe.dwSize = sizeof(pe);
  if (Process32First(h, &pe)) {
    do {
      out[pe.th32ProcessID] = pe.szExeFile;
    } while (Process32Next(h, &pe));
  }
  CloseHandle(h);
  return out;
}

void process_watcher_thread_fn() {
  g_procs = snapshot_procs();
  while (g_running) {
    Sleep(2000);
    auto now = snapshot_procs();
    // Started
    for (auto &[pid, name] : now) {
      if (g_procs.find(pid) == g_procs.end())
        emitf("{\"event\":\"process\",\"action\":\"start\","
              "\"name\":\"%s\",\"pid\":%lu}",
              json_escape(name.c_str()).c_str(), (unsigned long)pid);
    }
    // Stopped
    for (auto &[pid, name] : g_procs) {
      if (now.find(pid) == now.end())
        emitf("{\"event\":\"process\",\"action\":\"stop\","
              "\"name\":\"%s\",\"pid\":%lu}",
              json_escape(name.c_str()).c_str(), (unsigned long)pid);
    }
    g_procs = std::move(now);
  }
}

// ══════════════════════════════════════════════════════════════════
//  6. RAW INPUT — Precision Touchpad + Mouse
//     Uses RegisterRawInputDevices on a hidden window.
//     Touchpads expose themselves as HID Usage 0x0D (Digitizer),
//     Usage 0x04 (Touchpad). We read contact counts + X/Y deltas.
// ══════════════════════════════════════════════════════════════════
HWND g_raw_hwnd = NULL;

// Gesture state
struct TouchState {
  int fingers = 0;
  LONG dx = 0, dy = 0;
  bool pinching = false;
  float pinch_scale = 1.0f;
  DWORD last_tap = 0;
};
static TouchState g_touch;

// Simple gesture classification from raw mouse deltas (fallback when
// full HID digitizer data isn't parseable without a full HID descriptor)
static void classify_mouse_gesture(LONG dx, LONG dy) {
  // We trust this only when called from WM_INPUT with touchpad source
  float mag = sqrtf((float)(dx * dx + dy * dy));
  if (mag < 3)
    return;
  const char *dir = (abs(dx) > abs(dy)) ? (dx > 0 ? "right" : "left")
                                        : (dy > 0 ? "down" : "up");
  (void)dir; // used in full HID path
  emitf("{\"event\":\"touchpad\",\"gesture\":\"swipe\","
        "\"dx\":%ld,\"dy\":%ld,\"fingers\":2,\"scale\":1.0}",
        dx, dy);
}

LRESULT CALLBACK raw_wnd_proc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
  if (msg == WM_INPUT) {
    UINT sz = 0;
    GetRawInputData((HRAWINPUT)lp, RID_INPUT, NULL, &sz,
                    sizeof(RAWINPUTHEADER));
    if (sz == 0)
      return 0;
    static std::vector<BYTE> buf;
    buf.resize(sz);
    if (GetRawInputData((HRAWINPUT)lp, RID_INPUT, buf.data(), &sz,
                        sizeof(RAWINPUTHEADER)) != sz)
      return 0;

    RAWINPUT *raw = (RAWINPUT *)buf.data();
    if (raw->header.dwType == RIM_TYPEMOUSE) {
      // Standard mouse events
      RAWMOUSE &m = raw->data.mouse;
      if (m.usButtonFlags & RI_MOUSE_LEFT_BUTTON_DOWN)
        emitf("{\"event\":\"mouse\",\"action\":\"lclick\","
              "\"x\":%ld,\"y\":%ld,\"delta\":0}",
              m.lLastX, m.lLastY);
      if (m.usButtonFlags & RI_MOUSE_RIGHT_BUTTON_DOWN)
        emitf("{\"event\":\"mouse\",\"action\":\"rclick\","
              "\"x\":%ld,\"y\":%ld,\"delta\":0}",
              m.lLastX, m.lLastY);
      if (m.usButtonFlags & RI_MOUSE_WHEEL) {
        short delta = (short)m.usButtonData;
        emitf("{\"event\":\"mouse\",\"action\":\"wheel\","
              "\"x\":%ld,\"y\":%ld,\"delta\":%d}",
              m.lLastX, m.lLastY, (int)delta);
      }
      // Two-finger swipe heuristic: MOUSE_MOVE_RELATIVE with no buttons
      if (!(m.usButtonFlags) && (m.usFlags & MOUSE_MOVE_RELATIVE) &&
          (abs(m.lLastX) > 5 || abs(m.lLastY) > 5)) {
        classify_mouse_gesture(m.lLastX, m.lLastY);
      }
    } else if (raw->header.dwType == RIM_TYPEHID) {
      // Precision touchpad HID — finger count in bRawData[0]
      // (valid for standard Windows Precision Touchpad descriptor)
      RAWHID &hid = raw->data.hid;
      if (hid.dwSizeHid >= 1) {
        int fingers = (int)(hid.bRawData[0] & 0x0F);
        if (fingers != g_touch.fingers) {
          g_touch.fingers = fingers;
          if (fingers == 0) {
            // finger lift — tap if short duration
            DWORD now = GetTickCount();
            if (now - g_touch.last_tap < 200)
              emitf("{\"event\":\"touchpad\",\"gesture\":\"tap\","
                    "\"dx\":0,\"dy\":0,\"fingers\":1,\"scale\":1.0}");
            g_touch.last_tap = now;
          }
        }
      }
    }
    return 0;
  }
  return DefWindowProcA(hwnd, msg, wp, lp);
}

void rawinput_thread_fn() {
  WNDCLASSA wc = {};
  wc.lpfnWndProc = raw_wnd_proc;
  wc.hInstance = GetModuleHandle(NULL);
  wc.lpszClassName = "AikoRawInputWnd";
  if (!RegisterClassA(&wc))
    return;
  g_raw_hwnd = CreateWindowExA(0, "AikoRawInputWnd", "", 0, 0, 0, 0, 0,
                               HWND_MESSAGE, NULL, NULL, NULL);
  if (!g_raw_hwnd)
    return;

  // Register mouse
  RAWINPUTDEVICE rid[2];
  rid[0].usUsagePage = HID_USAGE_PAGE_GENERIC;
  rid[0].usUsage = HID_USAGE_GENERIC_MOUSE;
  rid[0].dwFlags = RIDEV_INPUTSINK;
  rid[0].hwndTarget = g_raw_hwnd;
  // Register touchpad (HID digitizer, touchpad usage 0x05)
  rid[1].usUsagePage = 0x0D; // HID_USAGE_PAGE_DIGITIZER
  rid[1].usUsage = 0x05;     // Touchpad
  rid[1].dwFlags = RIDEV_INPUTSINK;
  rid[1].hwndTarget = g_raw_hwnd;

  RegisterRawInputDevices(rid, 2, sizeof(RAWINPUTDEVICE));

  MSG msg;
  while (g_running && GetMessage(&msg, NULL, 0, 0) > 0) {
    TranslateMessage(&msg);
    DispatchMessage(&msg);
  }
  DestroyWindow(g_raw_hwnd);
}

// ══════════════════════════════════════════════════════════════════
//  7. IDLE DETECTOR
//     Reports user idle time every 5s (for auto-greeter, screensaver, etc.)
// ══════════════════════════════════════════════════════════════════
void idle_thread_fn() {
  DWORD last_reported = 0;
  while (g_running) {
    LASTINPUTINFO li;
    li.cbSize = sizeof(li);
    GetLastInputInfo(&li);
    DWORD idle_ms = GetTickCount() - li.dwTime;
    // Report every 5s if idle > 30s (avoid spamming when active)
    if (idle_ms > 30000 && (idle_ms / 5000) != (last_reported / 5000)) {
      last_reported = idle_ms;
      emitf("{\"event\":\"idle\",\"idle_ms\":%lu}", (unsigned long)idle_ms);
    }
    Sleep(5000);
  }
}

// ══════════════════════════════════════════════════════════════════
//  MAIN — spin all threads
// ══════════════════════════════════════════════════════════════════
int main() {
  setvbuf(stdout, NULL, _IOLBF, 2048);

  // Emit hello
  emit("{\"event\":\"ready\",\"version\":\"2.0\"}");

  std::thread t_stats(stats_thread_fn);
  std::thread t_hotkeys(hotkey_thread_fn);
  std::thread t_window(window_watcher_thread_fn);
  std::thread t_clip(clipboard_thread_fn);
  std::thread t_procs(process_watcher_thread_fn);
  std::thread t_raw(rawinput_thread_fn);
  std::thread t_idle(idle_thread_fn);

  t_stats.detach();
  t_hotkeys.detach();
  t_window.detach();
  t_clip.detach();
  t_procs.detach();
  t_raw.detach();
  t_idle.detach();

  // Block main thread — wait for stdin close (Python terminating)
  while (g_running) {
    if (feof(stdin))
      g_running = false;
    Sleep(200);
  }
  return 0;
}
