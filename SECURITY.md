# Politique de sécurité

## Signaler une vulnérabilité

Merci de **ne pas publier de faille exploitable, de secrets, de données personnelles ou de captures sensibles dans une issue publique**. Utiliser les signalements privés de vulnérabilités GitHub lorsque cette fonction est activée pour le dépôt ; à défaut, contacter le mainteneur en privé via un canal indiqué sur son profil. Ne jamais joindre de mots de passe, jetons, clés d'API ou données médicales réelles.

Indiquer dans le rapport : la version/commit, le composant, les étapes minimales de reproduction avec des **données fictives**, l'impact attendu et les pistes d'atténuation. Aucun délai de traitement ni programme de récompenses n'est promis.

## Périmètre

Ce dépôt peut contenir un prototype ou une expérimentation. La publication du code, d'un README ou d'une démonstration **ne constitue pas** un audit de sécurité, une certification ou une autorisation d'usage en production.

Éviter de committer les fichiers `.env`, les clés privées, les jetons d'authentification, les sauvegardes d'utilisateurs et les exports de données personnelles. Vérifier manuellement les permissions, les dépendances tierces, la configuration de production et les flux réseau avant chaque déploiement.

## Assistants IA et actions automatisées

Surveiller particulièrement : injection de prompt, outils déclenchant des effets réels sans confirmation, permissions excessives, fuite de clés de fournisseurs, journaux de conversations, accès micro/caméra et dépendances distantes. Une réponse d'un modèle ou d'un outil externe ne doit jamais être interprétée comme une autorisation d'exécuter une action sensible.

## Mises à jour

Avant de corriger un incident : préparer un correctif limité, examiner les régressions, vérifier l'absence de secrets dans le diff et documenter les changements dans une pull request. Les avis de sécurité applicables dépendent des dépendances et versions réellement employées.

[Retour au profil Studio Niko Design](https://github.com/Nikoju1977).
