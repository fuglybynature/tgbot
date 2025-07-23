import json
import os

STORE_FILE = "latest_videos.json"

def load_video_store():
    if not os.path.exists(STORE_FILE):
        return {}
    try:
        with open(STORE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_video_store(data):
    try:
        with open(STORE_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving store: {e}")
