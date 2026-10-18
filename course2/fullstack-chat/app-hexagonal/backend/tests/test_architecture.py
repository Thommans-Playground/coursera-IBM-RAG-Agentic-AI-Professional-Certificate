"""Architecture tests: the rules of the hexagon, checked by reading the imports. Pure and fast.

    uv run python -m tests.test_architecture
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "chatapp"
CONTEXTS = ("conversation", "knowledge")
# Libraries that belong in adapters, never in the domain or the application layer.
TECHNOLOGY = ("fastapi", "starlette", "pydantic", "psycopg", "psycopg_pool", "pgvector", "redis", "celery",
              "langchain", "langchain_core", "langchain_openai", "langchain_text_splitters", "openai", "httpx", "numpy")
# The one file allowed to reach from Conversation into Knowledge.
ALLOWED_CROSSING = "conversation/adapters/outbound/knowledge_gateway.py"


def imports(path: Path) -> list[str]:
    names = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def files(layer: str):
    for context in CONTEXTS:
        yield from (ROOT / context / layer).rglob("*.py")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def test_domain_and_application_use_no_technology() -> None:
    for layer in ("domain", "application"):
        for path in files(layer):
            bad = [m for m in imports(path) if m.split(".")[0] in TECHNOLOGY]
            assert not bad, f"{rel(path)} imports technology: {bad}"


def test_domain_depends_on_nothing_outward() -> None:
    for path in files("domain"):
        bad = [m for m in imports(path) if m.startswith("chatapp.") and (".adapters" in m or ".application" in m)]
        assert not bad, f"{rel(path)} (domain) imports an outer layer: {bad}"


def test_application_does_not_import_adapters() -> None:
    for path in files("application"):
        bad = [m for m in imports(path) if ".adapters" in m or m.startswith("chatapp.container")]
        assert not bad, f"{rel(path)} (application) imports an adapter: {bad}"


def test_contexts_only_meet_in_the_gateway() -> None:
    for context, other in (("conversation", "knowledge"), ("knowledge", "conversation")):
        for path in (ROOT / context).rglob("*.py"):
            if rel(path) == ALLOWED_CROSSING:
                continue
            bad = [m for m in imports(path) if m.startswith(f"chatapp.{other}")]
            assert not bad, f"{rel(path)} reaches into the {other} context: {bad}"


def test_gateway_uses_only_knowledge_use_cases() -> None:
    gateway = ROOT / ALLOWED_CROSSING
    if not gateway.exists():  # you create it in step 9
        return
    bad = [m for m in imports(gateway) if m.startswith("chatapp.knowledge") and not m.startswith("chatapp.knowledge.application")]
    assert not bad, f"the gateway should only use Knowledge's application layer: {bad}"


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            test()
            print("ok  ", name)
    print("ARCHITECTURE TESTS PASSED")
