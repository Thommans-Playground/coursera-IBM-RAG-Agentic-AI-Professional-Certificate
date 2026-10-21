"""Pure domain tests. The domain has no database, web or AI code, so these need no services and no fakes.

    uv run python -m tests.test_domain
"""
from chatapp.conversation.domain.conversation import DEFAULT_TITLE, TITLE_LENGTH, Conversation, InvalidQuestion, clean_question
from chatapp.knowledge.domain.catalog import CATALOG, entry_for
from chatapp.knowledge.domain.document import Document, DocumentStatus


def test_first_message_names_the_conversation() -> None:
    c = Conversation.start()
    assert c.title == DEFAULT_TITLE
    first = "What is SQL injection and how do I prevent it?"
    assert c.name_from(first) is True
    assert c.title == first[:TITLE_LENGTH] and len(c.title) == TITLE_LENGTH
    assert c.name_from("A second message") is False  # later messages do not rename it
    assert c.title.startswith("What is SQL")


def test_question_must_not_be_blank() -> None:
    assert clean_question("  hello  ") == "hello"
    for blank in ("", "   ", "\n"):
        try:
            clean_question(blank)
        except InvalidQuestion:
            continue
        raise AssertionError(f"{blank!r} should be rejected")


def test_document_life_cycle() -> None:
    doc = Document.queued(entry_for("A05:2025"))
    assert doc.status is DocumentStatus.QUEUED and doc.title == "A05:2025 Injection"
    assert doc.url == "https://owasp.org/Top10/2025/A05_2025-Injection/"
    doc.start()
    assert doc.status is DocumentStatus.PROCESSING
    doc.finish(16)
    assert (doc.status, doc.chunks, doc.error) == (DocumentStatus.READY, 16, "")
    doc.fail("x" * 500)
    assert doc.status is DocumentStatus.FAILED and len(doc.error) == 200
    doc.requeue()
    assert (doc.status, doc.error) == (DocumentStatus.QUEUED, "")


def test_embedding_text_puts_the_title_first() -> None:
    doc = Document.queued(entry_for("A05:2025"))
    assert doc.embedding_text("Use parameterized queries.") == "A05:2025 Injection\n\nUse parameterized queries."


def test_catalog_is_the_ten_owasp_categories() -> None:
    assert len(CATALOG) == 10
    assert [e.key for e in CATALOG] == [f"A{n:02d}:2025" for n in range(1, 11)]
    assert len({e.slug for e in CATALOG}) == 10


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            test()
            print("ok  ", name)
    print("DOMAIN TESTS PASSED")
