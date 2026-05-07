
import asyncio
import json

from src.services.llm_manager import ChatMessage, llm_manager


async def test_multimodal_openai_client():
    print("Testing OpenAIClient with multimodal content (simulating local vision model)...")
    
    # Simulate a request for a vision model
    model_id = "llava"
    dynamic_config = {
        "provider": "openai",
        "base_url": "http://localhost:1234/v1", # Typical LM Studio URL
        "supports_vision": True,
        "api_key": "sk-local"
    }
    
    # Sample multimodal message
    messages = [
        ChatMessage(
            role="user",
            content=[
                {"type": "text", "text": "Describe this image."},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZnaGlqc3R1dnd4eXqGhc4SFhoeIiOipKCk5SVlpeYmZqio6Slpqeoqaqys7S12t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD5/ooooA//2Q=="}
                }
            ]
        )
    ]
    
    print(f"Messages to send: {messages}")
    
    # We don't actually call the API since we don't have a local server running,
    # but we can verify the payload construction by mocking the session.post
    
    from unittest.mock import AsyncMock, patch
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "I see a tiny white square."}}]
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        try:
            response = await llm_manager.chat_completion(
                model_id=model_id,
                messages=messages,
                dynamic_config=dynamic_config
            )
            print(f"Mock Response: {response}")
            
            # Verify payload
            args, kwargs = mock_post.call_args
            payload = kwargs.get('json')
            print(f"Constructed Payload: {json.dumps(payload, indent=2)}")
            
            # Assertions
            assert payload['model'] == model_id
            assert isinstance(payload['messages'][0]['content'], list)
            assert payload['messages'][0]['content'][1]['type'] == 'image_url'
            print("Test PASSED: Payload correctly constructed for multimodal content.")
            
        except Exception as e:
            print(f"Test FAILED: {e}")

async def test_multimodal_ollama_client():
    print("\nTesting OllamaClient with multimodal content...")
    
    model_id = "llava"
    dynamic_config = {
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "supports_vision": True
    }
    
    messages = [
        ChatMessage(
            role="user",
            content=[
                {"type": "text", "text": "Describe this image."},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZnaGlqc3R1dnd4eXqGhc4SFhoeIiOipKCk5SVlpeYmZqio6Slpqeoqaqys7S12t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD5/ooooA//2Q=="}
                }
            ]
        )
    ]
    
    from unittest.mock import AsyncMock, patch
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "message": {"content": "I see a tiny white square."}
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        try:
            response = await llm_manager.chat_completion(
                model_id=model_id,
                messages=messages,
                dynamic_config=dynamic_config
            )
            print(f"Mock Response: {response}")
            
            args, kwargs = mock_post.call_args
            payload = kwargs.get('json')
            print(f"Constructed Payload: {json.dumps(payload, indent=2)}")
            
            # Assertions for Ollama format
            assert payload['model'] == model_id
            assert payload['messages'][0]['content'] == "Describe this image."
            assert isinstance(payload['messages'][0]['images'], list)
            assert len(payload['messages'][0]['images']) == 1
            print("Test PASSED: Payload correctly constructed for Ollama multimodal content.")
            
        except Exception as e:
            print(f"Test FAILED: {e}")

if __name__ == "__main__":
    async def main():
        await test_multimodal_openai_client()
        await test_multimodal_ollama_client()
    asyncio.run(main())
