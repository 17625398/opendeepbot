"""
Agent Orchestrator 单元测试 (第一部分)
测试 Workflow, WorkflowStep, WorkflowStepType 的功能
"""

import pytest
import asyncio
from datetime import datetime
from src.agents.unified.orchestrator import (
    Workflow,
    WorkflowStep,
    WorkflowStepType,
    WorkflowResult
)
from src.agents.unified.base import AgentInput, AgentOutput


# 创建测试Agent
class MockAgent:
    """模拟Agent"""
    
    def __init__(self, name="mock"):
        self.name = name
        self.processed_count = 0
    
    async def process(self, input_data):
        self.processed_count += 1
        return AgentOutput(
            success=True,
            data={"result": f"Processed by {self.name}"}
        )


class TestWorkflowStep:
    """测试工作流步骤"""
    
    def test_create_simple_step(self):
        """测试创建简单步骤"""
        step = WorkflowStep(
            name="step1",
            agent_type="test_agent",
            input_data=AgentInput(query="test")
        )
        
        assert step.name == "step1"
        assert step.agent_type == "test_agent"
        assert step.step_type == WorkflowStepType.SEQUENTIAL
        assert step.enabled is True
    
    def test_create_parallel_step(self):
        """测试创建并行步骤"""
        step = WorkflowStep(
            name="parallel_step",
            agent_type="test_agent",
            step_type=WorkflowStepType.PARALLEL
        )
        
        assert step.step_type == WorkflowStepType.PARALLEL
    
    def test_create_conditional_step(self):
        """测试创建条件步骤"""
        def condition_func(ctx):
            return ctx.get("flag", False)
        
        step = WorkflowStep(
            name="conditional_step",
            agent_type="test_agent",
            step_type=WorkflowStepType.CONDITIONAL,
            condition=condition_func
        )
        
        assert step.step_type == WorkflowStepType.CONDITIONAL
        assert callable(step.condition)
    
    def test_create_loop_step(self):
        """测试创建循环步骤"""
        def max_iterations_func(ctx):
            return ctx.get("max_iterations", 3)
        
        step = WorkflowStep(
            name="loop_step",
            agent_type="test_agent",
            step_type=WorkflowStepType.LOOP,
            max_iterations=max_iterations_func
        )
        
        assert step.step_type == WorkflowStepType.LOOP
        assert callable(step.max_iterations)
    
    def test_step_dependencies(self):
        """测试步骤依赖"""
        step1 = WorkflowStep(name="step1", agent_type="agent1")
        step2 = WorkflowStep(name="step2", agent_type="agent2")
        
        step2.depends_on = ["step1"]
        
        assert "step1" in step2.depends_on


class TestWorkflow:
    """测试工作流"""
    
    def test_create_empty_workflow(self):
        """测试创建空工作流"""
        workflow = Workflow(name="test_workflow")
        
        assert workflow.name == "test_workflow"
        assert len(workflow.steps) == 0
    
    def test_create_workflow_with_steps(self):
        """测试创建带步骤的工作流"""
        steps = [
            WorkflowStep(name="step1", agent_type="agent1"),
            WorkflowStep(name="step2", agent_type="agent2"),
        ]
        
        workflow = Workflow(name="test_workflow", steps=steps)
        
        assert len(workflow.steps) == 2
        assert workflow.steps[0].name == "step1"
        assert workflow.steps[1].name == "step2"
    
    def test_add_step(self):
        """测试添加步骤"""
        workflow = Workflow(name="test_workflow")
        step = WorkflowStep(name="step1", agent_type="agent1")
        
        workflow.add_step(step)
        
        assert len(workflow.steps) == 1
        assert workflow.steps[0].name == "step1"
    
    def test_remove_step(self):
        """测试移除步骤"""
        workflow = Workflow(name="test_workflow")
        workflow.add_step(WorkflowStep(name="step1", agent_type="agent1"))
        workflow.add_step(WorkflowStep(name="step2", agent_type="agent2"))
        
        workflow.remove_step("step1")
        
        assert len(workflow.steps) == 1
        assert workflow.steps[0].name == "step2"
    
    def test_get_step(self):
        """测试获取步骤"""
        workflow = Workflow(name="test_workflow")
        workflow.add_step(WorkflowStep(name="step1", agent_type="agent1"))
        
        step = workflow.get_step("step1")
        
        assert step is not None
        assert step.name == "step1"
    
    def test_get_nonexistent_step(self):
        """测试获取不存在的步骤"""
        workflow = Workflow(name="test_workflow")
        
        step = workflow.get_step("nonexistent")
        
        assert step is None
    
    def test_validate_workflow(self):
        """测试验证工作流"""
        workflow = Workflow(name="test_workflow")
        workflow.add_step(WorkflowStep(name="step1", agent_type="agent1"))
        
        # 应该通过验证
        assert workflow.validate()
    
    def test_validate_circular_dependencies(self):
        """测试验证循环依赖"""
        workflow = Workflow(name="test_workflow")
        step1 = WorkflowStep(name="step1", agent_type="agent1")
        step2 = WorkflowStep(name="step2", agent_type="agent2")
        step3 = WorkflowStep(name="step3", agent_type="agent3")
        
        step1.depends_on = ["step2"]
        step2.depends_on = ["step3"]
        step3.depends_on = ["step1"]  # 循环依赖
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        
        # 应该验证失败
        assert not workflow.validate()
    
    def test_validate_missing_dependency(self):
        """测试验证缺失的依赖"""
        workflow = Workflow(name="test_workflow")
        step = WorkflowStep(name="step1", agent_type="agent1")
        step.depends_on = ["nonexistent_step"]
        
        workflow.add_step(step)
        
        # 应该验证失败
        assert not workflow.validate()
    
    def test_get_execution_order(self):
        """测试获取执行顺序"""
        workflow = Workflow(name="test_workflow")
        
        # 步骤: 1 -> 2 -> 3 (串行依赖)
        step1 = WorkflowStep(name="step1", agent_type="agent1")
        step2 = WorkflowStep(name="step2", agent_type="agent2")
        step2.depends_on = ["step1"]
        step3 = WorkflowStep(name="step3", agent_type="agent3")
        step3.depends_on = ["step2"]
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        
        order = workflow.get_execution_order()
        
        assert order == ["step1", "step2", "step3"]
    
    def test_get_parallel_execution_groups(self):
        """测试获取并行执行组"""
        workflow = Workflow(name="test_workflow")
        
        # 步骤: 1 -> (2, 3) -> 4
        step1 = WorkflowStep(name="step1", agent_type="agent1")
        step2 = WorkflowStep(name="step2", agent_type="agent2")
        step2.depends_on = ["step1"]
        step3 = WorkflowStep(name="step3", agent_type="agent3")
        step3.depends_on = ["step1"]
        step4 = WorkflowStep(name="step4", agent_type="agent4")
        step4.depends_on = ["step2", "step3"]
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        workflow.add_step(step4)
        
        groups = workflow.get_parallel_execution_groups()
        
        assert len(groups) == 3  # 3个执行组
        assert groups[0] == ["step1"]
        assert set(groups[1]) == {"step2", "step3"}  # 并行
        assert groups[2] == ["step4"]
    
    def test_workflow_metadata(self):
        """测试工作流元数据"""
        workflow = Workflow(
            name="test_workflow",
            description="Test workflow description"
        )
        
        workflow.set_metadata("key", "value")
        
        assert workflow.get_metadata("key") == "value"
        assert workflow.description == "Test workflow description"
    
    def test_set_max_concurrency(self):
        """测试设置最大并发数"""
        workflow = Workflow(name="test_workflow")
        workflow.set_max_concurrency(5)
        
        assert workflow.max_concurrency == 5
    
    def test_set_timeout(self):
        """测试设置超时"""
        workflow = Workflow(name="test_workflow")
        workflow.set_timeout(60)
        
        assert workflow.timeout == 60


# 继续测试 AgentOrchestrator
from src.agents.unified.orchestrator import AgentOrchestrator
from src.agents.unified.base import AgentContext


class TestAgentOrchestrator:
    """测试Agent编排器"""
    
    @pytest.fixture
    def mock_registry(self):
        """创建Mock注册表"""
        class MockRegistry:
            def __init__(self):
                self.agents = {}
            
            def register(self, name, agent_class):
                self.agents[name] = agent_class
            
            def get(self, name, **kwargs):
                if name not in self.agents:
                    raise ValueError(f"Agent {name} not found")
                return self.agents[name](**kwargs)
        
        registry = MockRegistry()
        registry.register("test_agent", MockAgent)
        registry.register("slow_agent", MockAgent)
        registry.register("failing_agent", MockAgent)
        
        return registry
    
    @pytest.fixture
    def orchestrator(self, mock_registry):
        """创建编排器实例"""
        return AgentOrchestrator(max_concurrency=2, timeout=30)
    
    def test_orchestrator_creation(self, orchestrator):
        """测试创建编排器"""
        assert orchestrator.max_concurrency == 2
        assert orchestrator.timeout == 30
        assert orchestrator._running_tasks == 0
    
    def test_register_agent(self, orchestrator, mock_registry):
        """测试注册Agent"""
        orchestrator.register_agent("test_agent", MockAgent)
        
        assert "test_agent" in orchestrator._agent_registry
        assert orchestrator.has_agent("test_agent")
    
    def test_has_agent(self, orchestrator, mock_registry):
        """测试检查Agent是否存在"""
        assert not orchestrator.has_agent("nonexistent")
        
        orchestrator.register_agent("test_agent", MockAgent)
        assert orchestrator.has_agent("test_agent")
    
    def test_get_agent(self, orchestrator):
        """测试获取Agent"""
        orchestrator.register_agent("test_agent", MockAgent)
        
        agent = orchestrator.get_agent("test_agent")
        
        assert agent is not None
        assert agent.name == "test_agent"
    
    @pytest.mark.asyncio
    async def test_execute_step_sequential(self, orchestrator):
        """测试执行顺序步骤"""
        orchestrator.register_agent("test_agent", MockAgent)
        
        step = WorkflowStep(
            name="step1",
            agent_type="test_agent",
            input_data=AgentInput(query="test")
        )
        
        context = AgentContext()
        result = await orchestrator.execute_step(step, context)
        
        assert result.success
        assert result.step_outputs["step1"]["result"] == "Processed by test_agent"
    
    @pytest.mark.asyncio
    async def test_execute_workflow_sequential(self, orchestrator):
        """测试执行顺序工作流"""
        orchestrator.register_agent("agent1", MockAgent)
        orchestrator.register_agent("agent2", MockAgent)
        orchestrator.register_agent("agent3", MockAgent)
        
        workflow = Workflow(name="test_workflow")
        workflow.add_step(WorkflowStep(name="step1", agent_type="agent1"))
        workflow.add_step(WorkflowStep(name="step2", agent_type="agent2"))
        workflow.add_step(WorkflowStep(name="step3", agent_type="agent3"))
        
        context = AgentContext()
        result = await orchestrator.execute_workflow(workflow, context)
        
        assert result.success
        assert result.completed_steps == 3
        assert len(result.step_outputs) == 3
    
    @pytest.mark.asyncio
    async def test_execute_workflow_parallel(self, orchestrator):
        """测试执行并行工作流"""
        orchestrator.register_agent("agent1", MockAgent)
        orchestrator.register_agent("agent2", MockAgent)
        orchestrator.register_agent("agent3", MockAgent)
        
        workflow = Workflow(name="test_workflow")
        
        step1 = WorkflowStep(name="step1", agent_type="agent1")
        step2 = WorkflowStep(
            name="step2",
            agent_type="agent2",
            step_type=WorkflowStepType.PARALLEL
        )
        step3 = WorkflowStep(
            name="step3",
            agent_type="agent3",
            step_type=WorkflowStepType.PARALLEL
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        
        context = AgentContext()
        result = await orchestrator.execute_workflow(workflow, context)
        
        assert result.success
        assert result.completed_steps == 3
    
    @pytest.mark.asyncio
    async def test_workflow_with_dependencies(self, orchestrator):
        """测试带依赖的工作流"""
        orchestrator.register_agent("agent1", MockAgent)
        orchestrator.register_agent("agent2", MockAgent)
        orchestrator.register_agent("agent3", MockAgent)
        
        workflow = Workflow(name="test_workflow")
        
        step1 = WorkflowStep(name="step1", agent_type="agent1")
        step2 = WorkflowStep(
            name="step2",
            agent_type="agent2",
            depends_on=["step1"]
        )
        step3 = WorkflowStep(
            name="step3",
            agent_type="agent3",
            depends_on=["step1"]
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        
        context = AgentContext()
        result = await orchestrator.execute_workflow(workflow, context)
        
        assert result.success
        assert result.completed_steps == 3
        
        # 验证执行顺序
        assert "step1" in result.execution_order
        idx1 = result.execution_order.index("step1")
        idx2 = result.execution_order.index("step2")
        idx3 = result.execution_order.index("step3")
        
        assert idx1 < idx2
        assert idx1 < idx3
    
    @pytest.mark.asyncio
    async def test_conditional_step_execution(self, orchestrator):
        """测试条件步骤执行"""
        orchestrator.register_agent("agent1", MockAgent)
        orchestrator.register_agent("agent2", MockAgent)
        
        workflow = Workflow(name="test_workflow")
        
        step1 = WorkflowStep(name="step1", agent_type="agent1")
        step2 = WorkflowStep(
            name="step2",
            agent_type="agent2",
            step_type=WorkflowStepType.CONDITIONAL,
            condition=lambda ctx: ctx.get("flag", False)
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        
        # flag=False, step2不应该执行
        context1 = AgentContext()
        context1.set("flag", False)
        result1 = await orchestrator.execute_workflow(workflow, context1)
        
        assert result1.completed_steps == 1
        assert "step2" not in result1.step_outputs
        
        # flag=True, step2应该执行
        context2 = AgentContext()
        context2.set("flag", True)
        result2 = await orchestrator.execute_workflow(workflow, context2)
        
        assert result2.completed_steps == 2
        assert "step2" in result2.step_outputs
    
    @pytest.mark.asyncio
    async def test_loop_step_execution(self, orchestrator):
        """测试循环步骤执行"""
        class LoopAgent(MockAgent):
            def __init__(self):
                super().__init__()
                self.count = 0
            
            async def process(self, input_data):
                self.count += 1
                return AgentOutput(
                    success=True,
                    data={"count": self.count}
                )
        
        orchestrator.register_agent("loop_agent", LoopAgent)
        
        workflow = Workflow(name="test_workflow")
        
        step = WorkflowStep(
            name="loop_step",
            agent_type="loop_agent",
            step_type=WorkflowStepType.LOOP,
            max_iterations=lambda ctx: 3
        )
        
        workflow.add_step(step)
        
        context = AgentContext()
        result = await orchestrator.execute_workflow(workflow, context)
        
        assert result.success
        assert result.completed_steps == 1
        # 循环应该在步骤内部处理
    
    @pytest.mark.asyncio
    async def test_workflow_cancellation(self, orchestrator):
        """测试工作流取消"""
        orchestrator.register_agent("agent1", MockAgent)
        orchestrator.register_agent("agent2", MockAgent)
        
        workflow = Workflow(name="test_workflow")
        
        step1 = WorkflowStep(name="step1", agent_type="agent1")
        step2 = WorkflowStep(name="step2", agent_type="agent2")
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        
        context = AgentContext()
        
        # 创建取消任务
        async def cancel_after_delay():
            await asyncio.sleep(0.01)
            context.cancel("Test cancellation")
        
        # 并发执行和取消
        cancel_task = asyncio.create_task(cancel_after_delay())
        result = await orchestrator.execute_workflow(workflow, context)
        
        await cancel_task
        
        # 应该被取消
        assert result.cancelled
        assert result.cancellation_reason == "Test cancellation"
    
    @pytest.mark.asyncio
    async def test_workflow_timeout(self, orchestrator):
        """测试工作流超时"""
        class SlowAgent:
            async def process(self, input_data):
                await asyncio.sleep(10)  # 超过超时时间
                return AgentOutput(success=True, data={})
        
        orchestrator.register_agent("slow_agent", SlowAgent)
        orchestrator.timeout = 0.1
        
        workflow = Workflow(name="test_workflow")
        workflow.add_step(WorkflowStep(name="step1", agent_type="slow_agent"))
        
        context = AgentContext()
        result = await orchestrator.execute_workflow(workflow, context)
        
        # 应该超时
        assert not result.success
        assert "timeout" in result.error.lower().casefold()
    
    @pytest.mark.asyncio
    async def test_concurrency_limit(self, orchestrator):
        """测试并发限制"""
        orchestrator.register_agent("agent1", MockAgent)
        
        workflow = Workflow(name="test_workflow")
        
        # 创建5个并行步骤
        for i in range(5):
            workflow.add_step(
                WorkflowStep(
                    name=f"step{i}",
                    agent_type="agent1",
                    step_type=WorkflowStepType.PARALLEL
                )
            )
        
        context = AgentContext()
        result = await orchestrator.execute_workflow(workflow, context)
        
        assert result.success
        # 所有步骤都应该完成
        assert len(result.step_outputs) == 5
    
    @pytest.mark.asyncio
    async def test_step_data_passing(self, orchestrator):
        """测试步骤间数据传递"""
        class DataAgent:
            async def process(self, input_data):
                value = input_data.metadata.get("value", 0)
                return AgentOutput(
                    success=True,
                    data={"result": value + 1}
                )
        
        orchestrator.register_agent("agent1", DataAgent)
        
        workflow = Workflow(name="test_workflow")
        
        step1 = WorkflowStep(
            name="step1",
            agent_type="agent1",
            input_data=AgentInput(metadata={"value": 1})
        )
        
        workflow.add_step(step1)
        
        context = AgentContext()
        result = await orchestrator.execute_workflow(workflow, context)
        
        assert result.success
        assert result.step_outputs["step1"]["result"] == 2
    
    def test_get_statistics(self, orchestrator):
        """测试获取统计信息"""
        orchestrator.register_agent("agent1", MockAgent)
        
        stats = orchestrator.get_statistics()
        
        assert stats["registered_agents"] == 1
        assert stats["active_tasks"] == 0
        assert stats["max_concurrency"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src/agents/unified/orchestrator", "--cov-report=html"])
