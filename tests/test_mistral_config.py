"""Static safety checks for the interactive Mistral setup (no real credentials)."""
from pathlib import Path
import ast

def test_mistral_setup_cli_syntax():
    source = Path("scripts/configure_mistral.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "getpass.getpass" in source
    assert "secret=secret" in source
    assert "sys.stdin.isatty()" in source

def test_mistral_setup_uses_native_encrypted_vault():
    source = Path("nanomuse/nikoassist/mistral.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "CredentialVault" in source
    assert "vault.set(MISTRAL_SECRET_NAME" in source
    assert "MISTRAL_PLACEHOLDER" in source
    assert "save_app_settings" in source

def test_documentation_never_requests_chat_secret():
    text = Path("docs/MISTRAL_VAULT.md").read_text(encoding="utf-8")
    assert "Ne la collez pas dans ChatGPT" in text
    assert "--check" in text
