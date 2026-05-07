"""
法律 Worker Agent 测试脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.services.agent.legal_worker import get_legal_worker


async def test_legal_worker():
    """测试法律 Worker 功能"""
    print("=" * 60)
    print("法律 Worker Agent 功能测试")
    print("=" * 60)
    
    # 1. 创建 Worker
    print("\n[1/5] 创建法律 Worker...")
    worker = await get_legal_worker()
    print(f"✓ Worker 已创建：{worker.name} (ID: {worker.worker_id})")
    print(f"  技能：{worker.skills}")
    
    # 2. 测试法律问答
    print("\n[2/5] 测试法律问答...")
    result = await worker.execute_task(
        task_description="回答法律咨询问题",
        task_type="legal_qa",
        question="朋友欠钱不还怎么办？",
        top_k=3,
    )
    
    print(f"  任务类型：{result.get('task_type')}")
    print(f"  成功：{result.get('success')}")
    print(f"  分类：{result.get('category')}")
    print(f"  置信度：{result.get('confidence', 0):.2%}")
    print(f"  答案数量：{len(result.get('answers', []))}")
    if result.get('answers'):
        print(f"  最佳答案：{result['answers'][0][:50]}...")
    
    # 3. 测试罪名预测
    print("\n[3/5] 测试罪名预测...")
    result = await worker.execute_task(
        task_description="预测涉嫌罪名",
        task_type="crime_prediction",
        fact_description="张三盗窃他人财物 5000 元",
        top_k=5,
    )
    
    print(f"  任务类型：{result.get('task_type')}")
    print(f"  成功：{result.get('success')}")
    print(f"  预测罪名：{result.get('predicted_crime')}")
    print(f"  置信度：{result.get('confidence', 0):.2%}")
    if result.get('top_crimes'):
        print(f"  Top 3 罪名：{[c.get('crime_name') for c in result['top_crimes'][:3]]}")
    
    # 4. 测试量刑分析
    print("\n[4/5] 测试量刑分析...")
    result = await worker.execute_task(
        task_description="分析量刑建议",
        task_type="sentencing_analysis",
        crime_id=1,
        circumstances=["自首", "赔偿损失"],
    )
    
    print(f"  任务类型：{result.get('task_type')}")
    print(f"  成功：{result.get('success')}")
    print(f"  量刑建议：{result.get('recommended_sentence')}")
    print(f"  置信度：{result.get('confidence', 0):.2%}")
    
    # 5. 获取统计信息
    print("\n[5/5] 获取 Worker 统计信息...")
    stats = worker.get_stats()
    
    print(f"  Worker 名称：{stats.get('name')}")
    print(f"  状态：{stats.get('status')}")
    print(f"  技能列表：{stats.get('skills')}")
    print(f"  总任务数：{stats.get('stats', {}).get('total_tasks')}")
    print(f"  成功任务数：{stats.get('stats', {}).get('successful_tasks')}")
    print(f"  失败任务数：{stats.get('stats', {}).get('failed_tasks')}")
    print(f"  平均置信度：{stats.get('stats', {}).get('avg_confidence', 0):.2%}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


async def test_skill_handlers():
    """测试技能处理器"""
    print("\n" + "=" * 60)
    print("法律技能处理器测试")
    print("=" * 60)
    
    from src.services.agent.legal_skills import execute_legal_skill, get_legal_skill_registry
    
    # 获取注册表
    registry = get_legal_skill_registry()
    skills = registry.get_all_skills()
    
    print(f"\n已注册技能：{skills}")
    
    # 测试罪名预测技能
    print("\n[1/2] 测试罪名预测技能处理器...")
    result = await execute_legal_skill(
        skill_type="crime_prediction",
        task_data={
            "fact_description": "张三盗窃他人财物 5000 元",
            "top_k": 5,
        },
    )
    
    print(f"  成功：{result.get('success')}")
    print(f"  技能类型：{result.get('skill_type')}")
    print(f"  预测罪名：{result.get('predicted_crime')}")
    print(f"  置信度：{result.get('confidence', 0):.2%}")
    
    # 测试法律问答技能
    print("\n[2/2] 测试法律问答技能处理器...")
    result = await execute_legal_skill(
        skill_type="legal_qa",
        task_data={
            "question": "离婚时财产怎么分割？",
            "top_k": 3,
        },
    )
    
    print(f"  成功：{result.get('success')}")
    print(f"  技能类型：{result.get('skill_type')}")
    print(f"  分类：{result.get('category')}")
    print(f"  置信度：{result.get('confidence', 0):.2%}")
    print(f"  答案数量：{len(result.get('answers', []))}")
    
    print("\n" + "=" * 60)
    print("技能处理器测试完成！")
    print("=" * 60)


async def main():
    """主测试函数"""
    try:
        # 测试 Worker
        await test_legal_worker()
        
        # 测试技能处理器
        await test_skill_handlers()
        
        print("\n✅ 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
