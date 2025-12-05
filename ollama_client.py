import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:1b"


def _extract_json_block(text: str) -> str:
    """
    Extrait proprement le JSON même si Ollama renvoie du texte autour.
    Supporte:
    - ```json ... ```
    - texte avant/après
    - contenu bavard
    """
    if not text:
        raise ValueError("Réponse Ollama vide.")

    cleaned = text.strip()

    # Retirer les backticks CODEBLOCKS
    cleaned = re.sub(r"```json", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "").strip()

    # Trouver le premier { et le dernier }
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Aucun bloc JSON valide trouvé dans la réponse Ollama.")

    return cleaned[start:end+1]


def update_structured_summary(previous_summary: dict, transcript: str) -> dict:
    transcript = (transcript or "").strip()
    if not transcript:
        return previous_summary or {
            "title": "",
            "subtitle": "",
            "bullets": []
        }

    system_prompt = (
        "Tu résumes une conversation orale EN FRANÇAIS.\n"
        "RENVOIE EXCLUSIVEMENT un JSON VALIDE, sans aucun texte avant ni après.\n"
        "FORMAT STRICT OBLIGATOIRE :\n"
        "{\n"
        '  \"title\": \"Titre court\",\n'
        '  \"subtitle\": \"Sous-titre\",\n'
        '  \"bullets\": [\"• point 1\", \"• point 2\"]\n'
        "}\n"
        "Ne parle pas, ne commente pas, ne mets PAS de ```.\n"
    )

    if previous_summary:
        previous_json_str = json.dumps(previous_summary, ensure_ascii=False)
        user_msg = (
            "Résumé précédent :\n"
            f"{previous_json_str}\n\n"
            "Nouveau texte à intégrer :\n"
            f"{transcript}\n\n"
            "Mets à jour CE RÉSUMÉ UNIQUEMENT. Ne renvoie que du JSON strict."
        )
    else:
        user_msg = (
            "Texte à résumer :\n"
            f"{transcript}\n\n"
            "Renvoie un JSON strict conforme au format demandé."
        )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ],
        "stream": False
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        raw = data.get("message", {}).get("content", "")
        print("\n=== RAW OLLAMA RESPONSE ===")
        print(raw)
        print("=== END RAW ===\n")

        json_str = _extract_json_block(raw)
        parsed = json.loads(json_str)

        # normalisation
        title = str(parsed.get("title", "")).strip()
        subtitle = str(parsed.get("subtitle", "")).strip()
        bullets_raw = parsed.get("bullets", [])

        bullets = []
        if isinstance(bullets_raw, list):
            for item in bullets_raw:
                if isinstance(item, str) and item.strip():
                    bullets.append(item.strip())

        # Fusion intelligente
        if previous_summary:
            if not title:
                title = previous_summary.get("title", "")
            if not subtitle:
                subtitle = previous_summary.get("subtitle", "")
            if not bullets:
                bullets = previous_summary.get("bullets", [])

        return {
            "title": title or "Résumé",
            "subtitle": subtitle or "",
            "bullets": bullets,
        }

    except Exception as e:
        print("❌ Erreur parsing JSON Ollama :", e)
        return previous_summary or {
            "title": "Résumé",
            "subtitle": "",
            "bullets": []
        }

import requests

def summarize_text(text):
    payload = {
        "model": "llama3",
        "prompt": f"Résumé en JSON strict :\n{text}\n\nFORMAT JSON : {{\"title\":\"\",\"subtitle\":\"\",\"bullets\":[\"...\"]}}"
    }

    r = requests.post("http://localhost:11434/api/generate", json=payload)
    raw_text = r.text

    print("\n=== RAW OLLAMA RESPONSE ===")
    print(raw_text)
    print("=== END RAW ===\n")

    json_data = _extract_json_block(raw_text)

    if json_data is None:
        return {"title": "", "subtitle": "", "bullets": []}

    # Normalisation du résultat (certains modèles renvoient "bullets" comme objets)
    bullets = json_data.get("bullets", [])
    bullets = [b if isinstance(b, str) else b.get("text", "") for b in bullets]

    return {
        "title": json_data.get("title", ""),
        "subtitle": json_data.get("subtitle", ""),
        "bullets": bullets
    }
