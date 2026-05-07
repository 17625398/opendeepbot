#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeerFlow 基础使用示例

本示例展示 DeerFlow 的基本功能：
1. 初始化 DeerFlow
2. 在沙箱中执行代码
3. 处理执行结果
4. 错误处理

运行前请确保：
1. 已安装 DeerFlow: pip install deerflow
2. 已配置 .env.deerflow 文件
3. Docker 服务正在运行
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv

env_path = project_root / ".env.deerflow"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ 已加载环境变量: {env_path}")
else:
    print(f"⚠ 未找到环境变量文件: {env_path}")
    print("  将使用默认配置")


def example_1_basic_execution():
    """示例 1: 基础代码执行"""
    print("\n" + "=" * 60)
    print("示例 1: 基础代码执行")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        # 初始化 DeerFlow
        print("\n[1] 初始化 DeerFlow...")
        flow = DeerFlow()
        print("✓ DeerFlow 初始化成功")

        # 执行简单代码
        print("\n[2] 执行 Python 代码...")
        code = """
import math

# 计算圆的面积
def circle_area(radius):
    return math.pi * radius ** 2

radius = 5
area = circle_area(radius)
print(f"半径为 {radius} 的圆面积: {area:.2f}")
print(f"数学常数 π: {math.pi:.10f}")
"""

        result = flow.execute(code, language="python")

        # 显示结果
        print("\n[3] 执行结果:")
        print(f"  状态: {result.status}")
        print(f"  退出码: {result.exit_code}")
        print(f"  执行时间: {result.execution_time:.2f} 秒")
        print(f"\n  输出:")
        print("  " + "-" * 50)
        for line in result.output.strip().split("\n"):
            print(f"  {line}")
        print("  " + "-" * 50)

        if result.error:
            print(f"\n  错误输出:\n  {result.error}")

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def example_2_multiple_languages():
    """示例 2: 多语言支持"""
    print("\n" + "=" * 60)
    print("示例 2: 多语言支持")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        flow = DeerFlow()

        # JavaScript 代码示例
        js_code = """
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(n => n * 2);
const sum = numbers.reduce((a, b) => a + b, 0);

console.log('原始数组:', numbers);
console.log('翻倍后:', doubled);
console.log('总和:', sum);
console.log('当前时间:', new Date().toISOString());
"""

        print("\n[1] 执行 JavaScript 代码...")
        result = flow.execute(js_code, language="javascript")

        print(f"\n  状态: {result.status}")
        print(f"  输出:")
        print("  " + "-" * 50)
        for line in result.output.strip().split("\n"):
            print(f"  {line}")
        print("  " + "-" * 50)

        # Bash 代码示例
        bash_code = """
echo "系统信息:"
echo "  当前目录: $(pwd)"
echo "  当前用户: $(whoami)"
echo "  主机名: $(hostname)"
echo "  时间: $(date)"
echo ""
echo "环境变量:"
env | grep -E '^(PATH|HOME|USER)=' || true
"""

        print("\n[2] 执行 Bash 脚本...")
        result = flow.execute(bash_code, language="bash")

        print(f"\n  状态: {result.status}")
        print(f"  输出:")
        print("  " + "-" * 50)
        for line in result.output.strip().split("\n"):
            print(f"  {line}")
        print("  " + "-" * 50)

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def example_3_data_processing():
    """示例 3: 数据处理任务"""
    print("\n" + "=" * 60)
    print("示例 3: 数据处理任务")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        flow = DeerFlow()

        # 数据处理代码
        code = """
import json
import statistics

# 模拟销售数据
sales_data = [
    {"product": "A", "quantity": 100, "price": 10.5},
    {"product": "B", "quantity": 150, "price": 20.0},
    {"product": "C", "quantity": 80, "price": 15.75},
    {"product": "D", "quantity": 200, "price": 5.5},
    {"product": "E", "quantity": 120, "price": 30.0},
]

# 计算每个产品的销售额
for item in sales_data:
    item['revenue'] = item['quantity'] * item['price']

# 统计分析
quantities = [item['quantity'] for item in sales_data]
prices = [item['price'] for item in sales_data]
revenues = [item['revenue'] for item in sales_data]

print("销售数据分析:")
print("=" * 50)
print(f"{'产品':<10} {'数量':<10} {'单价':<10} {'销售额':<10}")
print("-" * 50)

for item in sales_data:
    print(f"{item['product']:<10} {item['quantity']:<10} ${item['price']:<9.2f} ${item['revenue']:<9.2f}")

print("-" * 50)
print(f"{'总计':<10} {sum(quantities):<10} {'':<10} ${sum(revenues):<9.2f}")

print("\n统计信息:")
print(f"  平均数量: {statistics.mean(quantities):.2f}")
print(f"  平均单价: ${statistics.mean(prices):.2f}")
print(f"  最高销售额: ${max(revenues):.2f}")
print(f"  最低销售额: ${min(revenues):.2f}")

# 输出 JSON 格式
print("\nJSON 格式输出:")
print(json.dumps(sales_data, indent=2, ensure_ascii=False))
"""

        print("\n[1] 执行数据处理...")
        result = flow.execute(code, language="python")

        print(f"\n  状态: {result.status}")
        print(f"  输出:")
        print("  " + "-" * 50)
        for line in result.output.strip().split("\n"):
            print(f"  {line}")
        print("  " + "-" * 50)

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def example_4_error_handling():
    """示例 4: 错误处理"""
    print("\n" + "=" * 60)
    print("示例 4: 错误处理")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        flow = DeerFlow()

        # 故意包含错误的代码
        print("\n[1] 执行包含错误的代码...")
        bad_code = """
print("开始执行...")

# 除以零错误
x = 10 / 0

print("这行不会执行")
"""

        result = flow.execute(bad_code, language="python")

        print(f"\n  状态: {result.status}")
        print(f"  退出码: {result.exit_code}")

        if result.status == "error":
            print("\n  ✓ 正确捕获到错误")
            print(f"\n  错误输出:")
            print("  " + "-" * 50)
            # 只显示前几行错误
            error_lines = result.error.strip().split("\n")[:5]
            for line in error_lines:
                print(f"  {line}")
            print("  " + "-" * 50)

        # 超时示例
        print("\n[2] 测试超时处理...")
        slow_code = """
import time
print("开始长时间运行...")
time.sleep(10)
print("完成")
"""

        print("  执行会超时的代码 (超时时间: 2 秒)...")
        result = flow.execute(slow_code, language="python", timeout=2)

        print(f"\n  状态: {result.status}")
        if result.status == "timeout":
            print("  ✓ 正确触发超时")

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def example_5_custom_config():
    """示例 5: 自定义沙箱配置"""
    print("\n" + "=" * 60)
    print("示例 5: 自定义沙箱配置")
    print("=" * 60)

    try:
        from deerflow import DeerFlow

        # 使用自定义配置
        print("\n[1] 使用自定义沙箱配置...")

        custom_config = {
            "sandbox": {
                "memory_limit": "1g",
                "cpu_limit": 2.0,
                "timeout": 60,
                "network_enabled": True,
            }
        }

        flow = DeerFlow(config=custom_config)
        print("✓ 使用自定义配置初始化成功")

        # 执行需要更多资源的代码
        code = """
import sys

print("自定义配置测试:")
print(f"Python 版本: {sys.version}")
print(f"平台: {sys.platform}")

# 内存测试
large_list = list(range(1000000))
print(f"创建大列表，长度: {len(large_list)}")
print(f"列表内存占用: ~{sys.getsizeof(large_list) / 1024 / 1024:.2f} MB")

print("\n✓ 自定义配置运行成功")
"""

        result = flow.execute(
            code,
            language="python",
            sandbox_config={
                "memory_limit": "1g",
                "timeout": 30,
            },
        )

        print(f"\n  状态: {result.status}")
        print(f"  输出:")
        print("  " + "-" * 50)
        for line in result.output.strip().split("\n"):
            print(f"  {line}")
        print("  " + "-" * 50)

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DeerFlow 基础使用示例")
    print("=" * 60)

    # 检查 DeerFlow 是否可用
    try:
        from deerflow import DeerFlow

        print("\n✓ DeerFlow 包已安装")
    except ImportError:
        print("\n✗ DeerFlow 包未安装")
        print("  请运行: pip install deerflow")
        return 1

    # 运行所有示例
    examples = [
        ("基础代码执行", example_1_basic_execution),
        ("多语言支持", example_2_multiple_languages),
        ("数据处理任务", example_3_data_processing),
        ("错误处理", example_4_error_handling),
        ("自定义配置", example_5_custom_config),
    ]

    results = []
    for name, func in examples:
        try:
            success = func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ 示例 '{name}' 失败: {e}")
            results.append((name, False))

    # 显示总结
    print("\n" + "=" * 60)
    print("示例运行总结")
    print("=" * 60)

    for name, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"  {name:<20} {status}")

    success_count = sum(1 for _, s in results if s)
    total_count = len(results)

    print(f"\n总计: {success_count}/{total_count} 个示例成功")

    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
