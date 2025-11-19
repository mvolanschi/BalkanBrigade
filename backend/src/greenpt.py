import os
import asyncio
from typing import List, Dict, Any

import httpx


class GreenPTClient:
    """Thin async wrapper for the GreenPT API.

    Configure with environment variables:
    - `GREENPT_API_KEY`: API key
    - `GREENPT_API_URL`: base URL for the API (defaults to a common path)
    """

    def __init__(self, api_key: str | None = None, api_url: str | None = None):
        self.api_key = api_key or os.getenv("GREENPT_API_KEY")
        self.api_url = api_url or os.getenv(
            "GREENPT_API_URL", "https://api.greenpt.ai/v1/chat/completions"
        )
        self._client = httpx.AsyncClient(timeout=30.0)

    async def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> Dict[str, Any]:
        """Send a chat-style request to GreenPT.

        `messages` should be a list of objects like {"role": "user|assistant|system", "content": "..."}
        Returns the parsed JSON response (dict).
        """
        if not self.api_key:
            raise RuntimeError("GREENPT_API_KEY not configured")

        payload = {
            "model": kwargs.get("model", "green-l"),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 512),
            "stream": kwargs.get("stream", False),
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        resp = await self._client.post(self.api_url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        await self._client.aclose()


# convenience singleton for simple apps
_client: GreenPTClient | None = None


def get_client() -> GreenPTClient:
    global _client
    if _client is None:
        _client = GreenPTClient()
    return _client
