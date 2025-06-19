from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

@app.route("/voice-test", methods=["POST"])
def voice():
    print("📞 Входящий звонок получен")
    print(request.form)

    twiml = VoiceResponse()
    twiml.say("Dies ist ein Test. Vielen Dank für Ihren Anruf.", voice="Polly.Marlene", language="de-DE")

    return Response(str(twiml), mimetype="application/xml")

if __name__ == "__main__":
    app.run(debug=True, port=5000)