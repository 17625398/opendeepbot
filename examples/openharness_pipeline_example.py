"""
OpenHarness 流水线使用示例

展示如何使用流水线系统组合多个工具
"""

import asyncio
from src.integrations.openharness import (
    create_pipeline,
    PipelineStep,
    PipelineExecutor,
    StepType,
    create_all_tools,
)


async def simple_pipeline_example():
    """简单流水线示例"""
    print("=" * 50)
    print("示例 1: 简单工具流水线")
    print("=" * 50)
    
    # 创建工具注册表
    tools = create_all_tools()
    tool_registry = {tool.name: tool for tool in tools}
    
    # 创建流水线
    pipeline = create_pipeline("文件处理流水线", "读取、处理、保存文件")
    
    # 步骤 1: 读取文件
    step1 = PipelineStep(
        id="read_file",
        name="读取文件",
        type=StepType.TOOL,
        config={
            "tool": "file_read",
            "arguments": {
                "path": "input.txt"
            }
        },
        on_success="process_content"
    )
    pipeline.add_step(step1)
    
    # 步骤 2: 处理内容
    step2 = PipelineStep(
        id="process_content",
        name="处理内容",
        type=StepType.TOOL,
        config={
            "tool": "bash",
            "arguments": {
                "command": "echo '${read_file}' | tr 'a-z' 'A-Z'",
                "working_dir": "."
            }
        },
        on_success="save_file"
    )
    pipeline.add_step(step2)
    
    # 步骤 3: 保存文件
    step3 = PipelineStep(
        id="save_file",
        name="保存文件",
        type=StepType.TOOL,
        config={
            "tool": "file_write",
            "arguments": {
                "path": "output.txt",
                "content": "${process_content}"
            }
        }
    )
    pipeline.add_step(step3)
    
    # 设置起始步骤
    pipeline.set_start_step("read_file")
    
    # 执行流水线
    executor = PipelineExecutor(tool_registry)
    result = await executor.execute(pipeline)
    
    print(f"流水线执行结果: {result['success']}")
    print(f"执行步骤: {result['executed_steps']}")


async def conditional_pipeline_example():
    """条件分支流水线示例"""
    print("\n" + "=" * 50)
    print("示例 2: 条件分支流水线")
    print("=" * 50)
    
    tools = create_all_tools()
    tool_registry = {tool.name: tool for tool in tools}
    
    # 创建流水线
    pipeline = create_pipeline("条件处理流水线", "根据条件选择不同分支")
    
    # 步骤 1: 检查文件大小
    step1 = PipelineStep(
        id="check_size",
        name="检查文件大小",
        type=StepType.TOOL,
        config={
            "tool": "bash",
            "arguments": {
                "command": "stat -f%z data.txt 2>/dev/null || echo 0",
                "working_dir": "."
            }
        },
        on_success="size_condition"
    )
    pipeline.add_step(step1)
    
    # 步骤 2: 条件判断
    step2 = PipelineStep(
        id="size_condition",
        name="大小判断",
        type=StepType.CONDITION,
        config={
            "condition": "${check_size} > 1024",
            "true_branch": "compress_file",
            "false_branch": "copy_file"
        }
    )
    pipeline.add_step(step2)
    
    # 分支 1: 压缩大文件
    step3 = PipelineStep(
        id="compress_file",
        name="压缩文件",
        type=StepType.TOOL,
        config={
            "tool": "bash",
            "arguments": {
                "command": "gzip -c data.txt > data.txt.gz",
                "working_dir": "."
            }
        }
    )
    pipeline.add_step(step3)
    
    # 分支 2: 复制小文件
    step4 = PipelineStep(
        id="copy_file",
        name="复制文件",
        type=StepType.TOOL,
        config={
            "tool": "bash",
            "arguments": {
                "command": "cp data.txt data_backup.txt",
                "working_dir": "."
            }
        }
    )
    pipeline.add_step(step4)
    
    pipeline.set_start_step("check_size")
    
    # 执行
    executor = PipelineExecutor(tool_registry)
    result = await executor.execute(pipeline)
    
    print(f"流水线执行结果: {result['success']}")
    print(f"执行步骤: {result['executed_steps']}")


async def parallel_pipeline_example():
    """并行执行流水线示例"""
    print("\n" + "=" * 50)
    print("示例 3: 并行执行流水线")
    print("=" * 50)
    
    tools = create_all_tools()
    tool_registry = {tool.name: tool for tool in tools}
    
    # 创建流水线
    pipeline = create_pipeline("并行处理流水线", "并行处理多个文件")
    
    # 并行步骤
    step1 = PipelineStep(
        id="parallel_process",
        name="并行处理",
        type=StepType.PARALLEL,
        config={
            "branches": [
                {
                    "id": "process_a",
                    "steps": [
                        {"id": "read_a", "type": "tool", "config": {"tool": "file_read", "arguments": {"path": "file_a.txt"}}},
                        {"id": "transform_a", "type": "tool", "config": {"tool": "bash", "arguments": {"command": "echo '${read_a}' | sort"}}}
                    ]
                },
                {
                    "id": "process_b",
                    "steps": [
                        {"id": "read_b", "type": "tool", "config": {"tool": "file_read", "arguments": {"path": "file_b.txt"}}},
                        {"id": "transform_b", "type": "tool", "config": {"tool": "bash", "arguments": {"command": "echo '${read_b}' | uniq"}}}
                    ]
                },
                {
                    "id": "process_c",
                    "steps": [
                        {"id": "read_c", "type": "tool", "config": {"tool": "file_read", "arguments": {"path": "file_c.txt"}}},
                        {"id": "transform_c", "type": "tool", "config": {"tool": "bash", "arguments": {"command": "echo '${read_c}' | wc -l"}}}
                    ]
                }
            ],
            "max_concurrency": 3
        },
        on_success="merge_results"
    )
    pipeline.add_step(step1)
    
    # 合并结果
    step2 = PipelineStep(
        id="merge_results",
        name="合并结果",
        type=StepType.TOOL,
        config={
            "tool": "bash",
            "arguments": {
                "command": "echo '所有文件处理完成'",
                "working_dir": "."
            }
        }
    )
    pipeline.add_step(step2)
    
    pipeline.set_start_step("parallel_process")
    
    # 执行
    executor = PipelineExecutor(tool_registry)
    result = await executor.execute(pipeline)
    
    print(f"流水线执行结果: {result['success']}")
    print(f"执行步骤: {result['executed_steps']}")


async def loop_pipeline_example():
    """循环流水线示例"""
    print("\n" + "=" * 50)
    print("示例 4: 循环流水线")
    print("=" * 50)
    
    tools = create_all_tools()
    tool_registry = {tool.name: tool for tool in tools}
    
    # 创建流水线
    pipeline = create_pipeline("批量处理流水线", "批量处理多个文件")
    
    # 循环步骤
    step1 = PipelineStep(
        id="batch_process",
        name="批量处理",
        type=StepType.LOOP,
        config={
            "loop_type": "for",
            "items": ["file1.txt", "file2.txt", "file3.txt"],
            "item_var": "filename",
            "steps": [
                {
                    "id": "read",
                    "type": "tool",
                    "config": {"tool": "file_read", "arguments": {"path": "${filename}"}}
                },
                {
                    "id": "process",
                    "type": "tool",
                    "config": {"tool": "bash", "arguments": {"command": "echo '${read}' | head -5"}}
                }
            ],
            "max_iterations": 10
        }
    )
    pipeline.add_step(step1)
    
    pipeline.set_start_step("batch_process")
    
    # 执行
    executor = PipelineExecutor(tool_registry)
    result = await executor.execute(pipeline)
    
    print(f"流水线执行结果: {result['success']}")
    print(f"执行步骤: {result['executed_steps']}")


async def complex_pipeline_example():
    """复杂流水线示例"""
    print("\n" + "=" * 50)
    print("示例 5: 复杂流水线")
    print("=" * 50)
    
    tools = create_all_tools()
    tool_registry = {tool.name: tool for tool in tools}
    
    # 创建流水线
    pipeline = create_pipeline(
        "数据处理流水线",
        "完整的数据处理流程：提取、转换、加载"
    )
    
    # 1. 数据提取
    step1 = PipelineStep(
        id="extract",
        name="数据提取",
        type=StepType.TOOL,
        config={
            "tool": "database_query",
            "arguments": {
                "connection": {"db_type": "sqlite", "database": "source.db"},
                "query": "SELECT * FROM users WHERE created_at > '2024-01-01'",
                "max_rows": 1000
            }
        },
        on_success="validate"
    )
    pipeline.add_step(step1)
    
    # 2. 数据验证
    step2 = PipelineStep(
        id="validate",
        name="数据验证",
        type=StepType.CONDITION,
        config={
            "condition": "${extract.row_count} > 0",
            "true_branch": "transform",
            "false_branch": "no_data"
        }
    )
    pipeline.add_step(step2)
    
    # 3. 数据转换
    step3 = PipelineStep(
        id="transform",
        name="数据转换",
        type=StepType.TOOL,
        config={
            "tool": "bash",
            "arguments": {
                "command": "echo '${extract}' | jq '.rows | map({id: .id, name: .name | ascii_upcase, email: .email})'",
                "working_dir": "."
            }
        },
        on_success="load"
    )
    pipeline.add_step(step3)
    
    # 4. 数据加载
    step4 = PipelineStep(
        id="load",
        name="数据加载",
        type=StepType.TOOL,
        config={
            "tool": "database_insert",
            "arguments": {
                "connection": {"db_type": "sqlite", "database": "target.db"},
                "table": "processed_users",
                "data": "${transform}"
            }
        },
        on_success="notify"
    )
    pipeline.add_step(step4)
    
    # 5. 发送通知
    step5 = PipelineStep(
        id="notify",
        name="发送通知",
        type=StepType.TOOL,
        config={
            "tool": "webhook_trigger",
            "arguments": {
                "webhook_url": "https://hooks.example.com/notify",
                "payload": {
                    "status": "success",
                    "processed_count": "${load.inserted_count}",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            }
        }
    )
    pipeline.add_step(step5)
    
    # 无数据处理分支
    step6 = PipelineStep(
        id="no_data",
        name="无数据处理",
        type=StepType.TOOL,
        config={
            "tool": "bash",
            "arguments": {
                "command": "echo '没有需要处理的数据'",
                "working_dir": "."
            }
        }
    )
    pipeline.add_step(step6)
    
    pipeline.set_start_step("extract")
    
    # 执行
    executor = PipelineExecutor(tool_registry)
    result = await executor.execute(pipeline)
    
    print(f"流水线执行结果: {result['success']}")
    print(f"执行步骤: {result['executed_steps']}")


async def main():
    """主函数"""
    print("OpenHarness 流水线使用示例")
    print("=" * 50)
    
    # 运行所有示例
    await simple_pipeline_example()
    await conditional_pipeline_example()
    await parallel_pipeline_example()
    await loop_pipeline_example()
    await complex_pipeline_example()
    
    print("\n" + "=" * 50)
    print("所有示例执行完成!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
