"""Offline regression tests for the source-separated OpenMontage bridge."""
from __future__ import annotations

import json

import pytest
from nanomuse.nikoassist.openmontage import (
    OpenMontageError, installed_root, pipelines, preflight, prepare, status,
)
from nanomuse.nikoassist.core import Role, selected_tools


@pytest.fixture
def montage(tmp_path, monkeypatch):
    root = tmp_path / "OpenMontage"
    (root / "pipeline_defs").mkdir(parents=True)
    (root / "lib").mkdir()
    (root / "lib/pipeline_loader.py").write_text("# fixture\n")
    (root / "pipeline_defs/animated-explainer.yaml").write_text("name: animated-explainer\n")
    (root / "pipeline_defs/documentary-montage.yaml").write_text("name: documentary-montage\n")
    monkeypatch.setenv("NIKOASSIST_OPENMONTAGE_ROOT", str(root))
    return root


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("NIKOASSIST_OPENMONTAGE_ROOT", raising=False)
    with pytest.raises(OpenMontageError, match="n'est pas configuré"):
        installed_root()


def test_list_reads_known_pipelines_only(montage):
    (montage / "pipeline_defs/INVALID SPACE.yaml").write_text("junk")
    assert pipelines() == ["animated-explainer", "documentary-montage"]
    assert preflight()["automated_rendering"] is False


def test_prepare_is_atomic_and_non_destructive(montage):
    response = prepare(pipeline="animated-explainer", project="un-projet",
                       brief="Vidéo explicative de sécurité et de confiance", duration_seconds=60)
    assert response["status"] == "prepared_not_rendered"
    request = montage / "projects/nikoassist-un-projet/nikoassist-request.json"
    doc = json.loads(request.read_text())
    assert doc["pipeline"] == "animated-explainer"
    assert doc["render_executed"] is False
    assert status(project="un-projet")["render_verified"] is False
    with pytest.raises(OpenMontageError, match="existe déjà"):
        prepare(pipeline="animated-explainer", project="un-projet",
                brief="Une deuxième tentative qui ne doit rien écraser")
    assert json.loads(request.read_text()) == doc


@pytest.mark.parametrize("project", ["../evil", "Test Upper", "../..", "", "a" * 41])
def test_denies_path_traversal(montage, project):
    with pytest.raises(OpenMontageError):
        prepare(pipeline="animated-explainer", project=project,
                brief="Une description suffisamment longue")


@pytest.mark.parametrize("duration", [0, -1, 1801, True, "60", 60.1])
def test_denies_invalid_duration(montage, duration):
    with pytest.raises(OpenMontageError):
        prepare(pipeline="animated-explainer", project="essai",
                brief="Une description suffisamment longue", duration_seconds=duration)


def test_unknown_pipeline_does_not_create_project(montage):
    with pytest.raises(OpenMontageError):
        prepare(pipeline="nonexistent", project="test",
                brief="Une description suffisamment longue")
    assert not (montage / "projects").exists()


def test_symlink_project_blocked(montage, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (montage / "projects").symlink_to(outside, target_is_directory=True)
    with pytest.raises(OpenMontageError):
        prepare(pipeline="animated-explainer", project="essai",
                brief="Une description suffisamment longue")
    assert not list(outside.iterdir())


def test_file_presence_does_not_claim_render_verified(montage):
    prepare(pipeline="animated-explainer", project="essai",
            brief="Une description suffisamment longue")
    renders = montage / "projects/nikoassist-essai/renders"
    renders.mkdir()
    (renders / "broken.mp4").write_bytes(b"NOT_A_VIDEO")
    report = status(project="essai")
    assert report["state"] == "video_files_present_unverified"
    assert report["render_verified"] is False


def test_role_permissions_allow_only_creator(montage):
    available = {"openmontage", "shell", "files", "skills"}
    assert "openmontage" in selected_tools(Role.CREATOR, available)
    assert "openmontage" not in selected_tools(Role.RESEARCHER, available)
    assert "openmontage" not in selected_tools(Role.OPERATOR, available)
