"""
Agent Context 单元测试
测试 AgentContext, CancellationToken, TraceContext, SessionContext 的功能
"""

import pytest
import asyncio
import time
from datetime import datetime
from src.agents.unified.context import (
    AgentContext,
    CancellationToken,
    TraceContext,
    SessionContext,
    get_current_context,
    create_context,
    CURRENT_CONTEXT
)


class TestCancellationToken:
    """测试取消令牌"""
    
    def test_initial_state(self):
        """测试初始状态"""
        token = CancellationToken()
        
        assert not token.is_cancelled
        assert token.cancellation_reason is None
    
    def test_cancel_operation(self):
        """测试取消操作"""
        token = CancellationToken()
        
        # 取消
        token.cancel("Test cancellation")
        
        # 验证
        assert token.is_cancelled
        assert token.cancellation_reason == "Test cancellation"
    
    def test_register_callback(self):
        """测试注册回调"""
        token = CancellationToken()
        callback_called = []
        
        def callback():
            callback_called.append("called")
        
        token.register_callback(callback)
        token.cancel()
        
        # 验证回调被调用
        assert len(callback_called) == 1
        assert callback_called[0] == "called"
    
    def test_multiple_callbacks(self):
        """测试多个回调"""
        token = CancellationToken()
        callbacks = []
        
        for i in range(3):
            def make_callback(idx):
                def callback():
                    callbacks.append(idx)
                return callback
            token.register_callback(make_callback(i))
        
        token.cancel()
        
        # 验证所有回调都被调用
        assert len(callbacks) == 3
        assert set(callbacks) == {0, 1, 2}
    
    def test_callback_on_already_cancelled(self):
        """测试在已取消的令牌上注册回调"""
        token = CancellationToken()
        token.cancel()
        
        callback_called = []
        token.register_callback(lambda: callback_called.append("called"))
        
        # 回调应该立即执行
        assert len(callback_called) == 1
    
    def test_linked_token(self):
        """测试链式令牌"""
        parent = CancellationToken()
        linked = parent.create_linked_token()
        
        assert not linked.is_cancelled
        assert not parent.is_cancelled
        
        # 取消父令牌
        parent.cancel("Parent cancelled")
        
        # 链接的令牌也应该被取消
        assert linked.is_cancelled
        assert "Parent cancelled" in linked.cancellation_reason


class TestTraceContext:
    """测试追踪上下文"""
    
    def test_trace_creation(self):
        """测试追踪创建"""
        trace = TraceContext()
        
        assert trace.trace_id is not None
        assert trace.span_id is not None
        assert trace.parent_span_id is None
        assert trace.end_time is None
    
    def test_trace_with_parent(self):
        """测试带父span的追踪"""
        parent = TraceContext(trace_id="parent-id", span_id="parent-span")
        child = parent.create_child_span()
        
        assert child.trace_id == parent.trace_id
        assert child.parent_span_id == parent.span_id
        assert child.span_id != parent.span_id
    
    def test_add_tags(self):
        """测试添加标签"""
        trace = TraceContext()
        trace.add_tag("key1", "value1")
        trace.add_tag("key2", "value2")
        
        assert trace.tags["key1"] == "value1"
        assert trace.tags["key2"] == "value2"
    
    def test_add_log(self):
        """测试添加日志"""
        trace = TraceContext()
        trace.add_log("Test log", extra="value")
        
        assert len(trace.logs) == 1
        assert trace.logs[0]["message"] == "Test log"
        assert trace.logs[0]["extra"] == "value"
    
    def test_complete_trace(self):
        """测试完成追踪"""
        trace = TraceContext()
        time.sleep(0.01)  # 确保有时间差
        trace.complete()
        
        assert trace.end_time is not None
        assert trace.duration_ms is not None
        assert trace.duration_ms > 0


class TestSessionContext:
    """测试会话上下文"""
    
    def test_session_creation(self):
        """测试会话创建"""
        session = SessionContext()
        
        assert session.session_id is not None
        assert session.user_id is None
        assert len(session.roles) == 0
        assert len(session.permissions) == 0
    
    def test_session_with_user(self):
        """测试带用户的会话"""
        session = SessionContext(
            user_id="user123",
            username="testuser"
        )
        
        assert session.user_id == "user123"
        assert session.username == "testuser"
    
    def test_update_activity(self):
        """测试更新活动时间"""
        session = SessionContext()
        old_activity = session.last_activity
        
        time.sleep(0.01)
        session.update_activity()
        
        assert session.last_activity > old_activity
    
    def test_check_expired(self):
        """测试检查过期"""
        session = SessionContext()
        
        # 新创建的会话不应该过期
        assert not session.is_expired(ttl_seconds=3600)
        
        # 过去的会话应该过期
        session.last_activity = datetime.fromtimestamp(0)
        assert session.is_expired(ttl_seconds=3600)
    
    def test_has_permission(self):
        """测试检查权限"""
        session = SessionContext(permissions=["read", "write"])
        
        assert session.has_permission("read")
        assert session.has_permission("write")
        assert not session.has_permission("delete")
        
        # 通配符权限
        session.permissions.append("*")
        assert session.has_permission("any_permission")
    
    def test_has_role(self):
        """测试检查角色"""
        session = SessionContext(roles=["admin", "user"])
        
        assert session.has_role("admin")
        assert session.has_role("user")
        assert not session.has_role("guest")


class TestAgentContext:
    """测试Agent上下文"""
    
    def test_context_creation(self):
        """测试上下文创建"""
        context = AgentContext()
        
        assert context.trace_id is not None
        assert context.session_id is not None
        assert context.user_id is None
        assert not context.cancellation_token.is_cancelled
    
    def test_context_with_user(self):
        """测试带用户的上下文"""
        context = AgentContext(
            user_id="user123",
            session_id="session456"
        )
        
        assert context.user_id == "user123"
        assert context.session_id == "session456"
        assert context.session.session_id == "session456"
    
    def test_get_set_metadata(self):
        """测试获取和设置元数据"""
        context = AgentContext()
        
        # 设置简单键
        context.set("key1", "value1")
        assert context.get("key1") == "value1"
        
        # 设置嵌套键
        context.set("user.settings.theme", "dark")
        assert context.get("user.settings.theme") == "dark"
        
        # 获取不存在的键
        assert context.get("nonexistent") is None
        assert context.get("nonexistent", "default") == "default"
    
    def test_update_metadata(self):
        """测试批量更新元数据"""
        context = AgentContext()
        
        context.update({
            "key1": "value1",
            "key2": "value2",
            "nested": {"key": "value"}
        })
        
        assert context.get("key1") == "value1"
        assert context.get("key2") == "value2"
        assert context.get("nested.key") == "value"
    
    def test_cancel_context(self):
        """测试取消上下文"""
        context = AgentContext()
        
        context.cancel("User cancelled")
        
        assert context.cancellation_token.is_cancelled
        assert context.cancellation_token.cancellation_reason == "User cancelled"
    
    def test_create_child_context(self):
        """测试创建子上下文"""
        parent = AgentContext(user_id="user123")
        child = parent.create_child()
        
        # 子上下文应该继承父上下文的某些属性
        assert child.trace_id == parent.trace_id
        assert child.session_id == parent.session_id
        assert child.user_id == parent.user_id
        
        # 但应该有不同的创建时间
        assert child.created_at >= parent.created_at
    
    def test_to_dict(self):
        """测试转换为字典"""
        context = AgentContext(
            user_id="user123",
            session_id="session456"
        )
        context.set("key", "value")
        
        data = context.to_dict()
        
        assert data["trace_id"] == context.trace_id
        assert data["session_id"] == context.session_id
        assert data["user_id"] == "user123"
        assert data["metadata"]["key"] == "value"
        assert "is_cancelled" in data
    
    def test_log_event(self, caplog):
        """测试记录事件"""
        context = AgentContext()
        
        context.log_event("test_event", extra_data="value")
        
        # 验证事件被记录到trace
        assert len(context.trace.logs) == 1
        assert context.trace.logs[0]["event_type"] == "test_event"
        assert context.trace.logs[0]["extra_data"] == "value"
    
    def test_context_manager(self):
        """测试上下文管理器"""
        with AgentContext() as context:
            # 在上下文中
            assert get_current_context() is context
        
        # 退出后应该清除当前上下文
        assert get_current_context() is None
        
        # 追踪应该完成
        assert context.trace.end_time is not None


class TestContextVariables:
    """测试上下文变量"""
    
    def test_get_current_context_none(self):
        """测试获取当前上下文(无)"""
        # 重置上下文变量
        CURRENT_CONTEXT.set(None)
        
        assert get_current_context() is None
    
    def test_context_manager_sets_current(self):
        """测试上下文管理器设置当前上下文"""
        context = AgentContext(user_id="user123")
        
        with context:
            current = get_current_context()
            assert current is context
            assert current.user_id == "user123"
    
    def test_create_context_function(self):
        """测试create_context函数"""
        context = create_context(
            user_id="user123",
            session_id="session456"
        )
        
        assert isinstance(context, AgentContext)
        assert context.user_id == "user123"
        assert context.session_id == "session456"
    
    def test_nested_contexts(self):
        """测试嵌套上下文"""
        parent_context = AgentContext(user_id="parent")
        
        with parent_context:
            assert get_current_context().user_id == "parent"
            
            child_context = AgentContext.from_parent(parent, user_id="child")
            with child_context:
                assert get_current_context().user_id == "child"
                assert get_current_context().trace_id == parent_context.trace_id
            
            # 退出子上下文后应该回到父上下文
            assert get_current_context().user_id == "parent"


# 并发测试
class TestConcurrentContext:
    """测试并发上下文"""
    
    @pytest.mark.asyncio
    async def test_concurrent_context_creation(self):
        """测试并发创建上下文"""
        async def create_context():
            return AgentContext()
        
        # 并发创建100个上下文
        contexts = await asyncio.gather(*[create_context() for _ in range(100)])
        
        # 验证所有上下文都有唯一的ID
        trace_ids = [ctx.trace_id for ctx in contexts]
        assert len(set(trace_ids)) == 100
    
    @pytest.mark.asyncio
    async def test_concurrent_cancellation(self):
        """测试并发取消"""
        context = AgentContext()
        
        async def check_cancelled():
            for _ in range(10):
                if context.cancellation_token.is_cancelled:
                    return True
                await asyncio.sleep(0.01)
            return False
        
        # 异步取消
        cancel_task = asyncio.create_task(asyncio.sleep(0.05))
        check_task = asyncio.create_task(check_cancelled())
        
        await cancel_task
        context.cancel()
        
        result = await check_task
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src/agents/unified/context", "--cov-report=html"])
