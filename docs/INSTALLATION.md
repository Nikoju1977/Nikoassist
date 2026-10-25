# NikoAssist — installation et validation

**Éditeur : Niko Studio Design**  
Base technique : [nanoMuse](https://github.com/nano-muse/nanoMuse) (GPL-3.0-or-later).

## Ce que contient le dépôt

- `nanomuse/nikoassist/core.py` : politique déterministe, budgets, délégation limitée.
- `nanomuse/nikoassist/tool.py` : outil `agent_team` branché sur le moteur `MuseAgent` existant.
- `scripts/install_nikoassist.py` : surcouche atomique, idempotente et prévisualisable.
- `tests/` : tests hors ligne (aucune clé API).
- `.github/workflows/verify.yml` : tests sur GitHub Actions et intégration dans un clone épinglé de nanoMuse.

## Installer la surcouche sur un clone nanoMuse

```bash
git clone https://github.com/nano-muse/nanoMuse.git nanoMuse
git -C nanoMuse fetch --depth 1 origin 34439cf8a82e8163004fae14c731c87fd6e69ebf
git -C nanoMuse checkout --detach 34439cf8a82e8163004fae14c731c87fd6e69ebf
git clone https://github.com/Nikoju1977/Nikoassist.git
cd Nikoassist
python scripts/install_nikoassist.py --target ../nanoMuse --dry-run
python scripts/install_nikoassist.py --target ../nanoMuse
python -m pip install 'pytest>=8,<10' 'pydantic>=2,<3'
python -m pytest -q tests/
```

Installe ensuite nanoMuse selon ses instructions (iOS : macOS et Xcode + signature Apple ; Android : JDK/Gradle/NDK). Les builds natifs et l'installation sur téléphones réels exigent une validation spécifique et ne sont pas garantis par les tests Python.

## Agent teamwork

`agent_team(goal=..., mode="research", max_agents=3)`

- `research` : recherche et analyse, sans accès aux opérations sur appareils.
- `create` : créations de fichiers dans la zone autorisée. Déclenche un contrôle de sensibilité Sentinel.
- `act` : action sur les interfaces connectées, contrôlée par Sentinel ; sur iOS les opérations permises sont restreintes par le système.

Les sous-agents partagent les outils du runtime, mais seulement selon une liste blanche stricte. Chaque appel d'outil reste soumis à Sentinel. Un outil appelé n'est pas une preuve de réussite. Les actions indéterminées ne sont pas automatiquement rejouées.

Les budgets par défaut sont de 3 sous-agents, 8 étapes au maximum par sous-agent, 90 secondes par appel de planification/revue et 600 secondes par agent. Une annulation en cours d'action doit être vérifiée avant reprise manuelle.

## Sécurité et limites

- Ne publie aucune clé API, certificat, keystore ou donnée personnelle.
- Les applications iOS/Android ne reçoivent pas encore des agents locaux multi-processus : elles peuvent déléguer à un runtime nanoMuse relié.
- Les modifications de nom concernent les écrans natifs identifiés. Les identifiants internes `nanoMuse` et les protocoles ne sont pas renommés, afin de préserver les connexions.
- Les tests hors ligne ne démontrent pas un gain de puissance ou fiabilité de 10×. Un benchmark comparatif est nécessaire.
- Source d'origine : nanoMuse/OpenMinis, sous GPL-3.0-or-later. Redistribution selon les conditions GPL, avec code correspondant et mentions intactes.
