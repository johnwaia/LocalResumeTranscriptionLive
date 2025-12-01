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


// ---- Boutons ----

document.getElementById("start-session").disabled = true;

// Choix du modèle => active le bouton démarrer
document.getElementById("model-select").onchange = async (e) => {
  await fetch("/model/set", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: e.target.value }),
  });

  console.log("🟢 Modèle prêt → vous pouvez démarrer");
  document.getElementById("start-session").disabled = false;
};

// 🚀 Bouton Démarrer Session (MANQUANT AVANT)
document.getElementById("start-session").onclick = async () => {
  await fetch("/session/start", { method: "POST" });
  console.log("🎤 Session démarrée !");
};

// Bouton Stop Session
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
