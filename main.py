# main.py
from flask import Flask, render_template, Response, request, jsonify
from flask_cors import CORS
import threading
import queue
import json
import time
import re


from stt_vosk import stt_loop, get_current_text, reset_transcript
from ollama_client import update_structured_summary

app = Flask(__name__)
CORS(app)

# Queue pour envoyer des événements SSE au front
events_queue: "queue.Queue" = queue.Queue()

# Résumé courant (structuré)
# {
#   "title": "Titre",
#   "subtitle": "Sous-titre",
#   "bullets": ["pt1", "pt2", ...]
# }
current_summary = {
    "title": "",
    "subtitle": "",
    "bullets": [],
}

# Pour éviter plusieurs résumés simultanés
summarizer_busy = False

# Gestion des sessions
session_active = False
session_reset_requested = False

# --- Détection simple de mots-clés --- #

FRENCH_STOPWORDS = {
    "les", "des", "une", "un", "le", "la", "de", "du", "et",
    "pour", "avec", "sur", "dans", "que", "qui", "en", "au",
    "aux", "par", "à", "ce", "ces", "ses", "son", "sa", "vos",
    "nos", "notre", "votre", "leurs", "leur", "mais",
    "ou", "où", "donc", "or", "ni", "car", "ne", "pas", "plus",
    "moins", "très", "tout", "tous", "toute", "toutes"
}

def extract_tags_from_text(text: str, max_tags: int = 10):
    """
    Heuristique simple :
    - mots de 4+ lettres
    - on vire les mots vides
    - on favorise majuscules / chiffres
    """
    words = re.findall(r"\b[\wÀ-ÖØ-öø-ÿ\-]{4,}\b", text)
    scores = {}

    for w in words:
        lw = w.lower()
        if lw in FRENCH_STOPWORDS:
            continue

        score = 1
        if any(c.isupper() for c in w):
            score += 1
        if any(c.isdigit() for c in w):
            score += 1

        scores[lw] = scores.get(lw, 0) + score

    sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    tags = []
    for lw, _sc in sorted_words[:max_tags]:
        label = None
        for w in words:
            if w.lower() == lw:
                label = w
                break
        if not label:
            label = lw
        tags.append({"label": label, "type": "autre"})

    return tags



# ------------ Routes Flask ------------

@app.route("/")
def index():
    return render_template("index.html")


def event_stream():
    """Générateur SSE -> envoie des événements JSON au front."""
    while True:
        data = events_queue.get()
        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.route("/stream")
def stream():
    return Response(event_stream(), mimetype="text/event-stream")


@app.route("/session/start", methods=["POST"])
def start_session():
    """Démarre une nouvelle session (reset transcript + résumé)."""
    global current_summary, session_active, session_reset_requested

    print("[SESSION] Démarrage nouvelle session.")

    # reset STT
    reset_transcript()

    # reset résumé structuré
    current_summary = {
        "title": "",
        "subtitle": "",
        "bullets": [],
    }

    session_active = True
    session_reset_requested = True

    # informer le front
    events_queue.put({
        "type": "session",
        "status": "started",
    })

    return jsonify({"status": "ok"})


@app.route("/session/stop", methods=["POST"])
def stop_session():
    """Termine la session (on garde le dernier résumé affiché)."""
    global session_active
    print("[SESSION] Fin de session.")
    session_active = False

    events_queue.put({
        "type": "session",
        "status": "stopped",
    })

    return jsonify({"status": "ok"})


# ------------ Thread de résumé structuré ------------

def summarizer_loop():
    """
    Met à jour le résumé structuré (titre + sous-titre + bullets)
    sans jamais effacer le résumé affiché :
      - tant que Ollama n'a pas répondu, l'ancien résumé reste à l'écran
      - quand une nouvelle version arrive, on remplace proprement.
    """
    global current_summary, summarizer_busy
    global session_active, session_reset_requested

    last_text = ""

    print("[SUMMARY] Thread résumé démarré (structuré).")

    while True:
        try:
            # si aucune session -> on ne résume pas
            if not session_active:
                time.sleep(0.2)
                continue

            # reset demandé (nouvelle session)
            if session_reset_requested:
                print("[SUMMARY] Reset pour nouvelle session.")
                last_text = ""
                current_summary = {
                    "title": "",
                    "subtitle": "",
                    "bullets": [],
                }
                session_reset_requested = False

            live_text = get_current_text()

            if live_text and not summarizer_busy:
                # tu peux soit résumer TOUT le texte,
                # soit seulement le delta. Ici on prend tout le texte
                # pour garder un résumé cohérent.
                if len(live_text) > len(last_text):
                    new_segment = live_text[len(last_text):]
                else:
                    new_segment = live_text

                # on évite les updates pour 3 mots
                if len(new_segment.strip()) > 20:
                    last_text = live_text
                    summarizer_busy = True

                    print("\n[SUMMARY] Mise à jour du résumé structuré...")
                    print("Texte utilisé (live_text) :")
                    print(live_text)
                    print("---------------------------------")

                    # appel Ollama (synchrone)
                    updated = update_structured_summary(
                        previous_summary=current_summary,
                        transcript=live_text,  # ou new_segment si tu veux contexte + léger
                    )
                    current_summary = updated

                    print("[SUMMARY] Nouveau résumé structuré :")
                    print(current_summary)
                    print("====================================\n")

                    # envoi au front : on remplace tout le bloc résumé
                    events_queue.put({
                        "type": "summary_structured",
                        "summary": current_summary,
                    })

                    tags = extract_tags_from_text(live_text)
                    events_queue.put({
                        "type": "tags",
                        "tags": tags,
                    })

                    summarizer_busy = False

            time.sleep(1.0)  # fréquence d'update du résumé

        except Exception as e:
            print("Erreur dans summarizer_loop:", e)
            summarizer_busy = False
            time.sleep(1.0)


# ------------ Lancement des threads + serveur ------------

if __name__ == "__main__":
    # Thread STT (Vosk)
    t_stt = threading.Thread(target=stt_loop, args=(events_queue,), daemon=True)
    t_stt.start()

    # Thread Résumé structuré
    t_sum = threading.Thread(target=summarizer_loop, daemon=True)
    t_sum.start()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        threaded=True,
        use_reloader=False,
    )
