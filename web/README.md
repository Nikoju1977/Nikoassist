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
