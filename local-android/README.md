# NikoAssist Local — Android hors ligne (Galaxy S20 FE 5G)

**Objectif : une première application Android autonome, 0 € / mois, sans serveur,
sans abonnement, sans clé API, sans compte et sans connexion pendant les conversations.**

Ce module est une **application Android distincte du client nanoMuse/OpenMinis** et
se concentre uniquement sur le chat local. Il ne fait **pas encore** tourner la
chaîne complète multi-agents, les actions JARVIS, Sentinel ou les automatisations.
La PWA Vercel reste un frontend séparé et ne fournit pas cette IA locale.

## Matériel visé

- Samsung Galaxy S20 FE **5G** : Snapdragon 865, architecture **arm64-v8a**.
- Android **13 ou plus** : le code de l'exemple llama.cpp actuellement intégré
  requiert minSdk 33. Vérifier *Paramètres → À propos du téléphone →
  Informations sur le logiciel* avant installation.
- Au moins **2 Go d'espace libre** avant l'importation d'un modèle de 397 Mo :
  le fichier est copié en stockage privé et les bibliothèques occupent de l'espace.
- 6 Go de RAM peuvent suffire à un petit modèle ; les performances et la consommation
  varient avec la taille du modèle, la longueur de conversation et la température.

## Première utilisation

1. Installer l'APK **NikoAssist-Local-S20FE5G-debug.apk**, obtenu après une compilation
   GitHub Actions **réussie**.
2. Dans NikoAssist Local, toucher le texte d'accueil pour ouvrir le téléchargement
   du modèle GGUF dans le navigateur du téléphone (ou utiliser le lien ci-dessous).
3. Télécharger **[Qwen3 0.6B Q4_K_M, 397 Mo](https://huggingface.co/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf)**,
   modèle gratuit sous licence Apache-2.0.
4. Revenir dans l'application, toucher l'icône de **dossier** et sélectionner
   le fichier `.gguf` dans *Téléchargements*. L'importation copie les poids
   dans le stockage privé de l'application.
5. Quand « IA hors ligne activée » apparaît, couper Wi-Fi et données mobiles :
   la génération des réponses ne fait aucune requête réseau.

**SHA-256 du modèle 0.6B, annoncé par l'hébergeur :**
`ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a`.
Comparer l'empreinte après téléchargement si possible.

Après cette première installation, l'application recharge automatiquement le modèle
local au démarrage. Elle ne télécharge aucun poids par elle-même : seul le navigateur
extérieur sert au téléchargement initial. Les conversations de cette première version
ne sont pas encore persistées lors de la fermeture.

**Modèle plus avancé (optionnel) :**
[Qwen3 1.7B Q4_K_M (~1,1 Go)](https://huggingface.co/unsloth/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q4_K_M.gguf).
Commencer par le 0.6B. Le 1.7B peut provoquer un arrêt faute de RAM sur un
téléphone utilisé par plusieurs applications. L'import d'un nouveau modèle alors
qu'un modèle est déjà chargé nécessitera une fonction de remplacement dans une
future version ; pour cette première version, vider les données de l'application
supprime le modèle précédent **et toute donnée locale associée**.

## Générer gratuitement l'APK

Sur GitHub :
**Actions → NikoAssist Local — Offline Android APK → Run workflow**.
Le workflow publie un artefact `NikoAssist-Local-S20FE5G` comprenant l'APK
et son SHA-256. Cet APK est **signé avec la clé debug** du runner ; ne pas
le traiter comme une release Play Store. La compilation doit être terminée
avec succès avant de partager l'APK comme installable.

Le workflow vérifie que l'APK ne demande **pas** `android.permission.INTERNET`
et que l'identifiant Android est `fr.nikostudio.nikoassist.local`.

Pour bâtir localement depuis le checkout de NikoAssist `main` :

```sh
git clone https://github.com/ggml-org/llama.cpp.git
git -C llama.cpp checkout c6fb3b5be2209f6c12339833198190f6f6829581
python3 local-android/prepare.py --llama llama.cpp
cd llama.cpp/examples/llama.android
./gradlew :app:assembleDebug
```

Installer avant compilation : Java 17, Android SDK 36, NDK `29.0.14206865`,
CMake `3.31.6` et les outils Android standard.

## Architecture et sécurité

- Moteur d'inférence local : [llama.cpp](https://github.com/ggml-org/llama.cpp)
  (MIT), Android JNI officiel, version amont épinglée et vérifiée dans
  `prepare.py`.
- Interface et comportement NikoAssist Local : `local-android/app/MainActivity.kt`
  (GPL-3.0-or-later).
- Une **copie locale** du GGUF est placée dans le répertoire privé de l'application.
- L'APK n'exige pas de permission Internet. La sélection du modèle utilise
  le sélecteur de documents Android. **Aucun jeton Mistral n'est nécessaire.**
- Les actions système et les permissions avancées du client OpenMinis ne sont
  pas incluses dans cette édition de chat : ne pas confondre avec l'APK principal.
- **Limitations** : texte uniquement, chat de base, pas de recherche Web, pas de
  synchronisation et pas de mémoire conversationnelle après redémarrage.

## Licences et attribution

Le moteur et l'exemple de base sont extraits de
`ggml-org/llama.cpp` au commit
`c6fb3b5be2209f6c12339833198190f6f6829581` (licence MIT,
voir [LICENSE amont](https://github.com/ggml-org/llama.cpp/blob/c6fb3b5be2209f6c12339833198190f6f6829581/LICENSE)).
Les modifications de NikoAssist Local sont publiées sous GPL-3.0-or-later.
Le modèle Qwen3 est soumis à la licence Apache-2.0 indiquée dans sa fiche.
Le workflow ne reconditionne ni ne revend des poids de modèles.

**Critère de livraison réel :** un APK construit avec succès est une étape ;
la vérification finale exige d'installer sur un S20 FE 5G réel, d'importer le
GGUF, de générer une réponse en mode avion et de mesurer les performances.
