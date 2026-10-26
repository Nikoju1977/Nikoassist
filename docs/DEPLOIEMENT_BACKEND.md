# Relier NikoAssist PWA à son moteur IA (nanoMuse)

La PWA publique `https://nikoassist-pwa.vercel.app` est un **frontend statique**. Les conversations, la mémoire, les outils, la supervision Sentinel et les WebSockets nécessitent un processus nanoMuse **toujours actif** et des volumes persistants. Une compilation Vercel réussie ne déploie pas ce processus. L'absence de `/api/health` sur le site statique est donc attendue tant que ce backend n'a pas été installé.

**Ne pas coller la clé Mistral dans la PWA, dans GitHub ou dans une requête d'assistance.**

## Hébergement recommandé

Utiliser une VM Linux ou un hébergeur de conteneurs prenant en charge :
- un serveur HTTP **avec WebSockets persistants** ;
- des volumes persistants pour `/data` (coffre, identité et historique) et `/workspace` ;
- un domaine et TLS/HTTPS via reverse proxy (Caddy, Nginx ou équivalent) ;
- une gestion privée des variables d'environnement et des sauvegardes.

Une fonction serverless Vercel standard ne remplace pas à elle seule le serveur nanoMuse, qui attend des connexions WebSocket durables et une mémoire persistante.

## Installation du backend sur un serveur Linux

Commandes indicatives à lancer **sur la VM**, après installation de Docker et création d'un domaine pointant vers la VM :

```bash
git clone --branch source-nikoassist --recurse-submodules https://github.com/Nikoju1977/Nikoassist.git
cd Nikoassist
umask 077
cp .env.example .env
mkdir -p workspace
sudo chown 1000:1000 workspace
```

Éditer `.env` *sur le serveur*, sans y inscrire de clé Mistral en clair. Ajouter ou mettre à jour :

```dotenv
NANOMUSE_LLM_PROVIDER=mistral
NANOMUSE_LLM_MODEL=mistral-small-latest
NANOMUSE_LLM_BASE_URL=https://api.mistral.ai/v1
NANOMUSE_LLM_API_KEY={{vault:MISTRAL_API_KEY}}
NANOMUSE_SERVER_TOKEN=REMPLACER_PAR_UN_JETON_LONG_ALEATOIRE
```

Le jeton d'accès doit être généré localement avec un générateur cryptographique (par exemple `openssl rand -hex 32`) et rester privé. Ne jamais utiliser la valeur d'exemple en production. Protéger `.env` (permissions 0600) et ne pas le committer.

```bash
docker build -t nikoassist-runtime .
docker volume create nikoassist-data
docker run -d --name nikoassist --restart unless-stopped \
  --env-file .env \
  -p 127.0.0.1:8787:8787 \
  -v nikoassist-data:/data \
  -v "$PWD/workspace:/workspace" \
  nikoassist-runtime
```

Si le conteneur démarre, enregistrer la **vraie clé Mistral de l'utilisateur** directement dans le coffre chiffré, avec saisie interactive :

```bash
docker exec -it nikoassist nanomuse vault set MISTRAL_API_KEY
docker restart nikoassist
```

Cette commande ne demande pas de passer la clé dans un argument de processus. Elle est chiffrée dans le volume persistant `/data` avec le coffre fourni par nanoMuse.

## Exposition HTTPS et WebSocket

Installer Caddy ou un proxy équivalent sur la VM ; exemple de Caddyfile **en remplaçant le domaine par le vôtre**, une fois son DNS pointé sur la VM :

```caddyfile
assistant.exemple.fr {
    encode zstd gzip
    reverse_proxy 127.0.0.1:8787
}
```

Caddy gère les WebSockets et le certificat TLS. Ne jamais exposer directement le port 8787 au réseau public sans chiffrement.

Vérifier ensuite :

```bash
curl --fail --show-error https://assistant.exemple.fr/api/health
```

Ouvrir ensuite `https://assistant.exemple.fr/` dans le navigateur mobile : le **serveur nanoMuse sert lui-même la PWA**, et `/api` et `/ws` fonctionnent sous la même origine. Utiliser le jeton `NANOMUSE_SERVER_TOKEN` lors de l'authentification ; ne jamais le partager par message ou dans une URL publiée.

**Important :** les WebSockets de nanoMuse ne sont pas raccordés automatiquement au projet Vercel statique. L'option la plus fiable est d'installer la PWA depuis le **domaine HTTPS du backend**. L'ancienne PWA Vercel peut rester une page informative, mais ne doit pas prétendre fournir un chat IA avant qu'un backend ne soit associé à la même origine.

## Critères de recette

- `/api/health` retourne HTTP 200 avec `ok: true` sur l'URL HTTPS du backend.
- Une connexion WebSocket `/ws` est établie par le navigateur authentifié.
- La sélection du modèle et le coffre Mistral fonctionnent après redémarrage, avec une **clé réelle renseignée localement**.
- Les données `/data` persistent après remplacement du conteneur.
- Les outils sensibles restent soumis à Sentinel ; aucune permission d'appareil n'est activée par défaut.
- Les essais sur Android et iOS sont validés avant d'annoncer un assistant pleinement opérationnel.

Aucun hébergeur de backend n'a été provisionné automatiquement par ces instructions. Un domaine, une VM et la clé personnelle Mistral restent nécessaires.
