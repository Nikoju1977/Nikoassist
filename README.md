# NikoAssist — par Niko Studio Design

**Assistant IA multi-agents pour iOS, Android et ordinateurs**, construit à partir du projet libre [nanoMuse](https://github.com/nano-muse/nanoMuse).

## Deux branches sur ce GitHub

- **[source-nikoassist](https://github.com/Nikoju1977/Nikoassist/tree/source-nikoassist)** : **code source complet** nanoMuse, avec la marque NikoAssist sur les projets iOS/Android et l'outil multi-agents raccordé au moteur Python.
- **[main](https://github.com/Nikoju1977/Nikoassist)** : extension maintenable, installateur, tests et workflows d'intégration.

## Fonctions implémentées

- Un orchestrateur **`agent_team`** avec jusqu'à **4 sous-agents spécialisés** : recherche, analyse, création, exécution.
- **Planification contrôlée** : filtrage des tâches, des rôles et des outils, sans escalade de privilèges depuis un résultat généré par IA.
- **Budgets d'exécution** : nombre d'agents, étapes, taille des messages et délais plafonnés.
- **Sentinel** : actions et outils sensibles soumis aux autorisations du moteur nanoMuse ; `create` et `act` classés sensibles avant la délégation.
- **Récupération prudente** : jamais de relance automatique des actions dont le résultat est incertain ; contrôle final et états vérifiables.
- **Installateur idempotent et atomique**, `--dry-run`, restauration en cas d'échec d'écriture.
- **18 tests de régression** dans `main` et workflow d'intégration sur le commit nanoMuse analysé.

## Installer

Consulter [le guide d'installation](docs/INSTALLATION.md). Depuis un clone de ce dépôt et un clone nanoMuse :

```bash
python scripts/install_nikoassist.py --target ../nanoMuse --dry-run
python scripts/install_nikoassist.py --target ../nanoMuse
python -m pip install 'pytest>=8,<10' 'pydantic>=2,<3'
python -m pytest -q tests/
```

## Niveau de validation

**Vérifié :** tests de la politique, intégration automatisée de la surcouche dans un clone épinglé de nanoMuse, syntaxe Python et présence des points d'identité Android/iOS.

**Non encore vérifié :** application Android signée et installée sur des appareils réels, build iOS signé et tests sur iPhone, contrôle de l'OS sur toutes les versions, performances en production.

La couche multi-agents est disponible dans le **runtime Python associé** ; les applications mobiles peuvent lui déléguer du travail via les connexions de nanoMuse. Il ne s'agit pas encore d'une nouvelle interface native avec des agents exécutés chacun directement sur le téléphone. Les restrictions iOS continuent de s'appliquer.

**Objectif de fiabilité :** l'amélioration est mesurée par les tests et les builds. L'expression « dix fois plus fiable ou puissant » n'est pas un résultat démontré sans protocole de benchmark avant/après.

## Licence

Le code dérivé de nanoMuse et OpenMinis reste sous **GNU GPL-3.0-or-later**, avec les obligations de redistribution et les crédits d'origine. Voir [crédits et licences](LICENSE_NOTICE.md).

Création : **Niko Studio Design**. Projet indépendant, non affilié à nanoMuse ou Meta.
