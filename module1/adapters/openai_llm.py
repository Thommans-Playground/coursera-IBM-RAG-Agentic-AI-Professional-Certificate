from langchain_openai import ChatOpenAI
from domain.settings import GenerationSettings


class OpenAILLM:
    """
    A class to interact with OpenAI's language model API.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the OpenAILLM instance.
        """
        self._client = ChatOpenAI(model=model)

    def generate(self, prompt: str, settings: GenerationSettings) -> str:
        """
        Generate text based on the given prompt and generation settings.

        Args:
            prompt (str): The input prompt for text generation.
            settings (GenerationSettings): The settings for text generation.
        Returns:
            str: The generated text from OpenAI's API.
        """

        message = self._client.invoke(
            prompt,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            top_p=settings.top_p,
            frequency_penalty=settings.frequency_penalty,
            presence_penalty=settings.presence_penalty,
        )

        return message.content
