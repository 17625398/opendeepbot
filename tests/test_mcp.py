#!/usr/bin/env python3
"""
MCP 集成测试脚本
"""

import json
import sys

import requests

# 配置
BASE_URL = "http://localhost:8000"
MCP_URL = f"{BASE_URL}/api/v1/mcp"


def test_mcp_status():
    """测试 MCP 状态"""
    print("\n[1] 测试 MCP 状态...")
    try:
        response = requests.get(f"{MCP_URL}/status", timeout=5)
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def test_mcp_config():
    """测试 MCP 配置"""
    print("\n[2] 测试 MCP 配置...")
    try:
        response = requests.get(f"{MCP_URL}/config", timeout=5)
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def test_list_tools():
    """测试列出工具"""
    print("\n[3] 测试列出 MCP 工具...")
    try:
        response = requests.get(f"{MCP_URL}/tools", timeout=5)
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  可用工具数: {len(data)}")
            for tool in data[:3]:  # 只显示前3个
                print(f"    - {tool['name']}: {tool['description'][:50]}...")
            return True
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def test_tool_categories():
    """测试工具分类"""
    print("\n[4] 测试工具分类...")
    try:
        response = requests.get(f"{MCP_URL}/tools/categories", timeout=5)
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  分类: {list(data.keys())}")
            return True
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def test_call_tool():
    """测试调用工具"""
    print("\n[5] 测试调用 MCP 工具...")
    try:
        response = requests.post(
            f"{MCP_URL}/tools/call",
            json={
                "tool_name": "get_system_info",
                "parameters": {}
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  成功: {result.get('success')}")
            print(f"  数据: {json.dumps(result.get('data'), indent=2, ensure_ascii=False)[:200]}...")
            return result.get('success', False)
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def test_server_status():
    """测试 MCP Server 状态"""
    print("\n[6] 测试 MCP Server 状态...")
    try:
        response = requests.get(f"{MCP_URL}/server/status", timeout=5)
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def main():
    print("="*60)
    print("MCP 集成测试")
    print("="*60)
    print(f"服务器地址: {MCP_URL}")
    
    # 运行测试
    tests = [
        ("MCP 状态", test_mcp_status),
        ("MCP 配置", test_mcp_config),
        ("列出工具", test_list_tools),
        ("工具分类", test_tool_categories),
        ("调用工具", test_call_tool),
        ("Server 状态", test_server_status),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} 测试失败: {e}")
            results.append((name, False))
    
    # 打印总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {status}: {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n✓ 所有测试通过！")
        return 0
    else:
        print("\n✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
