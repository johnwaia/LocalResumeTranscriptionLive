// =========================
// ELEMENTS UI
// =========================
const btnToggle = document.getElementById("session-toggle");
const btnDownload = document.getElementById("download-summary");
const partialBox = document.getElementById("partial");
const transcriptBox = document.getElementById("transcript");

const modal = document.getElementById("model-modal");
const confirmModelBtn = document.getElementById("confirm-model");
const modelSelect = document.getElementById("modal-model-select");

const voiceAnim = document.getElementById("voice-anim"); // Animation bars

// Loader overlay
const loaderOverlay = document.getElementById("model-loading-overlay");
const loaderProgress = document.getElementById("loader-progress");

// =========================
// STATE
// =========================
let sessionActive = false;
let eventSource = null;
let audioContext = null;
let analyser = null;
let microphoneStream = null;

let lastFinal = ""; // anti-duplicates

// =========================
// 1) SHOW MODEL PICKER ON LOAD
// =========================
window.onload = () => {
    modal.style.display = "flex";
};

// =========================
// 2) LOAD MODEL
// =========================
confirmModelBtn.onclick = async () => {
    const modelName = modelSelect.value;

    modal.style.display = "none";
    loaderOverlay.style.display = "flex";
    loaderProgress.style.width = "0%";

    // Fake loading bar animation
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
            alert("❌ Erreur : " + data.message);
            loaderOverlay.style.display = "none";
            modal.style.display = "flex";
            return;
        }

        loaderProgress.style.width = "100%";
        setTimeout(() => loaderOverlay.style.display = "none", 300);

    } catch (err) {
        clearInterval(interval);
        loaderOverlay.style.display = "none";
        alert("Erreur réseau.");
    }
};

// =========================
// 3) START / STOP SESSION
// =========================
btnToggle.onclick = async () => {
    if (sessionActive) {
        stopVoiceAnimation();
        stopAudioLevelListener();
        await fetch("/session/stop", { method: "POST" });

        sessionActive = false;
        btnToggle.classList.add("is-play");
        btnToggle.classList.remove("is-pause");

        if (eventSource) eventSource.close();
        return;
    }

    // START SESSION
    const res = await fetch("/session/start", { method: "POST" });
    const data = await res.json();

    if (data.status === "started") {
        sessionActive = true;
        btnToggle.classList.remove("is-play");
        btnToggle.classList.add("is-pause");

        lastFinal = "";
        transcriptBox.textContent = "";

        startStream();
        startVoiceAnimation();      // 👈 animation ON
        startAudioLevelListener();  // 👈 sync animation with mic volume
    }
};

// =========================
// 4) STREAM TRANSCRIPT
// =========================
function startStream() {
    if (eventSource) eventSource.close();
    eventSource = new EventSource("/stream");

    eventSource.onmessage = (event) => {
        let packet;
        try {
            packet = JSON.parse(event.data);
        } catch {
            return;
        }

        const partial = packet.partial || "";
        const finalText = packet.final || "";

        partialBox.textContent = partial;

        if (finalText && finalText !== lastFinal) {
            transcriptBox.textContent += finalText + " ";
            lastFinal = finalText;
            updateSummary(transcriptBox.textContent);
        }
    };

    eventSource.onerror = () => console.log("SSE stream error");
}

// =========================
// 5) MICRO VOLUME → ANIMATION BARS
// =========================
function startAudioLevelListener() {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        audioContext = new AudioContext();
        analyser = audioContext.createAnalyser();
        microphoneStream = audioContext.createMediaStreamSource(stream);

        analyser.fftSize = 256;
        microphoneStream.connect(analyser);

        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        function update() {
            if (!sessionActive) return;
            analyser.getByteFrequencyData(dataArray);

            const volume = dataArray.reduce((a, b) => a + b) / dataArray.length;

            // Map volume → bar height
            const scaled = Math.min(100, Math.max(5, volume / 2));

            voiceAnim.style.transform = `scaleY(${scaled / 30})`;

            requestAnimationFrame(update);
        }
        update();
    });
}

function stopAudioLevelListener() {
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
}

// =========================
// 6) ANIMATION STATE
// =========================
function startVoiceAnimation() {
    voiceAnim.classList.remove("hidden");
}

function stopVoiceAnimation() {
    voiceAnim.classList.add("hidden");
    voiceAnim.style.transform = "scaleY(1)";
}

// =========================
// 7) UPDATE SUMMARY
// =========================
async function updateSummary(fullText) {
    try {
        const res = await fetch("/summary/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: fullText })
        });

        const data = await res.json();
        const summary = data.summary;
        if (!summary) return;

        document.getElementById("summary-title").textContent =
            summary.title || "";

        document.getElementById("summary-subtitle").textContent =
            summary.subtitle || "";

        const ul = document.getElementById("summary-list");
        ul.innerHTML = "";

        (summary.bullets || []).forEach(b => {
            const li = document.createElement("li");
            li.textContent = b;
            ul.appendChild(li);
        });

    } catch (err) {
        console.log("Résumé error:", err);
    }
}

// =========================
// 8) Placeholder export
// =========================
btnDownload.onclick = () => alert("Export PDF en cours d’implémentation.");
