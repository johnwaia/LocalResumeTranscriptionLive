class SharedState:
    def __init__(self):
        self.partial = ""
        self.final = ""
        self.lock = False

        # AJOUT : stockage du résumé
        self.summary = {}

    def reset(self):
        self.partial = ""
        self.final = ""
        self.summary = {}   # AJOUT : reset propre du résumé

    def update_partial(self, text):
        self.partial = text

    def update_final(self, text):
        self.final += (" " + text).strip()

    def get_for_stream(self):
        return {
            "partial": self.partial,
            "final": self.final
        }


shared_state = SharedState()
