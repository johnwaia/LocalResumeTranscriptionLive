// =========================
// ELEMENTS UI
// =========================
const btnToggle = document.getElementById("session-toggle");
const btnDownload = document.getElementById("download-summary");
const partialBox = document.getElementById("partial");
const transcriptBox = document.getElementById("transcript");

// Modal
const modal = document.getElementById("model-modal");
const confirmModelBtn = document.getElementById("confirm-model");
const modelSelect = document.getElementById("modal-model-select");

// Loader overlay
const loaderOverlay = document.getElementById("model-loading-overlay");
const loaderProgress = document.getElementById("loader-progress");

// =========================
// STATE
// =========================
let sessionActive = false;
let eventSource = null;

// 🔥 Anti-doublons transcript final
let lastFinal = "";

// =========================
// 1) OUVERTURE DU MODAL AU DEMARRAGE
// =========================
window.onload = () => {
    modal.style.display = "flex";
};


// =========================
// 2) CHOIX DU MODELE
// =========================
confirmModelBtn.onclick = async () => {

    const modelName = modelSelect.value;
    modal.style.display = "none";

    loaderOverlay.style.display = "flex";
    loaderProgress.style.width = "0%";

    // Simule l’avancement visuel du chargement
    let fakeProgress = 0;
    const interval = setInterval(() => {
        fakeProgress += 5;
        if (fakeProgress > 90) fakeProgress = 90;
        loaderProgress.style.width = fakeProgress + "%";
    }, 150);

    try {
        const res = await fetch("/model/set", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model: modelName })
        });

        const data = await res.json();
        clearInterval(interval);

        if (!res.ok) {
            alert("❌ Le backend a refusé le modèle : " + data.message);
            loaderProgress.style.width = "0%";
            loaderOverlay.style.display = "none";
            modal.style.display = "flex";
            return;
        }

        loaderProgress.style.width = "100%";
        setTimeout(() => loaderOverlay.style.display = "none", 400);

    } catch (err) {
        clearInterval(interval);
        loaderOverlay.style.display = "none";
        alert("Erreur réseau lors du chargement du modèle.");
    }
};


// =========================
// 3) DEMARRER / STOPPER SESSION
// =========================
btnToggle.onclick = async () => {

    // STOP
    if (sessionActive) {
        await fetch("/session/stop", { method: "POST" });
        btnToggle.classList.remove("is-pause");
        btnToggle.classList.add("is-play");
        sessionActive = false;

        if (eventSource) eventSource.close();
        return;
    }

    // START
    const res = await fetch("/session/start", { method: "POST" });
    const data = await res.json();

    if (data.status === "started") {
        btnToggle.classList.remove("is-play");
        btnToggle.classList.add("is-pause");
        sessionActive = true;

        // Reset anti-doublons
        lastFinal = "";
        transcriptBox.textContent = "";

        startStream();
    }
};


// =========================
// 4) STREAM DES DONNÉES (instantané)
// =========================
function startStream() {
    if (eventSource) eventSource.close();

    eventSource = new EventSource("/stream");

    eventSource.onmessage = (event) => {
        let packet;
        try {
            packet = JSON.parse(event.data);
        } catch (e) {
            console.warn("Données SSE invalides :", event.data);
            return;
        }

        const partial = packet.partial || "";
        const finalText = packet.final || "";

        // Affichage du texte partiel
        partialBox.textContent = partial;

        // 🔥 Anti-duplication du texte final
        if (finalText && finalText !== lastFinal) {
            transcriptBox.textContent += finalText + " ";
            lastFinal = finalText;

            // Envoi du texte cumulatif pour résumé
            updateSummary(transcriptBox.textContent);
        }

    };

    eventSource.onerror = () => {
        console.log("SSE stream error");
    };
}


// =========================
// 5) Export résumé (placeholder)
// =========================
btnDownload.onclick = () => {
    alert("Fonction d’export non implémentée ici.");
};

async function updateSummary(fullText) {
    try {
        const res = await fetch("/summary/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: fullText })
        });

        const data = await res.json();

        // ⚠️ correct : le backend renvoie { summary: { ... } }
        const summary = data.summary;

        if (!summary) {
            console.log("⚠️ Pas de résumé renvoyé");
            return;
        }

        // Affichage du titre et sous-titre
        document.getElementById("summary-title").textContent =
            summary.title || "";

        document.getElementById("summary-subtitle").textContent =
            summary.subtitle || "";

        // Affichage des puces
        const ul = document.getElementById("summary-list");
        ul.innerHTML = "";

        (summary.bullets || []).forEach(b => {
            const li = document.createElement("li");
            li.textContent = b;
            ul.appendChild(li);
        });

    } catch (err) {
        console.log("⚠️ Erreur MAJ résumé :", err);
    }
}

