from unittest.mock import AsyncMock, patch

import pytest

from src.core.llm.cloud_provider import _openai_stream, complete


@pytest.mark.asyncio
async def test_dify_complete_standard_format():
    """Test Dify completion with standard OpenAI format."""
    mock_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello from Dify Standard"
                }
            }
        ]
    }
    
    with patch("src.core.llm.cloud_provider.openai_complete_if_cache", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = "Hello from Dify Standard"
        
        result = await complete(
            prompt="Hello",
            binding="dify",
            api_key="test-key",
            base_url="https://api.dify.ai/v1"
        )
        
        assert result == "Hello from Dify Standard"
        mock_complete.assert_called_once()

@pytest.mark.asyncio
async def test_dify_complete_native_fallback():
    """Test Dify completion fallback to native format when standard fails."""
    
    # Mock openai_complete_if_cache to raise an exception
    with patch("src.core.llm.cloud_provider.openai_complete_if_cache", side_effect=Exception("Invalid response")):
        
        # Mock aiohttp session for fallback
        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__.return_value = mock_session
            
            # Mock response with native Dify format (answer field)
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"answer": "Hello from Dify Native"}
            mock_session.post.return_value = mock_response
            
            result = await complete(
                prompt="Hello",
                binding="dify",
                api_key="test-key",
                base_url="https://api.dify.ai/v1"
            )
            
            assert result == "Hello from Dify Native"

@pytest.mark.asyncio
async def test_dify_stream_native_format():
    """Test Dify streaming with native format (direct JSON lines)."""
    
    # Mock aiohttp session
    with patch("aiohttp.ClientSession") as mock_session_cls:
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        
        # Mock streaming response
        mock_response = AsyncMock()
        mock_response.status = 200
        
        # Simulate Dify native stream chunks
        chunks = [
            b'{"event": "message", "answer": "Hello "}',
            b'{"event": "message", "answer": "from "}',
            b'{"event": "message", "answer": "Dify"}'
        ]
        
        # Async iterator for content
        async def async_iter():
            for chunk in chunks:
                yield chunk
        
        mock_response.content = async_iter()
        mock_session.post.return_value = mock_response
        
        # Collect stream results
        stream_gen = _openai_stream(
            model="dify-model",
            prompt="Hello",
            system_prompt="sys",
            api_key="key",
            base_url="url",
            binding="dify"
        )
        
        results = []
        async for chunk in stream_gen:
            results.append(chunk)
            
        assert "".join(results) == "Hello from Dify"
