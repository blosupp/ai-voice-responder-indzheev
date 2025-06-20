from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse
import requests
import tempfile
import subprocess
from dotenv import load_dotenv
from app.utils.whisper_service import transcribe_audio

from shutil import copyfile

import os
from pathlib import Path

load_dotenv()
NGROK_URL = os.getenv("NGROK_URL")

app = Flask(__name__)

@app.route("/voice-test", methods=["POST"])
def voice():
    print("📞 Входящий звонок получен")
    print(request.form)

    response = VoiceResponse()
    response.record(
        max_length=15,
        timeout=5,
        trim="trim-silence",
        play_beep=True,
        action=f"{NGROK_URL}/process-recording",
        method="POST"
    )

    return Response(str(response), mimetype="application/xml")

@app.route("/process-recording", methods=["POST"])
def process_recording():
    print("🎧 Обработка входящего аудио")
    recording_url = request.form.get("RecordingUrl")


    if not recording_url:
        return "❌ Нет записи", 400

    try:
        # Скачиваем
        audio_url = f"{recording_url}.mp3"
        audio_data = requests.get(audio_url).content

        # Сохраняем как mp3
        raw_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        with open(raw_path, "wb") as f:
            f.write(audio_data)
        print("📥 Сохранили входящее аудио как .raw:", raw_path)
        print("📦 Размер .raw файла:", os.path.getsize(raw_path), "байт")


        # 2. Готовим путь для перекодированного .wav
        converted_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name

        # 3. Конвертируем raw → wav, указываем явно mulaw
        result = subprocess.run([
            "C:\\tools\\ffmpeg\\bin\\ffmpeg.exe", "-y",
            "-i", raw_path,
            "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le", converted_path
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print("❌ Ошибка ffmpeg:")
            print(result.stderr)
            return "Ошибка при декодировании", 500
        else:
            print("✅ Аудио успешно перекодировано:", converted_path)
            print("📦 Размер .wav файла:", os.path.getsize(converted_path), "байт")
            debug_wav_path = Path(__file__).parent / "audio" / "last_call.wav"
            copyfile(converted_path, debug_wav_path)
            print("🎧 Сохранили копию .wav в:", debug_wav_path)

        # Распознавание
        user_text = transcribe_audio(converted_path)
        print("🧠 Распознанный текст:")
        print("👉", user_text)

        # Финальный ответ
        response = VoiceResponse()
        response.say("Спасибо. Сообщение получено.", voice="Polly.Marlene", language="de-DE")

        return Response(str(response), mimetype="application/xml")

    except Exception as e:
        print("❌ Ошибка:", e)
        return "Ошибка сервера", 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
