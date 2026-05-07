"""
Web Access Skill - 站点经验示例

本示例展示如何使用 Web Access Skill 的站点经验学习功能：
- 站点经验记录
- 智能方法推荐
- 成功率统计
- 经验数据管理

运行前请确保：
1. 已配置 Web Access Skill
2. 已安装依赖: pip install requests aiohttp
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# 尝试导入 WebAccessSkill
try:
    from src.skills.web_access import WebAccessSkill
    from src.skills.web_access.experience import get_experience_manager
except ImportError:
    print("警告: 无法导入 WebAccessSkill，使用模拟实现")
    
    class MockExperienceManager:
        """模拟经验管理器"""
        
        def __init__(self):
            self.experiences = {}
        
        def get_recommended_method(self, url: str) -> str:
            """获取推荐方法"""
            domain = url.split('/')[2] if '//' in url else url
            exp = self.experiences.get(domain)
            if exp:
                # 根据成功率推荐
                total = exp.get('success', 0) + exp.get('failure', 0)
                if total > 0:
                    success_rate = exp.get('success', 0) / total
                    if success_rate > 0.8:
                        return exp.get('best_method', 'fetch')
            return 'fetch'  # 默认使用 fetch
        
        def record_success(self, url: str, method: str):
            """记录成功"""
            domain = url.split('/')[2] if '//' in url else url
            if domain not in self.experiences:
                self.experiences[domain] = {
                    'domain': domain,
                    'success': 0,
                    'failure': 0,
                    'best_method': method,
                    'methods': {}
                }
            self.experiences[domain]['success'] += 1
            self.experiences[domain]['methods'][method] = \
                self.experiences[domain]['methods'].get(method, 0) + 1
        
        def record_failure(self, url: str, error: str, method: str):
            """记录失败"""
            domain = url.split('/')[2] if '//' in url else url
            if domain not in self.experiences:
                self.experiences[domain] = {
                    'domain': domain,
                    'success': 0,
                    'failure': 0,
                    'best_method': method,
                    'methods': {}
                }
            self.experiences[domain]['failure'] += 1
        
        def get_experience_stats(self) -> Dict[str, Any]:
            """获取统计信息"""
            total_sites = len(self.experiences)
            total_success = sum(e.get('success', 0) for e in self.experiences.values())
            total_failure = sum(e.get('failure', 0) for e in self.experiences.values())
            total = total_success + total_failure
            
            return {
                'total_sites': total_sites,
                'total_attempts': total,
                'total_success': total_success,
                'total_failure': total_failure,
                'success_rate': total_success / total if total > 0 else 0,
                'sites': list(self.experiences.keys())
            }
        
        def get_site_experience(self, domain: str) -> Dict[str, Any]:
            """获取特定站点经验"""
            return self.experiences.get(domain, {})
    
    class MockWebAccessSkill:
        def __init__(self):
            self.name = "WebAccessSkill (Mock)"
            self._experience_manager = MockExperienceManager()
        
        async def execute(self, **kwargs):
            action = kwargs.get("action")
            
            if action == "fetch":
                url = kwargs.get("url", '')
                # 模拟记录经验
                self._experience_manager.record_success(url, 'fetch')
                
                return MockResult({
                    "success": True,
                    "data": {
                        "url": url,
                        "title": "Mock Page",
                        "content": "Mock content...",
                        "method": "fetch"
                    }
                })
            
            return MockResult({"success": False, "error": "Unknown action"})
        
        def get_stats(self):
            return {
                "experiences": self._experience_manager.get_experience_stats()
            }
        
        @property
        def experience_manager(self):
            return self._experience_manager
    
    class MockResult:
        def __init__(self, data):
            self.success = data.get("success", False)
            self.data = data.get("data")
            self.error = data.get("error")
            self.execution_time = 0.5
    
    WebAccessSkill = MockWebAccessSkill
    get_experience_manager = MockExperienceManager


@dataclass
class SiteExperience:
    """站点经验数据类"""
    domain: str
    success_count: int = 0
    failure_count: int = 0
    best_method: str = "fetch"
    last_access: str = ""
    notes: str = ""
    
    @property
    def total_attempts(self) -> int:
        return self.success_count + self.failure_count
    
    @property
    def success_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return self.success_count / self.total_attempts
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "total_attempts": self.total_attempts,
            "success_rate": f"{self.success_rate:.2%}"
        }


class ExperienceExamples:
    """站点经验示例类"""
    
    def __init__(self):
        self.skill = WebAccessSkill()
        self.experience_manager = getattr(self.skill, 'experience_manager', None)
        if not self.experience_manager:
            self.experience_manager = get_experience_manager()
    
    async def example_1_basic_experience_recording(self):
        """
        示例 1: 基础经验记录
        
        展示如何记录站点的访问经验
        """
        print("\n" + "="*60)
        print("示例 1: 基础经验记录")
        print("="*60)
        
        test_urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.org/article",
            "https://test-site.com/docs",
        ]
        
        print(f"\n🌐 访问 {len(test_urls)} 个 URL 并记录经验:")
        
        for url in test_urls:
            print(f"\n   访问: {url}")
            
            # 执行获取
            result = await self.skill.execute(
                action="fetch",
                url=url,
                extract_content=True
            )
            
            if result.success:
                print(f"   ✅ 成功 - 方法: {result.data.get('method', 'unknown')}")
                # 经验会自动记录
            else:
                print(f"   ❌ 失败 - 错误: {result.error}")
                # 失败也会被记录
        
        print("\n📊 经验记录完成")
    
    async def example_2_smart_method_recommendation(self):
        """
        示例 2: 智能方法推荐
        
        展示如何根据经验获取推荐访问方法
        """
        print("\n" + "="*60)
        print("示例 2: 智能方法推荐")
        print("="*60)
        
        # 先积累一些经验
        print("\n📚 积累站点经验...")
        
        sites = [
            ("https://example.com", "fetch"),
            ("https://example.com", "fetch"),
            ("https://example.com", "fetch"),
            ("https://complex-site.com", "browser"),
            ("https://complex-site.com", "browser"),
        ]
        
        for url, method in sites:
            if method == "fetch":
                self.experience_manager.record_success(url, method)
            else:
                # 模拟浏览器访问成功
                self.experience_manager.record_success(url, method)
        
        # 测试推荐
        print("\n🔍 测试智能推荐:")
        
        test_urls = [
            "https://example.com/new-page",
            "https://complex-site.com/page",
            "https://unknown-site.com/page",
        ]
        
        for url in test_urls:
            recommended = self.experience_manager.get_recommended_method(url)
            domain = url.split('/')[2]
            
            print(f"\n   URL: {url}")
            print(f"   域名: {domain}")
            print(f"   推荐方法: {recommended}")
            
            # 获取站点经验详情
            exp = self.experience_manager.get_site_experience(domain)
            if exp:
                success = exp.get('success', 0)
                failure = exp.get('failure', 0)
                total = success + failure
                rate = success / total if total > 0 else 0
                print(f"   历史成功率: {rate:.1%} ({success}/{total})")
            else:
                print(f"   历史成功率: 无记录")
    
    async def example_3_success_rate_analysis(self):
        """
        示例 3: 成功率分析
        
        展示如何分析不同站点的访问成功率
        """
        print("\n" + "="*60)
        print("示例 3: 成功率分析")
        print("="*60)
        
        # 模拟不同成功率的数据
        print("\n📊 模拟不同站点的访问数据...")
        
        site_data = [
            ("high-success.com", 9, 1),    # 90% 成功率
            ("medium-success.com", 6, 4),  # 60% 成功率
            ("low-success.com", 2, 8),     # 20% 成功率
            ("perfect-site.com", 10, 0),   # 100% 成功率
        ]
        
        for domain, success, failure in site_data:
            for _ in range(success):
                self.experience_manager.record_success(f"https://{domain}", "fetch")
            for _ in range(failure):
                self.experience_manager.record_failure(f"https://{domain}", "Timeout", "fetch")
        
        # 获取统计
        stats = self.experience_manager.get_experience_stats()
        
        print(f"\n📈 整体统计:")
        print(f"   - 总站点数: {stats.get('total_sites', 0)}")
        print(f"   - 总尝试: {stats.get('total_attempts', 0)}")
        print(f"   - 总成功: {stats.get('total_success', 0)}")
        print(f"   - 总失败: {stats.get('total_failure', 0)}")
        print(f"   - 整体成功率: {stats.get('success_rate', 0):.1%}")
        
        # 站点成功率排名
        print(f"\n🏆 站点成功率排名:")
        
        sites = stats.get('sites', [])
        site_stats = []
        
        for domain in sites:
            exp = self.experience_manager.get_site_experience(domain)
            if exp:
                success = exp.get('success', 0)
                failure = exp.get('failure', 0)
                total = success + failure
                rate = success / total if total > 0 else 0
                site_stats.append((domain, rate, total))
        
        # 按成功率排序
        site_stats.sort(key=lambda x: x[1], reverse=True)
        
        for i, (domain, rate, total) in enumerate(site_stats, 1):
            bar = "█" * int(rate * 20)
            print(f"   {i}. {domain:20} {bar:20} {rate:>6.1%} ({total}次)")
    
    async def example_4_method_effectiveness_comparison(self):
        """
        示例 4: 方法效果对比
        
        展示不同访问方法的效果对比
        """
        print("\n" + "="*60)
        print("示例 4: 方法效果对比")
        print("="*60)
        
        print("\n🔬 对比不同方法的效果...")
        
        # 模拟同一站点不同方法的效果
        methods = ["fetch", "browser"]
        
        for method in methods:
            print(f"\n   方法: {method}")
            
            # 模拟不同成功率
            if method == "fetch":
                success, failure = 7, 3  # 70% 成功率
            else:
                success, failure = 9, 1  # 90% 成功率
            
            for _ in range(success):
                self.experience_manager.record_success("https://test-site.com", method)
            for _ in range(failure):
                self.experience_manager.record_failure("https://test-site.com", "Error", method)
            
            total = success + failure
            rate = success / total
            print(f"   成功率: {rate:.1%} ({success}/{total})")
        
        # 获取推荐
        recommended = self.experience_manager.get_recommended_method("https://test-site.com")
        print(f"\n💡 推荐方法: {recommended}")
        print("   (基于历史成功率)")
    
    async def example_5_experience_persistence(self):
        """
        示例 5: 经验数据持久化
        
        展示如何保存和加载经验数据
        """
        print("\n" + "="*60)
        print("示例 5: 经验数据持久化")
        print("="*60)
        
        # 添加一些经验数据
        print("\n💾 添加经验数据...")
        
        test_data = [
            ("https://site-a.com", True, "fetch"),
            ("https://site-a.com", True, "fetch"),
            ("https://site-b.com", False, "fetch"),
            ("https://site-b.com", True, "browser"),
        ]
        
        for url, success, method in test_data:
            if success:
                self.experience_manager.record_success(url, method)
            else:
                self.experience_manager.record_failure(url, "Error", method)
        
        print(f"   已添加 {len(test_data)} 条经验记录")
        
        # 获取当前统计
        stats = self.experience_manager.get_experience_stats()
        print(f"\n📊 当前经验统计:")
        print(f"   - 站点数: {stats.get('total_sites', 0)}")
        print(f"   - 记录数: {stats.get('total_attempts', 0)}")
        
        # 模拟保存（实际实现会保存到文件）
        print("\n💾 保存经验数据...")
        save_data = {
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
            "sites": {
                domain: self.experience_manager.get_site_experience(domain)
                for domain in stats.get('sites', [])
            }
        }
        
        # 显示保存的数据结构
        print(f"   数据结构:")
        print(f"   - 时间戳: {save_data['timestamp']}")
        print(f"   - 站点数: {len(save_data['sites'])}")
        
        # 模拟导出为 JSON
        json_str = json.dumps(save_data, indent=2, default=str)
        print(f"\n📄 导出数据大小: {len(json_str)} 字符")
        
        print("\n✅ 经验数据持久化演示完成")
        print("   实际使用时，经验会自动保存到配置目录")
    
    async def example_6_adaptive_learning(self):
        """
        示例 6: 自适应学习
        
        展示系统如何根据经验自适应调整
        """
        print("\n" + "="*60)
        print("示例 6: 自适应学习")
        print("="*60)
        
        print("\n🧠 自适应学习演示:")
        print("-" * 40)
        
        target_site = "https://adaptive-test.com"
        
        # 阶段 1: 初始尝试
        print("\n阶段 1: 初始尝试 (使用默认方法)")
        print("   方法: fetch")
        
        # 模拟失败
        for _ in range(3):
            self.experience_manager.record_failure(target_site, "Timeout", "fetch")
        
        recommended = self.experience_manager.get_recommended_method(target_site)
        print(f"   推荐方法: {recommended}")
        print(f"   (fetch 失败较多，系统可能推荐其他方法)")
        
        # 阶段 2: 尝试替代方法
        print("\n阶段 2: 尝试替代方法")
        print("   方法: browser")
        
        # 模拟成功
        for _ in range(5):
            self.experience_manager.record_success(target_site, "browser")
        
        recommended = self.experience_manager.get_recommended_method(target_site)
        print(f"   推荐方法: {recommended}")
        print(f"   (browser 成功率高，系统推荐使用)")
        
        # 阶段 3: 稳定使用
        print("\n阶段 3: 稳定使用推荐方法")
        
        for _ in range(10):
            self.experience_manager.record_success(target_site, recommended)
        
        # 最终统计
        exp = self.experience_manager.get_site_experience("adaptive-test.com")
        if exp:
            success = exp.get('success', 0)
            failure = exp.get('failure', 0)
            total = success + failure
            rate = success / total if total > 0 else 0
            
            print(f"\n📊 最终统计:")
            print(f"   - 总尝试: {total}")
            print(f"   - 成功: {success}")
            print(f"   - 失败: {failure}")
            print(f"   - 成功率: {rate:.1%}")
            print(f"   - 推荐方法: {exp.get('best_method', 'unknown')}")
        
        print("\n✅ 自适应学习演示完成")
        print("   系统通过试错学习，自动优化访问策略")
    
    def print_experience_summary(self):
        """打印经验数据摘要"""
        print("\n" + "="*60)
        print("站点经验数据摘要")
        print("="*60)
        
        stats = self.experience_manager.get_experience_stats()
        
        print(f"\n📊 整体统计:")
        print(f"   - 已记录站点: {stats.get('total_sites', 0)}")
        print(f"   - 总访问次数: {stats.get('total_attempts', 0)}")
        print(f"   - 成功次数: {stats.get('total_success', 0)}")
        print(f"   - 失败次数: {stats.get('total_failure', 0)}")
        print(f"   - 整体成功率: {stats.get('success_rate', 0):.1%}")
        
        sites = stats.get('sites', [])
        if sites:
            print(f"\n🌐 已记录站点:")
            for domain in sites[:10]:  # 显示前 10 个
                exp = self.experience_manager.get_site_experience(domain)
                if exp:
                    success = exp.get('success', 0)
                    failure = exp.get('failure', 0)
                    total = success + failure
                    rate = success / total if total > 0 else 0
                    method = exp.get('best_method', 'unknown')
                    print(f"   - {domain:30} {rate:>6.1%} ({method})")
            
            if len(sites) > 10:
                print(f"   ... 还有 {len(sites) - 10} 个站点")
        
        print("\n💡 经验数据用途:")
        print("   1. 智能推荐最佳访问方法")
        print("   2. 预测访问成功率")
        print("   3. 自动选择最优策略")
        print("   4. 避免重复失败")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("Web Access Skill - 站点经验示例")
    print("="*60)
    
    examples = ExperienceExamples()
    
    # 运行示例
    try:
        await examples.example_1_basic_experience_recording()
        await examples.example_2_smart_method_recommendation()
        await examples.example_3_success_rate_analysis()
        await examples.example_4_method_effectiveness_comparison()
        await examples.example_5_experience_persistence()
        await examples.example_6_adaptive_learning()
        
        # 打印摘要
        examples.print_experience_summary()
        
    except Exception as e:
        print(f"\n❌ 运行示例时出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("示例运行完成!")
    print("="*60)
    print("\n💡 提示:")
    print("   - 站点经验会自动积累和学习")
    print("   - 经验数据会持久化保存")
    print("   - 系统会根据经验智能选择访问方法")
    print("   - 定期清理过期经验以保持数据准确")


if __name__ == "__main__":
    asyncio.run(main())
