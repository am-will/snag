"""Gemini Vision API integration for Snag."""

import base64
import os
import time
from io import BytesIO
from typing import Optional

import requests
from dotenv import load_dotenv
from PIL import Image

# Load .env file (overrides exported env vars, so .env takes priority)
load_dotenv(override=True)


class VisionError(Exception):
    """Error during vision API call."""

    pass


# Model configurations
MODELS = {
    "gemini-2.5-flash": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        "version": "2.5",
    },
    "gemini-3-flash-preview": {
        "endpoint": "https://generativelanguage.googleapis.com/v1alpha/models/gemini-3-flash-preview:generateContent",
        "version": "3.x",
    },
}

DEFAULT_MODEL = "gemini-2.5-flash"

PROMPT = """Analyze this image and provide a comprehensive description in clean markdown format.

If the image contains:
- **Text**: Transcribe it accurately, preserving formatting where possible
- **Code**: Format it as a code block with appropriate language syntax highlighting
- **Diagrams/Charts**: Describe the structure, relationships, and data shown
- **UI elements**: Describe the interface, controls, and their arrangement
- **Images/Graphics**: Describe what is depicted

Output clean markdown that can be directly pasted into a document or LLM conversation.
Be thorough but concise. Focus on accurately capturing the content."""


def get_api_key() -> str:
    """Get Gemini API key from environment or .env file."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise VisionError(
            "GEMINI_API_KEY not found.\n"
            "Get an API key at: https://aistudio.google.com/apikey\n"
            "Then either:\n"
            "  export GEMINI_API_KEY='your-key'\n"
            "  or add to .env file: GEMINI_API_KEY=your-key"
        )
    return key


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def describe_image(
    image: Image.Image,
    model: str = DEFAULT_MODEL,
    max_retries: int = 3,
) -> str:
    """Send image to Gemini and get description.

    Args:
        image: PIL Image to describe
        model: Model name to use
        max_retries: Number of retry attempts on failure

    Returns:
        Markdown description of the image content

    Raises:
        VisionError: If API call fails after retries
    """
    if model not in MODELS:
        available = ", ".join(MODELS.keys())
        raise VisionError(f"Unknown model '{model}'. Available: {available}")

    api_key = get_api_key()
    model_config = MODELS[model]
    endpoint = f"{model_config['endpoint']}?key={api_key}"

    # Build payload based on model version
    image_b64 = image_to_base64(image)

    if model_config["version"] == "2.5":
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": PROMPT},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_b64,
                            }
                        },
                    ]
                }
            ]
        }
    else:  # 3.x
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": PROMPT},
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": image_b64,
                            }
                        },
                    ]
                }
            ]
        }

    # Retry with exponential backoff
    last_error = None
    for attempt in range(max_retries):
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60,
            )

            if response.status_code == 200:
                data = response.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError) as e:
                    raise VisionError(f"Unexpected API response format: {e}")

            elif response.status_code == 429:
                # Rate limited, wait and retry
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                last_error = VisionError(f"Rate limited (429), retrying...")
                continue

            else:
                error_msg = response.text
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = error_data["error"].get("message", error_msg)
                except Exception:
                    pass
                raise VisionError(
                    f"API error ({response.status_code}): {error_msg}"
                )

        except requests.exceptions.Timeout:
            last_error = VisionError("Request timed out")
            wait_time = 2 ** attempt
            time.sleep(wait_time)
            continue

        except requests.exceptions.RequestException as e:
            last_error = VisionError(f"Network error: {e}")
            wait_time = 2 ** attempt
            time.sleep(wait_time)
            continue

    raise last_error or VisionError("Failed after retries")
