# test_vosk.py
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer

MODEL_PATH = "vosk-model-fr"  # dossier du modèle FR


def main():
    print("=== Appareils audio dispo ===")
    print(sd.query_devices())
    print("=============================\n")

    # On prend la fréquence d'échantillonnage par défaut de l'entrée
    default_input = sd.default.device[0]  # index entrée
    device_info = sd.query_devices(default_input, "input")
    samplerate = int(device_info["default_samplerate"])
    print(f"Utilisation du device #{default_input} à {samplerate} Hz")

    print("Chargement du modèle Vosk...")
    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, samplerate)

    def callback(indata, frames, time_info, status):
        if status:
            print("Status:", status)

        data_bytes = bytes(indata)

        if rec.AcceptWaveform(data_bytes):
            result = json.loads(rec.Result())
            text = result.get("text", "").strip()
            if text:
                print(f"[FINAL] {text}")
        else:
            partial = json.loads(rec.PartialResult()).get("partial", "").strip()
            if partial:
                print(f"[PARTIAL] {partial}", end="\r")

    with sd.RawInputStream(
        samplerate=samplerate,
        blocksize=4000,
        dtype="int16",
        channels=1,
        callback=callback,
    ):
        print("🎤 Parle (CTRL+C pour quitter)...")
        try:
            while True:
                sd.sleep(100)
        except KeyboardInterrupt:
            print("\nFin.")


if __name__ == "__main__":
    main()
