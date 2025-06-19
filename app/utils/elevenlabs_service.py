import requests
import os
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")


def generate_voice_mp3(text: str):
    print("🎙️ Генерация mp3 через ElevenLabs...")

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

        os.makedirs("/static", exist_ok=True)
        with open("/static/response.mp3", "wb") as f:
            f.write(response.content)

        print("✅ mp3 сохранён в static/response.mp3")

    except Exception as e:
        print("❌ Ошибка от ElevenLabs:", e)
