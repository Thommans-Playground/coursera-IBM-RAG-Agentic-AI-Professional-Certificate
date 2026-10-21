class ConversationError(Exception):
    """Base class for the things that can go wrong in the Conversation use cases."""


class ConversationNotFound(ConversationError):
    pass


class RateLimitExceeded(ConversationError):
    pass


class KnowledgeBaseEmpty(ConversationError):
    pass
