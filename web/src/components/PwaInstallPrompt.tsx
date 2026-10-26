import { Download, Share2, X } from "lucide-react";
import { useEffect, useState } from "react";

type InstallEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
};

const DISMISS_KEY = "nikoassist_pwa_install_dismissed_v1";

function installed(): boolean {
  return window.matchMedia("(display-mode: standalone)").matches ||
    Boolean((navigator as Navigator & { standalone?: boolean }).standalone);
}

function iosSafari(): boolean {
  const ua = navigator.userAgent;
  const ios = /iPhone|iPad|iPod/i.test(ua) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  return ios && /Safari/i.test(ua) && !/CriOS|FxiOS|EdgiOS|OPiOS/i.test(ua);
}

/** Optional, dismissible native install affordance; no push permission requested. */
export function PwaInstallPrompt() {
  const [event, setEvent] = useState<InstallEvent | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);
  const [dismissed, setDismissed] = useState(true);
  const [showHelp, setShowHelp] = useState(false);
  const onIOS = iosSafari();

  useEffect(() => {
    setIsInstalled(installed());
    try { setDismissed(localStorage.getItem(DISMISS_KEY) === "1"); }
    catch { setDismissed(false); }
    const onPrompt = (e: Event) => {
      e.preventDefault();
      setEvent(e as InstallEvent);
    };
    const onInstalled = () => { setEvent(null); setIsInstalled(true); };
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  const dismiss = () => {
    setDismissed(true);
    try { localStorage.setItem(DISMISS_KEY, "1"); } catch { /* optional */ }
  };

  if (dismissed || isInstalled || (!event && !onIOS)) return null;
  const install = async () => {
    if (!event) {
      setShowHelp(true);
      return;
    }
    try {
      await event.prompt();
      const choice = await event.userChoice;
      if (choice.outcome === "accepted") setIsInstalled(true);
    } finally {
      setEvent(null);
    }
  };

  return (
    <aside
      aria-label="Installer NikoAssist"
      className="fixed bottom-[calc(env(safe-area-inset-bottom)+5.5rem)] right-3 z-[90] w-[min(23rem,calc(100vw-1.5rem))] rounded-2xl border border-border bg-bg p-4 shadow-xl"
    >
      <button type="button" aria-label="Fermer la proposition d'installation"
        onClick={dismiss} className="absolute right-3 top-3 rounded-lg p-1 text-muted">
        <X size={18} />
      </button>
      <div className="flex items-start gap-3 pr-5">
        <img src="/icon.svg" alt="" width={48} height={48} className="rounded-xl" />
        <div>
          <p className="text-sm font-semibold">Installer NikoAssist</p>
          <p className="mt-1 text-xs text-muted">Accès rapide depuis l'écran d'accueil, sans App Store.</p>
        </div>
      </div>
      {showHelp ? (
        <p className="mt-3 text-sm">
          Dans Safari : touche <strong>Partager</strong> puis
          <strong> Sur l'écran d'accueil</strong>, puis <strong>Ajouter</strong>.
        </p>
      ) : null}
      <button type="button" onClick={() => void install()}
        className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-[color:var(--accent,#3be2d0)] px-4 py-2.5 text-sm font-semibold text-[color:var(--bg,#10192b)]">
        {onIOS && !event ? <Share2 size={16} /> : <Download size={16} />}
        {onIOS && !event ? "Instructions iPhone / iPad" : "Installer"}
      </button>
    </aside>
  );
}
