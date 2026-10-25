"""Offline simulation for NikoAssist's real multi-agent tool dispatch contract.

Tests role scoping without provider keys or access to a phone.
"""
from __future__ import annotations

import asyncio
import copy
import importlib
import sys
import types
from enum import Enum
from types import SimpleNamespace
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
    SAFE = "safe"
    MODERATE = "moderate"
    SENSITIVE = "sensitive"


class MessageRole(str, Enum):
    ASSISTANT = "assistant"
    TOOL = "tool"


class FakeToolResult:
    def __init__(self, output: str = "", error: str | None = None):
        self.output = output
        self.error = error

    @classmethod
    def fail(cls, reason: str):
        return cls(error=reason)


class FakeMessage:
    @classmethod
    def system(cls, content: str):
        return SimpleNamespace(role="system", content=content)

    @classmethod
    def user(cls, content: str):
        return SimpleNamespace(role="user", content=content)


class FakeBaseTool(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    risk: RiskLevel = RiskLevel.SAFE


class FakeCollection:
    def __init__(self, *tools):
        self.tools = list(tools)

    def __iter__(self):
        return iter(self.tools)


class FakeTerminate:
    name = "terminate"


class FakeMuseAgent:
    instances: list = []

    def __init__(self, *, settings, llm, tools, sentinel, **kwargs):
        self.settings = settings
        self.llm = llm
        self.tools = tools
        self.sentinel = sentinel
        self.messages = []
        self.__class__.instances.append(self)

    async def run(self, text, purpose=None):
        return f"Mission simulée par {self.settings.agent.name}"


def test_agents_are_limited_and_share_sentinel(monkeypatch):
    def stub(name, **contents):
        module = types.ModuleType(name)
        for key, val in contents.items():
            setattr(module, key, val)
        monkeypatch.setitem(sys.modules, name, module)

    stub("nanomuse.agent", MuseAgent=FakeMuseAgent)
    stub("nanomuse.llm", __path__=[])
    stub("nanomuse.llm.base", BaseLLM=type("BaseLLM", (), {}))
    stub("nanomuse.schema", Message=FakeMessage, RiskLevel=RiskLevel, Role=MessageRole,
         ToolResult=FakeToolResult)
    stub("nanomuse.tools", __path__=[])
    stub("nanomuse.tools.base", BaseTool=FakeBaseTool,
         CallAssessment=type("CallAssessment", (), {
             "__init__": lambda self, **kwargs: self.__dict__.update(kwargs)
         }),
         ToolCollection=FakeCollection,
         int_arg=lambda n, default, low, high: min(max(int(n), low), high))
    stub("nanomuse.tools.terminate", Terminate=FakeTerminate)

    sys.modules.pop("nanomuse.nikoassist.tool", None)
    module = importlib.import_module("nanomuse.nikoassist.tool")

    class FakeLLM:
        def __init__(self):
            self.responses = [
                '{"tasks":[{"role":"operator","objective":"Act on phone"},'
                '{"role":"researcher","objective":"Read sources"}]}',
                "Contrôle critique",
                "Rapport d'équipe",
            ]

        async def ask(self, messages, **kwargs):
            return SimpleNamespace(content=self.responses.pop(0))

    class Settings:
        def __init__(self):
            self.agent = SimpleNamespace(name="NikoAssist", max_steps=30, instructions="")

        def model_copy(self, deep=False):
            return copy.deepcopy(self)

    app = SimpleNamespace(
        llm=FakeLLM(),
        settings=Settings(),
        sentinel=object(),
        ui=object(),
        audit=object(),
        memory=None,
        goals=None,
        calendar=None,
        contacts=None,
        skills=None,
        tools=[SimpleNamespace(name=n) for n in (
            "agent_team", "web_search", "web_fetch", "phone_act", "shell",
            "device__clipboard_read", "device__secret_dump", "files",
        )],
    )
    FakeMuseAgent.instances.clear()
    team = module.NikoAssistTeamTool(app=app)
    assert team.assess({"mode": "act", "goal": "Mission"}).risk == RiskLevel.SENSITIVE
    assert team.assess({"mode": "research", "goal": "Mission"}).risk == RiskLevel.MODERATE

    result = asyncio.run(team.execute(goal="Faire deux tâches", mode="act", max_agents=4))
    assert "NikoAssist | 2 sous-agent(s)" in result.output
    assert len(FakeMuseAgent.instances) == 2
    operator, researcher = FakeMuseAgent.instances
    assert operator.settings.agent.max_steps == 8
    assert researcher.settings.agent.max_steps == 8
    assert operator.sentinel is app.sentinel and researcher.sentinel is app.sentinel
    assert {x.name for x in operator.tools} == {
        "terminate", "phone_act", "device__clipboard_read",
    }
    assert {x.name for x in researcher.tools} == {
        "terminate", "web_search", "web_fetch",
    }
    assert "device__secret_dump" not in result.output
    assert not app.llm.responses
