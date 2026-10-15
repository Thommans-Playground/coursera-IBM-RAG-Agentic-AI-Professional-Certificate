from dataclasses import (
    dataclass,
    field,
)

from collections import Counter
import re

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

from application import prompt_library as prompts
from application.ports import LLMPort
from domain.settings import GenerationSettings


_FINAL = re.compile(r"final answer:\s*(.+)", re.IGNORECASE)


def _normalize(answer: str) -> str:
    """
    Normalizes the answer by stripping whitespace and converting to lowercase.

    Args:
        answer (str): The answer to normalize.
    Returns:
        str: The normalized answer.
    """
    return answer.strip().lower()


@dataclass
class RunTemplate:
    """
    A data class to hold the run template for the AI model.
    """

    llm: LLMPort
    template: PromptTemplate
    settings: GenerationSettings = field(default_factory=GenerationSettings)

    def execute(self, **variables) -> str:
        """
        Execute the run template with the provided variables.

        Args:
            **variables: The variables to fill in the prompt template.
        Returns:
            str: The generated text from the LLM.
        """
        chain = self.template | RunnableLambda(
            lambda prompt: self.llm.generate(prompt.to_string(), self.settings)
        )
        return chain.invoke(variables).strip()


@dataclass
class SelfConsistency:
    llm: LLMPort
    samples: int = 5
    settings: GenerationSettings = field(default_factory=GenerationSettings)

    def execute(self, **variables) -> str:
        chain = prompts.REASON | RunnableLambda(
            lambda prompt: self.llm.generate(prompt.to_string(), self.settings)
        )
        answers = [chain.invoke(variables).strip() for _ in range(5)]
        answer_counts = Counter(answers)
        most_common_answer, _ = answer_counts.most_common(1)[0]
        return most_common_answer
