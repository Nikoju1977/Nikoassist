# NikoAssist — compilation Android et iOS

Ce dépôt propose des **workflows de compilation expérimentaux** pour les sources mobiles
de la branche [`source-nikoassist`](https://github.com/Nikoju1977/Nikoassist/tree/source-nikoassist).
Les workflows eux-mêmes sont versionnés dans `main`. Ils ne nécessitent
**aucune clé Mistral, clé de signature ni certificat Apple**.

## Android — APK de développement

Workflow : [NikoAssist - Android debug APK](https://github.com/Nikoju1977/Nikoassist/actions/workflows/build-android.yml).

- Runner : Ubuntu 24.04, Java 17, Android SDK 36, NDK 27.2.12479018
  (version épinglée dans `android/src/android/app/build.gradle.kts`).
- Initialise les sous-modules Git, compile PRoot et ses chargeurs natifs,
  télécharge le système de fichiers Alpine et lance `assembleDebug`.
- Vérifie la présence des composants natifs dans l'APK.
- Produit, **si tous les contrôles passent**, l'artefact Actions
  `NikoAssist-Android-arm64-debug` contenant `app-debug.apk` et son SHA256.
- Durée de conservation de l'artefact : 14 jours.

L'APK est **signé avec une clé Android de développement**, non une clé de distribution
pérenne. C'est une version de test, non une release Play Store. Il est destiné à
un appareil Android arm64 de test. L'identifiant d'application Android provient
encore du projet source : il doit être personnalisé et audité avant une
distribution publique, pour éviter les collisions et vérifier les autorités
des providers, deep links et permissions.

## iOS — compilation d'appareil sans signature

Workflow : [NikoAssist - iOS unsigned device build](https://github.com/Nikoju1977/Nikoassist/actions/workflows/build-ios.yml).

- Runner : GitHub Actions `macos-26` (Apple Silicon), Xcode avec iOS SDK récent.
- Initialise les sous-modules, installe Meson, Ninja, LLVM et libarchive.
- Compile dans l'ordre **LAME → FFmpeg → iSH → Alpine rootfs**, puis la cible
  `Minis` pour `generic/platform=iOS` en désactivant la signature.
- Produit, **si la compilation réussit**, l'artefact Actions
  `NikoAssist-iOS-arm64-unsigned-app`, archive ZIP du `.app` non signé,
  avec empreinte SHA256. Rétention : 7 jours.

**Un `.app` non signé n'est pas un IPA installable sur iPhone.**
Pour TestFlight, l'App Store ou un appareil réel, prévoir l'Apple Developer
Program, des identifiants d'application/entitlements propres à NikoAssist,
un profil de provisionnement, une signature et des essais matériels.
Aucun de ces secrets ne se trouve dans ce dépôt.

## Déclencher / récupérer les artefacts

1. Ouvrir le workflow Android ou iOS (liens ci-dessus).
2. Choisir **Run workflow** depuis la branche `main`.
3. Consulter chaque étape du journal et s'assurer que toutes sont vertes.
4. Une fois le run réussi, ouvrir sa section **Artifacts** et télécharger
   l'archive correspondante.

Les workflows se déclenchent également quand **leurs propres fichiers changent**
sur `main`. Ils ne se lancent pas à chaque modification du code pour éviter
les compilations natives longues et coûteuses. Une réussite des tests Python
ne garantit pas la réussite des builds mobiles.

## Capacités et sécurité

La branche complète fournit le code natif Android/iOS de nanoMuse ainsi que
le module NikoAssist côté runtime Python. **Compiler le client mobile ne prouve
pas que les fonctions multi-agents Python y tournent localement** : leur
intégration de bout en bout et les connexions au backend doivent être validées
sur des appareils. Le module OpenMontage est également une passerelle facultative
et ne garantit pas une génération vidéo opérationnelle.

Le coffre chiffré Mistral reste côté runtime et se configure localement selon
[le guide Mistral](MISTRAL_VAULT.md). Ne jamais mettre une clé API, un secret
GitHub, un `.p12` ou un keystore privé dans l'APK, l'IPA, les logs ou
un artefact public. Conserver les licences GPL et les avis tiers.
