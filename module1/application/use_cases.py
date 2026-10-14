from dataclasses import (
    dataclass,
    field,
)

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

from application.ports import LLMPort
from domain.settings import GenerationSettings


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
