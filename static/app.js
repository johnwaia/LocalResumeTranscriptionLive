// static/app.js
document.addEventListener("DOMContentLoaded", () => {
  // --- Références DOM --- //
  const partialEl = document.getElementById("partial");
  const transcriptEl = document.getElementById("transcript");
  const summaryTitleEl = document.getElementById("summary-title");
  const summarySubtitleEl = document.getElementById("summary-subtitle");
  const summaryListEl = document.getElementById("summary-list");
  const startBtn = document.getElementById("start-session");
  const stopBtn = document.getElementById("stop-session");

  // --- État côté front --- //
  let currentTranscript = "";
  let structuredSummary = {
    title: "",
    subtitle: "",
    bullets: [],
  };
  let currentTags = []; // [{label, type}, ...]

  // --- Helpers pour surligner les mots-clés --- //
  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function escapeRegExp(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function highlightWithTags(text) {
    if (!text) return "";
    let html = escapeHtml(text);

    currentTags.forEach((tag) => {
      const label = tag.label || "";
      if (!label) return;

      const pattern = new RegExp("\\b(" + escapeRegExp(label) + ")\\b", "gi");
      html = html.replace(
        pattern,
        '<span class="keyword-span">$1</span>'
      );
    });

    return html;
  }

  // --- Fonctions de rendu --- //
  function renderTranscript() {
    if (!transcriptEl) return;
    transcriptEl.innerHTML = highlightWithTags(currentTranscript);
  }

  function renderStructuredSummary() {
    if (!summaryTitleEl || !summarySubtitleEl || !summaryListEl) return;

    const title = structuredSummary.title || "Résumé de la conversation";
    const subtitle = structuredSummary.subtitle || "";
    const bullets = structuredSummary.bullets || [];

    summaryTitleEl.innerHTML = highlightWithTags(title);
    summarySubtitleEl.innerHTML = highlightWithTags(subtitle);

    summaryListEl.innerHTML = "";
    bullets.forEach((b) => {
      const li = document.createElement("li");
      li.innerHTML = highlightWithTags(b);
      summaryListEl.appendChild(li);
    });
  }

  // --- SSE : événements backend --- //
  const source = new EventSource("/stream");

  source.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      if (data.type === "partial") {
        if (partialEl) partialEl.textContent = data.text || "";

      } else if (data.type === "transcript_live" || data.type === "transcript") {
        currentTranscript = data.text || "";
        renderTranscript();

      } else if (data.type === "summary_structured") {
        structuredSummary = data.summary || structuredSummary;
        renderStructuredSummary();

      } else if (data.type === "tags") {
        currentTags = data.tags || [];
        // re-render transcript + summary avec les nouveaux mots-clés
        renderTranscript();
        renderStructuredSummary();

      } else if (data.type === "session") {
        if (data.status === "started") {
          if (partialEl) partialEl.textContent = "";
          currentTranscript = "";
          structuredSummary = { title: "", subtitle: "", bullets: [] };
          currentTags = [];
          renderTranscript();
          renderStructuredSummary();
        }
      }
    } catch (e) {
      console.error("Erreur parsing event:", e);
    }
  };

  source.onerror = (err) => {
    console.error("Erreur EventSource:", err);
  };

  // --- Boutons start / stop --- //
  if (startBtn) {
    startBtn.addEventListener("click", async () => {
      try {
        await fetch("/session/start", { method: "POST" });
      } catch (e) {
        console.error("Erreur start session:", e);
      }
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener("click", async () => {
      try {
        await fetch("/session/stop", { method: "POST" });
      } catch (e) {
        console.error("Erreur stop session:", e);
      }
    });
  }
});
