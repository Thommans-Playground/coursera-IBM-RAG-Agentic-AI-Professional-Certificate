from typing import Protocol

from domain.settings import GenerationSettings


class LLMPort(Protocol):
    """
    A protocol that defines the interface for a Language Model (LLM) port.
    """

    def generate(self, prompt: str, settings: GenerationSettings) -> str:
        """
        Generate text based on the given prompt and generation settings.

        Args:
            prompt (str): The input prompt for text generation.
            settings (GenerationSettings): The settings for text generation.
        Returns:
            str: The generated text.
        """
