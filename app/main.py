from flask import Flask, request, Response, send_file
from twilio.twiml.voice_response import VoiceResponse
import requests
import tempfile
import os
from dotenv import load_dotenv
from pathlib import Path

# Импорт собственных модулей
from app.utils.whisper_service import transcribe_audio
from utils.gpt_service import load_profile, generate_reply
from utils.elevenlabs_service import generate_voice_mp3


# Загрузка переменных окружения
load_dotenv()
NGROK_URL = os.getenv("NGROK_URL")

app = Flask(__name__)

@app.route("/voice-test", methods=["POST"])
def voice():
    print("📞 Входящий звонок получен")
    print(request.form)

    response = VoiceResponse()

    # 🟡 Слушаем сразу
    response.record(
        max_length=10,
        action=f"{NGROK_URL}/process-recording",
        method="POST",
        play_beep=True,
        trim="trim-silence"
    )

    return Response(str(response), mimetype="application/xml")

@app.route("/process-recording", methods=["POST"])
def process_recording():
    print("🎧 Обработка голосового сообщения...")
    recording_url = request.form.get("RecordingUrl")

    if not recording_url:
        return "❌ Нет записи", 400

    try:
        # 1. Скачиваем аудио напрямую и сохраняем
        audio_url = f"{recording_url}.mp3"
        print("📥 Скачиваем:", audio_url)
        audio_data = requests.get(audio_url).content

        tmp_audio_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        with open(tmp_audio_path, "wb") as f:
            f.write(audio_data)
        print("📁 mp3 сохранён во временный файл:", tmp_audio_path)

        # 2. Распознаём
        user_text = transcribe_audio(tmp_audio_path)
        print("🗣️ Сказали:", user_text)

        # 3. Генерация
        profile = load_profile()
        reply_text = generate_reply(user_text, profile)
        print("🤖 Ответ GPT:", reply_text)

        # 4. Озвучка
        generate_voice_mp3(reply_text)

        # 5. Отдача и продолжение диалога
        response = VoiceResponse()
        response.play(f"{NGROK_URL}/static/response.mp3")
        response.record(
            max_length=10,
            action=f"{NGROK_URL}/process-recording",
            method="POST",
            play_beep=True,
            trim="trim-silence"
        )

        return Response(str(response), mimetype="application/xml")

    except Exception as e:
        print("❌ Ошибка при обработке:", e)
        return "Ошибка сервера", 500

@app.route("/static/response.mp3")
def serve_audio():
    response_path = Path(__file__).parent / "static" / "response.mp3"

    if not response_path.exists():
        print("❌ Файл response.mp3 не найден!")
        return "Файл не найден", 404

    return send_file(response_path, mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
