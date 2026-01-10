"""Vision API integration for Snag (Google Gemini and OpenRouter)."""

import base64
import os
import time
from io import BytesIO
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image

from .config import DEFAULT_MODEL, DEFAULT_PROVIDER, GOOGLE_MODELS

# Load .env from multiple locations (first found wins, overrides shell env)
# Priority: ~/.config/snag/.env > ~/.snag.env > ./.env
_config_dir = Path.home() / ".config" / "snag"
_env_locations = [
    _config_dir / ".env",
    Path.home() / ".snag.env",
    Path.cwd() / ".env",
]

for _env_path in _env_locations:
    if _env_path.exists():
        load_dotenv(_env_path, override=True)
        break


class VisionError(Exception):
    """Error during vision API call."""

    pass


# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# For backwards compatibility
MODELS = GOOGLE_MODELS

PROMPT = """Analyze this image and provide a comprehensive description in clean markdown format.

If the image contains:
- **Text**: Transcribe it accurately, preserving formatting where possible
- **Code**: Format it as a code block with appropriate language syntax highlighting
- **Diagrams/Charts**: Describe the structure, relationships, and data shown
- **UI elements**: Describe the interface, controls, and their arrangement
- **Images/Graphics**: Describe what is depicted

Output clean markdown that can be directly pasted into a document or LLM conversation.
Be thorough but concise. Focus on accurately capturing the content."""


def get_gemini_api_key() -> str:
    """Get Gemini API key from environment or .env file."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise VisionError(
            "GEMINI_API_KEY not found.\n"
            "Get an API key at: https://aistudio.google.com/apikey\n"
            "Run 'snag --setup' to configure."
        )
    return key


def get_openrouter_api_key() -> str:
    """Get OpenRouter API key from environment or .env file."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise VisionError(
            "OPENROUTER_API_KEY not found.\n"
            "Get an API key at: https://openrouter.ai/keys\n"
            "Run 'snag --setup' to configure."
        )
    return key


# Backwards compatibility alias
get_api_key = get_gemini_api_key


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def describe_image_google(
    image: Image.Image,
    model: str = DEFAULT_MODEL,
    max_retries: int = 3,
) -> str:
    """Send image to Google Gemini and get description.

    Args:
        image: PIL Image to describe
        model: Model name to use (must be a known Google model)
        max_retries: Number of retry attempts on failure

    Returns:
        Markdown description of the image content

    Raises:
        VisionError: If API call fails after retries
    """
    if model not in GOOGLE_MODELS:
        available = ", ".join(GOOGLE_MODELS.keys())
        raise VisionError(f"Unknown Google model '{model}'. Available: {available}")

    api_key = get_gemini_api_key()
    model_config = GOOGLE_MODELS[model]
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
                last_error = VisionError("Rate limited (429), retrying...")
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


def describe_image_openrouter(
    image: Image.Image,
    model: str,
    max_retries: int = 3,
) -> str:
    """Send image to OpenRouter and get description.

    Args:
        image: PIL Image to describe
        model: OpenRouter model name (e.g., "google/gemini-2.5-flash-lite")
        max_retries: Number of retry attempts on failure

    Returns:
        Markdown description of the image content

    Raises:
        VisionError: If API call fails after retries
    """
    api_key = get_openrouter_api_key()
    image_b64 = image_to_base64(image)

    # OpenRouter uses OpenAI-compatible format with base64 data URLs
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        }
                    }
                ]
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/snag-cli/snag",
        "X-Title": "Snag Screenshot Tool",
    }

    # Retry with exponential backoff
    last_error = None
    for attempt in range(max_retries):
        try:
            response = requests.post(
                OPENROUTER_API_URL,
                json=payload,
                headers=headers,
                timeout=60,
            )

            if response.status_code == 200:
                data = response.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError) as e:
                    raise VisionError(f"Unexpected API response format: {e}")

            elif response.status_code == 429:
                # Rate limited, wait and retry
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                last_error = VisionError("Rate limited (429), retrying...")
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


def describe_image(
    image: Image.Image,
    model: str = DEFAULT_MODEL,
    provider: str = DEFAULT_PROVIDER,
    max_retries: int = 3,
) -> str:
    """Send image to vision API and get description.

    Args:
        image: PIL Image to describe
        model: Model name to use
        provider: Provider to use ("google" or "openrouter")
        max_retries: Number of retry attempts on failure

    Returns:
        Markdown description of the image content

    Raises:
        VisionError: If API call fails after retries
    """
    if provider == "google":
        return describe_image_google(image, model=model, max_retries=max_retries)
    elif provider == "openrouter":
        return describe_image_openrouter(image, model=model, max_retries=max_retries)
    else:
        raise VisionError(f"Unknown provider '{provider}'. Available: google, openrouter")
