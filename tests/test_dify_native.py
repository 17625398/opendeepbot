import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.llm.cloud_provider import _dify_complete, _dify_stream


class TestDifyNative(unittest.TestCase):
    def test_dify_complete(self):
        async def run_test():
            with patch("aiohttp.ClientSession") as mock_session_cls:
                # session must be an async context manager
                mock_session = MagicMock()
                mock_session_cls.return_value.__aenter__.return_value = mock_session
                
                # session.post returns an async context manager
                mock_resp = AsyncMock()
                mock_resp.status = 200
                
                # _dify_complete now uses streaming internally, so we must mock streaming response
                chunks = [
                    b'data: {"event": "message", "answer": "Hello "}',
                    b'data: {"event": "message", "answer": "Dify"}'
                ]
                
                async def async_iter():
                    for c in chunks:
                        yield c
                
                mock_resp.content = async_iter()
                
                post_ctx = MagicMock()
                post_ctx.__aenter__.return_value = mock_resp
                post_ctx.__aexit__.return_value = None
                
                # Make session.post return the context manager
                mock_session.post.return_value = post_ctx
                
                result = await _dify_complete(
                    model="dify",
                    prompt="Hello",
                    system_prompt="sys",
                    api_key="key",
                    base_url="http://host/v1",
                    user="test-user"
                )
                
                self.assertEqual(result, "Hello Dify")
                
                # Verify URL construction
                args, kwargs = mock_session.post.call_args
                self.assertEqual(args[0], "http://host/v1/chat-messages")
                self.assertEqual(kwargs["json"]["user"], "test-user")
                # response_mode should be streaming now
                self.assertEqual(kwargs["json"]["response_mode"], "streaming")

        asyncio.run(run_test())

    def test_dify_files_param(self):
        async def run_test():
            with patch("aiohttp.ClientSession") as mock_session_cls:
                mock_session = MagicMock()
                mock_session_cls.return_value.__aenter__.return_value = mock_session
                
                mock_resp = AsyncMock()
                mock_resp.status = 200
                
                chunks = [b'data: {"event": "message", "answer": "OK"}']
                async def async_iter():
                    for c in chunks:
                        yield c
                mock_resp.content = async_iter()
                
                post_ctx = MagicMock()
                post_ctx.__aenter__.return_value = mock_resp
                post_ctx.__aexit__.return_value = None
                mock_session.post.return_value = post_ctx
                
                files = [{"type": "image", "transfer_method": "remote_url", "url": "http://example.com/image.png"}]
                
                gen = _dify_stream(
                    model="dify",
                    prompt="Analyze image",
                    system_prompt="sys",
                    api_key="key",
                    base_url="http://host/v1",
                    files=files
                )
                
                async for _ in gen:
                    pass
                
                args, kwargs = mock_session.post.call_args
                self.assertEqual(kwargs["json"]["files"], files)

        asyncio.run(run_test())

    def test_dify_url_stripping(self):
        async def run_test():
            with patch("aiohttp.ClientSession") as mock_session_cls:
                mock_session = MagicMock()
                mock_session_cls.return_value.__aenter__.return_value = mock_session
                
                mock_resp = AsyncMock()
                mock_resp.status = 200
                
                # Mock streaming response
                chunks = [b'data: {"event": "message", "answer": "Hello"}']
                async def async_iter():
                    for c in chunks:
                        yield c
                mock_resp.content = async_iter()
                
                post_ctx = MagicMock()
                post_ctx.__aenter__.return_value = mock_resp
                post_ctx.__aexit__.return_value = None
                mock_session.post.return_value = post_ctx
                
                # Test with spaces in URL and API Key
                await _dify_complete(
                    model="dify",
                    prompt="Hello",
                    system_prompt="sys",
                    api_key="  key-with-spaces  ",
                    base_url="  http://host/v1/  ",
                    user="test-user"
                )
                
                args, kwargs = mock_session.post.call_args
                self.assertEqual(args[0], "http://host/v1/chat-messages")
                self.assertEqual(kwargs["headers"]["Authorization"], "Bearer key-with-spaces")

        asyncio.run(run_test())

    def test_dify_stream(self):
        async def run_test():
            with patch("aiohttp.ClientSession") as mock_session_cls:
                mock_session = MagicMock()
                mock_session_cls.return_value.__aenter__.return_value = mock_session
                
                mock_resp = AsyncMock()
                mock_resp.status = 200
                
                chunks = [
                    b'data: {"event": "message", "answer": "Hello "}',
                    b'data: {"event": "agent_message", "answer": "World"}', # Test agent_message support
                    b'data: {"event": "workflow_finished"}' # Should be ignored
                ]
                
                async def async_iter():
                    for c in chunks:
                        yield c
                
                mock_resp.content = async_iter()
                
                post_ctx = MagicMock()
                post_ctx.__aenter__.return_value = mock_resp
                post_ctx.__aexit__.return_value = None
                
                mock_session.post.return_value = post_ctx
                
                gen = _dify_stream(
                    model="dify",
                    prompt="Hello",
                    system_prompt="sys",
                    api_key="key",
                    base_url="http://host/v1"
                )
                
                results = []
                async for chunk in gen:
                    results.append(chunk)
                    
                self.assertEqual("".join(results), "Hello World")

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
