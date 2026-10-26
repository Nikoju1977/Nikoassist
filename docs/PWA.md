# NikoAssist — PWA Android, iOS et ordinateur

NikoAssist inclut déjà une interface web React/Vite compatible **Progressive Web App (PWA)** dans la branche [source-nikoassist](https://github.com/Nikoju1977/Nikoassist/tree/source-nikoassist/web).

## Générer l'archive PWA

Dans GitHub, ouvrir **Actions → NikoAssist PWA — build and checks → Run workflow** sur `main`. Après un build réussi, télécharger l'artifact **NikoAssist-PWA-web**, qui contient `NikoAssist-PWA.zip` et une empreinte SHA-256. Le workflow lance les contrôles ESLint, TypeScript, Vitest et vérifie les fichiers manifest, service worker et offline.

En local, depuis `source-nikoassist` :

```bash
cd web
npm ci
npm run check
npm run build
```

La compilation est générée dans `nanomuse/server/static/`.

## Installer sur un appareil

1. Déployer le serveur nanoMuse/NikoAssist et sa PWA sous une **URL HTTPS** de confiance. L'archive statique seule ne fournit **pas** le moteur IA ni les endpoints `/api` et `/ws` ; un hébergement statique isolé ne permet pas d'utiliser le chat.
2. **Android / Chrome** : ouvrir l'URL HTTPS, menu → *Installer l'application*.
3. **iPhone / Safari** : ouvrir l'URL HTTPS, bouton *Partager* → *Sur l'écran d'accueil* → *Ajouter*.
4. **Ordinateur** : utiliser le bouton d'installation du navigateur compatible.

## Sécurité

Le service worker ne doit jamais mettre en cache les réponses `/api`, les messages privés, les identifiants ou les clés Mistral. Il fournit uniquement un écran de secours hors ligne et met en cache les assets publics versionnés. Une PWA **ne peut pas remplacer** les permissions système d'une application native pour toutes les actions d'agent sur Android/iOS.

## Limites

La présence d'un manifest et d'un service worker ne prouve pas la compatibilité sur tous les navigateurs. Le workflow compile et vérifie le frontend ; l'installation sur appareils réels et l'accès à un backend HTTPS opérationnel doivent encore être testés. Aucune URL publique de déploiement n'est configurée par ce workflow.
