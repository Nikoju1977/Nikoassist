#!/usr/bin/env python3
"""Configure Mistral for NikoAssist without exposing an API key in argv/Git.

Run from the overlay checkout after installing it in an upstream nanoMuse:
    python scripts/configure_mistral.py --target ../nanoMuse
    python scripts/configure_mistral.py --target ../nanoMuse --check
"""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path


def _bootstrap_target(target: Path | None) -> None:
    if target is None:
        return
    root = target.expanduser().resolve()
    if not (root / "nanomuse/config.py").is_file() or not (
        root / "nanomuse/nikoassist/mistral.py"
    ).is_file():
        raise RuntimeError("Installer d'abord NikoAssist dans ce dépôt nanoMuse (--target).")
    sys.path.insert(0, str(root))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Configurer Mistral AI dans le coffre NikoAssist")
    parser.add_argument("--target", type=Path, help="Racine du clone nanoMuse intégrant NikoAssist")
    parser.add_argument("--config", type=Path, help="Fichier config.toml nanoMuse (optionnel)")
    parser.add_argument("--data-dir", type=Path, help="Dossier des données locales nanoMuse")
    parser.add_argument("--model", default="mistral-small-latest", help="Modèle Mistral")
    parser.add_argument("--use-existing", action="store_true", help="Réutiliser la clé du coffre")
    parser.add_argument("--check", action="store_true", help="Vérification locale sans appel API")
    args = parser.parse_args(argv)
    try:
        _bootstrap_target(args.target)
        from nanomuse.config import load_settings
        from nanomuse.nikoassist.mistral import (
            MistralSetupError, configure_mistral, mistral_status,
        )
        data_dir = args.data_dir.expanduser().resolve() if args.data_dir else load_settings(args.config).data_dir
        if args.check:
            state = mistral_status(data_dir=data_dir)
            print("Mistral :", "prêt localement" if state["ready_offline"] else "non configuré")
            print("Clé chiffrée présente :", "oui" if state["key_present"] else "non")
            print("Test réseau : non exécuté")
            return 0 if state["ready_offline"] else 1
        if args.use_existing:
            result = configure_mistral(data_dir=data_dir, model=args.model, use_existing=True)
        else:
            if not sys.stdin.isatty():
                raise MistralSetupError(
                    "Clé à saisir dans un terminal interactif, jamais sur la ligne de commande. "
                    "Utiliser --use-existing si le coffre possède déjà la clé."
                )
            secret = getpass.getpass("Clé API Mistral (entrée masquée) : ")
            result = configure_mistral(data_dir=data_dir, model=args.model, secret=secret)
        print("Mistral configuré :", result["model"])
        print("Clé : stockée dans le coffre chiffré nanoMuse (non affichée)")
        print("Serveur : redémarrer nanoMuse pour activer la nouvelle configuration")
        print("Tester : python scripts/configure_mistral.py --check [--target CHEMIN]")
        return 0
    except Exception as exc:
        # Never echo the exception message of a third-party library: it might contain secrets.
        if type(exc).__name__ == "MistralSetupError":
            print(f"Erreur : {exc}", file=sys.stderr)
        else:
            print(f"Erreur de configuration ({type(exc).__name__}). La clé n'est pas affichée.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
