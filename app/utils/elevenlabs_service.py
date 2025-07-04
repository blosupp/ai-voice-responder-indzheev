import requests
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

def generate_voice_mp3(text: str):
    print("🎙️ Генерация mp3 через ElevenLabs...")
    print("📌 VOICE_ID:", VOICE_ID)

    if not VOICE_ID or not ELEVENLABS_API_KEY:
        print("❌ Проверь .env: VOICE_ID или API_KEY пустой")
        return

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        static_path = Path(__file__).parent.parent / "static"
        static_path.mkdir(parents=True, exist_ok=True)

        output_path = static_path / "response.mp3"
        with open(output_path, "wb") as f:
            f.write(response.content)

        print("✅ Файл сохранён:", output_path)

    except Exception as e:
        print("❌ Ошибка от ElevenLabs:", e)
