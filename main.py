import os
import time
import json
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS

from ollama_client import update_structured_summary
from shared_state import shared_state
from stt_vosk import load_model, start_stt, stop_stt

app = Flask(__name__)
CORS(app)

print("🧠 Vosk en attente du modèle utilisateur...")


@app.route("/")
def index():
    return render_template("index.html")


# ------------- API : Sélection modèle ---------------- #
@app.route("/model/set", methods=["POST"])
def set_model():
    data = request.json
    model_name = data.get("model")

    model_path = os.path.join("models", model_name)

    print(f"📥 Chargement du modèle : {model_name}")
    print(f"📁 Modèle défini : {model_path}")

    try:
        load_model(model_path)
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"❌ Erreur chargement modèle : {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ------------- API : Lancer STT ---------------- #
@app.route("/session/start", methods=["POST"])
def start_session():
    shared_state.reset()
    start_stt()
    return jsonify({"status": "started"})


# ------------- API : Arrêter STT ---------------- #
@app.route("/session/stop", methods=["POST"])
def stop_session():
    stop_stt()
    return jsonify({"status": "stopped"})


# ----------- API : STREAMING SSE (transcription temps réel) ----------- #
@app.route("/stream")
def stream():
    def event_stream():
        while True:
            data = shared_state.get_for_stream()
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(0.1)

    return Response(event_stream(), mimetype="text/event-stream")

# ------------------------ API RÉSUMÉ ------------------------ #


@app.route("/summary/update", methods=["POST"])
def update_summary():
    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"error": "Aucune transcription fournie"}), 400

    print(f"📄 Résumé demandé pour : {text[:80]} ...")

    try:
        # Résumé précédent (ou {} si vide)
        previous = shared_state.summary or {}

        # Nouveau résumé structuré
        new_summary = update_structured_summary(previous, text)

        # On stocke le résumé mis à jour
        shared_state.summary = new_summary

        print("📘 Résumé mis à jour :", new_summary)

        return jsonify({"summary": new_summary})

    except Exception as e:
        print("❌ Erreur résumé :", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
