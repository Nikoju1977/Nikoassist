# NikoAssist — par Niko Studio Design

**NikoAssist** est un projet d'assistant IA agentique multi-appareils, destiné à iOS, Android et aux ordinateurs.

## État de développement

Ce dépôt contient une **extension multi-agents pour le runtime Python [nanoMuse](https://github.com/nano-muse/nanoMuse)**. Ce n'est **pas encore** une application Android/iOS autonome, compilée, signée ou publiée sur les stores.

Le moteur multi-agents répartit une mission entre des agents spécialisés (recherche, analyse, création, exécution) en conservant la couche de contrôle des actions **Sentinel** de nanoMuse. Les sous-agents disposent de listes d'outils limitées. Les appels aux outils restent soumis aux permissions de l'application d'origine.

- Agent Recherche : recherche Web et sources.
- Agent Analyse : structuration et analyse.
- Agent Création : création locale sous contrôle.
- Agent Exécution : agir sur les appareils connectés, selon les permissions.

La base source utilisée pour préparer l'intégration est le projet [nano-muse/nanoMuse](https://github.com/nano-muse/nanoMuse), à la révision `34439cf8a82e8163004fae14c731c87fd6e69ebf` (octobre 2026).

## Installer dans nanoMuse

```bash
git clone https://github.com/nano-muse/nanoMuse.git
git clone https://github.com/Nikoju1977/Nikoassist.git
cd Nikoassist
python scripts/install_nikoassist.py --target ../nanoMuse
```

Exécuter ensuite les procédures de build et de tests officielles de nanoMuse. L'extension destinée aux ordinateurs/serveurs s'appuie sur une délégation depuis le téléphone ; elle ne débloque pas les restrictions d'iOS.

## Validation

Les tests de l'extension doivent être lancés avec `python -m pytest -q tests/`. Les builds natifs iOS et Android ne sont pas certifiés ici.

## Licence et attribution

Les éléments dérivés du projet nanoMuse/OpenMinis restent soumis à **GPL-3.0-or-later**. Conserver les mentions de copyright et distribuer le code source correspondant conformément à la licence. NikoAssist est un projet indépendant, par Niko Studio Design.

**Attention :** ne jamais commiter de clés API, données privées, certificats Apple ou keystores Android.
