import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { markDesktopShell } from "./desktop";
import { applyLang } from "./i18n";
import { PwaInstallPrompt } from "./components/PwaInstallPrompt";
import { registerWorker } from "./push";
import { StoreProvider } from "./store";
import { applyTheme } from "./theme";
import "./index.css";

applyLang();
applyTheme();
markDesktopShell();
// Register the same worker used by Web Push, even when push is disabled.
// The service worker caches only public, hashed static files and a generic offline screen.
void registerWorker();
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <StoreProvider>
      <App />
      <PwaInstallPrompt />
    </StoreProvider>
  </React.StrictMode>,
);
