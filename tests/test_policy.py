"""Offline reliability and security regressions for NikoAssist."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

from nanomuse.nikoassist.core import (
    ExecutionBudget, Role, bounded_excerpt, clamp_int, parse_plan,
    report_status, selected_tools,
)


def test_safe_fallback_on_invalid_json():
    assert parse_plan("{broken", "goal", mode="act")[0].role == Role.ANALYST


def test_research_cannot_escalate():
    raw = json.dumps({"tasks": [
        {"role": "operator", "objective": "send message"},
        {"role": "creator", "objective": "write file"},
        {"role": "researcher", "objective": "compare sources"},
    ]})
    assert [t.role for t in parse_plan(raw, "goal", mode="research")] == [Role.RESEARCHER]


def test_creator_mode_denies_operator():
    raw = json.dumps({"tasks": [
        {"role": "operator", "objective": "buy something"},
        {"role": "creator", "objective": "create a file"},
    ]})
    assert [t.role for t in parse_plan(raw, "goal", mode="create")] == [Role.CREATOR]


def test_capped_agents():
    raw = json.dumps({"tasks": [
        {"role": "analyst", "objective": f"step {i}"} for i in range(20)
    ]})
    assert len(parse_plan(raw, "goal", max_agents=2)) == 2


def test_markdown_fence():
    raw = chr(96) * 3 + 'json\n{"tasks":[{"role":"analyst","objective":"study"}]}\n' + chr(96) * 3
    assert parse_plan(raw, "goal")[0].objective == "study"


def test_duplicate_tasks_removed():
    raw = json.dumps({"tasks": [
        {"role": "researcher", "objective": "  Check Facts "},
        {"role": "researcher", "objective": "check  facts"},
        {"role": "analyst", "objective": "Compare"},
    ]})
    assert len(parse_plan(raw, "goal")) == 2


def test_bad_types_and_bogus_permissions():
    raw = json.dumps({"tasks": [
        {"role": ["operator"], "objective": "take over"},
        {"role": "analyst", "objective": ["take over"]},
        {"role": "analyst", "objective": "read only", "tools": ["shell"]},
    ]})
    tasks = parse_plan(raw, "goal")
    assert len(tasks) == 1 and tasks[0].objective == "read only"


def test_large_untrusted_plan_rejected():
    assert parse_plan(" " * 24001, "goal", mode="act")[0].role == Role.ANALYST


def test_operator_allowlist_excludes_new_device_methods():
    available = {"agent_team", "device__clipboard_read", "device__calendar_create",
                 "device__calendar_delete", "device__sms_send", "browser", "shell"}
    assert selected_tools(Role.OPERATOR, available) == ["browser", "device__clipboard_read"]


def test_creator_no_shell_or_python():
    available = {"files", "skills", "shell", "python_execute", "agent_team"}
    assert selected_tools(Role.CREATOR, available) == ["files", "skills"]


def test_research_roles_only_research_tools():
    available = {"web_search", "files", "computer_task", "device__location"}
    assert selected_tools(Role.RESEARCHER, available) == ["web_search"]
    assert selected_tools(Role.ANALYST, available) == ["web_search"]


def test_budget_caps():
    bounded = ExecutionBudget(max_agents=999, steps_per_agent=999,
                              seconds_per_agent=0, seconds_per_model_call=99999).bounded()
    assert (bounded.max_agents, bounded.steps_per_agent) == (4, 12)
    assert (bounded.seconds_per_agent, bounded.seconds_per_model_call) == (30, 240)
    assert clamp_int(True, 3, 1, 4) == 3


def test_conservative_status():
    assert report_status(error="timeout", tool_errors=[], tool_calls=2) == "failed"
    assert report_status(error=None, tool_errors=["bad"], tool_calls=2) == "partial"
    assert report_status(error=None, tool_errors=[], tool_calls=2) == "reported"
    assert report_status(error=None, tool_errors=[], tool_calls=0) == "unverified"


def test_excerpt_bound():
    assert len(bounded_excerpt("x" * 50000, 100)) < 130


def _fixture(tmp_path):
    root = tmp_path / "nanoMuse"
    (root / "nanomuse").mkdir(parents=True)
    (root / "nanomuse/app.py").write_text(
        "class App:\n    def __init__(self):\n"
        "        self.tools = self._build_tools()\n"
    )
    (root / "android/src/ios/Minis.xcodeproj").mkdir(parents=True)
    (root / "android/src/ios/Minis.xcodeproj/project.pbxproj").write_text(
        "INFOPLIST_KEY_CFBundleDisplayName = nanoMuse;"
    )
    (root / "android/src/android/app/src/main/res/values-fr").mkdir(parents=True)
    (root / "android/src/android/app/src/main/res/values-fr/strings.xml").write_text(
        '<resources><string name="app_name">nanoMuse</string>'
        '<string name="license">GPL-3.0 attribution nanoMuse</string>'
        '<string name="about_minis_tagline">Original tagline</string></resources>'
    )
    return root


def _installer():
    spec = importlib.util.spec_from_file_location(
        "nikoassist_installer", Path(__file__).resolve().parents[1]
        / "scripts/install_nikoassist.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_installer_dry_run_no_change(tmp_path):
    root = _fixture(tmp_path)
    before = (root / "nanomuse/app.py").read_bytes()
    planned = _installer().apply(root, dry_run=True)
    assert "nanomuse/app.py" in planned
    assert before == (root / "nanomuse/app.py").read_bytes()
    assert not (root / "nanomuse/nikoassist").exists()


def test_installer_idempotent(tmp_path):
    root = _fixture(tmp_path)
    patch = _installer()
    changes = patch.apply(root)
    assert changes
    assert patch.apply(root) == []
    assert (root / "nanomuse/app.py").read_text().count(patch.INSTALL_MARK) == 1


def test_installer_keeps_license(tmp_path):
    root = _fixture(tmp_path)
    _installer().apply(root)
    xml = (root / "android/src/android/app/src/main/res/values-fr/strings.xml").read_text()
    assert "GPL-3.0 attribution nanoMuse" in xml
    assert "NikoAssist" in xml and "Niko Studio Design" in xml


def test_installer_invalid_anchor_cannot_partially_modify(tmp_path):
    root = _fixture(tmp_path)
    (root / "nanomuse/app.py").write_text("# changed upstream; anchor missing\n")
    import pytest
    with pytest.raises(ValueError):
        _installer().apply(root)
    assert not (root / "nanomuse/nikoassist").exists()
