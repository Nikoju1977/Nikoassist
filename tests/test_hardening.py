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


def test_control_calls_are_not_business_evidence():
    from nanomuse.nikoassist.core import business_tool_calls, report_status
    names = business_tool_calls(["terminate", "agent_team"])
    assert names == []
    assert report_status(error=None, tool_errors=[], tool_calls=len(names)) == "unverified"
    assert business_tool_calls(["web_search", "terminate"]) == ["web_search"]


def test_mutating_delegation_stops_even_after_report():
    from nanomuse.nikoassist.core import halt_delegation
    assert halt_delegation("reported", "create", Role.CREATOR)
    assert halt_delegation("reported", "act", Role.OPERATOR)
    assert not halt_delegation("reported", "act", Role.RESEARCHER)


def test_total_budget_bounded():
    from nanomuse.nikoassist.core import ExecutionBudget
    assert ExecutionBudget(seconds_per_mission=1).bounded().seconds_per_mission == 30
    assert ExecutionBudget(seconds_per_mission=99999).bounded().seconds_per_mission == 3600
