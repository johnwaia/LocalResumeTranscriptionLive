import sounddevice as sd
import numpy as np
from vosk import Model, KaldiRecognizer
from shared_state import shared_state
import os
import json


model_obj = None
recognizer = None


def load_model(model_path):
    global model_obj, recognizer

    if not os.path.isdir(model_path):
        raise FileNotFoundError(f"Modèle introuvable : {model_path}")

    print(f"📦 Tentative de chargement modèle : {model_path}")
    model_obj = Model(model_path)
    recognizer = KaldiRecognizer(model_obj, 16000)

    shared_state.model_loaded = True
    shared_state.current_model_path = model_path
    print("🎤 Modèle chargé avec succès.")


def start_stt():
    if not shared_state.model_loaded:
        print("❌ Aucun modèle chargé — transcription impossible.")
        return False

    shared_state.stt_running = True

    import threading
    th = threading.Thread(target=stt_loop, daemon=True)
    th.start()

    return True


def stop_stt():
    shared_state.stt_running = False
    print("🛑 STT stoppé.")


def stt_loop():
    global recognizer

    if recognizer is None:
        print("❌ Aucun recognizer initialisé.")
        return

    print("🎙️ Écoute active — parlez.")

    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=audio_callback
    ):
        while shared_state.stt_running:
            sd.sleep(50)


def audio_callback(indata, frames, time, status):
    global recognizer

    if status:
        print("⚠ Status audio:", status)

    # Convertit le buffer CFFI → bytes Python
    pcm_bytes = bytes(indata)

    if recognizer.AcceptWaveform(pcm_bytes):
        res = json.loads(recognizer.Result())
        if res.get("text"):
            shared_state.update_final(res["text"])
    else:
        res = json.loads(recognizer.PartialResult())
        shared_state.update_partial(res.get("partial", ""))


def get_current_text():
    return shared_state.get_for_stream()
