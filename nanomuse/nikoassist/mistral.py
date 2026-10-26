"""Mistral AI onboarding for the existing nanoMuse provider and encrypted vault.

This module does not implement a second secret store, network client, or key format.
The native nanoMuse OpenAI-compatible client and CredentialVault remain authoritative.
No API token may be supplied through command-line flags, config files or Git.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

MISTRAL_PROVIDER = "mistral"
MISTRAL_BASE_URL = "https://api.mistral.ai/v1"
MISTRAL_MODEL = "mistral-small-latest"
MISTRAL_SECRET_NAME = "MISTRAL_API_KEY"
MISTRAL_PLACEHOLDER = "{{vault:MISTRAL_API_KEY}}"


class MistralSetupError(RuntimeError):
    """Safe message for user-facing setup errors; never includes any secret."""


def validate_model(model: str) -> str:
    """Prevent accidental paths, control chars, or secrets in the model identifier."""
    model = model.strip() if isinstance(model, str) else ""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", model):
        raise MistralSetupError("Nom de modèle invalide (lettres, chiffres, '-', '_' et '.' uniquement).")
    return model


def validate_secret(key: str) -> str:
    """Conservative validation without assuming a vendor-specific token prefix."""
    if not isinstance(key, str) or not 8 <= len(key) <= 4096 or any(
        x in key for x in ("\r", "\n", "\x00")
    ) or key != key.strip() or "{{vault:" in key:
        raise MistralSetupError("Clé API absente ou mal formée.")
    return key


def merged_app_settings(existing: dict[str, Any], model: str = MISTRAL_MODEL) -> dict[str, Any]:
    """Preserve all unrelated app settings; never persist a plaintext key."""
    if not isinstance(existing, dict) or (
        "llm" in existing and not isinstance(existing["llm"], dict)
    ):
        raise MistralSetupError("Configuration de l'application invalide : aucun fichier modifié.")
    model = validate_model(model)
    updated = dict(existing)
    llm = dict(updated.get("llm", {}))
    llm.update({
        "provider": MISTRAL_PROVIDER,
        "model": model,
        # Required: nanoMuse overlays app settings onto the existing base_url.
        # An empty URL could leave a previous DeepSeek/OpenAI endpoint active.
        "base_url": MISTRAL_BASE_URL,
        "api_key": MISTRAL_PLACEHOLDER,
        "tool_mode": "auto",
        "vision": "auto",
    })
    updated["llm"] = llm
    return updated


def _read_existing(data_dir: Path) -> dict[str, Any]:
    """Reject damaged files rather than silently overwriting prior configuration."""
    from nanomuse.config import APP_SETTINGS_FILE

    path = data_dir / APP_SETTINGS_FILE
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MistralSetupError("Configuration existante illisible : aucun fichier modifié.") from exc
    if not isinstance(raw, dict):
        raise MistralSetupError("Configuration existante invalide : aucun fichier modifié.")
    return raw


def _require_upstream_provider() -> None:
    from nanomuse.llm import catalogue

    provider = catalogue.load().get(MISTRAL_PROVIDER)
    if provider is None or provider.protocol != "openai":
        raise MistralSetupError("Cette version de nanoMuse ne prend pas en charge Mistral AI.")


def configure_mistral(
    *, data_dir: Path, model: str = MISTRAL_MODEL, secret: str | None = None,
    use_existing: bool = False,
) -> dict[str, Any]:
    """Store secret encrypted then persist only its vault placeholder.

    `secret` is accepted in this in-process API only. The CLI obtains it by
    getpass, never from a positional argument or process command line.
    If config saving fails after the vault write, the key remains encrypted
    and the user may retry with --use-existing.
    """
    from nanomuse.config import save_app_settings
    from nanomuse.vault import CredentialVault

    if (secret is None) == (not use_existing):
        raise MistralSetupError("Choisir une nouvelle clé OU l'option --use-existing.")
    model = validate_model(model)
    data_dir = Path(data_dir).expanduser().resolve()
    _require_upstream_provider()
    previous = _read_existing(data_dir)
    updated = merged_app_settings(previous, model)
    vault = CredentialVault(data_dir / "vault.enc", data_dir / "vault.key")
    if use_existing:
        if not vault.get(MISTRAL_SECRET_NAME):
            raise MistralSetupError("Aucune clé Mistral dans le coffre. Lance l'assistant interactif.")
    else:
        vault.set(MISTRAL_SECRET_NAME, validate_secret(secret))
    save_app_settings(data_dir, updated)
    return {
        "provider": MISTRAL_PROVIDER,
        "model": model,
        "base_url": MISTRAL_BASE_URL,
        "credential": "stored-in-encrypted-vault",
        "settings_path": str(data_dir / "app-settings.json"),
        "network_verified": False,
    }


def mistral_status(*, data_dir: Path) -> dict[str, Any]:
    """Check local configuration only, without reading out or returning the key."""
    from nanomuse.vault import CredentialVault

    data_dir = Path(data_dir).expanduser().resolve()
    existing = _read_existing(data_dir)
    llm = existing.get("llm", {})
    if not isinstance(llm, dict):
        raise MistralSetupError("Configuration du modèle invalide.")
    vault = CredentialVault(data_dir / "vault.enc", data_dir / "vault.key")
    configured = (
        llm.get("provider") == MISTRAL_PROVIDER
        and llm.get("base_url") == MISTRAL_BASE_URL
        and llm.get("api_key") == MISTRAL_PLACEHOLDER
    )
    # `get` checks actual decryptability, not mere ciphertext existence.
    key_present = bool(vault.get(MISTRAL_SECRET_NAME))
    return {"configured": configured, "key_present": key_present,
            "ready_offline": configured and key_present, "network_verified": False,
            "model": str(llm.get("model", "")) if configured else ""}
