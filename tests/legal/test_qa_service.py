"""
法律问答服务测试脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.legal.legal_qa import get_qa_service


def test_qa_service():
    """测试法律问答服务"""
    print("=" * 60)
    print("法律问答服务测试")
    print("=" * 60)
    
    # 获取服务实例
    service = get_qa_service()
    
    # 测试问题
    test_questions = [
        "朋友欠钱不还怎么办？",
        "离婚时财产怎么分割？",
        "老板拖欠工资怎么办？",
        "发生交通事故后如何处理？",
        "醉酒驾车会判什么罪？",
    ]
    
    print(f"\n语料库大小：{len(service.retriever.qa_pairs)} 个问答对")
    print(f"服务已初始化：{service.is_initialized}")
    
    # 测试每个问题
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"问题：{question}")
        print(f"{'='*60}")
        
        result = service.answer_question(question, top_k=3)
        
        print(f"分类：{result.category}")
        print(f"置信度：{result.confidence:.2%}")
        print(f"处理时间：{result.processing_time_ms:.2f}ms")
        print(f"\n答案:")
        for i, answer in enumerate(result.answers, 1):
            print(f"  {i}. {answer}")
    
    # 测试分类功能
    print(f"\n{'='*60}")
    print("分类功能测试")
    print(f"{'='*60}")
    
    categories = service.get_categories()
    print(f"\n共 {len(categories)} 个分类:")
    for cat_id, cat_name in categories.items():
        print(f"  {cat_id}: {cat_name}")
    
    # 测试批量分类
    print(f"\n{'='*60}")
    print("批量分类测试")
    print(f"{'='*60}")
    
    for question in test_questions[:3]:
        cat_id, confidence, cat_name = service.classifier.classify(question)
        print(f"问题：{question}")
        print(f"  -> 分类：{cat_name} (ID: {cat_id}, 置信度：{confidence:.2%})")
    
    print(f"\n{'='*60}")
    print("测试完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    test_qa_service()
