"""Run every ```python block in a markdown file against a fake chat model.

Usage: uv run python check_snippets.py path/to/tutorial.md

Blocks starting with a "# needs:" comment are skipped (missing package or credentials).
This verifies structure and wiring only; it never calls a real API.
"""
import itertools
import os
import re
import sys
import traceback

import langchain_openai
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

REPLY = '{"name": "Japan", "capital": "Tokyo", "questions": ["q1", "q2", "q3"]}'  # valid JSON for parsers


class FakeChat(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        # Stateless on purpose: agents may re-bind tools on every model call.
        def respond(messages):
            if tools and not any(getattr(m, "type", "") == "tool" for m in _as_list(messages)):
                tool = tools[0]
                args = {key: "x" for key in getattr(tool, "args", {})}  # dummy value per parameter
                return AIMessage(content="", tool_calls=[{"name": tool.name, "args": args, "id": "call_1"}])
            return AIMessage(content="done")

        return RunnableLambda(respond)


def _as_list(messages):
    return messages.to_messages() if hasattr(messages, "to_messages") else list(messages)


def fake_chat_openai(**_kwargs):
    return FakeChat(messages=itertools.cycle([AIMessage(content=REPLY)]))


def fake_embeddings(**_kwargs):
    return DeterministicFakeEmbedding(size=32)  # same text -> same vector, no API call


langchain_openai.ChatOpenAI = fake_chat_openai
langchain_openai.OpenAIEmbeddings = fake_embeddings
os.environ.setdefault("USER_AGENT", "tutorial-check")

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
