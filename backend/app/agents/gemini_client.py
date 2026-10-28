import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


def get_gemini_client():
    """
    Create a Gemini API client.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing from the environment."
        )

    return genai.Client(api_key=api_key)


def get_gemini_model() -> str:
    """
    Read the configured Gemini model name.
    """

    model = os.getenv("GEMINI_MODEL")

    if not model:
        raise ValueError(
            "GEMINI_MODEL is missing from the environment."
        )

    return model
import os
import time

from google import genai
from google.genai import errors


def generate_with_retry(contents, config=None):
    """
    Generate Gemini responses with retry handling.

    Uses the model already configured in .env.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing."
        )

    primary_model = os.getenv("GEMINI_MODEL")

    if not primary_model:
        raise ValueError(
            "GEMINI_MODEL is missing."
        )

    fallback_model = os.getenv(
        "GEMINI_FALLBACK_MODEL"
    )

    models = [primary_model]

    if fallback_model and fallback_model != primary_model:
        models.append(fallback_model)

    client = genai.Client(
        api_key=api_key
    )

    last_error = None

    for model in models:

        for attempt in range(3):

            try:
                return client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )

            except (
                errors.ServerError,
                errors.ClientError,
            ) as exc:

                status_code = getattr(
                    exc,
                    "code",
                    None,
                )

                if status_code not in {
                    429,
                    500,
                    502,
                    503,
                    504,
                }:
                    raise

                last_error = exc

                if attempt < 2:
                    time.sleep(
                        2 ** (attempt + 1)
                    )

    raise RuntimeError(
        "Gemini is temporarily unavailable."
    ) from last_error