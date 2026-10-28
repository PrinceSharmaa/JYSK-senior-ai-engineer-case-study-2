from uuid import uuid4

from backend.app.services.conversation_memory import (
    get_conversation_history,
    add_conversation_message,
    clear_conversation_history,
)


def test_conversation_memory():
    file_id = str(uuid4())

    add_conversation_message(
        file_id,
        "user",
        "Create a Revenue column.",
    )

    add_conversation_message(
        file_id,
        "assistant",
        "Revenue column created.",
    )

    history = get_conversation_history(file_id)

    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"

    clear_conversation_history(file_id)

    assert get_conversation_history(file_id) == []


def test_memory_isolation():
    first_id = str(uuid4())
    second_id = str(uuid4())

    add_conversation_message(
        first_id,
        "user",
        "Analyze sales.",
    )

    assert len(get_conversation_history(first_id)) == 1
    assert get_conversation_history(second_id) == []

    clear_conversation_history(first_id)