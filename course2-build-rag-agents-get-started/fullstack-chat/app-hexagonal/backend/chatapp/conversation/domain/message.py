from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class Source:
    """A passage an answer was based on. Conversation's own word for it: it does not import Knowledge's."""
    title: str
    url: str
    text: str
    score: float


@dataclass(frozen=True)
class Message:
    role: Role
    content: str
    sources: tuple[Source, ...] = ()
