# Mistral AI + coffre chiffré — NikoAssist / Niko Studio Design

NikoAssist utilise le fournisseur `mistral` et le **coffre natif** de nanoMuse. Aucun SDK Mistral supplémentaire n'est requis : nanoMuse utilise son client de chat compatible OpenAI vers `https://api.mistral.ai/v1`.

## 1. Obtenir la clé

Depuis votre propre compte Mistral Studio, ouvrez <https://console.mistral.ai/api-keys> et créez une **clé API d'inférence**. Copiez-la une seule fois dans un gestionnaire de secrets. **Ne la collez pas dans ChatGPT, GitHub, un ticket ou un canal de discussion.**

## 2. Préparer NikoAssist

Depuis le dossier du dépôt NikoAssist :

```bash
# nanoMuse doit déjà exister dans ../nanoMuse
python scripts/install_nikoassist.py --target ../nanoMuse
python scripts/configure_mistral.py --target ../nanoMuse
```

La deuxième commande vous demande la clé **sans l'afficher dans le terminal** (`getpass`). Ne mettez pas la clé dans la ligne de commande : les arguments des processus peuvent être visibles par d'autres programmes.

Par défaut, le modèle est `mistral-small-latest` (adapter avec `--model NOM_MODELE`). Un modèle donné doit être accessible à votre compte Mistral.

Si nanoMuse utilise un autre dossier de données, passez `--data-dir DOSSIER` ; s'il utilise un autre fichier TOML, passez `--config CONFIG_TOML`.

## 3. Où se trouve le secret ?

- `<data_dir>/vault.enc` : les secrets chiffrés avec le mécanisme **Fernet** déjà fourni par nanoMuse.
- `<data_dir>/vault.key` : clé de chiffrement distincte des jetons Mistral, à protéger et sauvegarder séparément.
- `<data_dir>/app-settings.json` : configuration sans secret brut : `"api_key": "{{vault:MISTRAL_API_KEY}}"`.

Les fichiers sensibles sont **locaux à l'ordinateur/serveur exécutant nanoMuse** et ne doivent jamais être transférés dans le dépôt Git. Par défaut, les fichiers ont des permissions limitées sur les systèmes de type Unix, mais le coffre **n'est pas un module de sécurité matériel** : tout processus disposant des deux fichiers peut déchiffrer la clé. Pour isoler la clé de chiffrement, configurez `NANOMUSE_VAULT_KEY` via un gestionnaire de secrets externe et protégez aussi cette variable.

## 4. Vérifier et redémarrer

```bash
python scripts/configure_mistral.py --target ../nanoMuse --check
# Après changement, redémarrer le runtime nanoMuse.
```

`--check` vérifie la configuration, la présence de la clé et la possibilité de lire le coffre, **sans appel réseau**. Il ne prouve pas que Mistral accepte la clé ni que le compte dispose des droits d'accès au modèle.

Pour réutiliser une clé déjà stockée sans la saisir :

```bash
python scripts/configure_mistral.py --target ../nanoMuse --use-existing --model mistral-small-latest
```

Pour une connexion via iOS/Android, le téléphone utilise le backend nanoMuse configuré : **ne jamais intégrer la clé Mistral dans l'APK ou l'IPA**. Les capacités du téléphone restent soumises aux autorisations système et aux décisions de Sentinel.

## 5. Révoquer / renouveler

Générer une nouvelle clé sur Mistral Studio, la saisir via le configurateur, puis révoquer l'ancienne sur Mistral Studio. Pour supprimer uniquement la clé locale :

```bash
# À exécuter dans le clone nanoMuse ayant les dépendances installées
nanomuse vault delete MISTRAL_API_KEY
```

Après révocation, les requêtes de l'ancien runtime peuvent continuer jusqu'à son redémarrage si la clé a déjà été chargée en mémoire. Redémarrez le runtime après rotation.

## Tests

`python -m pytest -q tests/test_mistral_vault.py` (sans clés réelles). Le workflow CI réalise aussi un test d'intégration avec le vrai catalogue nanoMuse, le vrai coffre Fernet, et une **fausse** clé non fonctionnelle. Aucun appel à l'API Mistral n'est exécuté en CI.
