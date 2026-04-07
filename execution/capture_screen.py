import cv2
import pyautogui
import numpy as np
import os
import time

def capture():
    # Ensure assets dir exists for temp captures
    temp_dir = os.path.join(os.getcwd(), ".tmp", "vision_captures")
    os.makedirs(temp_dir, exist_ok=True)
    
    screenshot = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    timestamp = int(time.time())
    file_path = os.path.join(temp_dir, f"screen_{timestamp}.jpg")
    cv2.imwrite(file_path, frame)
    return file_path

if __name__ == "__main__":
    print(capture())
