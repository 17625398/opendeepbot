#!/usr/bin/env python3
"""
ReRank Service 测试脚本
"""

import json
import sys
import time

import requests

# 配置
BASE_URL = "http://localhost:8000"  # 主服务地址
RERANK_URL = f"{BASE_URL}/api/rerank"


def test_health():
    """测试健康检查"""
    print("\n[1] 测试健康检查...")
    try:
        response = requests.get(f"{RERANK_URL}/health", timeout=5)
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def test_info():
    """测试模型信息"""
    print("\n[2] 测试模型信息...")
    try:
        response = requests.get(f"{RERANK_URL}/info", timeout=5)
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def test_rerank():
    """测试重排序功能"""
    print("\n[3] 测试重排序...")
    
    test_data = {
        "query": "什么是人工智能",
        "documents": [
            {"id": "doc1", "content": "人工智能是计算机科学的一个分支，致力于创造能够模拟人类智能的系统。"},
            {"id": "doc2", "content": "机器学习是人工智能的子集，通过数据训练模型来做出预测。"},
            {"id": "doc3", "content": "深度学习是机器学习的一种方法，使用神经网络处理复杂任务。"},
            {"id": "doc4", "content": "今天天气很好，适合出去散步。"},
            {"id": "doc5", "content": "Python 是一种流行的编程语言，广泛用于数据科学。"},
            {"id": "doc6", "content": "自然语言处理是人工智能的重要应用领域，用于理解和生成人类语言。"},
            {"id": "doc7", "content": "计算机视觉让机器能够看懂图像和视频内容。"},
            {"id": "doc8", "content": "强化学习通过与环境交互来学习最优策略。"}
        ],
        "top_k": 5,
        "threshold": 0.0
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{RERANK_URL}/rank",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        elapsed = (time.time() - start_time) * 1000
        
        print(f"  状态码: {response.status_code}")
        print(f"  耗时: {elapsed:.2f}ms")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n  查询: {result.get('query')}")
            print(f"  模型: {result.get('model')}")
            print(f"  算法: {result.get('algorithm')}")
            print(f"  处理时间: {result.get('processing_time_ms')}ms")
            print("\n  排序结果:")
            
            for i, doc in enumerate(result.get('results', []), 1):
                print(f"\n    {i}. [{doc.get('rank')}] {doc.get('id')}")
                print(f"       内容: {doc.get('content', '')[:60]}...")
                print(f"       相关度: {doc.get('relevance_score', 0):.4f}")
                scores = doc.get('scores', {})
                print(f"       分数详情 - 关键词: {scores.get('keyword', 0):.4f}, "
                      f"Jaccard: {scores.get('jaccard', 0):.4f}, "
                      f"Embedding: {scores.get('embedding', 0):.4f}")
            
            return True
        else:
            print(f"  ✗ 错误响应: {response.text}")
            return False
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def test_rerank_v1():
    """测试 OpenAI 兼容接口"""
    print("\n[4] 测试 OpenAI 兼容接口...")
    
    test_data = {
        "query": "机器学习",
        "documents": [
            "机器学习是人工智能的一个分支",
            "深度学习是机器学习的一种方法",
            "今天天气很好"
        ],
        "top_n": 2
    }
    
    try:
        response = requests.post(
            f"{RERANK_URL}/v1/rerank",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  返回结果数: {len(result.get('data', []))}")
            print(f"  模型: {result.get('model', 'unknown')}")
            print("\n  结果:")
            for item in result.get('data', []):
                print(f"    - Index: {item.get('index')}, Score: {item.get('relevance_score', 0):.4f}")
            return True
        else:
            print(f"  ✗ 错误响应: {response.text}")
            return False
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def test_config():
    """测试配置接口"""
    print("\n[5] 测试配置接口...")
    
    try:
        # 获取配置
        print("  获取当前配置...")
        response = requests.get(f"{RERANK_URL}/config", timeout=5)
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            config = response.json()
            print(f"  当前配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
        
        # 更新配置
        print("\n  更新配置...")
        new_config = {
            "algorithm": "keyword",
            "keyword_weight": 0.8,
            "jaccard_weight": 0.2,
            "embedding_weight": 0.0,
            "top_k": 10
        }
        
        response = requests.post(
            f"{RERANK_URL}/config",
            json=new_config,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"  响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        # 恢复默认配置
        print("\n  恢复默认配置...")
        default_config = {
            "algorithm": "hybrid",
            "keyword_weight": 0.4,
            "jaccard_weight": 0.4,
            "embedding_weight": 0.2,
            "top_k": 10
        }
        
        response = requests.post(
            f"{RERANK_URL}/config",
            json=default_config,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        return response.status_code == 200
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def test_scores():
    """测试仅获取分数"""
    print("\n[6] 测试获取分数...")
    
    test_data = {
        "query": "人工智能应用",
        "documents": [
            {"id": "doc1", "content": "人工智能在医疗领域的应用"},
            {"id": "doc2", "content": "人工智能在金融领域的应用"},
            {"id": "doc3", "content": "今天吃什么好呢"}
        ]
    }
    
    try:
        response = requests.post(
            f"{RERANK_URL}/scores",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("  分数列表:")
            for score in result.get('scores', []):
                print(f"    - {score.get('id')}: {score.get('relevance_score', 0):.4f}")
            return True
        else:
            print(f"  ✗ 错误响应: {response.text}")
            return False
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def main():
    print("="*60)
    print("ReRank Service 测试")
    print("="*60)
    print(f"服务器地址: {RERANK_URL}")
    
    # 运行测试
    tests = [
        ("健康检查", test_health),
        ("模型信息", test_info),
        ("重排序", test_rerank),
        ("OpenAI 兼容接口", test_rerank_v1),
        ("配置接口", test_config),
        ("获取分数", test_scores),
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
