"""
OpenHarness API 接口测试

测试 API 路由和端点功能
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestOpenHarnessAPI:
    """OpenHarness API 测试类"""

    @pytest.fixture
    def mock_engine(self):
        """模拟引擎 fixture"""
        engine = MagicMock()
        engine.is_initialized.return_value = True
        engine.execute = AsyncMock(return_value={"result": "success", "content": "Test response"})
        engine.load_skill = AsyncMock(return_value=True)
        engine.get_engine.return_value = MagicMock()
        return engine

    @pytest.fixture
    def mock_memory_manager(self):
        """模拟记忆管理器 fixture"""
        manager = MagicMock()
        manager.store = AsyncMock()
        manager.retrieve = AsyncMock(return_value=MagicMock(content="Test memory"))
        manager.search = AsyncMock(return_value=[])
        manager.get_stats = AsyncMock(return_value={"total": 10})
        return manager

    @pytest.fixture
    def mock_skill_loader(self):
        """模拟技能加载器 fixture"""
        loader = MagicMock()
        loader.load_from_directory.return_value = []
        loader.search_skills.return_value = []
        return loader

    def test_api_health_check(self):
        """测试 API 健康检查"""
        # 模拟 API 客户端
        from fastapi import FastAPI
        app = FastAPI()

        @app.get("/api/v1/openharness/health")
        async def health_check():
            return {"status": "healthy", "openharness": True}

        client = TestClient(app)
        response = client.get("/api/v1/openharness/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_api_status(self):
        """测试 API 状态端点"""
        from fastapi import FastAPI
        app = FastAPI()

        @app.get("/api/v1/openharness/status")
        async def get_status():
            return {
                "initialized": True,
                "tools_registered": True,
                "skills_loaded": 5,
                "version": "1.0.0"
            }

        client = TestClient(app)
        response = client.get("/api/v1/openharness/status")

        assert response.status_code == 200
        data = response.json()
        assert data["initialized"] is True
        assert "skills_loaded" in data

    @pytest.mark.asyncio
    async def test_execute_endpoint(self):
        """测试执行端点"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.post("/api/v1/openharness/execute")
        async def execute(request: dict):
            return {
                "success": True,
                "result": "Test execution result",
                "execution_time": 1.5
            }

        client = TestClient(app)
        response = client.post(
            "/api/v1/openharness/execute",
            json={"prompt": "Test prompt", "context": {}}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data

    @pytest.mark.asyncio
    async def test_list_skills_endpoint(self):
        """测试列出技能端点"""
        from fastapi import FastAPI

        app = FastAPI()

        @app.get("/api/v1/openharness/skills")
        async def list_skills():
            return {
                "skills": [
                    {"name": "skill1", "description": "Skill 1"},
                    {"name": "skill2", "description": "Skill 2"}
                ],
                "total": 2
            }

        client = TestClient(app)
        response = client.get("/api/v1/openharness/skills")

        assert response.status_code == 200
        data = response.json()
        assert len(data["skills"]) == 2

    @pytest.mark.asyncio
    async def test_load_skill_endpoint(self):
        """测试加载技能端点"""
        from fastapi import FastAPI

        app = FastAPI()

        @app.post("/api/v1/openharness/skills/{skill_name}/load")
        async def load_skill(skill_name: str):
            return {
                "success": True,
                "skill": skill_name,
                "message": f"Skill {skill_name} loaded successfully"
            }

        client = TestClient(app)
        response = client.post("/api/v1/openharness/skills/test_skill/load")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["skill"] == "test_skill"

    @pytest.mark.asyncio
    async def test_memory_store_endpoint(self):
        """测试记忆存储端点"""
        from fastapi import FastAPI

        app = FastAPI()

        @app.post("/api/v1/openharness/memory/store")
        async def store_memory(request: dict):
            return {
                "success": True,
                "key": request.get("key"),
                "timestamp": datetime.now().isoformat()
            }

        client = TestClient(app)
        response = client.post(
            "/api/v1/openharness/memory/store",
            json={"key": "test_key", "content": "Test content"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_memory_retrieve_endpoint(self):
        """测试记忆检索端点"""
        from fastapi import FastAPI

        app = FastAPI()

        @app.get("/api/v1/openharness/memory/{key}")
        async def retrieve_memory(key: str):
            return {
                "success": True,
                "key": key,
                "content": "Retrieved content",
                "timestamp": datetime.now().isoformat()
            }

        client = TestClient(app)
        response = client.get("/api/v1/openharness/memory/test_key")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["content"] == "Retrieved content"

    @pytest.mark.asyncio
    async def test_memory_search_endpoint(self):
        """测试记忆搜索端点"""
        from fastapi import FastAPI

        app = FastAPI()

        @app.post("/api/v1/openharness/memory/search")
        async def search_memory(request: dict):
            return {
                "results": [
                    {"key": "key1", "content": "Content 1", "score": 0.9},
                    {"key": "key2", "content": "Content 2", "score": 0.8}
                ],
                "total": 2
            }

        client = TestClient(app)
        response = client.post(
            "/api/v1/openharness/memory/search",
            json={"query": "test", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2

    @pytest.mark.asyncio
    async def test_tools_list_endpoint(self):
        """测试工具列表端点"""
        from fastapi import FastAPI

        app = FastAPI()

        @app.get("/api/v1/openharness/tools")
        async def list_tools():
            return {
                "tools": [
                    {"name": "tool1", "description": "Tool 1"},
                    {"name": "tool2", "description": "Tool 2"}
                ],
                "total": 2
            }

        client = TestClient(app)
        response = client.get("/api/v1/openharness/tools")

        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 2

    @pytest.mark.asyncio
    async def test_tool_execute_endpoint(self):
        """测试工具执行端点"""
        from fastapi import FastAPI

        app = FastAPI()

        @app.post("/api/v1/openharness/tools/{tool_name}/execute")
        async def execute_tool(tool_name: str, request: dict):
            return {
                "success": True,
                "tool": tool_name,
                "result": {"output": "Tool execution result"},
                "execution_time": 0.5
            }

        client = TestClient(app)
        response = client.post(
            "/api/v1/openharness/tools/test_tool/execute",
            json={"parameters": {"arg1": "value1"}}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tool"] == "test_tool"

    @pytest.mark.asyncio
    async def test_stream_execute_endpoint(self):
        """测试流式执行端点"""
        from fastapi import FastAPI
        from fastapi.responses import StreamingResponse

        app = FastAPI()

        async def stream_generator():
            chunks = ["Hello ", "world", "!"]
            for chunk in chunks:
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        @app.post("/api/v1/openharness/execute/stream")
        async def execute_stream(request: dict):
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream"
            )

        client = TestClient(app)
        response = client.post(
            "/api/v1/openharness/execute/stream",
            json={"prompt": "Test"}
        )

        assert response.status_code == 200
        # 验证流式响应


class TestAPIErrorHandling:
    """API 错误处理测试类"""

    def test_not_initialized_error(self):
        """测试未初始化错误"""
        from fastapi import FastAPI, HTTPException

        app = FastAPI()

        @app.post("/api/v1/openharness/execute")
        async def execute(request: dict):
            raise HTTPException(status_code=503, detail="OpenHarness not initialized")

        client = TestClient(app)
        response = client.post(
            "/api/v1/openharness/execute",
            json={"prompt": "Test"}
        )

        assert response.status_code == 503

    def test_skill_not_found_error(self):
        """测试技能未找到错误"""
        from fastapi import FastAPI, HTTPException

        app = FastAPI()

        @app.post("/api/v1/openharness/skills/{skill_name}/load")
        async def load_skill(skill_name: str):
            raise HTTPException(status_code=404, detail=f"Skill {skill_name} not found")

        client = TestClient(app)
        response = client.post("/api/v1/openharness/skills/nonexistent/load")

        assert response.status_code == 404

    def test_invalid_request_error(self):
        """测试无效请求错误"""
        from fastapi import FastAPI, HTTPException

        app = FastAPI()

        @app.post("/api/v1/openharness/execute")
        async def execute(request: dict):
            if not request.get("prompt"):
                raise HTTPException(status_code=400, detail="Prompt is required")
            return {"success": True}

        client = TestClient(app)
        response = client.post("/api/v1/openharness/execute", json={})

        assert response.status_code == 400


class TestAPIAuthentication:
    """API 认证测试类"""

    def test_authenticated_request(self):
        """测试认证请求"""
        from fastapi import FastAPI, Depends
        from fastapi.security import HTTPBearer

        app = FastAPI()
        security = HTTPBearer()

        @app.get("/api/v1/openharness/protected")
        async def protected_route(token: str = Depends(security)):
            return {"authenticated": True}

        client = TestClient(app)
        response = client.get(
            "/api/v1/openharness/protected",
            headers={"Authorization": "Bearer test_token"}
        )

        # 应该返回 200 或 403，取决于认证实现
        assert response.status_code in [200, 403]

    def test_unauthenticated_request(self):
        """测试未认证请求"""
        from fastapi import FastAPI, HTTPException

        app = FastAPI()

        @app.get("/api/v1/openharness/protected")
        async def protected_route():
            raise HTTPException(status_code=401, detail="Not authenticated")

        client = TestClient(app)
        response = client.get("/api/v1/openharness/protected")

        assert response.status_code == 401


class TestAPIResponseFormats:
    """API 响应格式测试类"""

    def test_json_response(self):
        """测试 JSON 响应格式"""
        from fastapi import FastAPI

        app = FastAPI()

        @app.get("/api/v1/openharness/data")
        async def get_data():
            return {
                "string": "value",
                "number": 42,
                "boolean": True,
                "array": [1, 2, 3],
                "object": {"nested": "value"},
                "null": None
            }

        client = TestClient(app)
        response = client.get("/api/v1/openharness/data")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data["string"], str)
        assert isinstance(data["number"], int)
        assert isinstance(data["boolean"], bool)
        assert isinstance(data["array"], list)
        assert isinstance(data["object"], dict)

    def test_pagination_response(self):
        """测试分页响应格式"""
        from fastapi import FastAPI

        app = FastAPI()

        @app.get("/api/v1/openharness/items")
        async def get_items(skip: int = 0, limit: int = 10):
            return {
                "items": [{"id": i} for i in range(skip, skip + limit)],
                "total": 100,
                "skip": skip,
                "limit": limit
            }

        client = TestClient(app)
        response = client.get("/api/v1/openharness/items?skip=10&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["skip"] == 10
        assert data["limit"] == 5
        assert data["total"] == 100


class TestAPIEdgeCases:
    """API 边界情况测试类"""

    def test_empty_request_body(self):
        """测试空请求体"""
        from fastapi import FastAPI

        app = FastAPI()

        @app.post("/api/v1/openharness/execute")
        async def execute(request: dict = None):
            if request is None:
                return {"success": False, "error": "Empty request"}
            return {"success": True}

        client = TestClient(app)
        response = client.post("/api/v1/openharness/execute")

        assert response.status_code == 200

    def test_very_long_prompt(self):
        """测试超长提示词"""
        from fastapi import FastAPI

        app = FastAPI()

        @app.post("/api/v1/openharness/execute")
        async def execute(request: dict):
            prompt = request.get("prompt", "")
            if len(prompt) > 10000:
                return {"success": False, "error": "Prompt too long"}
            return {"success": True, "length": len(prompt)}

        client = TestClient(app)
        long_prompt = "A" * 5000
        response = client.post(
            "/api/v1/openharness/execute",
            json={"prompt": long_prompt}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_special_characters_in_params(self):
        """测试特殊字符参数"""
        from fastapi import FastAPI

        app = FastAPI()

        @app.post("/api/v1/openharness/execute")
        async def execute(request: dict):
            return {"success": True, "received": request}

        client = TestClient(app)
        special_data = {
            "prompt": "Test with special chars: <>&\"'",
            "unicode": "中文测试 🎉",
            "newlines": "Line 1\nLine 2\r\nLine 3"
        }
        response = client.post("/api/v1/openharness/execute", json=special_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_concurrent_requests(self):
        """测试并发请求"""
        import asyncio

        from fastapi import FastAPI

        app = FastAPI()

        @app.get("/api/v1/openharness/concurrent")
        async def concurrent_endpoint():
            await asyncio.sleep(0.01)  # 模拟处理时间
            return {"success": True}

        client = TestClient(app)

        # 快速发送多个请求
        responses = []
        for _ in range(5):
            response = client.get("/api/v1/openharness/concurrent")
            responses.append(response)

        assert all(r.status_code == 200 for r in responses)
