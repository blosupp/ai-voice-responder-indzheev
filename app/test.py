from utils.elevenlabs_service import generate_voice_mp3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def main():
    text = "Привет! Это тест голосом Indzheev через ElevenLabs."
    generate_voice_mp3(text)

    response_path = Path(__file__).parent / "static" / "response.mp3"
    print("📍 Ожидаем файл:", response_path)

    if response_path.exists():
        print("✅ УСПЕХ: mp3 создан!")
    else:
        print("❌ НЕ УСПЕХ: Файл не появился.")

if __name__ == "__main__":
    main()
