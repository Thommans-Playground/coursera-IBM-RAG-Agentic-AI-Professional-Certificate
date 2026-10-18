"""What a streamed answer is made of. The inbound adapter turns these into server-sent events."""
from dataclasses import dataclass

from chatapp.conversation.domain.message import Source


@dataclass(frozen=True)
class TokenGenerated:
    text: str


@dataclass(frozen=True)
class SourcesFound:
    sources: tuple[Source, ...]


@dataclass(frozen=True)
class AnswerFailed:
    message: str


@dataclass(frozen=True)
class AnswerFinished:
    pass


ChatEvent = TokenGenerated | SourcesFound | AnswerFailed | AnswerFinished
