from typing import Any, Protocol

from domain.settings import GenerationSettings


class LLMPort(Protocol):
    """
    A protocol that defines the interface for a Language Model (LLM) port.
    """

    def generate_text(self, prompt: str, settings: GenerationSettings) -> Any:
        """
        Generate text based on the given prompt and generation settings.

        Args:
            prompt (str): The input prompt for text generation.
            settings (GenerationSettings): The settings for text generation.
        Returns:
            Any: The generated text.
        """
