"""Fail-closed regression tests for the NikoAssist delegation policy."""
import json
from nanomuse.nikoassist.core import Role, parse_plan, selected_tools, should_halt


def test_abort_on_unknown_or_partial_results():
    for mode in ("research", "create", "act"):
        for status in ("unknown", "partial", "failed"):
            assert should_halt(status, mode)


def test_act_must_not_chain_an_unverified_answer():
    assert should_halt("unverified", "act")
    assert not should_halt("unverified", "research")
    assert not should_halt("reported", "act")


def test_untrusted_plan_cannot_select_phone_in_research():
    raw = json.dumps({"tasks": [
        {"role": "operator", "objective": "phone_act", "tools": ["phone_act"]},
        {"role": "researcher", "objective": "verify"},
    ]})
    plan = parse_plan(raw, "goal", mode="research")
    assert [(t.role, t.objective) for t in plan] == [(Role.RESEARCHER, "verify")]
    assert "phone_act" not in selected_tools(
        Role.RESEARCHER, {"phone_act", "web_search", "agent_team"}
    )
