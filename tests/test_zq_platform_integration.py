"""
zq-platform Integration Tests
=============================

测试 zq-platform 企业级功能集成。
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.services.jwt_auth import JWTAuth
from src.services.data_permission import DataScope, DataPermissionService


class TestJWTAuth:
    """测试 JWT 认证"""
    
    @pytest.fixture
    def jwt_auth(self):
        return JWTAuth(
            secret_key="test-secret-key",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7
        )
    
    def test_create_access_token(self, jwt_auth):
        """测试创建 Access Token"""
        access_token = jwt_auth.create_access_token(
            data={"sub": "user-123"}
        )
        
        assert access_token is not None
        assert isinstance(access_token, str)
    
    def test_create_refresh_token(self, jwt_auth):
        """测试创建 Refresh Token"""
        refresh_token = jwt_auth.create_refresh_token(
            data={"sub": "user-123"}
        )
        
        assert refresh_token is not None
        assert isinstance(refresh_token, str)
    
    def test_verify_token(self, jwt_auth):
        """测试验证 Token"""
        access_token = jwt_auth.create_access_token(
            data={"sub": "user-123"}
        )
        
        payload = jwt_auth.verify_token(access_token, token_type="access")
        
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
    
    def test_refresh_access_token(self, jwt_auth):
        """测试刷新 Access Token"""
        refresh_token = jwt_auth.create_refresh_token(
            data={"sub": "user-123"}
        )
        
        new_token_pair = jwt_auth.refresh_access_token(refresh_token)
        
        assert new_token_pair is not None
        assert "access_token" in new_token_pair
        assert "refresh_token" in new_token_pair
        assert "token_type" in new_token_pair


class TestDataScope:
    """测试数据范围枚举"""
    
    def test_data_scope_values(self):
        """测试数据范围值"""
        assert DataScope.ALL.value == "all"
        assert DataScope.DEPT_ONLY.value == "dept_only"
        assert DataScope.DEPT_AND_CHILD.value == "dept_and_child"
        assert DataScope.SELF_ONLY.value == "self_only"


class TestDataPermissionService:
    """测试数据权限服务"""
    
    def test_service_creation(self):
        """测试服务创建"""
        mock_db = Mock()
        service = DataPermissionService(db=mock_db)
        
        assert service is not None
        assert service.db is mock_db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
