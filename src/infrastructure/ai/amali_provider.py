import httpx
import asyncio
from typing import List, Dict, Any
from domain.interfaces import IAIProvider
from core.config import settings
from core.exceptions import AIProviderException
from core.logger import logger

class AmaliAIProvider(IAIProvider):
    def __init__(self):
        self.base_url = settings.AMALI_API_URL
        self.api_key = settings.AMALI_API_KEY
        self.provider = settings.AMALI_PROVIDER_NAME

        # We do NOT use 'Authorization: Bearer <token>'
        self.headers = {
            "X-Api-Key": self.api_key,
            "Provider": self.provider,
            "Content-Type": "application/json"
        }

    async def _make_request(self, method: str, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{self.base_url}{endpoint}"
            try:
                response = await client.request(method, url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error("amali_api_status_error", status_code=e.response.status_code, response=e.response.text)
                raise AIProviderException(f"API Error: {e.response.status_code}", details={"response": e.response.text})
            except httpx.RequestError as e:
                logger.error("amali_api_request_error", error=str(e))
                raise AIProviderException(f"Request failed: {str(e)}")

    async def generate_completion(self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini", **kwargs) -> str:
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        res = await self._make_request("POST", "/chat/completions", payload)
        try:
            return res["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise AIProviderException("Unexpected response format from Chat Completions", details={"raw": res})

    async def _generate_single_embedding(self, text: str, model: str) -> List[float]:
        payload = {
            "input": text,
            "model": model
        }
        res = await self._make_request("POST", "/embeddings", payload)
        try:
            return res["data"][0]["embedding"]
        except (KeyError, IndexError) as e:
            raise AIProviderException("Unexpected response format from Embeddings", details={"raw": res})

    async def generate_embeddings(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        # The gateway may support single-string inputs only.
        # We embed them concurrently and use asyncio.gather to preserve original order.
        tasks = [self._generate_single_embedding(text, model) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_embeddings = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error("embedding_generation_failed_for_chunk", index=i, error=str(res))
                raise res
            final_embeddings.append(res)

        return final_embeddings
