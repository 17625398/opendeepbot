#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentScope Integration Examples
================================

AgentScope Studio 集成使用示例。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def example_1_basic_monitoring():
    """示例 1: 基础监控。"""
    print("=" * 60)
    print("示例 1: 基础监控")
    print("=" * 60)
    
    from src.integrations.agentscope import AgentScopeMonitor
    
    # 创建监控器
    monitor = AgentScopeMonitor(
        studio_url="http://localhost:5000",
        project_name="DeepTutor-Example"
    )
    
    # 启用监控
    if monitor.enable():
        print("✓ 监控已启用")
        print(f"  Studio URL: {monitor.studio_url}")
        print(f"  项目名称: {monitor.project_name}")
        
        # 获取状态
        status = monitor.get_status()
        print(f"  状态: {status}")
        
        # 禁用监控
        monitor.disable()
        print("✓ 监控已禁用")
    else:
        print("⚠ 监控启用失败（可能未安装 AgentScope）")


def example_2_wrap_agent():
    """示例 2: 包装 Agent。"""
    print("\n" + "=" * 60)
    print("示例 2: 包装 Agent")
    print("=" * 60)
    
    from src.integrations.agentscope import wrap_agent
    
    # 创建模拟 Agent
    class CaseAnalysisAgent:
        def process(self, case_data):
            return f"案件分析结果: {case_data}"
    
    agent = CaseAnalysisAgent()
    
    # 包装 Agent
    wrapped = wrap_agent(
        agent,
        name="CaseAnalysisAgent",
        sys_prompt="你是一个案件分析专家"
    )
    
    print(f"✓ Agent 已包装: {wrapped.name}")
    print(f"  是否成功包装: {wrapped.is_wrapped()}")
    
    # 使用包装的 Agent
    result = wrapped.process("测试案件数据")
    print(f"  处理结果: {result}")


def example_3_service_usage():
    """示例 3: 使用服务。"""
    print("\n" + "=" * 60)
    print("示例 3: 使用服务")
    print("=" * 60)
    
    from src.integrations.agentscope import AgentScopeService
    
    # 创建服务
    service = AgentScopeService(auto_enable=False)
    
    print("✓ 服务已创建")
    
    # 创建并包装多个 Agent
    class Agent1:
        def process(self, data):
            return f"Agent1: {data}"
    
    class Agent2:
        def process(self, data):
            return f"Agent2: {data}"
    
    agent1 = Agent1()
    agent2 = Agent2()
    
    service.wrap_agent(agent1, name="Agent1")
    service.wrap_agent(agent2, name="Agent2")
    
    print(f"✓ 已包装 Agent: {service.list_wrapped_agents()}")
    
    # 获取状态
    status = service.get_status()
    print(f"  服务状态: {status['service']}")
    print(f"  包装的 Agent 数量: {len(status['wrapped_agents'])}")


def example_4_environment_config():
    """示例 4: 环境变量配置。"""
    print("\n" + "=" * 60)
    print("示例 4: 环境变量配置")
    print("=" * 60)
    
    import os
    from src.integrations.agentscope import AgentScopeMonitor
    
    # 设置环境变量
    os.environ["AGENTSCOPE_STUDIO_URL"] = "http://localhost:5000"
    os.environ["AGENTSCOPE_PROJECT"] = "DeepTutor"
    os.environ["AGENTSCOPE_ENABLED"] = "false"  # 不自动启用
    
    # 从环境变量创建
    monitor = AgentScopeMonitor.from_env()
    
    print("✓ 从环境变量创建监控器")
    print(f"  Studio URL: {monitor.studio_url}")
    print(f"  项目名称: {monitor.project_name}")
    print(f"  是否启用: {monitor.is_enabled()}")
    
    # 清理环境变量
    for key in ["AGENTSCOPE_STUDIO_URL", "AGENTSCOPE_PROJECT", "AGENTSCOPE_ENABLED"]:
        if key in os.environ:
            del os.environ[key]


def example_5_workflow_simulation():
    """示例 5: 工作流模拟。"""
    print("\n" + "=" * 60)
    print("示例 5: 工作流模拟")
    print("=" * 60)
    
    from src.integrations.agentscope import AgentScopeService
    
    # 创建服务
    service = AgentScopeService(auto_enable=False)
    
    # 模拟 DeepTutor 工作流中的多个 Agent
    class DocumentParserAgent:
        def process(self, document):
            return {"text": f"解析的文本: {document}", "tables": []}
    
    class CaseAnalyzerAgent:
        def process(self, parsed_data):
            return {"analysis": f"分析结果: {parsed_data['text']}", "score": 0.95}
    
    class ReportGeneratorAgent:
        def process(self, analysis):
            return f"报告: {analysis['analysis']}"
    
    # 创建并包装 Agent
    parser = DocumentParserAgent()
    analyzer = CaseAnalyzerAgent()
    reporter = ReportGeneratorAgent()
    
    wrapped_parser = service.wrap_agent(parser, name="DocumentParser")
    wrapped_analyzer = service.wrap_agent(analyzer, name="CaseAnalyzer")
    wrapped_reporter = service.wrap_agent(reporter, name="ReportGenerator")
    
    print("✓ 工作流 Agent 已创建")
    
    # 模拟工作流执行
    print("\n执行工作流:")
    
    # 步骤 1: 解析文档
    doc_result = wrapped_parser.process("案件文档.docx")
    print(f"  1. 文档解析: {doc_result}")
    
    # 步骤 2: 分析案件
    analysis_result = wrapped_analyzer.process(doc_result)
    print(f"  2. 案件分析: {analysis_result}")
    
    # 步骤 3: 生成报告
    report_result = wrapped_reporter.process(analysis_result)
    print(f"  3. 报告生成: {report_result}")
    
    print("\n✓ 工作流执行完成")


def example_6_check_availability():
    """示例 6: 检查可用性。"""
    print("\n" + "=" * 60)
    print("示例 6: 检查可用性")
    print("=" * 60)
    
    from src.integrations.agentscope import AgentScopeService
    
    is_available = AgentScopeService.is_available()
    
    if is_available:
        print("✓ AgentScope 已安装且可用")
        print("  可以使用完整的 AgentScope Studio 功能")
    else:
        print("⚠ AgentScope 未安装")
        print("  安装方法: pip install agentscope")
        print("  当前仍可使用基础包装功能")


def main():
    """运行所有示例。"""
    print("AgentScope Integration Examples")
    print("=" * 60)
    
    examples = [
        example_1_basic_monitoring,
        example_2_wrap_agent,
        example_3_service_usage,
        example_4_environment_config,
        example_5_workflow_simulation,
        example_6_check_availability,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n✗ 示例执行失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
