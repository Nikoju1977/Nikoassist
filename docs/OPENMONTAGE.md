# OpenMontage dans NikoAssist (connecteur vidéo optionnel)

Projet amont **officiel** : https://github.com/calesthio/OpenMontage  
Licence du projet tiers : **AGPL-3.0**. nanoMuse/NikoAssist reste sous GPL-3.0 ; le dépôt amont n'est pas recopié, fusionné ou redistribué ici.

## Ce qui est réellement intégré

Le nouvel outil natif `openmontage` de NikoAssist propose trois opérations :

- `list` : énumère les pipelines vidéo présents et vérifie la disponibilité de FFmpeg et Node.js ;
- `prepare` : crée **une seule fois** un dossier de projet et un fichier `nikoassist-request.json` structuré, après autorisation Sentinel (niveau **sensitive**) ;
- `status` : indique si des fichiers vidéo apparaissent dans le dossier du projet, **sans les déclarer valides ni terminés**.

Le rôle **creator** de l'orchestrateur multi-agents peut utiliser l'outil. Les rôles researcher et operator n'y ont pas accès en délégation.

**Limitation intentionnelle** : OpenMontage est orchestré par un agent de développement qui lit des manifests YAML et des skills ; ce n'est pas un programme doté d'un unique endpoint de rendu stable. Ce connecteur prépare et transmet un brief. Il **ne lance pas** de scripts tiers, de génération vidéo, de téléchargement ni de facturation. Le rendu doit être explicitement déclenché et supervisé dans l'agent OpenMontage.

## Installation sur le serveur de NikoAssist

Depuis un terminal sur votre propre ordinateur ou serveur :

```bash
git clone https://github.com/calesthio/OpenMontage.git /opt/OpenMontage
cd /opt/OpenMontage
make setup
```

**Réviser le code source et les dépendances avant `make setup`**. Cette commande installe des paquets Python/Node et peut télécharger des outils. Ne lancez pas de programme depuis un fork ou un dépôt d'installation non vérifié.

Dans l'environnement du serveur nanoMuse/NikoAssist :

```bash
export NIKOASSIST_OPENMONTAGE_ROOT=/opt/OpenMontage
python scripts/install_nikoassist.py --target ../nanoMuse
# Redémarrer le backend nanoMuse pour charger l'outil.
```

Le chemin doit être **absolu**, vers un clone OpenMontage situé **sur le même serveur** que nanoMuse. L'outil reste inactif de façon sûre quand la variable n'est pas définie. Sous systemd ou Docker, définir cette variable dans la configuration du service et rendre le clone accessible au processus.

## Exemple d'appel de l'outil

```json
{"action":"list"}
```

Après avoir sélectionné un pipeline réellement installé et demandé l'autorisation de création :

```json
{
  "action": "prepare",
  "pipeline": "animated-explainer",
  "project": "demo-nikoassist",
  "brief": "Présenter NikoAssist et expliquer ses protections de confidentialité.",
  "duration_seconds": 60
}
```

Le fichier de passation sera :
`/opt/OpenMontage/projects/nikoassist-demo-nikoassist/nikoassist-request.json`.

Ouvrez ce fichier **dans votre agent de production OpenMontage**, puis validez le pipeline et les coûts avant le rendu. La simple existence d'un MP4 ne prouve pas sa qualité : un contrôle humain et un contrôle `ffprobe` sont nécessaires.

## Architecture et sécurité

- Le coffre Mistral reste **sur le serveur nanoMuse** : ce connecteur ne lit jamais les identifiants.
- Aucune commande shell, installation, appel API ni exécution d'outils OpenMontage n'est lancée par la passerelle.
- Les identifiants de projet sont strictement filtrés pour éviter les traversées de répertoires.
- Le connecteur refuse les doublons et certains liens symboliques ; il n'écrase pas un projet existant.
- `prepare` est classée **sensitive** : la stratégie Sentinel décide de la confirmation.
- N'ajoutez jamais des secrets dans le brief : le fichier de passation n'est pas un coffre.

Pour les tests sans modèle ni clé API : `python -m pytest -q tests/test_openmontage.py`.

## Statut de livraison

Interface d'intégration Python et tests automatisés : implémentés. **Rendu de bout en bout, application mobile compilée et test vidéo réel : non validés.** Le connecteur n'est pas un éditeur vidéo complet intégré nativement à Android/iOS.
