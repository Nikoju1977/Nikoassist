import asyncio
import json
import unittest
from nanomuse.nikoassist.core import Role, parse_plan, selected_tools
from nanomuse.nikoassist.runtime import AgentRuntime, ApprovalRequired

class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_research_plan_excludes_operator(self):
        plan = json.dumps({"tasks": [{"role":"operator","objective":"send SMS"},
                                      {"role":"researcher","objective":"look up"}]})
        tasks = parse_plan(plan, "research", mode="research")
        self.assertEqual([t.role for t in tasks], [Role.RESEARCHER])

    async def test_unknown_tool_never_granted(self):
        self.assertEqual(selected_tools(Role.RESEARCHER, {"shell", "web_search", "agent_team"}), ["web_search"])

    async def test_requires_approval_for_action(self):
        async def execute(*args): return "ok"
        with self.assertRaises(ApprovalRequired):
            await AgentRuntime(execute).run("send message", "", {"phone_act"}, mode="act")

    async def test_timeout_is_bounded(self):
        async def execute(*args):
            await asyncio.sleep(.1)
            return "ok"
        runtime = AgentRuntime(execute, timeout_seconds=.01, max_retries=0)
        outcome = await runtime.run("research", "", {"web_search"})
        self.assertFalse(outcome.steps[0].ok)

    async def test_success_not_automatically_verified(self):
        async def execute(*args): return "completed"
        result = await AgentRuntime(execute).run("research", "", {"web_search"})
        self.assertTrue(result.steps[0].ok)
        self.assertFalse(result.verified)

    async def test_no_retry_for_operator(self):
        count = 0
        async def execute(*args):
            nonlocal count
            count += 1
            raise TimeoutError("unknown outcome")
        result = await AgentRuntime(execute, max_retries=3).run(
            "act", '{"tasks":[{"role":"operator","objective":"perform"}]}',
            {"phone_act"}, mode="act", approved=True)
        self.assertEqual(count, 1)
        self.assertFalse(result.steps[0].ok)

if __name__ == "__main__":
    unittest.main()
