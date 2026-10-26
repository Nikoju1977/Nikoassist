"""Regression tests for Mistral setup, without any real provider credentials."""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest
from cryptography.fernet import Fernet, InvalidToken

from nanomuse.nikoassist.mistral import (
    MISTRAL_BASE_URL,
    MISTRAL_PLACEHOLDER,
    MistralSetupError,
    configure_mistral,
    merged_app_settings,
    mistral_status,
    validate_model,
    validate_secret,
)


@pytest.fixture
def fake_upstream(monkeypatch):
    """Mirror the pinned nanoMuse interface; CI also checks against real upstream."""
    config = types.ModuleType("nanomuse.config")
    config.APP_SETTINGS_FILE = "app-settings.json"

    def save_app_settings(data_dir: Path, data: dict):
        data_dir.mkdir(parents=True, exist_ok=True)
        path = data_dir / config.APP_SETTINGS_FILE
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version": 1, **data}), "utf-8")
        tmp.replace(path)

    config.save_app_settings = save_app_settings

    class CredentialVault:
        def __init__(self, path, key_path):
            self.path, self.key_path = Path(path), Path(key_path)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.key_path.exists():
                self.key_path.write_bytes(Fernet.generate_key())

        def _read(self):
            if not self.path.exists():
                return {}
            return json.loads(Fernet(self.key_path.read_bytes()).decrypt(self.path.read_bytes()))

        def get(self, name):
            return self._read().get(name)

        def set(self, name, value):
            data = self._read()
            data[name] = value
            self.path.write_bytes(Fernet(self.key_path.read_bytes()).encrypt(json.dumps(data).encode()))

    vault = types.ModuleType("nanomuse.vault")
    vault.CredentialVault = CredentialVault

    catalogue = types.ModuleType("nanomuse.llm.catalogue")
    catalogue.load = lambda: types.SimpleNamespace(get=lambda name: (
        types.SimpleNamespace(protocol="openai") if name == "mistral" else None
    ))
    llm = types.ModuleType("nanomuse.llm")
    llm.catalogue = catalogue
    monkeypatch.setitem(sys.modules, "nanomuse.config", config)
    monkeypatch.setitem(sys.modules, "nanomuse.vault", vault)
    monkeypatch.setitem(sys.modules, "nanomuse.llm", llm)
    monkeypatch.setitem(sys.modules, "nanomuse.llm.catalogue", catalogue)
    return CredentialVault


def test_preserves_other_settings_and_replaces_old_endpoint():
    previous = {
        "version": 1,
        "llm": {"provider": "deepseek", "base_url": "https://api.deepseek.com", "api_key": "old", "proxy": ""},
        "calendar": {"enabled": True},
        "unrelated": [1, 2, 3],
    }
    current = merged_app_settings(previous)
    assert current["llm"]["provider"] == "mistral"
    assert current["llm"]["base_url"] == MISTRAL_BASE_URL
    assert current["llm"]["api_key"] == MISTRAL_PLACEHOLDER
    assert current["llm"]["proxy"] == ""
    assert current["calendar"] == previous["calendar"]
    assert current["unrelated"] == previous["unrelated"]
    assert previous["llm"]["provider"] == "deepseek"


@pytest.mark.parametrize("model", ["", "../../evil", "aa\nhi", "test value", "x" * 129])
def test_rejects_invalid_model_names(model):
    with pytest.raises(MistralSetupError):
        validate_model(model)


@pytest.mark.parametrize("key", ["", "too", "a\nbbbbbbbbbbb", " 123456789 ", "{{vault:BAD}}"])
def test_rejects_invalid_credentials(key):
    with pytest.raises(MistralSetupError):
        validate_secret(key)


def test_real_encryption_round_trip_and_offline_status(tmp_path, fake_upstream):
    demo = "mistral-example-token-NEVER-ACTIVE"
    report = configure_mistral(data_dir=tmp_path, model="mistral-small-latest", secret=demo)
    raw = (tmp_path / "app-settings.json").read_text("utf-8")
    assert demo not in raw
    assert MISTRAL_PLACEHOLDER in raw
    ciphertext = (tmp_path / "vault.enc").read_bytes()
    assert demo.encode() not in ciphertext
    assert json.loads(raw)["llm"]["base_url"] == MISTRAL_BASE_URL
    assert report["network_verified"] is False
    assert mistral_status(data_dir=tmp_path) == {
        "configured": True, "key_present": True, "ready_offline": True,
        "network_verified": False, "model": "mistral-small-latest",
    }


def test_use_existing_reconfigures_without_requiring_secret(tmp_path, fake_upstream):
    secret = "mistral-example-token-NEVER-ACTIVE"
    configure_mistral(data_dir=tmp_path, secret=secret)
    (tmp_path / "app-settings.json").unlink()
    configure_mistral(data_dir=tmp_path, use_existing=True, model="mistral-medium-latest")
    assert mistral_status(data_dir=tmp_path)["model"] == "mistral-medium-latest"
    assert fake_upstream(tmp_path / "vault.enc", tmp_path / "vault.key").get("MISTRAL_API_KEY") == secret


def test_existing_secrets_never_overwritten_on_invalid_app_settings(tmp_path, fake_upstream):
    path = tmp_path / "app-settings.json"
    path.write_text("{invalid json", "utf-8")
    with pytest.raises(MistralSetupError):
        configure_mistral(data_dir=tmp_path, secret="mistral-example-token-NEVER-ACTIVE")
    assert path.read_text("utf-8") == "{invalid json"
    assert not (tmp_path / "vault.enc").exists()


def test_existing_llm_not_dict_is_rejected():
    with pytest.raises(MistralSetupError):
        merged_app_settings({"llm": "corrupted"})


def test_cannot_use_existing_when_vault_empty(tmp_path, fake_upstream):
    with pytest.raises(MistralSetupError):
        configure_mistral(data_dir=tmp_path, use_existing=True)
    assert not (tmp_path / "app-settings.json").exists()


def test_rotated_key_still_requires_original_vault_key(tmp_path, fake_upstream):
    configure_mistral(data_dir=tmp_path, secret="mistral-example-token-NEVER-ACTIVE")
    (tmp_path / "vault.key").write_bytes(Fernet.generate_key())
    with pytest.raises(InvalidToken):
        mistral_status(data_dir=tmp_path)


def test_rejects_conflicting_key_modes(tmp_path, fake_upstream):
    with pytest.raises(MistralSetupError):
        configure_mistral(data_dir=tmp_path, use_existing=True, secret="mistral-example-token")
    with pytest.raises(MistralSetupError):
        configure_mistral(data_dir=tmp_path)
