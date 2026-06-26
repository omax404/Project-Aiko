import pyautogui
import os
import time

def capture():
    # Ensure assets dir exists for temp captures
    temp_dir = os.path.join(os.getcwd(), ".tmp", "vision_captures")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        screenshot = pyautogui.screenshot()
    except OSError as e:
        if "screen grab failed" in str(e).lower():
            return "ERROR: Screen capture offline (session locked or display sleep)"
        raise
        
    timestamp = int(time.time())
    file_path = os.path.join(temp_dir, f"screen_{timestamp}.jpg")
    screenshot.save(file_path, "JPEG")
    return file_path

if __name__ == "__main__":
    print(capture())
