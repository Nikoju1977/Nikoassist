"""Offline checks: never use a real API key."""
from pathlib import Path
import ast

def test_mistral_config_uses_vault():
    source = Path("scripts/configure_mistral.py").read_text()
    ast.parse(source)
    assert "CredentialVault" in source
    assert "getpass.getpass" in source
    assert "vault.set(VAULT_NAME" in source

def test_mistral_config_contains_no_literal_secret():
    source = Path("scripts/configure_mistral.py").read_text()
    assert "api_key = \"{PLACEHOLDER}\"" in source
    assert 'provider = "mistral"' in source

def test_documentation_recommends_local_entry():
    text = Path("docs/MISTRAL_VAULT.md").read_text()
    assert "terminal local" in text
    assert "aucune clé n'a été créée" in text
