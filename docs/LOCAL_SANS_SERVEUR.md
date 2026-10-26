# NikoAssist Local — application utilisable sans serveur IA

**Objectif : zéro abonnement, zéro clé API et aucune machine serveur dédiée.**

La PWA propose désormais un véritable mode de **conversation avec un modèle open source exécuté dans le navigateur du téléphone**, et non un simple écran de démonstration.

- Application : https://nikoassist-pwa.vercel.app/local.html
- Code : branche `source-nikoassist`, fichiers `web/public/local.html`, `local-app.js`, `local-worker.js`
- Interface complète nanoMuse (nécessite un serveur) : https://nikoassist-pwa.vercel.app/

## Installation gratuite

1. Ouvrir l'application HTTPS dans Chrome (Android) ou Safari (iOS récent).
2. Choisir un modèle : **SmolLM2-135M-Instruct** pour les téléphones plus modestes (environ **181 Mo** de poids de modèle) ou **Qwen2.5-0.5B-Instruct** pour une meilleure qualité en français (environ **786 Mo** de poids q4). Les fichiers auxiliaires et le moteur occupent de l'espace supplémentaire.
3. Appuyer sur « Charger l'IA » et accepter le téléchargement via une connexion Wi-Fi.
4. Une fois le modèle chargé, discuter directement avec NikoAssist. L'inférence est faite sur l'appareil, avec accélération WebGPU si disponible, sinon avec WebAssembly/CPU.
5. Dans Chrome, choisir *Installer l'application* ; sur iOS Safari, *Partager → Sur l'écran d'accueil*.

L'historique de conversation est conservé dans le stockage local du navigateur ; le bouton « Effacer » le supprime. **Ne pas saisir de secrets sensibles** : l'historique dans `localStorage` n'est pas un coffre chiffré. Le programme ne transmet pas les conversations à une API IA ; le moteur JavaScript vient d'un CDN tiers et les poids du modèle sont téléchargés depuis Hugging Face.

## Coût et limites réelles

L'application et les modèles sont gratuits, sans compte Mistral ni achat de tokens. L'hébergement actuel utilise un plan gratuit Vercel **dans ses limites et selon ses conditions d'usage**. L'utilisation de votre réseau mobile peut entraîner des frais auprès de l'opérateur si vous n'avez pas de données incluses.

Ce mode est une **première version de chat local** : pas d'automatisation du téléphone, pas de commande vocale JARVIS, pas de navigation Web réelle, pas de synchronisation entre appareils et pas de moteur multi-agent nanoMuse. Les réponses des petits modèles sont moins fiables que celles des grands modèles distants.

Le premier téléchargement nécessite Internet. Les poids du modèle et le runtime sont mis en cache par Transformers.js lorsque le navigateur l'autorise ; le service worker met en cache l'interface publique. **Le fonctionnement complètement hors ligne n'est pas garanti** : les navigateurs peuvent vider leur cache ou bloquer les fichiers externes. En cas de blocage, utiliser le modèle léger, libérer de la mémoire, relancer Chrome ou redémarrer l'appareil.

## Technique et licences

- [Transformers.js](https://github.com/huggingface/transformers.js) (runtime gratuit dans le navigateur), chargé depuis le CDN jsDelivr avec version figée.
- [SmolLM2-135M-Instruct-ONNX](https://huggingface.co/onnx-community/SmolLM2-135M-Instruct-ONNX).
- [Qwen2.5-0.5B-Instruct ONNX](https://huggingface.co/onnx-community/Qwen2.5-0.5B-Instruct).
- Aucun endpoint `/api` ou `/ws` n'est appelé en mode local.
- Aucun jeton Mistral, mot de passe, coffre serveur ou clé Apple n'est requis.

Cette solution n'exige pas de VM ni de conteneur allumé 24 heures sur 24. Elle n'impose aucun abonnement. Les builds et la compatibilité des différents navigateurs doivent continuer d'être testés sur appareils physiques.
