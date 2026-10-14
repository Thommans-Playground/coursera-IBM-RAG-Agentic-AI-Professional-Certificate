import os
from collections.abc import Mapping
from typing import Any

from .adapters import OpenAITextGenerationAdapter, WatsonxTextGenerationAdapter
from .ports import TextGenerationPort


def create_text_generator(
    provider: str | None = None,
    *,
    default_params: Mapping[str, Any] | None = None,
) -> TextGenerationPort:
    selected_provider = (provider or os.getenv("LLM_PROVIDER", "watsonx")).lower()

    if selected_provider == "openai":
        return OpenAITextGenerationAdapter(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            default_params=default_params,
        )
    if selected_provider == "watsonx":
        return WatsonxTextGenerationAdapter(
            model_id=os.getenv("WATSONX_MODEL_ID", "ibm/granite-4-h-small"),
            url=os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
            project_id=os.environ["WATSONX_PROJECT_ID"],
            api_key=os.getenv("WATSONX_API_KEY"),
            default_params=default_params,
        )

    raise ValueError(
        f"Unsupported LLM_PROVIDER {selected_provider!r}; "
        "expected 'watsonx' or 'openai'."
    )
