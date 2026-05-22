import tempfile
from flask import Flask, request, jsonify, send_file
from flask_socketio import SocketIO
from flask_cors import CORS
from llm import Brain
from stt import transcribe
from tts import speak
from intent_router import route
from config import FLASK_HOST, FLASK_PORT
from memory.conversation_log import get_message_count, get_session_count
from memory.mistake_tracker import log_mistake, get_recent_mistakes, get_mistake_count, is_correction
from memory.brain_indexer import index_brain_wiki
from memory.chroma_store import query as chroma_query, collection_count
from auth import require_auth, get_or_create_token
from memory.maintenance import run_daily_maintenance, get_storage_metrics
from memory.backup import backup_sqlite, backup_chroma, list_backups

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

brain = Brain()

# Track last exchange for correction detection
_last_user_query = ""
_last_assistant_response = ""


@app.route("/api/chat", methods=["POST"])
@require_auth
def chat():
    global _last_user_query, _last_assistant_response
    data = request.json
    user_input = data.get("message", "")
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    # Check if this is a correction of the last response
    if is_correction(user_input) and _last_user_query:
        log_mistake(
            user_query=_last_user_query,
            wrong_response=_last_assistant_response,
            correction=user_input,
            countermeasure=f"When asked about '{_last_user_query}', use this correction instead.",
        )

    llm_response = brain.think(user_input)
    result = route(llm_response)

    if result["type"] == "action_result":
        summary = brain.think(
            f"System command result: {result['result']}. "
            "Summarize this for the user conversationally in one sentence."
        )
        result["spoken"] = summary
        _last_assistant_response = summary
    else:
        _last_assistant_response = result["result"]

    _last_user_query = user_input
    return jsonify(result)


@app.route("/api/voice", methods=["POST"])
@require_auth
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
    storage = get_storage_metrics()
    return jsonify({
        "status": "online",
        "assistant": "MICKEY",
        "model": "hermes3:8b",
        "memory": {
            "conversations": get_message_count(),
            "sessions": get_session_count(),
            "mistakes": get_mistake_count(),
            "wiki_chunks": collection_count("brain_wiki"),
        },
        "storage": storage,
    })


@app.route("/api/correct", methods=["POST"])
@require_auth
def correct():
    data = request.json
    log_mistake(
        user_query=data.get("query", _last_user_query),
        wrong_response=data.get("wrong_response", _last_assistant_response),
        correction=data.get("correction", ""),
        countermeasure=data.get("countermeasure"),
        category=data.get("category", "general"),
    )
    return jsonify({"status": "ok", "message": "Correction logged. I'll remember this."})


@app.route("/api/memory/search", methods=["GET"])
def memory_search():
    q = request.args.get("q", "")
    if not q:
        return jsonify({"error": "No query provided"}), 400
    results = {
        "wiki": chroma_query("brain_wiki", q, n_results=3),
        "conversations": chroma_query("conversations", q, n_results=3),
        "mistakes": chroma_query("mistakes", q, n_results=2),
    }
    return jsonify(results)


@app.route("/api/memory/reindex", methods=["POST"])
@require_auth
def reindex():
    result = index_brain_wiki()
    return jsonify(result)


@app.route("/api/memory/mistakes", methods=["GET"])
def mistakes():
    return jsonify(get_recent_mistakes(limit=20))


@app.route("/api/maintenance", methods=["POST"])
@require_auth
def maintenance():
    """Run daily maintenance manually."""
    result = run_daily_maintenance()
    return jsonify(result)


@app.route("/api/storage", methods=["GET"])
def storage():
    """Get storage metrics."""
    return jsonify(get_storage_metrics())


@app.route("/api/backup", methods=["POST"])
@require_auth
def backup():
    """Create manual backup."""
    results = {
        "sqlite": backup_sqlite(),
        "chroma": backup_chroma(),
    }
    return jsonify(results)


@app.route("/api/backups", methods=["GET"])
def backups():
    """List all backups."""
    return jsonify(list_backups())


@socketio.on("user_message")
def handle_message(data):
    user_input = data.get("message", "")
    for token in brain.think_stream(user_input):
        socketio.emit("token", {"text": token})
    socketio.emit("response_complete")


@app.route("/api/token", methods=["GET"])
def get_token():
    """Get auth token (only accessible from localhost)."""
    from auth import is_local_request
    if not is_local_request():
        return jsonify({"error": "Token only accessible from localhost"}), 403
    return jsonify({"token": get_or_create_token()})


if __name__ == "__main__":
    # Index Brain wiki on startup
    print("🤖 MICKEY is starting up...")
    print("   Indexing Brain wiki...")
    result = index_brain_wiki()
    print(f"   Indexed {result.get('files_processed', 0)} files, {result.get('chunks_indexed', 0)} chunks")

    token = get_or_create_token()
    print(f"   Auth token: {token}")
    print(f"   Server: http://localhost:{FLASK_PORT}")
    print(f"   Health: http://localhost:{FLASK_PORT}/api/health")
    print(f"   Remote: https://<tailscale-hostname>/api/health")
    socketio.run(app, host=FLASK_HOST, port=FLASK_PORT, debug=True, allow_unsafe_werkzeug=True)
