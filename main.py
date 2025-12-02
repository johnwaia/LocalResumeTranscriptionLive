from flask import Flask, render_template, Response, request, jsonify
from flask_cors import CORS
import threading
import queue
import json
import time
import re
import os

from stt_vosk import stt_loop, get_current_text, reset_transcript, set_model_path
from ollama_client import update_structured_summary
import shared_state 

app = Flask(__name__)
CORS(app)

events_queue: "queue.Queue" = queue.Queue()

current_summary = {"title": "", "subtitle": "", "bullets": []}

summarizer_busy = False
session_reset_requested = False


@app.route("/")
def index():
    return render_template("index.html")


def event_stream():
    while True:
        yield f"data: {json.dumps(events_queue.get(), ensure_ascii=False)}\n\n"


@app.route("/stream")
def stream():
    return Response(event_stream(), mimetype="text/event-stream")


@app.route("/session/start", methods=["POST"])
def start_session():
    global current_summary, session_reset_requested

    reset_transcript()
    current_summary = {"title": "", "subtitle": "", "bullets": []}

    shared_state.session_active = True
    session_reset_requested = True

    events_queue.put({"type": "session", "status": "started"})
    return jsonify({"status": "ok"})


@app.route("/session/stop", methods=["POST"])
def stop_session():

    shared_state.session_active = False
    events_queue.put({"type": "session", "status": "stopped"})
    return jsonify({"status": "ok"})



@app.route("/model/set", methods=["POST"])
def select_model():
    data = request.json
    model_name = data.get("model")

    if not model_name:
        return jsonify({"error": "Aucun modèle reçu"}), 400

    model_path = f"models/{model_name}"

    if not os.path.exists(model_path):
        print(f"❌ Modèle introuvable : {model_path}")
        return jsonify({"error": "Modèle introuvable"}), 500

    set_model_path(model_path)
    print(f"📁 MODELS PATH = {model_path}")

    return jsonify({"status": "ok"})

def summarizer_loop():
    global current_summary, summarizer_busy, session_reset_requested

    last_text = ""
    while True:
        if not shared_state.session_active:
            time.sleep(0.2)
            continue

        live = get_current_text()

        if live and live.strip() != last_text.strip() and not summarizer_busy:
            last_text = live
            summarizer_busy = True

            current_summary = update_structured_summary(current_summary, live)

            events_queue.put({"type": "summary_structured", "summary": current_summary})
            summarizer_busy = False

        time.sleep(1)


if __name__ == "__main__":
    threading.Thread(target=stt_loop, args=(events_queue,), daemon=True).start()
    threading.Thread(target=summarizer_loop, daemon=True).start()

    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True, use_reloader=False)
