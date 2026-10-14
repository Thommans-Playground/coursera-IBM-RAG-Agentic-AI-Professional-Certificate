from collections.abc import Mapping
from typing import Any

from .ports import TextGenerationPort


class WatsonxTextGenerationAdapter:
    def __init__(
        self,
        *,
        model_id: str = "ibm/granite-4-h-small",
        url: str,
        project_id: str,
        api_key: str | None = None,
        default_params: Mapping[str, Any] | None = None,
    ) -> None:
        from langchain_ibm import WatsonxLLM

        self._llm = WatsonxLLM(
            model_id=model_id,
            url=url,
            project_id=project_id,
            api_key=api_key,
            params=dict(default_params or {}),
        )

    def generate(
        self,
        prompt: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> str:
        llm = self._llm
        if params:
            llm = llm.bind(params=dict(params))
        return str(llm.invoke(prompt))


class OpenAITextGenerationAdapter:
    def __init__(
        self,
        *,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        default_params: Mapping[str, Any] | None = None,
    ) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._default_params = dict(default_params or {})

    def generate(
        self,
        prompt: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> str:
        request_params = _openai_params(self._default_params | dict(params or {}))
        response = self._client.responses.create(
            model=self._model,
            input=prompt,
            **request_params,
        )
        return response.output_text


def _openai_params(params: Mapping[str, Any]) -> dict[str, Any]:
    translated = dict(params)
    if "max_new_tokens" in translated and "max_output_tokens" not in translated:
        translated["max_output_tokens"] = translated.pop("max_new_tokens")
    translated.pop("min_new_tokens", None)
    translated.pop("top_k", None)
    return translated


TextGenerationAdapter = WatsonxTextGenerationAdapter | OpenAITextGenerationAdapter
