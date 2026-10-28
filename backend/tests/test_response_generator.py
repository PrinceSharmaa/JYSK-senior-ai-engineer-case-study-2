from types import SimpleNamespace

from backend.app.agents import response_generator


def test_response_generator(monkeypatch):

    captured = {}

    def fake_generate(contents, config):
        captured["prompt"] = contents

        return SimpleNamespace(
            text=(
                "The dataset contains sales information. "
                "The Quantity column has no missing values."
            )
        )

    monkeypatch.setattr(
        response_generator,
        "generate_with_retry",
        fake_generate,
    )

    result = response_generator.generate_agent_response(
        user_request="Analyze the dataset",
        actions_executed=[
            {
                "tool": "analyze_missing_values",
                "arguments": {
                    "sheet_name": "Sales"
                },
                "result": {
                    "Quantity": {
                        "missing_count": 0
                    }
                },
            }
        ],
    )

    assert "sales information" in result
    assert "missing values" in result

    assert "analyze_missing_values" in captured["prompt"]
    assert "missing_count" in captured["prompt"]