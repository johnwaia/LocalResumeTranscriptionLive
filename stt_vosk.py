import json
import time
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import shared_state

full_transcript = ""
last_partial = ""
_samplerate = None
recognizer = None
model_object = None


def set_model_path(path: str):
    """Mis à jour via le front (Flask)"""
    shared_state.current_model_path = path
    shared_state.model_ready = True
    print(f"🔄 Modèle choisi par l'utilisateur : {path}")


def reset_transcript():
    global full_transcript, last_partial
    full_transcript = ""
    last_partial = ""


def get_current_text() -> str:
    global full_transcript, last_partial
    if last_partial:
        return (full_transcript + " " + last_partial).strip()
    return full_transcript.strip()


def load_model():
    """Charge un modèle uniquement après sélection utilisateur"""
    global recognizer, model_object, _samplerate

    if not shared_state.current_model_path:
        print("⚠ Aucun modèle sélectionné.")
        return

    print(f"📥 Chargement du modèle : {shared_state.current_model_path}")
    model_object = Model(shared_state.current_model_path)

    default_input = sd.default.device[0]
    samplerate = int(sd.query_devices(default_input, "input")["default_samplerate"])
    _samplerate = samplerate

    recognizer = KaldiRecognizer(model_object, samplerate)
    print(f"🎤 Modèle chargé ({samplerate} Hz)")


def stt_loop(events_queue: "queue.Queue"):
    global recognizer, last_partial, full_transcript

    print("🧠 Vosk en attente du modèle utilisateur...")

    while True:
        # attendre que user sélectionne un modèle
        if not shared_state.model_ready:
            time.sleep(0.3)
            continue

        if not shared_state.session_active:
            time.sleep(0.1)
            continue

        if recognizer is None:
            load_model()

        if recognizer is None:
            time.sleep(0.5)
            continue

        def callback(indata, frames, time_info, status):
            global full_transcript, last_partial

            if not shared_state.session_active:
                return

            if status:
                print("Status audio:", status)

            data_bytes = bytes(indata)

            if recognizer.AcceptWaveform(data_bytes):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()

                if text:
                    full_transcript = (full_transcript + " " + text).strip()
                    last_partial = ""

                    events_queue.put({"type": "transcript", "text": full_transcript})
                    events_queue.put({"type": "transcript_live", "text": full_transcript})

            else:
                partial = json.loads(recognizer.PartialResult()).get("partial", "").strip()
                last_partial = partial

                if partial:
                    live = get_current_text()
                    events_queue.put({"type": "partial", "text": partial})
                    events_queue.put({"type": "transcript_live", "text": live})

        # IMPORTANT: utiliser InputStream (pas RawInputStream)
        with sd.InputStream(
            samplerate=_samplerate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            print("🎙️ Écoute active — parlez.")
            while shared_state.session_active:
                time.sleep(0.1)
