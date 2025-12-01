const source = new EventSource("/stream");

const partialBox = document.getElementById("partial");
const transcriptBox = document.getElementById("transcript");
const titleBox = document.getElementById("summary-title");
const subtitleBox = document.getElementById("summary-subtitle");
const listBox = document.getElementById("summary-list");

source.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "partial") partialBox.innerText = data.text;
  if (data.type === "transcript") transcriptBox.innerText = data.text;

  if (data.type === "summary_structured") {
    const s = data.summary;
    titleBox.innerText = s.title;
    subtitleBox.innerText = s.subtitle;
    listBox.innerHTML = "";
    s.bullets.forEach(b => {
      const li = document.createElement("li");
      li.innerText = b;
      listBox.appendChild(li);
    });
  }
};


// --------- MODAL LOGIQUE ---------
const modal = document.getElementById("model-modal");
const confirmBtn = document.getElementById("confirm-model");
const modalSelect = document.getElementById("modal-model-select");

// Empêche l'utilisateur de démarrer avant choix modèle
document.getElementById("start-session").disabled = true;

// User valide modèle
confirmBtn.onclick = async () => {
  const model = modalSelect.value;

  await fetch("/model/set", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model }),
  });

  console.log(`🟢 Modèle sélectionné: ${model}`);

  modal.style.display = "none";  
  document.getElementById("start-session").disabled = false;
};


// --------- BOUTONS ---------

document.getElementById("start-session").onclick = async () => {
  await fetch("/session/start", { method: "POST" });
  console.log("🎤 Session démarrée !");
};

document.getElementById("stop-session").onclick = async () => {
  await fetch("/session/stop", { method: "POST" });
  console.log("🛑 Session stoppée !");
};


// ---- Download résumé ----
document.getElementById("download-summary").onclick = () => {
  const text =
    `${titleBox.innerText}\n${subtitleBox.innerText}\n\n` +
    [...listBox.querySelectorAll("li")].map(li => "- " + li.innerText).join("\n");

  const blob = new Blob([text], { type: "text/plain" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "resume.txt";
  link.click();
};
