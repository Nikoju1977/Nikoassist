"""Deterministic safety and resource policy for NikoAssist.

Model output proposes work, but never grants permissions. No external imports.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Role(str, Enum):
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    CREATOR = "creator"
    OPERATOR = "operator"


@dataclass(frozen=True)
class Subtask:
    role: Role
    objective: str


@dataclass(frozen=True)
class ExecutionBudget:
    max_agents: int = 3
    steps_per_agent: int = 8
    max_goal_chars: int = 2000
    max_objective_chars: int = 900
    max_notes_chars: int = 6000
    max_response_chars: int = 12000
    seconds_per_agent: int = 600
    seconds_per_model_call: int = 90

    def bounded(self) -> "ExecutionBudget":
        return ExecutionBudget(
            max_agents=clamp_int(self.max_agents, 3, 1, 4),
            steps_per_agent=clamp_int(self.steps_per_agent, 8, 2, 12),
            max_goal_chars=clamp_int(self.max_goal_chars, 2000, 100, 4000),
            max_objective_chars=clamp_int(self.max_objective_chars, 900, 100, 1500),
            max_notes_chars=clamp_int(self.max_notes_chars, 6000, 200, 10000),
            max_response_chars=clamp_int(self.max_response_chars, 12000, 500, 20000),
            seconds_per_agent=clamp_int(self.seconds_per_agent, 600, 30, 1800),
            seconds_per_model_call=clamp_int(self.seconds_per_model_call, 90, 10, 240),
        )


ROLE_TOOLS: dict[Role, frozenset[str]] = {
    Role.RESEARCHER: frozenset({"web_search", "web_fetch", "recall"}),
    Role.ANALYST: frozenset({"web_search", "web_fetch", "recall"}),
    Role.CREATOR: frozenset({"files", "skills"}),
    Role.OPERATOR: frozenset({
        "phone_screen", "phone_act", "phone_task", "computer_screen",
        "computer_act", "computer_task", "browser", "devices",
    }),
}

# Never approve new, unreviewed device__* capabilities automatically.
# Side-effecting methods are excluded from this delegation allowlist.
ALLOWED_DEVICE_TOOLS: frozenset[str] = frozenset({
    "device__clipboard_read", "device__notify", "device__calendars",
    "device__calendar_list", "device__contacts_search", "device__location",
    "device__photo_pick", "device__notifications_read",
})

MODES = frozenset({"research", "create", "act"})
_MAX_JSON_CHARS = 24000


def clamp_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        if isinstance(value, bool):
            return default
        n = int(value)
    except (TypeError, ValueError, OverflowError):
        n = default
    return max(low, min(n, high))


def allowed_role(role: Role, mode: str) -> bool:
    if mode == "research":
        return role in (Role.RESEARCHER, Role.ANALYST)
    if mode == "create":
        return role in (Role.RESEARCHER, Role.ANALYST, Role.CREATOR)
    return mode == "act"


def parse_plan(raw: str, goal: str, *, mode: str = "research", max_agents: int = 3) -> list[Subtask]:
    """Strictly parse an untrusted plan; ignore extra fields and deduplicate."""
    if mode not in MODES:
        mode = "research"
    max_agents = clamp_int(max_agents, 3, 1, 4)
    stripped = (raw if isinstance(raw, str) else "").strip()
    if len(stripped) > _MAX_JSON_CHARS:
        stripped = ""
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\\s*```$", "", stripped)
    try:
        payload = json.loads(stripped)
    except (TypeError, ValueError, RecursionError):
        payload = None

    tasks: list[Subtask] = []
    seen: set[tuple[Role, str]] = set()
    if isinstance(payload, dict) and isinstance(payload.get("tasks"), list):
        for entry in payload["tasks"][:24]:
            if len(tasks) >= max_agents:
                break
            if not isinstance(entry, dict):
                continue
            try:
                role = Role(entry.get("role", ""))
            except (ValueError, TypeError):
                continue
            objective = entry.get("objective")
            if not allowed_role(role, mode) or not isinstance(objective, str):
                continue
            objective = objective.replace("\x00", "").strip()[:900]
            key = (role, " ".join(objective.casefold().split()))
            if objective and key not in seen:
                seen.add(key)
                tasks.append(Subtask(role, objective))
    fallback = (goal if isinstance(goal, str) else "").strip()[:900]
    return tasks or [Subtask(Role.ANALYST, fallback)]


def selected_tools(role: Role, available_names: set[str]) -> list[str]:
    """Explicit privilege subset; never include agent_team (recursion)."""
    allowed = ROLE_TOOLS[role]
    if role == Role.OPERATOR:
        allowed = allowed | ALLOWED_DEVICE_TOOLS
    return sorted(allowed & available_names)


def bounded_excerpt(text: str, limit: int = 4000) -> str:
    limit = clamp_int(limit, 4000, 64, 20000)
    clean = (text if isinstance(text, str) else str(text or "")).strip()
    return clean if len(clean) <= limit else clean[:limit] + "\n[… tronqué …]"


def report_status(*, error: str | None, tool_errors: list[str], tool_calls: int) -> str:
    """LLM output alone cannot prove a side effect was successful."""
    if error:
        return "failed"
    if tool_errors:
        return "partial"
    return "reported" if tool_calls else "unverified"
