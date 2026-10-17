from course1.module1.domain.settings import GenerationSettings


class FakeLLM:
    """
    A fake implementation of a Language Model (LLM) for testing purposes.
    """

    def __init__(self, reply: str = "fake reply"):
        self.reply = reply
        self.calls: list[tuple[str, GenerationSettings]] = []

    def generate(self, prompt: str, settings: GenerationSettings) -> str:
        self.calls.append((prompt, settings))
        return self.reply
