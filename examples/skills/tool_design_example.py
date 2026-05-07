"""
工具设计技能使用示例

这个示例展示了如何在 DeepTutor 中使用工具设计技能：
- 工具定义验证 - 验证工具定义是否符合最佳实践
- 文档生成 - 自动生成工具文档（Markdown格式）
- 使用示例生成 - 生成工具使用示例
- 参数验证 - 验证参数是否符合工具定义

运行说明:
    1. 确保已安装 DeepTutor 依赖
    2. 从项目根目录运行: python examples/skills/tool_design_example.py
    3. 或直接运行: python tool_design_example.py

功能演示:
    - 验证工具定义的正确性
    - 生成完整的工具文档
    - 生成多种使用示例
    - 验证工具参数
    - 检测工具设计问题
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.skills.tool_design import (
    ToolDesignSkill,
    ToolValidationReport,
    ValidationSeverity,
    ToolDocumentation,
    UsageExample,
)


# 示例工具定义 - 有效的工具
VALID_TOOL_DEFINITION = {
    "id": "data_processor",
    "name": "data_processor",
    "description": "处理和分析数据文件，支持CSV、JSON等格式。可以执行数据清洗、转换和统计分析。",
    "version": "1.2.0",
    "type": "custom",
    "status": "active",
    "parameters": [
        {
            "name": "file_path",
            "type": "string",
            "description": "要处理的数据文件路径",
            "required": True,
        },
        {
            "name": "operation",
            "type": "string",
            "description": "要执行的操作类型",
            "required": True,
            "enum": ["clean", "transform", "analyze", "convert"],
        },
        {
            "name": "output_format",
            "type": "string",
            "description": "输出格式",
            "required": False,
            "default": "csv",
            "enum": ["csv", "json", "excel"],
        },
        {
            "name": "options",
            "type": "object",
            "description": "额外的处理选项",
            "required": False,
        },
    ],
    "author": "DeepTutor Team",
    "tags": ["data", "processing", "analysis"],
    "category": "data_processing",
    "icon": "📊",
    "timeout": 60,
}

# 示例工具定义 - 有问题的工具
INVALID_TOOL_DEFINITION = {
    "id": "",
    "name": "Bad-Tool-Name",
    "description": "短",
    "version": "",
    "type": "api",
    "status": "active",
    "parameters": [
        {
            "name": "Param1",
            "type": "invalid_type",
            "description": "",
            "required": True,
        },
        {
            "name": "Param1",  # 重复参数名
            "type": "string",
            "description": "另一个参数",
            "required": False,
        },
    ],
}

# 示例工具定义 - 简单的计算器工具
CALCULATOR_TOOL = {
    "id": "calculator",
    "name": "calculator",
    "description": "执行基本的数学运算，包括加法、减法、乘法和除法。",
    "version": "1.0.0",
    "type": "custom",
    "status": "active",
    "parameters": [
        {
            "name": "operation",
            "type": "string",
            "description": "数学运算类型",
            "required": True,
            "enum": ["add", "subtract", "multiply", "divide"],
        },
        {
            "name": "operands",
            "type": "array",
            "description": "运算数列表",
            "required": True,
        },
        {
            "name": "precision",
            "type": "integer",
            "description": "结果精度（小数位数）",
            "required": False,
            "default": 2,
        },
    ],
    "author": "Math Team",
    "tags": ["math", "calculation"],
    "category": "utility",
    "icon": "🧮",
    "timeout": 10,
}

# 示例工具定义 - 文件搜索工具
FILE_SEARCH_TOOL = {
    "id": "file_search",
    "name": "file_search",
    "description": "在指定目录中搜索文件，支持按名称、类型、大小和修改时间过滤。",
    "version": "2.0.0",
    "type": "custom",
    "status": "active",
    "parameters": [
        {
            "name": "directory",
            "type": "string",
            "description": "搜索的起始目录路径",
            "required": True,
        },
        {
            "name": "pattern",
            "type": "string",
            "description": "文件名匹配模式（支持通配符）",
            "required": False,
            "default": "*",
        },
        {
            "name": "file_type",
            "type": "string",
            "description": "文件类型过滤",
            "required": False,
            "enum": ["file", "directory", "all"],
            "default": "all",
        },
        {
            "name": "recursive",
            "type": "boolean",
            "description": "是否递归搜索子目录",
            "required": False,
            "default": True,
        },
        {
            "name": "max_results",
            "type": "integer",
            "description": "最大返回结果数",
            "required": False,
            "default": 100,
        },
    ],
    "author": "File Utils Team",
    "tags": ["file", "search", "filesystem"],
    "category": "filesystem",
    "icon": "🔍",
    "timeout": 30,
}


async def demonstrate_tool_validation():
    """演示工具定义验证"""
    print("=" * 60)
    print("演示 1: 工具定义验证")
    print("=" * 60)
    print("\n特性说明:")
    print("  - 验证必填字段")
    print("  - 检查命名规范")
    print("  - 验证参数定义")
    print("  - 检查类型有效性")

    skill = ToolDesignSkill()

    # 验证有效工具
    print("\n✅ 验证有效工具定义:")
    print(f"  工具: {VALID_TOOL_DEFINITION['name']}")
    report = skill.validate_tool_definition(VALID_TOOL_DEFINITION)

    print(f"\n  验证结果:")
    print(f"    - 是否有效: {'是' if report.is_valid else '否'}")
    print(f"    - 错误数: {len(report.get_errors())}")
    print(f"    - 警告数: {len(report.get_warnings())}")

    if report.get_warnings():
        print("\n  警告信息:")
        for warning in report.get_warnings():
            print(f"    - {warning.message}")
            if warning.suggestion:
                print(f"      建议: {warning.suggestion}")

    # 验证有问题的工具
    print("\n" + "-" * 40)
    print("\n❌ 验证有问题的工具定义:")
    report = skill.validate_tool_definition(INVALID_TOOL_DEFINITION)

    print(f"\n  验证结果:")
    print(f"    - 是否有效: {'是' if report.is_valid else '否'}")
    print(f"    - 错误数: {len(report.get_errors())}")
    print(f"    - 警告数: {len(report.get_warnings())}")

    if report.get_errors():
        print("\n  错误信息:")
        for error in report.get_errors():
            print(f"    - [{error.field}] {error.message}")
            if error.suggestion:
                print(f"      建议: {error.suggestion}")

    if report.get_warnings():
        print("\n  警告信息:")
        for warning in report.get_warnings():
            print(f"    - [{warning.field}] {warning.message}")


async def demonstrate_documentation_generation():
    """演示文档生成"""
    print("\n" + "=" * 60)
    print("演示 2: 工具文档生成")
    print("=" * 60)

    skill = ToolDesignSkill()

    print("\n📝 生成数据处理器工具文档:")
    doc = skill.generate_tool_documentation(
        VALID_TOOL_DEFINITION,
        return_doc="返回处理后的数据，格式取决于 output_format 参数。"
    )

    print(f"\n  文档信息:")
    print(f"    - 工具ID: {doc.tool_id}")
    print(f"    - 名称: {doc.name}")
    print(f"    - 版本: {doc.version}")
    print(f"    - 参数数量: {len(doc.parameters_doc)}")
    print(f"    - 最佳实践数量: {len(doc.best_practices)}")

    print("\n  参数文档:")
    for param in doc.parameters_doc:
        req_marker = " (必填)" if param.get("required") else " (可选)"
        print(f"    - {param['name']}{req_marker}: {param['type']}")
        print(f"      {param['description']}")

    print("\n  最佳实践:")
    for i, practice in enumerate(doc.best_practices, 1):
        print(f"    {i}. {practice}")

    # 显示Markdown格式
    print("\n" + "-" * 40)
    print("\n📄 Markdown 格式预览（前30行）:")
    markdown = doc.to_markdown()
    lines = markdown.split('\n')[:30]
    for line in lines:
        print(f"  {line}")
    print("  ...")


async def demonstrate_usage_examples():
    """演示使用示例生成"""
    print("\n" + "=" * 60)
    print("演示 3: 使用示例生成")
    print("=" * 60)

    skill = ToolDesignSkill()

    print("\n🔧 生成文件搜索工具示例:")
    examples = skill.generate_usage_examples(FILE_SEARCH_TOOL, count=3)

    print(f"\n  生成了 {len(examples)} 个示例:")
    for i, example in enumerate(examples, 1):
        print(f"\n  示例 {i}: {example.title}")
        print(f"    描述: {example.description}")
        print(f"    参数:")
        for param_name, param_value in example.parameters.items():
            print(f"      - {param_name}: {param_value}")
        if example.expected_output:
            print(f"    预期输出: {example.expected_output}")
        if example.notes:
            print(f"    注意: {example.notes}")

    print("\n" + "-" * 40)
    print("\n🔧 生成计算器工具示例:")
    examples = skill.generate_usage_examples(CALCULATOR_TOOL, count=2)

    for i, example in enumerate(examples, 1):
        print(f"\n  示例 {i}: {example.title}")
        print(f"    参数: {example.parameters}")


async def demonstrate_parameter_validation():
    """演示参数验证"""
    print("\n" + "=" * 60)
    print("演示 4: 工具参数验证")
    print("=" * 60)

    skill = ToolDesignSkill()

    print("\n✅ 验证有效参数:")
    valid_params = {
        "operation": "add",
        "operands": [10, 20, 30],
        "precision": 2,
    }

    is_valid, error = skill.validate_tool_parameters(CALCULATOR_TOOL, valid_params)
    print(f"  参数: {valid_params}")
    print(f"  结果: {'有效' if is_valid else '无效'}")
    if error:
        print(f"  错误: {error}")

    print("\n" + "-" * 40)
    print("\n❌ 验证无效参数（缺少必填参数）:")
    invalid_params_1 = {
        "operation": "add",
        # 缺少 operands
    }

    is_valid, error = skill.validate_tool_parameters(CALCULATOR_TOOL, invalid_params_1)
    print(f"  参数: {invalid_params_1}")
    print(f"  结果: {'有效' if is_valid else '无效'}")
    print(f"  错误: {error}")

    print("\n" + "-" * 40)
    print("\n❌ 验证无效参数（枚举值错误）:")
    invalid_params_2 = {
        "operation": "power",  # 无效的运算类型
        "operands": [2, 3],
    }

    is_valid, error = skill.validate_tool_parameters(CALCULATOR_TOOL, invalid_params_2)
    print(f"  参数: {invalid_params_2}")
    print(f"  结果: {'有效' if is_valid else '无效'}")
    print(f"  错误: {error}")

    print("\n" + "-" * 40)
    print("\n❌ 验证无效参数（类型错误）:")
    invalid_params_3 = {
        "operation": "add",
        "operands": "10, 20",  # 应该是数组
    }

    is_valid, error = skill.validate_tool_parameters(CALCULATOR_TOOL, invalid_params_3)
    print(f"  参数: {invalid_params_3}")
    print(f"  结果: {'有效' if is_valid else '无效'}")
    print(f"  错误: {error}")


async def demonstrate_validation_scenarios():
    """演示各种验证场景"""
    print("\n" + "=" * 60)
    print("演示 5: 各种验证场景")
    print("=" * 60)

    skill = ToolDesignSkill()

    # 场景1: 缺少必填字段
    print("\n📋 场景 1: 缺少必填字段")
    tool_def = {
        "id": "incomplete_tool",
        "name": "incomplete",
        # 缺少 description
        "parameters": [],
    }
    report = skill.validate_tool_definition(tool_def)
    print(f"  错误数: {len(report.get_errors())}")
    for error in report.get_errors():
        print(f"    - {error.message}")

    # 场景2: 参数命名不规范
    print("\n📋 场景 2: 参数命名不规范")
    tool_def = {
        "id": "bad_params",
        "name": "bad_params",
        "description": "测试工具",
        "parameters": [
            {"name": "GoodParam", "type": "string", "description": "大写开头"},
            {"name": "param-with-dash", "type": "string", "description": "包含横线"},
            {"name": "123numeric", "type": "string", "description": "数字开头"},
        ],
    }
    report = skill.validate_tool_definition(tool_def)
    print(f"  警告数: {len(report.get_warnings())}")
    for warning in report.get_warnings():
        print(f"    - [{warning.field}] {warning.message}")

    # 场景3: 无效的类型
    print("\n📋 场景 3: 无效的类型")
    tool_def = {
        "id": "bad_types",
        "name": "bad_types",
        "description": "测试工具",
        "parameters": [
            {"name": "param1", "type": "float64", "description": "无效类型"},
            {"name": "param2", "type": "str", "description": "类型拼写错误"},
        ],
    }
    report = skill.validate_tool_definition(tool_def)
    print(f"  错误数: {len(report.get_errors())}")
    for error in report.get_errors():
        print(f"    - [{error.field}] {error.message}")

    # 场景4: 描述过短
    print("\n📋 场景 4: 描述过短")
    tool_def = {
        "id": "short_desc",
        "name": "short_desc",
        "description": "工具",
        "parameters": [
            {"name": "param1", "type": "string", "description": ""},
        ],
    }
    report = skill.validate_tool_definition(tool_def)
    print(f"  警告数: {len(report.get_warnings())}")
    for warning in report.get_warnings():
        print(f"    - [{warning.field}] {warning.message}")


async def demonstrate_skill_interface():
    """演示技能接口"""
    print("\n" + "=" * 60)
    print("演示 6: 技能接口使用")
    print("=" * 60)

    skill = ToolDesignSkill()

    print("\n🔌 技能元数据:")
    metadata = skill.metadata
    print(f"  - 名称: {metadata.name}")
    print(f"  - 描述: {metadata.description}")
    print(f"  - 类别: {metadata.category.value}")
    print(f"  - 版本: {metadata.version}")
    print(f"  - 作者: {metadata.author}")
    print(f"  - 标签: {metadata.tags}")
    print(f"  - 图标: {metadata.icon}")

    print("\n📡 使用 apply() 接口:")

    # 验证操作
    print("\n  操作: validate")
    result = await skill.apply({
        "operation": "validate",
        "tool_definition": CALCULATOR_TOOL,
    })
    print(f"    成功: {result['success']}")
    print(f"    有效: {result.get('is_valid', 'N/A')}")

    # 文档生成操作
    print("\n  操作: document")
    result = await skill.apply({
        "operation": "document",
        "tool_definition": CALCULATOR_TOOL,
    })
    print(f"    成功: {result['success']}")
    if result['success']:
        print(f"    文档名称: {result['documentation']['name']}")
        print(f"    参数数量: {len(result['documentation']['parameters_doc'])}")

    # 示例生成操作
    print("\n  操作: examples")
    result = await skill.apply({
        "operation": "examples",
        "tool_definition": CALCULATOR_TOOL,
    })
    print(f"    成功: {result['success']}")
    if result['success']:
        print(f"    示例数量: {len(result['examples'])}")

    # 参数验证操作
    print("\n  操作: validate_params")
    result = await skill.apply({
        "operation": "validate_params",
        "tool_definition": CALCULATOR_TOOL,
        "parameters": {
            "operation": "multiply",
            "operands": [5, 10],
        },
    })
    print(f"    成功: {result['success']}")
    print(f"    参数有效: {result.get('is_valid', 'N/A')}")


async def demonstrate_validation_history():
    """演示验证历史"""
    print("\n" + "=" * 60)
    print("演示 7: 验证历史")
    print("=" * 60)

    skill = ToolDesignSkill()

    # 执行多次验证
    print("\n📝 执行多次验证:")
    tools = [
        ("tool_a", {"id": "tool_a", "name": "tool_a", "description": "工具A", "parameters": []}),
        ("tool_b", {"id": "tool_b", "name": "tool_b", "description": "工具B", "parameters": []}),
        ("tool_c", {"id": "tool_c", "name": "tool_c", "description": "工具C", "parameters": []}),
    ]

    for tool_id, tool_def in tools:
        report = skill.validate_tool_definition(tool_def)
        print(f"  验证 {tool_id}: {'通过' if report.is_valid else '失败'}")

    # 查看验证历史
    print("\n📊 验证历史:")
    history = skill.get_validation_history()
    print(f"  总验证次数: {len(history)}")

    for i, report in enumerate(history, 1):
        print(f"\n  验证记录 {i}:")
        print(f"    - 工具ID: {report.tool_id}")
        print(f"    - 是否有效: {'是' if report.is_valid else '否'}")
        print(f"    - 时间: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    # 清空历史
    skill.clear_validation_history()
    print(f"\n🗑️ 清空历史后: {len(skill.get_validation_history())} 条记录")


async def demonstrate_complex_tool():
    """演示复杂工具定义"""
    print("\n" + "=" * 60)
    print("演示 8: 复杂工具定义")
    print("=" * 60)

    skill = ToolDesignSkill()

    # 定义一个复杂的API工具
    complex_tool = {
        "id": "weather_api",
        "name": "weather_api",
        "description": "获取指定城市的天气信息，支持当前天气、预报和历史数据查询。",
        "version": "2.1.0",
        "type": "api",
        "status": "active",
        "parameters": [
            {
                "name": "city",
                "type": "string",
                "description": "城市名称（中文或英文）",
                "required": True,
            },
            {
                "name": "data_type",
                "type": "string",
                "description": "数据类型",
                "required": True,
                "enum": ["current", "forecast", "history"],
            },
            {
                "name": "days",
                "type": "integer",
                "description": "预报天数（仅forecast类型有效）",
                "required": False,
                "default": 7,
            },
            {
                "name": "units",
                "type": "string",
                "description": "温度单位",
                "required": False,
                "enum": ["celsius", "fahrenheit"],
                "default": "celsius",
            },
            {
                "name": "include_details",
                "type": "boolean",
                "description": "是否包含详细天气信息（湿度、风速等）",
                "required": False,
                "default": True,
            },
            {
                "name": "language",
                "type": "string",
                "description": "返回数据的语言",
                "required": False,
                "enum": ["zh", "en", "ja", "ko"],
                "default": "zh",
            },
        ],
        "author": "Weather Service",
        "tags": ["weather", "api", "data"],
        "category": "weather",
        "icon": "🌤️",
        "timeout": 15,
    }

    print("\n🌍 验证复杂天气API工具:")
    report = skill.validate_tool_definition(complex_tool)
    print(f"  - 是否有效: {'是' if report.is_valid else '否'}")
    print(f"  - 参数数量: {len(complex_tool['parameters'])}")

    print("\n📝 生成文档:")
    doc = skill.generate_tool_documentation(complex_tool)
    print(f"  - 名称: {doc.name}")
    print(f"  - 参数文档数: {len(doc.parameters_doc)}")
    print(f"  - 最佳实践数: {len(doc.best_practices)}")

    print("\n🔧 生成使用示例:")
    examples = skill.generate_usage_examples(complex_tool, count=3)
    for i, example in enumerate(examples, 1):
        print(f"\n  示例 {i}: {example.title}")
        print(f"    参数:")
        for name, value in example.parameters.items():
            print(f"      - {name}: {value}")


async def demonstrate_best_practices():
    """演示工具设计最佳实践"""
    print("\n" + "=" * 60)
    print("演示 9: 工具设计最佳实践")
    print("=" * 60)

    print("\n📚 工具设计最佳实践:")

    practices = [
        {
            "title": "命名规范",
            "description": "工具名称应使用小写字母、数字和下划线",
            "example": "data_processor, file_search, api_client",
            "bad_example": "DataProcessor, file-search, APIClient",
        },
        {
            "title": "描述清晰",
            "description": "提供详细的工具描述，说明用途和功能",
            "example": "处理CSV文件，支持数据清洗、转换和统计分析",
            "bad_example": "处理文件",
        },
        {
            "title": "参数命名",
            "description": "参数名应简洁明了，使用小写字母和下划线",
            "example": "file_path, output_format, max_results",
            "bad_example": "FilePath, outputFormat, maxResults",
        },
        {
            "title": "必填vs可选",
            "description": "合理设置必填和可选参数，提供默认值",
            "example": "file_path (必填), output_format (可选, 默认csv)",
            "bad_example": "所有参数都必填，没有默认值",
        },
        {
            "title": "类型选择",
            "description": "使用正确的参数类型",
            "example": "string, integer, boolean, array, object",
            "bad_example": "使用自定义类型或不明确的类型",
        },
        {
            "title": "枚举值",
            "description": "对于有限选项的参数，使用enum限制可选值",
            "example": "operation: ['add', 'subtract', 'multiply', 'divide']",
            "bad_example": "operation: string (无限制)",
        },
        {
            "title": "超时设置",
            "description": "根据操作复杂度设置合理的超时时间",
            "example": "简单操作: 10s, API调用: 30s, 复杂处理: 60s+",
            "bad_example": "所有工具都使用默认30s",
        },
    ]

    for i, practice in enumerate(practices, 1):
        print(f"\n  {i}. {practice['title']}")
        print(f"     说明: {practice['description']}")
        print(f"     ✅ 正确: {practice['example']}")
        print(f"     ❌ 错误: {practice['bad_example']}")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DeepTutor 工具设计技能使用示例")
    print("=" * 60)
    print("\n本示例演示以下内容:")
    print("  1. 工具定义验证")
    print("  2. 工具文档生成")
    print("  3. 使用示例生成")
    print("  4. 工具参数验证")
    print("  5. 各种验证场景")
    print("  6. 技能接口使用")
    print("  7. 验证历史")
    print("  8. 复杂工具定义")
    print("  9. 工具设计最佳实践")
    print()

    try:
        # 运行所有演示
        await demonstrate_tool_validation()
        await demonstrate_documentation_generation()
        await demonstrate_usage_examples()
        await demonstrate_parameter_validation()
        await demonstrate_validation_scenarios()
        await demonstrate_skill_interface()
        await demonstrate_validation_history()
        await demonstrate_complex_tool()
        await demonstrate_best_practices()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
