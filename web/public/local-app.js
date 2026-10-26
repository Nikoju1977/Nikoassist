/* NikoAssist Local: privacy-first browser-only chat interface. */
const HISTORY_KEY = "nikoassist_local_history_v1";
const MODEL_KEY = "nikoassist_local_model_v1";
const $ = (id) => document.getElementById(id);
const chat = $("chat");
const form = $("chat-form");
const input = $("message");
const sendButton = $("send");
const loadButton = $("load");
const clearButton = $("clear");
const selector = $("model");
const status = $("status");
const progress = $("progress");

function safeHistory() {
  try {
    const value = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    if (!Array.isArray(value)) return [];
    return value.filter((message) => message && ["user", "assistant"].includes(message.role) &&
      typeof message.content === "string").slice(-24).map((message) => ({
        role: message.role, content: message.content.slice(0, 2500),
      }));
  } catch {
    return [];
  }
}

const models = ["compact", "quality"];
let history = safeHistory();
let ready = false;
let busy = false;
let worker = null;

function persist() {
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(-24))); }
  catch { setStatus("Stockage local saturé : les derniers messages risquent de ne pas être conservés.", true); }
}

function setStatus(message, error = false) {
  status.textContent = message;
  status.classList.toggle("error", error);
}

function setBusy(value) {
  busy = value;
  loadButton.disabled = value;
  selector.disabled = value;
  sendButton.disabled = value || !ready;
  input.disabled = value;
}

function setProgress(value) {
  if (typeof value !== "number") {
    progress.classList.remove("visible");
    return;
  }
  progress.classList.add("visible");
  progress.value = Math.max(0, Math.min(100, value));
}

function addMessage(role, content) {
  const item = document.createElement("article");
  item.className = "message " + (role === "user" ? "user" : "assistant");
  item.textContent = content;
  chat.append(item);
  chat.scrollTop = chat.scrollHeight;
}

function render() {
  chat.replaceChildren();
  if (!history.length) {
    const welcome = document.createElement("div");
    welcome.className = "welcome";
    const title = document.createElement("h2");
    title.textContent = "NikoAssist est prêt à discuter";
    const desc = document.createElement("p");
    desc.textContent = "Chargez un modèle libre pour commencer. Vos messages resteront sur cet appareil.";
    welcome.append(title, desc);
    chat.append(welcome);
  } else {
    for (const message of history) addMessage(message.role, message.content);
  }
}

function initializeWorker() {
  if (worker) worker.terminate();
  ready = false;
  setBusy(false);
  sendButton.disabled = true;
  setProgress(null);
  worker = new Worker("/local-worker.js", { type: "module" });
  worker.addEventListener("message", ({ data }) => {
    if (!data || typeof data.type !== "string") return;
    if (data.type === "status") {
      setStatus(data.message || "Chargement local…");
      setProgress(data.progress);
    }
    if (data.type === "ready") {
      ready = true;
      setBusy(false);
      setProgress(null);
      setStatus("Modèle chargé (" + data.device + "). Vous pouvez écrire à NikoAssist.");
    }
    if (data.type === "reply") {
      history.push({ role: "assistant", content: data.text });
      history = history.slice(-24);
      persist();
      addMessage("assistant", data.text);
      setBusy(false);
      setStatus("Réponse créée localement sur votre appareil (" + data.device + ").");
      input.focus();
    }
    if (data.type === "error") {
      setBusy(false);
      setProgress(null);
      setStatus("Erreur du modèle : " + (data.message || "échec inconnu") +
        ". Essayez le modèle léger ou libérez de la mémoire.", true);
    }
  });
  worker.addEventListener("error", () => {
    setBusy(false);
    ready = false;
    setProgress(null);
    sendButton.disabled = true;
    setStatus("Impossible de charger le moteur local. Vérifiez le réseau pour le premier téléchargement et la mémoire disponible.", true);
  });
}

try {
  const saved = localStorage.getItem(MODEL_KEY);
  if (models.includes(saved)) selector.value = saved;
} catch { /* private mode */ }
render();
initializeWorker();

selector.addEventListener("change", () => {
  if (busy) return;
  try { localStorage.setItem(MODEL_KEY, selector.value); } catch { /* optional */ }
  initializeWorker();
  setStatus("Modèle changé. Appuyez sur « Charger l’IA ».");
});

loadButton.addEventListener("click", () => {
  if (busy) return;
  setBusy(true);
  setStatus("Chargement en cours… Le premier téléchargement peut être volumineux.");
  worker.postMessage({ type: "load", model: selector.value });
});

clearButton.addEventListener("click", () => {
  if (busy) return;
  if (history.length && !window.confirm("Effacer toutes les conversations enregistrées sur cet appareil ?")) return;
  history = [];
  persist();
  render();
  setStatus(ready ? "Historique effacé. Modèle local prêt." : "Historique effacé. Chargez un modèle.");
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const content = input.value.trim();
  if (!ready || busy || !content || content.length > 2000) return;
  const message = { role: "user", content };
  history.push(message);
  history = history.slice(-24);
  persist();
  addMessage("user", content);
  input.value = "";
  setBusy(true);
  setStatus("Calcul local en cours… Cela peut être lent sur un téléphone.");
  worker.postMessage({ type: "generate", model: selector.value, history: history.slice(-12) });
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});

if ("serviceWorker" in navigator && window.isSecureContext) {
  navigator.serviceWorker.register("/sw.js").catch(() => { /* optional */ });
}
