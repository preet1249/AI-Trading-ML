"""
Qwen AI Client - REAL DATA
Integration with Qwen 3 via OpenRouter
NO MOCK DATA - Production-ready
"""
import aiohttp
import ssl
import certifi
import json
from typing import Dict, List, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Timeout for AI API calls (30 seconds - AI generation can take time)
AI_API_TIMEOUT = 30


class QwenClient:
    """Real Qwen 3 AI integration via OpenRouter"""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.base_url = getattr(settings, 'OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        self.temperature = settings.QWEN_TEMPERATURE
        self.max_tokens = settings.QWEN_MAX_TOKENS

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text using Qwen 3 via OpenRouter

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Temperature override (optional)
            max_tokens: Max tokens override (optional)

        Returns:
            Generated text response
        """
        try:
            if not self.api_key:
                raise Exception("OPENROUTER_API_KEY not configured")

            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # API request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ai-trading-predictor.app",
                "X-Title": "AI Trading Predictor"
            }

            logger.info(f"Calling Qwen API (model: {self.model}) with {AI_API_TIMEOUT}s timeout")

            # Create SSL context and timeout for production reliability
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=AI_API_TIMEOUT)

            # Make API request with timeout protection
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                        raise Exception(f"OpenRouter API error: {response.status}")

                    data = await response.json()

            # Extract response
            if "choices" not in data or len(data["choices"]) == 0:
                raise Exception("No response from OpenRouter")

            generated_text = data["choices"][0]["message"]["content"]

            logger.info(f"Successfully generated {len(generated_text)} characters from Qwen")
            return generated_text

        except Exception as e:
            logger.error(f"Error calling Qwen API: {str(e)}")
            raise

# Singleton instance
qwen_client = QwenClient()
