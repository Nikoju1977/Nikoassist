"""Rôles, contrôle de portée et planification multi-agents bornée."""
from __future__ import annotations
import json
import re
from dataclasses import dataclass
from enum import Enum

class Role(str, Enum):
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    CREATOR = "creator"
    OPERATOR = "operator"

@dataclass(frozen=True)
class Subtask:
    role: Role
    objective: str

ROLE_TOOLS: dict[Role, frozenset[str]] = {
    Role.RESEARCHER: frozenset({"web_search", "web_fetch", "recall"}),
    Role.ANALYST: frozenset({"web_search", "web_fetch", "recall"}),
    Role.CREATOR: frozenset({"files", "python_execute", "shell", "skills"}),
    Role.OPERATOR: frozenset({"phone_screen", "phone_act", "phone_task",
        "computer_screen", "computer_act", "computer_task", "browser", "devices"}),
}
# Permissions de périphérique reconnues par le projet amont à la date de validation.
# Les futures méthodes device__* ne sont pas acceptées automatiquement.
ALLOWED_DEVICE_TOOLS = frozenset({
    "device__clipboard_read", "device__clipboard_write", "device__notify",
    "device__calendars", "device__calendar_list", "device__calendar_create",
    "device__calendar_update", "device__calendar_delete",
    "device__contacts_search", "device__location", "device__alarm_set",
    "device__timer_set", "device__photo_pick", "device__notifications_read",
})
MODES = frozenset({"research", "create", "act"})

def allowed_role(role: Role, mode: str) -> bool:
    if mode == "research":
        return role in (Role.RESEARCHER, Role.ANALYST)
    if mode == "create":
        return role != Role.OPERATOR
    return mode == "act"

def parse_plan(raw: str, goal: str, *, mode: str = "research",
               max_agents: int = 3) -> list[Subtask]:
    """Le LLM ne peut pas élargir les permissions en modifiant son JSON."""
    if mode not in MODES:
        mode = "research"
    max_agents = max(1, min(int(max_agents), 4))
    data = (raw or "").strip()
    if data.startswith("```"):
        data = re.sub(r"^```(?:json)?\s*", "", data, flags=re.I)
        data = re.sub(r"\s*```$", "", data)
    try:
        payload = json.loads(data)
    except (TypeError, ValueError):
        payload = None
    tasks: list[Subtask] = []
    if isinstance(payload, dict) and isinstance(payload.get("tasks"), list):
        for entry in payload["tasks"]:
            if len(tasks) >= max_agents:
                break
            if not isinstance(entry, dict):
                continue
            try:
                role = Role(entry.get("role", ""))
            except (ValueError, TypeError):
                continue
            objective = entry.get("objective")
            if allowed_role(role, mode) and isinstance(objective, str) and objective.strip():
                tasks.append(Subtask(role, objective.strip()[:900]))
    return tasks or [Subtask(Role.ANALYST, goal.strip()[:900])]

def selected_tools(role: Role, available_names: set[str]) -> list[str]:
    """Liste blanche sans agent_team, pour empêcher les appels récursifs."""
    if role == Role.OPERATOR:
        return sorted((ROLE_TOOLS[role] | (ALLOWED_DEVICE_TOOLS & available_names))
                      & available_names)
    return sorted(ROLE_TOOLS[role] & available_names)

def bounded_excerpt(text: str, limit: int = 4000) -> str:
    clean = (text or "").strip()
    return clean if len(clean) <= limit else clean[:limit] + "\n[… tronqué …]"
