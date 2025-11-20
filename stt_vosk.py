# stt_vosk.py
import json
import time
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

MODEL_PATH = "vosk-model-fr"

full_transcript = ""
last_partial = ""
_samplerate = None


full_transcript = ""
last_partial = ""

def reset_transcript():
    global full_transcript, last_partial
    full_transcript = ""
    last_partial = ""



def get_current_text() -> str:
    global full_transcript, last_partial
    if last_partial:
        return (full_transcript + " " + last_partial).strip()
    return full_transcript.strip()


def stt_loop(events_queue: "queue.Queue"):
    global full_transcript, last_partial, _samplerate

    print("Chargement du modèle Vosk...")
    model = Model(MODEL_PATH)

    # Même logique que dans test_vosk.py
    default_input = sd.default.device[0]
    device_info = sd.query_devices(default_input, "input")
    samplerate = int(device_info["default_samplerate"])
    _samplerate = samplerate
    print(f"[STT] Utilisation du device #{default_input} à {samplerate} Hz")

    rec = KaldiRecognizer(model, samplerate)

    def callback(indata, frames, time_info, status):
        global full_transcript, last_partial

        if status:
            print("Status audio:", status)

        data_bytes = bytes(indata)

        if rec.AcceptWaveform(data_bytes):
            result = json.loads(rec.Result())
            text = result.get("text", "").strip()
            if text:
                full_transcript += " " + text
                full_transcript = full_transcript.strip()
                last_partial = ""

                # Transcription "fixée"
                events_queue.put({
                    "type": "transcript",
                    "text": full_transcript
                })

                # Live identique (sans partial)
                events_queue.put({
                    "type": "transcript_live",
                    "text": full_transcript
                })
        else:
            partial = json.loads(rec.PartialResult()).get("partial", "").strip()
            last_partial = partial

            if partial:
                events_queue.put({
                    "type": "partial",
                    "text": partial
                })

                live = get_current_text()
                events_queue.put({
                    "type": "transcript_live",
                    "text": live
                })

    with sd.RawInputStream(
        samplerate=samplerate,
        blocksize=4000,
        dtype="int16",
        channels=1,
        callback=callback,
    ):
        print("🎤 STT en écoute... Parle quand tu veux.")
        while True:
            time.sleep(0.1)
