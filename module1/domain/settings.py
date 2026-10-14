from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationSettings:
    """
    A data class to hold the generation settings for the AI model.
    """

    temperature: float = 0.7
    max_tokens: int = 150
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
