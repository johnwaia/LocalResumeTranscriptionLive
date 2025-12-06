class SharedState:
    def __init__(self):
        self.partial = ""
        self.final = ""
        self.lock = False

        # Infos modèle
        self.model_loaded = False
        self.current_model_path = None

        # État du STT
        self.stt_running = False

        # Résumé
        self.summary = {}

    def reset(self):
        """Reset complet transcription + résumé"""
        self.partial = ""
        self.final = ""
        self.summary = {}

    def update_partial(self, text):
        self.partial = text

    def update_final(self, text):
        """
        Ajout propre d'un segment final en évitant les mots collés.
        Exemple : "il" + "il tient" => "il il tient"
        """

        if not text:
            return

        # Si final vide → on met directement
        if not self.final:
            self.final = text
            return

        # On ajoute un espace propre uniquement si besoin
        if not self.final.endswith(" ") and not text.startswith(" "):
            self.final += " "

        self.final += text

    def get_for_stream(self):
        """Retourne la transcription pour /stream"""
        return {
            "partial": self.partial,
            "final": self.final
        }


shared_state = SharedState()
