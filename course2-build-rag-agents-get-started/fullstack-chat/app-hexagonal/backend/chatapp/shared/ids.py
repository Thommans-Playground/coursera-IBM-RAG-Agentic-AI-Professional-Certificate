"""The shared kernel: the few things every context needs. Keep it tiny."""
import uuid


def new_id() -> str:
    return uuid.uuid4().hex[:8]
