"""Execution engine with bounded retries, timeouts, auditing and approval gates."""
from __future__ import annotations
import asyncio
import inspect
import math
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable
from .core import Role, Subtask, parse_plan, selected_tools, bounded_excerpt, mutating_role

class ApprovalRequired(Exception):
    """An irreversible operation needs explicit user approval."""

@dataclass
class StepResult:
    role: str
    objective: str
    ok: bool
    output: str
    attempts: int
    duration_ms: int

@dataclass
class RunResult:
    goal: str
    steps: list[StepResult] = field(default_factory=list)
    verified: bool = False
    summary: str = ""

class AgentRuntime:
    """A controlled coordinator. Caller must supply the real nanoMuse tool gateway.

    execute(role, objective, allowed_tools) -> str is the only execution interface.
    The gateway MUST enforce Sentinel approvals for every tool invocation.
    """
    def __init__(self, execute: Callable[..., Awaitable[str]], *,
                 timeout_seconds: float = 45, max_retries: int = 1,
                 max_steps: int = 4, backoff_seconds: float = .25,
                 audit: Callable[[dict], Any] | None = None):
        if not callable(execute):
            raise TypeError("execute must be callable")
        if not 0 < timeout_seconds <= 600:
            raise ValueError("invalid timeout")
        if type(max_retries) is not int or not 0 <= max_retries <= 3:
            raise ValueError("invalid retry count")
        if type(max_steps) is not int or not 1 <= max_steps <= 4:
            raise ValueError("invalid step count")
        self.execute = execute
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_steps = max_steps
        if not math.isfinite(backoff_seconds) or backoff_seconds < 0:
            raise ValueError("invalid backoff")
        self.backoff_seconds = min(backoff_seconds, 5)
        self.audit = audit

    def _audit(self, event: dict) -> None:
        if self.audit:
            try:
                self.audit(event)
            except Exception:
                pass  # Logging must not override an execution outcome.

    async def run(self, goal: str, plan_json: str, available_tools: set[str],
                  *, mode: str = "research", approved: bool = False) -> RunResult:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("goal is required")
        if mode not in ("research", "create", "act"):
            raise ValueError("invalid mode")
        if mode in ("create", "act") and approved is not True:
            raise ApprovalRequired("User must approve creation or action mode")
        plan = parse_plan(plan_json, goal, mode=mode, max_agents=self.max_steps)
        result = RunResult(goal=goal)
        for step in plan[:self.max_steps]:
            tools = selected_tools(step.role, set(available_tools))
            # Tool restrictions are enforced again in the nanoMuse gateway.
            started = time.monotonic()
            attempts, output, ok = 0, "", False
            for retry in range(self.max_retries + 1):
                attempts += 1
                try:
                    response = self.execute(step.role, step.objective, tools)
                    if not inspect.isawaitable(response):
                        raise TypeError("execute must return an awaitable")
                    value = await asyncio.wait_for(response, timeout=self.timeout_seconds)
                    output = value if isinstance(value, str) else ""
                    ok = bool(output.strip())
                    if not ok:
                        output = "Empty agent response"
                    break
                except (ApprovalRequired, asyncio.CancelledError):
                    raise
                except (TimeoutError, OSError, ConnectionError) as exc:
                    output = f"{type(exc).__name__}: {exc}"
                    # Never replay operations with side effects automatically.
                    if mutating_role(step.role) or retry >= self.max_retries:
                        break
                    await asyncio.sleep(self.backoff_seconds * (2 ** retry))
                except Exception as exc:
                    output = f"{type(exc).__name__}: {exc}"
                    break
            record = StepResult(step.role.value, step.objective, ok,
                                bounded_excerpt(output), attempts,
                                round((time.monotonic() - started) * 1000))
            result.steps.append(record)
            self._audit({"role": record.role, "ok": ok,
                         "attempts": attempts, "duration_ms": record.duration_ms})
            if not ok or mutating_role(step.role):
                break
        result.verified = False  # Explicit verifier required; never infer from a fluent answer.
        result.summary = "\n".join(
            f"[{s.role}] {'REPORTED / UNVERIFIED' if s.ok else 'FAILED'}: {s.output}" for s in result.steps
        )
        return result
