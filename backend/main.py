import tempfile
from flask import Flask, request, jsonify, send_file
from flask_socketio import SocketIO
from flask_cors import CORS
from llm import Brain
from stt import transcribe
from tts import speak
from intent_router import route
from config import FLASK_HOST, FLASK_PORT

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

brain = Brain()


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message", "")
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    llm_response = brain.think(user_input)
    result = route(llm_response)

    if result["type"] == "action_result":
        summary = brain.think(
            f"System command result: {result['result']}. "
            "Summarize this for the user conversationally in one sentence."
        )
        result["spoken"] = summary

    return jsonify(result)


@app.route("/api/voice", methods=["POST"])
def voice():
    audio_file = request.files.get("audio")
    if not audio_file:
        return jsonify({"error": "No audio file"}), 400

    path = tempfile.mktemp(suffix=".wav")
    audio_file.save(path)

    text = transcribe(path)
    llm_response = brain.think(text)
    result = route(llm_response)

    spoken_text = result.get("spoken", result["result"])
    audio_path = speak(spoken_text)

    return send_file(audio_path, mimetype="audio/wav")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "assistant": "MICKEY",
        "model": brain.history[0]["content"][:50] + "...",
    })


@socketio.on("user_message")
def handle_message(data):
    user_input = data.get("message", "")
    for token in brain.think_stream(user_input):
        socketio.emit("token", {"text": token})
    socketio.emit("response_complete")


if __name__ == "__main__":
    print("🤖 MICKEY is starting up...")
    print(f"   Server: http://localhost:{FLASK_PORT}")
    print(f"   Health: http://localhost:{FLASK_PORT}/api/health")
    socketio.run(app, host=FLASK_HOST, port=FLASK_PORT, debug=True, allow_unsafe_werkzeug=True)
