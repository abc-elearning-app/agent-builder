import json
import requests
import os

# Apps Script URL for Flashcard Generator
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwMkGi_5S0OBH5esmLyRAbx9BBEv-OMLWRcTS1IHTi682AF5xMNtZOLxVv_Whamh3RZMw/exec"

def upload_flashcards(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: File {file_path} not found.")
        return

    print(f"📂 Reading flashcards from {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📤 Uploading {len(data['flashcards'])} flashcards for '{data['appName']}'...")
    try:
        response = requests.post(APPS_SCRIPT_URL, json=data, timeout=120)
        print(f"📡 Response Code: {response.status_code}")
        print(f"📄 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Flashcards have been inserted into Google Sheet.")
        else:
            print(f"❌ FAILED: Status code {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR during upload: {str(e)}")

if __name__ == "__main__":
    upload_flashcards("clf-c02-comprehensive-flashcards.json")
