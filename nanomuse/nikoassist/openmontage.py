"""Optional, non-executing bridge to the upstream OpenMontage project.

OpenMontage has an agent-first architecture, not a stable one-command video API.
No third-party code is imported or executed here. Installation is separate.
"""
from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_ENV = "NIKOASSIST_OPENMONTAGE_ROOT"
PIPELINE_RE = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
PROJECT_RE = re.compile(r"[a-z][a-z0-9-]{0,39}\Z")
MAX_BRIEF_CHARS = 5000


class OpenMontageError(ValueError):
    """Error whose message is safe to present to the user."""


def installed_root() -> Path:
    configured = os.environ.get(ROOT_ENV, "").strip()
    if not configured:
        raise OpenMontageError(
            "OpenMontage n'est pas configuré sur ce serveur. "
            "Définir NIKOASSIST_OPENMONTAGE_ROOT vers le clone officiel."
        )
    location = Path(configured).expanduser()
    if not location.is_absolute():
        raise OpenMontageError("Le chemin OpenMontage doit être absolu.")
    root = location.resolve(strict=True)
    if not (root / "pipeline_defs").is_dir() or not (root / "lib/pipeline_loader.py").is_file():
        raise OpenMontageError("Le dossier indiqué n'est pas une installation OpenMontage valide.")
    if (root / "pipeline_defs").is_symlink():
        raise OpenMontageError("Le répertoire pipeline_defs ne peut pas être un lien symbolique.")
    return root


def pipelines(root: Path | None = None) -> list[str]:
    root = root or installed_root()
    defs = root / "pipeline_defs"
    return sorted(
        entry.stem for entry in defs.glob("*.yaml")
        if entry.is_file() and not entry.is_symlink() and PIPELINE_RE.fullmatch(entry.stem)
    )[:128]


def _validate_project(project: str) -> str:
    if not isinstance(project, str) or not PROJECT_RE.fullmatch(project):
        raise OpenMontageError("Nom de projet invalide : lettres minuscules, chiffres, tirets (40 max).")
    return project


def _project_directory(root: Path, project: str) -> Path:
    return root / "projects" / ("nikoassist-" + _validate_project(project))


def prepare(
    *, pipeline: str, brief: str, project: str, duration_seconds: int = 60,
    root: Path | None = None,
) -> dict[str, Any]:
    """Prepare a one-time job handoff, never run renders, downloads or providers.

    Caller must obtain Sentinel approval before this operation.
    """
    root = root or installed_root()
    if not isinstance(pipeline, str) or not PIPELINE_RE.fullmatch(pipeline):
        raise OpenMontageError("Nom de pipeline invalide.")
    if pipeline not in pipelines(root):
        raise OpenMontageError("Pipeline inconnu ou indisponible.")
    if not isinstance(brief, str) or not (10 <= len(brief.strip()) <= MAX_BRIEF_CHARS):
        raise OpenMontageError("Description vidéo requise (10 à 5 000 caractères).")
    if "\x00" in brief:
        raise OpenMontageError("La description contient un caractère invalide.")
    if isinstance(duration_seconds, bool) or not isinstance(duration_seconds, int) or not 5 <= duration_seconds <= 1800:
        raise OpenMontageError("Durée autorisée : 5 à 1800 secondes.")

    projects = root / "projects"
    if projects.is_symlink():
        raise OpenMontageError("Le dossier projects ne doit pas être un lien symbolique.")
    projects.mkdir(mode=0o700, exist_ok=True)
    if projects.is_symlink():
        raise OpenMontageError("Le dossier projects ne doit pas être un lien symbolique.")
    target = _project_directory(root, project)
    try:
        target.mkdir(mode=0o700, exist_ok=False)
    except FileExistsError as exc:
        raise OpenMontageError("Ce projet existe déjà : aucun fichier n'a été écrasé.") from exc

    request = {
        "schema": "nikoassist.openmontage.request.v1",
        "project": project,
        "pipeline": pipeline,
        "duration_seconds": duration_seconds,
        "brief": brief.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "state": "prepared_requires_operator_approval",
        "source": "https://github.com/calesthio/OpenMontage",
        "manifest": f"pipeline_defs/{pipeline}.yaml",
        "render_executed": False,
    }
    output = target / "nikoassist-request.json"
    try:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(output, flags, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(request, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except Exception:
        try:
            output.unlink(missing_ok=True)
            target.rmdir()
        except OSError:
            pass
        raise
    return {
        "status": "prepared_not_rendered",
        "project": project,
        "pipeline": pipeline,
        "path": str(output),
        "next_step": "Ouvrir ce projet dans l'agent de production OpenMontage et valider le lancement.",
        "render_verified": False,
    }


def status(*, project: str, root: Path | None = None) -> dict[str, Any]:
    root = root or installed_root()
    target = _project_directory(root, project)
    if target.is_symlink():
        raise OpenMontageError("Lien symbolique de projet refusé.")
    request = target / "nikoassist-request.json"
    if not request.is_file() or request.is_symlink():
        raise OpenMontageError("Projet préparé introuvable.")
    try:
        payload = json.loads(request.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise OpenMontageError("Fichier de préparation illisible.") from exc
    if payload.get("schema") != "nikoassist.openmontage.request.v1" or payload.get("project") != project:
        raise OpenMontageError("Fichier de préparation incompatible.")
    renders = target / "renders"
    outputs = sorted(
        p.name for p in renders.glob("*.mp4") if p.is_file() and not p.is_symlink()
    )[:20] if renders.is_dir() and not renders.is_symlink() else []
    return {
        "project": project,
        "pipeline": payload.get("pipeline"),
        "state": "video_files_present_unverified" if outputs else "prepared_not_rendered",
        "video_files": outputs,
        "render_verified": False,
    }


def preflight() -> dict[str, Any]:
    root = installed_root()
    return {
        "root": str(root),
        "pipelines": pipelines(root),
        "ffmpeg_available": shutil.which("ffmpeg") is not None,
        "node_available": shutil.which("node") is not None,
        "automated_rendering": False,
        "note": "Préparation uniquement ; rendu géré par un agent OpenMontage séparé.",
    }
