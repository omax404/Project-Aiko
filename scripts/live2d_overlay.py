
import webview
import os
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "assets", "live2d", "index.html")

def start_overlay():
    # Create a transparent, frameless, always-on-top window
    window = webview.create_window(
        'Aiko Live2D',
        url=f'file:///{HTML_PATH}',
        width=400,
        height=400,
        transparent=True,
        frameless=True,
        on_top=True,
        background_color='#00000000' # Fully transparent
    )
    
    # Position on bottom right (approximate, pywebview positioning is basic)
    # Most Live2D models handle their own transparency in CSS, 
    # but we need the window itself to be transparent.
    
    webview.start()

if __name__ == "__main__":
    start_overlay()
