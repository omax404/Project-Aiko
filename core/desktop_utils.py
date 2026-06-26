"""
core/desktop_utils.py
─────────────────────
Helper to switch Windows thread desktop to WinSta0\Default.
Allows background execution run-times to access the user's interactive desktop.
"""

import sys
import contextlib
import logging

logger = logging.getLogger("DesktopUtils")

@contextlib.contextmanager
def use_interactive_desktop():
    """Context manager to temporarily switch the thread's desktop context to WinSta0\\Default.
    Only applicable on Windows. On other systems, it is a no-op.
    """
    if sys.platform != "win32":
        yield
        return

    import ctypes
    
    # Get current thread desktop handle
    thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
    h_current = ctypes.windll.user32.GetThreadDesktop(thread_id)
    
    # Open "Default" desktop with GENERIC_ALL access (0x10000000)
    GENERIC_ALL = 0x10000000
    h_default = ctypes.windll.user32.OpenDesktopW("Default", 0, False, GENERIC_ALL)
    
    if not h_default:
        # Fallback to no-op if we cannot open the desktop handle
        yield
        return
        
    switched = ctypes.windll.user32.SetThreadDesktop(h_default)
    try:
        yield
    finally:
        if switched:
            # Restore original desktop context
            ctypes.windll.user32.SetThreadDesktop(h_current)
        ctypes.windll.user32.CloseDesktop(h_default)

def launch_on_desktop(command_line, desktop="WinSta0\\Default"):
    """Launch a process on a specific desktop using CreateProcessW.
    Only applicable on Windows. On other systems, this falls back to subprocess.Popen.
    """
    if sys.platform != "win32":
        import subprocess
        return subprocess.Popen(command_line, shell=True).pid

    import ctypes
    from ctypes import wintypes
    import os

    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", ctypes.c_void_p),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE),
        ]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD),
        ]

    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(STARTUPINFOW)
    si.lpDesktop = desktop
    pi = PROCESS_INFORMATION()

    # CREATE_NEW_CONSOLE = 0x00000010
    dwCreationFlags = 0x00000010

    # Ensure path resolution works for simple names by launching via cmd start shim
    first_arg = command_line.split()[0] if command_line.split() else ""
    if not (command_line.startswith('"') or command_line.startswith("'") or os.path.exists(first_arg)):
        command_line = f'cmd.exe /c start "" {command_line}'

    success = ctypes.windll.kernel32.CreateProcessW(
        None,
        command_line,
        None,
        None,
        False,
        dwCreationFlags,
        None,
        None,
        ctypes.byref(si),
        ctypes.byref(pi)
    )

    if not success:
        err = ctypes.WinError(ctypes.get_last_error())
        logger.error(f"launch_on_desktop failed for '{command_line}': {err}")
        return None

    pid = pi.dwProcessId
    ctypes.windll.kernel32.CloseHandle(pi.hProcess)
    ctypes.windll.kernel32.CloseHandle(pi.hThread)
    return pid
