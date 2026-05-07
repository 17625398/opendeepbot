"""
法律问答 API 测试脚本

测试所有法律问答相关的 API 端点
"""

import requests
import json

# API 基础 URL
BASE_URL = "http://localhost:8000/api/v1"


def test_ask_question():
    """测试问答接口"""
    print("=" * 60)
    print("测试：法律咨询问答接口")
    print("=" * 60)
    
    url = f"{BASE_URL}/legal/qa/ask"
    
    test_data = {
        "question": "朋友欠钱不还怎么办？",
        "top_k": 3,
        "auto_classify": True
    }
    
    response = requests.post(url, json=test_data)
    
    print(f"状态码：{response.status_code}")
    print(f"响应：{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    
    return response.status_code == 200


def test_get_categories():
    """测试获取分类接口"""
    print("=" * 60)
    print("测试：获取问题分类列表")
    print("=" * 60)
    
    url = f"{BASE_URL}/legal/qa/categories"
    
    response = requests.get(url)
    
    print(f"状态码：{response.status_code}")
    print(f"响应：{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    
    return response.status_code == 200


def test_get_stats():
    """测试统计接口"""
    print("=" * 60)
    print("测试：获取问答库统计信息")
    print("=" * 60)
    
    url = f"{BASE_URL}/legal/qa/stats"
    
    response = requests.get(url)
    
    print(f"状态码：{response.status_code}")
    print(f"响应：{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    
    return response.status_code == 200


def test_search():
    """测试搜索接口"""
    print("=" * 60)
    print("测试：搜索相似问题")
    print("=" * 60)
    
    url = f"{BASE_URL}/legal/qa/search"
    params = {
        "question": "离婚财产分割",
        "top_k": 3
    }
    
    response = requests.get(url, params=params)
    
    print(f"状态码：{response.status_code}")
    print(f"响应：{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    
    return response.status_code == 200


def test_classify():
    """测试分类接口"""
    print("=" * 60)
    print("测试：问题分类接口")
    print("=" * 60)
    
    url = f"{BASE_URL}/legal/qa/classify"
    
    test_data = {
        "question": "朋友欠钱不还怎么办？"
    }
    
    response = requests.post(url, json=test_data)
    
    print(f"状态码：{response.status_code}")
    print(f"响应：{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    
    return response.status_code == 200


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("法律问答 API 测试套件")
    print("=" * 60 + "\n")
    
    tests = [
        ("获取分类列表", test_get_categories),
        ("获取统计信息", test_get_stats),
        ("问题分类", test_classify),
        ("搜索相似问题", test_search),
        ("法律咨询问答", test_ask_question),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ 测试失败：{e}\n")
            results.append((test_name, False))
    
    # 汇总结果
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {test_name}")
    
    print(f"\n总计：{passed}/{total} 测试通过")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    import sys
    
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ 无法连接到 API 服务器，请确保服务已启动：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行失败：{e}")
        sys.exit(1)
