"""MCP (Model Context Protocol) 使用示例

这个示例展示了如何在 DeepTutor 中使用 MCP 功能。
"""

import asyncio
import sys
sys.path.insert(0, 'D:\\aitools\\DeepTutor-main')

from src.nanobot.mcp import get_mcp_client
from src.nanobot.mcp.types import MCPTool, MCPToolParameter, MCPToolType, MCPResource, MCPPrompt


async def basic_usage():
    """基本使用示例"""
    print("=== MCP 基本使用示例 ===\n")
    
    # 1. 获取 MCP 客户端
    mcp_client = await get_mcp_client()
    
    # 2. 初始化客户端
    await mcp_client.initialize()
    print("✓ MCP 客户端初始化完成\n")
    
    # 3. 列出所有可用工具
    tools = mcp_client.list_tools()
    print(f"可用工具 ({len(tools)} 个):")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    print()
    
    # 4. 执行计算工具
    print("执行计算工具 (2 + 2 * 10):")
    result = await mcp_client.execute_tool("calculate", {
        "expression": "2 + 2 * 10"
    })
    print(f"  结果: {result}\n")
    
    # 5. 执行 Web 搜索
    print("执行 Web 搜索:")
    try:
        result = await mcp_client.execute_tool("web_search", {
            "query": "Python programming",
            "num_results": 3
        })
        print(f"  结果: {result}\n")
    except Exception as e:
        print(f"  错误: {e}\n")


async def custom_tool_example():
    """自定义工具示例"""
    print("=== 自定义工具示例 ===\n")
    
    mcp_client = await get_mcp_client()
    await mcp_client.initialize()
    
    # 定义自定义工具处理函数
    async def greet_handler(name: str, greeting: str = "Hello"):
        """问候用户"""
        return f"{greeting}, {name}! Welcome to DeepTutor."
    
    # 创建工具定义
    greet_tool = MCPTool(
        name="greet",
        description="Greet a user with a custom message",
        type=MCPToolType.EXECUTE,
        parameters=[
            MCPToolParameter(
                name="name",
                description="User's name",
                type="string",
                required=True
            ),
            MCPToolParameter(
                name="greeting",
                description="Greeting message",
                type="string",
                required=False,
                default="Hello"
            ),
        ],
        handler=greet_handler
    )
    
    # 注册工具
    mcp_client.register_tool(greet_tool)
    print("✓ 自定义工具 'greet' 已注册\n")
    
    # 执行自定义工具
    print("执行自定义工具:")
    result = await mcp_client.execute_tool("greet", {
        "name": "Alice",
        "greeting": "Hi"
    })
    print(f"  结果: {result}\n")


async def resource_example():
    """资源管理示例"""
    print("=== 资源管理示例 ===\n")
    
    mcp_client = await get_mcp_client()
    await mcp_client.initialize()
    
    from src.nanobot.mcp.types import MCPResourceType
    
    # 创建资源
    doc_resource = MCPResource(
        uri="docs://quickstart",
        name="Quick Start Guide",
        description="Quick start guide for DeepTutor",
        type=MCPResourceType.FILE,
        mime_type="text/markdown"
    )
    
    # 注册资源
    mcp_client.register_resource(doc_resource)
    print("✓ 资源已注册\n")
    
    # 获取资源
    resource = mcp_client.get_resource("docs://quickstart")
    if resource:
        print(f"资源信息:")
        print(f"  名称: {resource.name}")
        print(f"  描述: {resource.description}")
        print(f"  MIME类型: {resource.mime_type}\n")
    
    # 列出所有资源
    resources = mcp_client.list_resources()
    print(f"所有资源 ({len(resources)} 个):")
    for r in resources:
        print(f"  - {r.uri}: {r.name}")
    print()


async def prompt_example():
    """提示词模板示例"""
    print("=== 提示词模板示例 ===\n")
    
    mcp_client = await get_mcp_client()
    await mcp_client.initialize()
    
    # 创建提示词模板
    code_review_prompt = MCPPrompt(
        name="code_review",
        description="Review code for best practices",
        template="""Please review the following {language} code:

```{language}
{code}
```

Check for:
1. Code style issues
2. Potential bugs
3. Performance optimizations
4. Security concerns
"""
    )
    
    # 注册提示词
    mcp_client.register_prompt(code_review_prompt)
    print("✓ 提示词模板 'code_review' 已注册\n")
    
    # 获取提示词
    prompt = mcp_client.get_prompt("code_review")
    if prompt:
        print(f"提示词信息:")
        print(f"  名称: {prompt.name}")
        print(f"  描述: {prompt.description}")
        print(f"  模板预览: {prompt.template[:50]}...\n")


async def context_example():
    """上下文创建示例"""
    print("=== 上下文创建示例 ===\n")
    
    mcp_client = await get_mcp_client()
    await mcp_client.initialize()
    
    # 创建上下文
    context = mcp_client.create_context()
    print("✓ MCP 上下文已创建\n")
    
    print(f"上下文内容:")
    print(f"  资源数量: {len(context.resources)}")
    print(f"  工具数量: {len(context.tools)}")
    print(f"  提示词数量: {len(context.prompts)}\n")


async def main():
    """主函数"""
    print("MCP (Model Context Protocol) 示例\n")
    print("=" * 50)
    print()
    
    try:
        # 运行所有示例
        await basic_usage()
        await custom_tool_example()
        await resource_example()
        await prompt_example()
        await context_example()
        
        print("=" * 50)
        print("\n所有示例执行完成!")
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
