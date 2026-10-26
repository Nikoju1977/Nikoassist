# NikoAssist — builds mobiles expérimentaux

Deux workflows GitHub Actions complets sont disponibles sur la branche `main`. Ils compilent aussi les bibliothèques natives rclone, nécessaires aux applications :

- [Android APK](../.github/workflows/build-android.yml) : construit les dépendances natives et produit un APK **debug** arm64, signé avec la clé de débogage du runner. L'APK est destiné aux tests et **pas** à la distribution Play Store.
- [iOS build](../.github/workflows/build-ios.yml) : construit les dépendances iSH/FFmpeg/LAME et produit une archive ZIP de `Minis.app` **non signée**. Ce fichier **ne peut pas être installé directement sur un iPhone** : il faut une équipe Apple Developer, un identifiant d'application, des profils et certificats de signature, puis éventuellement TestFlight.

## Démarrer un build

Sur GitHub, ouvrir **Actions**, sélectionner le workflow Android ou iOS, cliquer **Run workflow** sur la branche `main`. À la fin, ouvrir la page de l'exécution et télécharger l'**artifact** sous **Artifacts**.

Le build utilise `source-nikoassist` (base nanoMuse + surcouche NikoAssist) et des sous-modules natifs. Les téléchargements des dépendances peuvent prendre longtemps et les premières compilations peuvent échouer pour des raisons d'outillage, de versions ou de sources externes. Un workflow créé ne signifie pas qu'un binaire a été compilé avec succès.

## Sécurité et limitations

Aucune clé Mistral, clé de chiffrement du coffre, certificat Apple ou clé de signature Android n'est ajoutée aux workflows ou aux binaires. Les clés de l'utilisateur doivent rester dans le coffre prévu à cet effet. Les builds sont **expérimentaux** et ne prouvent pas encore le fonctionnement de NikoAssist sur un téléphone réel. La base native utilise encore des noms et identifiants issus de nanoMuse/OpenMinis ; le rebranding et la validation fonctionnelle restent à terminer.

## En cas d'échec

Lire le premier step en échec dans les logs GitHub Actions. Sur Android, vérifier NDK/PRoot/Alpine ; sur iOS, vérifier version de Xcode, SDK iOS et compilation iSH/FFmpeg. Ne pas publier une release officielle tant que la compilation et les tests sur appareil ne sont pas concluants.
