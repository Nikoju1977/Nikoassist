# NikoAssist Web — Studio Niko

Cette interface **web/** est un complément **fonctionnel et autonome** du projet NikoAssist, créé pour réparer la configuration Vercel qui pointait vers un répertoire inexistant.

## Fonctionnalités vérifiables

- Consultation sourcée de Wikipédia (fr) via proxy HTTPS Vercel ; toute réponse renvoie à un article.
- Météo actuelle via géocodage et prévisions Open-Meteo, sur saisie manuelle de la ville (aucun GPS ni géolocalisation automatique).
- Calculatrice arithmétique sans \`eval\`.
- Liste de tâches stockée localement et export JSON (pas de synchronisation distante).
- Dictée vocale (si compatible et autorisée par le navigateur), synthèse vocale et PWA.

**Important :** l'outil web n'exécute **pas** les sous-agents de l'orchestrateur Python \`agent_team\`. Pour les activer, il faudra un backend sécurisé, une gestion des autorisations Sentinel et des identifiants API conservés sur serveur. L'absence de ces services n'est jamais dissimulée.

## Publication

- Vercel project \`nikoassist-pwa\`
- Root Directory : \`web\`
- Framework : Other / null
- No \`npm install\` ni build command requis ; endpoints disponibles sous \`/api/assistant\` et \`/api/health\`.
- Aucun jeton API n'est intégré au navigateur ou dans le dépôt.

## Sécurité

La route \`api/assistant.js\` ne contacte que deux services publics : Wikipédia et Open-Meteo. Les utilisateurs ne peuvent pas fournir d'URL arbitraire. Les entrées sont limitées en longueur, les requêtes ont un délai d'expiration et ne stockent aucune conversation. Les informations médicales confidentielles, les clés privées et les données de paiement n'ont pas leur place dans cette interface.

## Tests

\`node web/check.cjs\` vérifie la syntaxe JavaScript et la présence des contrôles. Les tests d'intégration réseau et mobile doivent ensuite être exécutés contre le déploiement Vercel.


## Import depuis Studio Niko Hub

L'utilisateur choisit **Envoyer les tâches à Nikoassist** dans l'atelier du Hub. Seuls le nom du projet et jusqu'à 20 titres de tâches sont encodés dans le fragment \`#handoff=...\` (pas dans la requête HTTP) et transmis à l'onglet Nikoassist. Un second consentement explicite est demandé côté Nikoassist. Le fragment est supprimé de la barre d'adresse avant le dialogue. Les tâches importées sont sauvegardées **uniquement dans le navigateur Nikoassist** et les doublons sont évités. Aucun média, donnée de santé ni clé API ne doit être partagé par ce mécanisme.


## Import et restauration de tâches (JSON, sans compte)

Depuis « Mes tâches », utilisez **Exporter JSON** pour enregistrer un fichier `nikoassist-taches.json`. Sur un autre navigateur ou téléphone, ouvrez NikoAssist, sélectionnez **Importer JSON**, choisissez ce fichier dans votre gestionnaire de fichiers, puis confirmez.

- Seul le format d'export `nikoassist-tasks-v1` est accepté (fichier de 256 Ko maximum, 200 tâches maximum).
- **La liste existante n'est jamais remplacée** : les titres identiques sont ignorés, et les tâches importées reçoivent de nouveaux identifiants locaux. L'état terminé/non terminé est conservé.
- Aucun serveur, compte, accès à la messagerie ni service d'IA n'est utilisé pour l'import. Les titres peuvent contenir des informations personnelles : la sauvegarde JSON est en clair et doit être conservée dans un espace privé.
- Un export ne synchronise pas les appareils automatiquement : l'utilisateur transfère volontairement le fichier.
- Le bouton d'import, les messages de confirmation et les retours d'erreur sont conçus pour PC, Android et iPhone, mais les tests sur téléphones physiques restent à effectuer.

**Preuves techniques :** `node web/check.cjs` exerce la validation et la fusion des sauvegardes ; `.github/workflows/verify.yml` l'exécute à chaque commit sur `main`. Cela ne vaut pas validation sur appareil physique.

## Installation PWA (Android, iPhone, ordinateur)

L'application dispose d'icônes PNG 192×192 et 512×512, d'un service worker pour les ressources statiques et d'un bouton « Installer la PWA ». Android Chrome : bouton Installer, ou menu ⋮ → Installer l'application / Ajouter à l'écran d'accueil. iPhone Safari : Partager → Sur l'écran d'accueil. Chrome/Edge desktop : icône d'installation dans la barre d'adresse ou menu du navigateur.

Une PWA n'est pas un APK signé. Hors ligne : interface et tâches locales accessibles si l'application a déjà été chargée ; recherche Wikipédia et météo nécessitent Internet.

## Audit de la version publique (lecture seule)

`node web/production-audit.cjs` effectue des requêtes HTTP publiques contre `https://nikoassist-pwa.vercel.app/`, sans identifiants et sans modification des tâches. Il vérifie le HTML d'accueil, le service worker `nikoassist-web-v7-network-first`, la logique d'aide mobile, le module de sauvegarde, le CSS et l'API de santé.

La CI exécute également `node web/production-audit.test.cjs` avec de fausses réponses réseau, puis l'audit réel. Le résultat figure dans le **résumé GitHub Actions** et dans un fichier JSON joint à l'exécution (`nikoassist-production-http-audit`). Tant que l'ancienne version est en ligne, le rapport signale `outdated_or_incomplete` : ce constat **n'empêche pas les tests du code source de réussir**. L'option `NIKOASSIST_AUDIT_STRICT=1` permet à un opérateur d'en faire volontairement un test bloquant.

Les statuts `http_verified`, `outdated_or_incomplete` et `partially_unreachable` portent exclusivement sur les réponses HTTP. Ils ne prouvent ni l'affichage iPhone/Android physique, ni l'exécution d'un moteur Python, ni les appels aux services IA externes. Vérifier indépendamment `target=production`, le SHA exact, puis la navigation et l'installation PWA.
