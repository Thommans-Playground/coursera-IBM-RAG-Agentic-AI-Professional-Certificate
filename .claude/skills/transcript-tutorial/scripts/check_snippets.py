"""Run every ```python block in a markdown file against a fake chat model.

Usage: uv run python check_snippets.py path/to/tutorial.md

Blocks starting with a "# needs:" comment are skipped (missing package or credentials).
This verifies structure and wiring only; it never calls a real API.
"""
import itertools
import re
import sys
import traceback

import langchain_openai
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

REPLY = '{"name": "Japan", "capital": "Tokyo"}'  # valid JSON, also parses as a list


class FakeChat(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        calls = {"n": 0}

        def respond(_messages):
            calls["n"] += 1
            if calls["n"] == 1 and tools:
                tool = tools[0]
                args = {key: "x" for key in getattr(tool, "args", {})}  # dummy value per parameter
                return AIMessage(content="", tool_calls=[{"name": tool.name, "args": args, "id": "call_1"}])
            return AIMessage(content="done")

        return RunnableLambda(respond)


def fake_chat_openai(**_kwargs):
    return FakeChat(messages=itertools.cycle([AIMessage(content=REPLY)]))


langchain_openai.ChatOpenAI = fake_chat_openai

source = open(sys.argv[1]).read()
blocks = re.findall(r"```python\n(.*?)```", source, re.S)
namespace, failures = {}, 0
for index, block in enumerate(blocks):
    if block.lstrip().startswith("# needs:"):
        print(f"block {index}: skipped")
        continue
    try:
        exec(block, namespace)
        print(f"block {index}: ok")
    except Exception:
        failures += 1
        print(f"block {index}: FAILED\n{block[:300]}")
        traceback.print_exc(limit=3)

print(f"\n{len(blocks)} blocks, {failures} failed")
sys.exit(1 if failures else 0)
