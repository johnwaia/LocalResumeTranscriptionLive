# Projet Veille Technologique

Ce projet permet de **créer une fiche projet à partir d'une conversation orale**, avec **transcription en temps réel** et **résumé structuré**.  


---

## Fonctionnalités principales

1. **Transcrire et comprendre la voix**
   - Utilisation de **Vosk** pour la reconnaissance vocale en temps réel.
   - Transcription instantanée de la conversation en français.

2. **Créer la fiche projet**
   - Résumé automatique de la conversation avec **Ollama**.
   - Génération d’un JSON structuré contenant :
     - `title` : titre du projet
     - `subtitle` : sous-titre
     - `bullets` : points clés

3. **Démonstration Front-end**
   - Interface web avec **Flask** pour afficher le résumé et les tags extraits en direct.

---

## Étapes du projet

1. **Transcrire et comprendre**
   - Transcription en temps réel via Vosk.
   - Analyse du texte pour extraire les informations clés.

2. **Générer la fiche projet**
   - Utilisation de Ollama pour résumer la conversation et créer un JSON structuré.

3. **Afficher le résultat**
   - Envoi des résumés et tags au front via **SSE** (Server-Sent Events) avec Flask.

---

## Installation sous Windows

### 1. Installer Vosk (transcription)

1. Aller sur [Vosk Models](https://alphacephei.com/vosk/models)  
2. Télécharger le modèle français :  
   [vosk-model-small-fr-0.22.zip](https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip)  
3. Extraire le dossier `vosk-model-small-fr-0.22` dans le projet.

---

### 2. Créer un environnement Python

1. Autoriser l’exécution de scripts PowerShell :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

2. Créer l’environnement dans le dossier du projet :

```powershell
python -m venv venv
```

3. Activer l’environnement :

```powershell
.\venv\Scripts\Activate.ps1
```

4. Pour quitter l’environnement :

```powershell
deactivate
```

---

### 3. Installer les dépendances

Dans l’environnement activé :

```powershell
pip install -r requirements.txt
```

**Liste des packages requis si pas de `requirements.txt`** :

```powershell
pip install vosk
pip install sounddevice
pip install flask
pip install flask_cors
pip install pywin32
pip install requests
```

---

### 4. Installer Ollama (résumé)

1. Télécharger Ollama pour Windows : [https://ollama.com/download](https://ollama.com/download)  
2. Installer et ouvrir le terminal.  
3. Télécharger le modèle `llama3` :

```powershell
ollama pull llama3
```

---

## Lancer le projet

1. Activer l’environnement Python.
2. Démarrer le serveur Flask :

```powershell
python main.py
```

3. Ouvrir le navigateur sur [http://localhost:5000](http://localhost:5000).  
4. Démarrer une session vocale pour créer la fiche projet en temps réel.

---

## Notes

- Le résumé JSON reste valide même si la conversation est longue.
- Les tags sont extraits automatiquement à partir du texte transcrit.
- Testé sur Windows 10/11 avec Python 3.10+.