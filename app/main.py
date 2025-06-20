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

import subprocess
import tempfile


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
        # 1. Скачиваем mp3
        audio_url = f"{recording_url}.mp3"
        print("📥 Скачиваем:", audio_url)
        audio_data = requests.get(audio_url).content

        # 2. Сохраняем исходный mp3
        raw_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        with open(raw_path, "wb") as f:
            f.write(audio_data)
        print("📁 mp3 сохранён:", raw_path)

        # 3. Готовим .wav путь
        converted_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name

        # 4. ffmpeg перекодировка
        result = subprocess.run([
            "C:\\tools\\ffmpeg\\bin\\ffmpeg.exe", "-y", "-i", raw_path,
            "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le", converted_path
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print("❌ Ошибка ffmpeg:")
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
            return "Ошибка ffmpeg", 500
        else:
            print("✅ ffmpeg завершён успешно.")

        tmp_audio_path = converted_path
        print("🎛️ Готов к Whisper:", tmp_audio_path)

        # 5. Whisper
        try:
            user_text = transcribe_audio(tmp_audio_path)
            print("🗣️ Сказали:", user_text)
            print("✅ Whisper завершён.")
        except Exception as whisper_error:
            print("❌ Whisper упал:", whisper_error)
            return "Ошибка Whisper", 500
        # 6. GPT
        profile = load_profile()
        reply_text = generate_reply(user_text, profile)
        print("🤖 Ответ GPT:", reply_text)
        print("✅ GPT-ответ получен.")

        # 7. Озвучка
        generate_voice_mp3(reply_text)
        print("✅ Озвучка завершена.")

        # 8. Удаление временных файлов
        try:
            os.remove(raw_path)
            os.remove(converted_path)
            print("🧹 Временные файлы удалены.")
        except Exception as cleanup_error:
            print("⚠️ Ошибка при удалении файлов:", cleanup_error)

        # 9. Ответ Twilio
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
