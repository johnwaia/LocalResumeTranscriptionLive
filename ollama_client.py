# ollama_client.py
import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3"  # adapte si tu utilises un autre modèle


def _extract_json_block(raw: str) -> str:
    """
    Essaie de récupérer un bloc JSON même si Ollama
    renvoie du texte autour ou des ```json ... ```.
    """
    # Enlever les fences ```json ... ```
    fence = re.search(r"```(?:json)?(.*)```", raw, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()

    raw = raw.strip()

    if raw.startswith("{"):
        return raw

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]

    return raw


def update_structured_summary(previous_summary: dict, transcript: str) -> dict:
    """
    Met à jour un résumé structuré :
      {
        "title": "Titre court",
        "subtitle": "Sous-titre",
        "bullets": ["point 1", "point 2", ...]
      }

    - previous_summary : dict (peut être vide au début)
    - transcript       : transcription (complète ou partielle)
    """
    transcript = (transcript or "").strip()
    if not transcript:
        return previous_summary or {
            "title": "",
            "subtitle": "",
            "bullets": [],
        }

    system_prompt = (
        "Tu résumes une conversation orale EN FRANÇAIS.\n"
        "Tu dois renvoyer STRICTEMENT un JSON valide, sans texte autour.\n\n"
        "Format JSON attendu :\n"
        "{\n"
        '  \"title\": \"Titre court et informatif\",\n'
        '  \"subtitle\": \"Sous-titre qui précise le contexte ou l\'objectif\",\n'
        '  \"bullets\": [\n'
        '    \"Premier point important\", \n'
        '    \"Deuxième point important\", \n'
        "    ...\n"
        "  ]\n"
        "}\n\n"
        "Toujours en français. PAS D'ANGLAIS."
    )

    if previous_summary:
        prev_json = json.dumps(previous_summary, ensure_ascii=False)
        user_content = (
            "Voici le résumé structuré ACTUEL (au format JSON) :\n"
            f"{prev_json}\n\n"
            "Voici la transcription ACTUELLE de la conversation (peut être partielle) :\n"
            f"{transcript}\n\n"
            "Mets à jour le résumé structuré en respectant le format JSON demandé."
        )
    else:
        user_content = (
            "Voici une transcription de conversation (peut être partielle) :\n"
            f"{transcript}\n\n"
            "Crée un premier résumé structuré en respectant le format JSON demandé."
        )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "stream": False,  # pas de streaming : on garde le résumé précédent jusqu'à la nouvelle version complète
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        raw = data.get("message", {}).get("content", "").strip()

        print("\n=== RAW OLLAMA SUMMARY ===")
        print(raw)
        print("=== END RAW ===\n")

        json_block = _extract_json_block(raw)
        parsed = json.loads(json_block)

        title = str(parsed.get("title", "")).strip()
        subtitle = str(parsed.get("subtitle", "")).strip()
        bullets_raw = parsed.get("bullets", [])

        bullets = []
        if isinstance(bullets_raw, list):
            for b in bullets_raw:
                if isinstance(b, str):
                    txt = b.strip()
                    if txt:
                        bullets.append(txt)

        # On fusionne intelligemment avec l'ancien résumé si besoin
        if previous_summary:
            if not title:
                title = previous_summary.get("title", "")
            if not subtitle:
                subtitle = previous_summary.get("subtitle", "")
            if not bullets:
                bullets = previous_summary.get("bullets", [])

        return {
            "title": title or "Résumé de la conversation",
            "subtitle": subtitle or "",
            "bullets": bullets,
        }

    except Exception as e:
        print("Erreur update_structured_summary:", e)
        # En cas d'erreur : on garde l'ancien résumé
        return previous_summary or {
            "title": "Résumé de la conversation",
            "subtitle": "",
            "bullets": [],
        }
