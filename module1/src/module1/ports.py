from collections.abc import Mapping
from typing import Any, Protocol


class TextGenerationPort(Protocol):
    def generate(
        self,
        prompt: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> str:
        """Generate text for a prompt."""

