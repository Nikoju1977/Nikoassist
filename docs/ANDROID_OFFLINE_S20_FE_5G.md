# NikoAssist — profil Android 100 % local (Galaxy S20 FE 5G)

**Statut : cahier de configuration et de validation, pas encore une intégration d'inférence prête à utiliser.**

Cible de validation : Samsung Galaxy **S20 FE 5G** (Snapdragon 865, Android arm64-v8a), versions 6 Go et 8 Go de RAM. Ne pas confondre avec certaines versions S20 FE 4G dotées d'un autre SoC. Le but est de faire fonctionner le chat sans serveur privé, sans abonnement et, une fois le modèle téléchargé, sans connexion réseau.

## Profil de lancement proposé

| Option | Par défaut | Raison |
| --- | --- | --- |
| ABI | `arm64-v8a` uniquement | Plateforme matérielle du téléphone |
| Moteur | llama.cpp compilé pour Android arm64 | Inférence GGUF dans le processus de l'application |
| Exécution | CPU d'abord, NEON générique | Plus portable que forcer ARMv8.6/I8MM/BF16 sur Snapdragon 865 |
| Modèle | `Qwen3-1.7B-Q4_K_M.gguf` | Français et bonne qualité par rapport à la taille |
| Modèle de secours | `Qwen3-0.6B`, GGUF Q4 | RAM disponible limitée, chauffe ou faible vitesse |
| Fenêtre de contexte initiale | 2048 tokens | Éviter une consommation mémoire excessive sur 6 Go de RAM |
| Génération initiale | 128 tokens par réponse, réglable | Éviter chauffe et longues attentes |
| Threads CPU | 4, réglable | À mesurer sur vrai téléphone |
| Stockage modèles | Privé à l'application; import explicite de GGUF | Ne pas injecter 1–2 Go dans l'APK |
| Mémoire de l'assistant | SQLite / stockage applicatif | Pas de base distante |
| Authentification / secrets | Android Keystore | Aucune clé cloud nécessaire pour le mode 100 % local |

**Ordres de grandeur :** Qwen3 1.7B Q4_K_M représente environ 1,1 à 1,3 Go à télécharger selon le dépôt de quantification. Le moteur, les allocations d'inférence et le cache KV portent la consommation RAM au-delà du poids du fichier (souvent environ 2 à 3 Go pour un petit contexte, à mesurer). Le système, le sandbox Alpine et les services Android utilisent également de la RAM. La machine peut manquer de mémoire ou chauffer : ne pas promettre un nombre de tokens par seconde sans mesurer.

Sources : Samsung France (S20 FE 5G Snapdragon 865, 6/8 Go), documentation llama.cpp Android, Qwen3 GGUF :
- https://news.samsung.com/fr/galaxy-s20-fan-edition
- https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md
- https://huggingface.co/unsloth/Qwen3-1.7B-GGUF
- https://huggingface.co/unsloth/Qwen3-0.6B-GGUF

## Intégration encore nécessaire

1. Compiler le vrai moteur `llama.cpp` depuis une révision vérifiée sous la licence appropriée, sans dépendance binaire non sourcée, comme bibliothèque Android JNI ou moteur Android intégré.
2. Ajouter une interface d'import/téléchargement GGUF avec validation de taille, contrôle d'intégrité SHA-256, stockage privé, reprise et effacement ; ne jamais exécuter des fichiers importés comme du code.
3. Brancher la sélection `local` dans le gestionnaire des fournisseurs LLM de l'application Android ; les messages doivent être traités sur le téléphone (et non via un WebSocket, un serveur localhost fictif, Vercel ou un service tiers).
4. Garantir une limite mémoire et une annulation de génération ; rendre la libération des ressources fiable lorsque l'app passe en arrière-plan.
5. Ajouter une sauvegarde des conversations en stockage local et des tests de permissions : aucune action d'agent ne se déclenche sans confirmation requise par Sentinel.
6. Définir la validation hors ligne : mode avion activé, application relancée, chat français avec le modèle déjà importé, aucune tentative de connexion de l'inférence à un serveur, au moins 10 requêtes, puis reprise après veille.
7. Tester sur un vrai Galaxy S20 FE 5G avec 6 Go de RAM avant de déclarer ce profil compatible. Une compilation CI ne suffit pas à prouver le fonctionnement.

## État du projet au 26 octobre 2026

- La PWA Vercel est **une interface statique** : elle ne sert pas d'hôte d'inférence local au téléphone.
- L'app Android native nanoMuse intégrée dans `source-nikoassist` possède un sandbox et des fournisseurs cloud, mais **pas encore** une intégration llama.cpp/Qwen3 opérationnelle.
- Le workflow Android `.github/workflows/build-android.yml` a eu un échec `OutOfMemoryError: Java heap space` pendant `:app:compileDebugKotlin`. Une correction du budget mémoire a été ajoutée sur `main`, et doit être confirmée par un nouveau build complet.
- L'app iOS nécessite un développement et des tests séparés : le S20 FE 5G est la cible Android prioritaire.

**Exigence financière :** 0 €/mois, pas de serveur, pas de service payant, pas d'API obligatoire. Une connexion Internet n'est requise que pour récupérer les modèles, les mises à jour ou les outils Web explicitement utilisés.
