"""The Conversation entity and its rules. No database, no web, no AI in here."""
from dataclasses import dataclass

from chatapp.shared.ids import new_id

DEFAULT_TITLE = "New chat"
TITLE_LENGTH = 40


class InvalidQuestion(ValueError):
    pass


def clean_question(text: str) -> str:
    text = text.strip()
    if not text:
        raise InvalidQuestion("The message is empty.")
    return text


@dataclass
class Conversation:
    id: str
    title: str = DEFAULT_TITLE

    @classmethod
    def start(cls) -> "Conversation":
        return cls(id=new_id())

    def name_from(self, first_message: str) -> bool:
        """The first message names the chat. Returns True when the title changed."""
        if self.title != DEFAULT_TITLE:
            return False
        self.title = first_message[:TITLE_LENGTH]
        return True
