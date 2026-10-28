from collections import defaultdict
from threading import Lock

MAX_HISTORY = 10

_conversations = defaultdict(list)
_lock = Lock()


def get_conversation_history(file_id: str) -> list[dict]:
    """Return recent conversation messages for a workbook."""
    with _lock:
        return [
            message.copy()
            for message in _conversations[file_id][-MAX_HISTORY:]
        ]


def add_conversation_message(
    file_id: str,
    role: str,
    content: str,
) -> None:
    """Save a user or assistant message."""
    if role not in {"user", "assistant"}:
        raise ValueError("Invalid conversation role.")

    with _lock:
        _conversations[file_id].append(
            {
                "role": role,
                "content": content,
            }
        )

        _conversations[file_id] = (
            _conversations[file_id][-MAX_HISTORY:]
        )


def clear_conversation_history(file_id: str) -> None:
    """Clear conversation history for a workbook."""
    with _lock:
        _conversations.pop(file_id, None)