from flask import Flask, request, Response, send_file
from twilio.twiml.voice_response import VoiceResponse
import requests
import tempfile
import os
from dotenv import load_dotenv

# Импорт собственных модулей
from app.utils.whisper_service import transcribe_audio
from utils.gpt_service import load_profile, generate_reply
from utils.elevenlabs_service import generate_voice_mp3

from pathlib import Path

# Загрузка переменных окружения
load_dotenv()
NGROK_URL = os.getenv("NGROK_URL")

app = Flask(__name__)

@app.route("/voice-test", methods=["POST"])
def voice():
    print("📞 Входящий звонок получен")
    print(request.form)

    response = VoiceResponse()

    # 🟡 Слушаем сразу, не говорим первым
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

    # 1. Скачиваем аудио
    audio_url = f"{recording_url}.mp3"
    audio_data = requests.get(audio_url).content

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_audio:
        tmp_audio.write(audio_data)
        tmp_audio_path = tmp_audio.name

    # 2. Распознаём текст
    user_text = transcribe_audio(tmp_audio_path)
    print("🗣️ Сказали:", user_text)

    # 3. Загружаем профиль и генерируем ответ
    profile = load_profile()
    reply_text = generate_reply(user_text, profile)
    print("🤖 Ответ GPT:", reply_text)

    # 4. Озвучка через ElevenLabs
    generate_voice_mp3(reply_text)

    # 5. Отдаём mp3 и снова слушаем
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


@app.route("/static/response.mp3")
def serve_audio():
    response_path = Path(__file__).parent / "static" / "response.mp3"

    if not response_path.exists():
        print("❌ Файл response.mp3 не найден!")
        return "Файл не найден", 404

    return send_file(response_path, mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
