/* NikoAssist Local — on-device inference worker.
 * No API tokens, server, cloud inference or conversation uploads.
 * Dependencies and public model weights are downloaded on first use.
 * Untrusted output is rendered as text, never as HTML.
 */
import { env, pipeline } from "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.1";

const MODELS = Object.freeze({
  compact: "onnx-community/SmolLM2-135M-Instruct-ONNX",
  quality: "onnx-community/Qwen2.5-0.5B-Instruct",
});
env.useBrowserCache = true;
env.useWasmCache = true;
env.allowLocalModels = false;

let engine = null;
let activeModel = "";
let activeDevice = "";
let working = false;

const send = (type, payload = {}) => self.postMessage({ type, ...payload });

async function load(model) {
  if (!(model in MODELS)) throw new Error("Modèle non reconnu.");
  if (engine && activeModel === model) return;
  send("status", { message: "Préparation du modèle local…", progress: null });
  const options = {
    dtype: "q4",
    progress_callback: (item) => {
      if (!item || typeof item !== "object") return;
      if (item.status === "progress" && Number.isFinite(item.progress)) {
        send("status", {
          message: "Téléchargement des fichiers du modèle…",
          progress: Math.max(0, Math.min(100, item.progress)),
        });
      } else if (item.status === "initiate") {
        send("status", { message: "Chargement du modèle dans le navigateur…", progress: null });
      }
    },
  };
  // WebGPU is faster if supported; WASM is compatible with more phones.
  const tryGpu = Boolean(self.navigator?.gpu);
  let loaded;
  let device;
  if (tryGpu) {
    try {
      loaded = await pipeline("text-generation", MODELS[model], { ...options, device: "webgpu" });
      device = "GPU";
    } catch (gpuError) {
      send("status", { message: "Accélération GPU indisponible, essai en mode CPU…", progress: null });
    }
  }
  if (!loaded) {
    loaded = await pipeline("text-generation", MODELS[model], { ...options, device: "wasm" });
    device = "CPU";
  }
  engine = loaded;
  activeModel = model;
  activeDevice = device;
  send("ready", { model, device });
}

function validatedHistory(value) {
  if (!Array.isArray(value)) throw new Error("Historique invalide.");
  const history = value.slice(-12);
  if (history.some((msg) => !msg || !["user", "assistant"].includes(msg.role) || typeof msg.content !== "string" || msg.content.length > 2500)) {
    throw new Error("Un message est invalide.");
  }
  return history.map((msg) => ({ role: msg.role, content: msg.content }));
}

self.addEventListener("message", async ({ data }) => {
  if (!data || !["load", "generate"].includes(data.type) || working) return;
  working = true;
  try {
    const model = data.model;
    await load(model);
    if (data.type === "generate") {
      const history = validatedHistory(data.history);
      if (!history.length || history.at(-1).role !== "user") throw new Error("Message manquant.");
      send("status", { message: "NikoAssist réfléchit directement sur cet appareil…", progress: null });
      const prompt = [
        { role: "system", content: "Tu es NikoAssist Local, un assistant francophone bienveillant. Réponds clairement, brièvement et en français. Ne prétends pas disposer d'un accès Internet, d'outils, d'applications ou d'un serveur. Si tu ne sais pas, dis-le." },
        ...history,
      ];
      const response = await engine(prompt, {
        max_new_tokens: model === "compact" ? 110 : 180,
        do_sample: true,
        temperature: 0.6,
        top_p: 0.9,
      });
      const generated = response?.[0]?.generated_text;
      let answer;
      if (Array.isArray(generated)) answer = generated.at(-1)?.content;
      else if (typeof generated === "string") answer = generated;
      if (Array.isArray(answer)) answer = answer.map((x) => x?.text ?? "").join("");
      if (typeof answer !== "string" || !answer.trim()) throw new Error("Aucune réponse du modèle.");
      send("reply", { text: answer.slice(0, 6000).trim(), device: activeDevice });
    }
  } catch (error) {
    send("error", {
      message: error instanceof Error ? error.message.slice(0, 220) : "Le moteur local n'a pas pu démarrer.",
    });
  } finally {
    working = false;
  }
});
