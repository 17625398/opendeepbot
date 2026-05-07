"""
Agent-Browser 性能基准测试工具

测试项目：
- 导航延迟
- 快照生成速度
- 元素操作延迟
- 缓存性能
- 并发性能
- 内存使用

Author: DeepTutor
Created: 2026-03-06
"""

import asyncio
import time
import statistics
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.integrations.mcp.agent_browser_cdp import get_browser
from src.integrations.mcp.agent_browser_native_daemon import get_daemon_manager, DaemonConfig
from src.integrations.mcp.agent_browser_snapshot import SnapshotEngine
from src.integrations.mcp.agent_browser_optimizer import get_optimizer, CacheConfig


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    iterations: int
    results: List[float] = field(default_factory=list)
    unit: str = "ms"
    
    @property
    def min(self) -> float:
        return min(self.results) if self.results else 0
    
    @property
    def max(self) -> float:
        return max(self.results) if self.results else 0
    
    @property
    def avg(self) -> float:
        return statistics.mean(self.results) if self.results else 0
    
    @property
    def median(self) -> float:
        return statistics.median(self.results) if self.results else 0
    
    @property
    def std_dev(self) -> float:
        return statistics.stdev(self.results) if len(self.results) > 1 else 0
    
    @property
    def p95(self) -> float:
        sorted_results = sorted(self.results)
        idx = int(len(sorted_results) * 0.95)
        return sorted_results[min(idx, len(sorted_results) - 1)]
    
    @property
    def p99(self) -> float:
        sorted_results = sorted(self.results)
        idx = int(len(sorted_results) * 0.99)
        return sorted_results[min(idx, len(sorted_results) - 1)]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "unit": self.unit,
            "min": round(self.min, 3),
            "max": round(self.max, 3),
            "avg": round(self.avg, 3),
            "median": round(self.median, 3),
            "std_dev": round(self.std_dev, 3),
            "p95": round(self.p95, 3),
            "p99": round(self.p99, 3)
        }


class BenchmarkSuite:
    """基准测试套件"""
    
    def __init__(self, output_dir: str = "./benchmarks"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
        self.browser = None
        self.session_name = "benchmark"
    
    async def setup(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")
        config = DaemonConfig(headless=True, session=self.session_name)
        manager = await get_daemon_manager(config)
        self.browser = await get_browser(self.session_name)
        print("✅ 浏览器已连接")
    
    async def teardown(self):
        """清理测试环境"""
        if self.browser:
            await self.browser.close()
            print("✅ 浏览器已关闭")
    
    async def run_benchmark(
        self,
        name: str,
        benchmark_func,
        iterations: int = 10
    ) -> BenchmarkResult:
        """运行单个基准测试"""
        print(f"\n📊 运行测试：{name} ({iterations} 次迭代)")
        
        result = BenchmarkResult(name=name, iterations=iterations)
        
        for i in range(iterations):
            start = time.perf_counter()
            await benchmark_func()
            duration = (time.perf_counter() - start) * 1000  # 转换为毫秒
            result.results.append(duration)
            
            if (i + 1) % 5 == 0:
                print(f"  进度：{i + 1}/{iterations}")
        
        self.results.append(result)
        
        # 打印结果
        print(f"\n✅ {name} 完成:")
        print(f"   最小值：{result.min:.3f} ms")
        print(f"   最大值：{result.max:.3f} ms")
        print(f"   平均值：{result.avg:.3f} ms")
        print(f"   中位数：{result.median:.3f} ms")
        print(f"   P95: {result.p95:.3f} ms")
        print(f"   标准差：{result.std_dev:.3f} ms")
        
        return result
    
    # ========== 导航测试 ==========
    
    async def benchmark_navigation(self):
        """导航延迟测试"""
        urls = [
            "https://example.com",
            "https://httpbin.org/html",
            "https://httpbin.org/delay/1"
        ]
        
        async def navigate():
            url = urls[len(self.results) % len(urls)]
            await self.browser.navigate(url)
        
        await self.run_benchmark("导航延迟", navigate, iterations=20)
    
    # ========== 快照测试 ==========
    
    async def benchmark_snapshot(self):
        """快照生成速度测试"""
        await self.browser.navigate("https://example.com")
        
        async def get_snapshot():
            await self.browser.get_snapshot(interactive_only=True)
        
        await self.run_benchmark("快照生成", get_snapshot, iterations=30)
    
    # ========== 点击测试 ==========
    
    async def benchmark_click(self):
        """点击延迟测试"""
        await self.browser.navigate("https://example.com")
        
        async def click():
            await self.browser.click("body")
        
        await self.run_benchmark("点击操作", click, iterations=20)
    
    # ========== JavaScript 执行测试 ==========
    
    async def benchmark_javascript(self):
        """JavaScript 执行速度测试"""
        scripts = [
            "document.title",
            "document.querySelectorAll('*').length",
            "window.location.href"
        ]
        
        async def execute_js():
            script = scripts[len(self.results) % len(scripts)]
            await self.browser.evaluate_js(script)
        
        await self.run_benchmark("JavaScript 执行", execute_js, iterations=20)
    
    # ========== 缓存性能测试 ==========
    
    async def benchmark_cache(self):
        """缓存性能测试"""
        optimizer = get_optimizer()
        cache = optimizer.cache
        
        # 写入缓存
        await cache.set("test_key", {"data": "value"}, ttl=300)
        
        async def read_cache():
            await cache.get("test_key")
        
        await self.run_benchmark("缓存读取", read_cache, iterations=50)
    
    # ========== 并发性能测试 ==========
    
    async def benchmark_concurrency(self):
        """并发性能测试"""
        optimizer = get_optimizer()
        executor = optimizer.executor
        
        async def fetch_item(item_id):
            await asyncio.sleep(0.01)  # 模拟 I/O
            return item_id
        
        concurrency_levels = [1, 5, 10, 20]
        
        for level in concurrency_levels:
            executor.max_concurrency = level
            
            async def run_batch():
                tasks = [(fetch_item, [i], {}) for i in range(level)]
                await executor.execute_batch(tasks)
            
            await self.run_benchmark(f"并发-{level}", run_batch, iterations=10)
    
    # ========== 内存使用测试 ==========
    
    async def benchmark_memory(self):
        """内存使用测试"""
        import tracemalloc
        
        tracemalloc.start()
        
        # 基线内存
        snapshot1 = tracemalloc.take_snapshot()
        
        # 执行一些操作
        await self.browser.navigate("https://example.com")
        for _ in range(10):
            await self.browser.get_snapshot()
        
        # 当前内存
        snapshot2 = tracemalloc.take_snapshot()
        
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        print("\n📊 内存使用 Top 10:")
        for stat in top_stats[:10]:
            print(f"  {stat.traceback}: {stat.size / 1024:.2f} KB")
        
        tracemalloc.stop()
    
    # ========== 运行所有测试 ==========
    
    async def run_all(self):
        """运行所有基准测试"""
        print("=" * 60)
        print("🚀 Agent-Browser 性能基准测试")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # 运行测试
            await self.benchmark_navigation()
            await self.benchmark_snapshot()
            await self.benchmark_click()
            await self.benchmark_javascript()
            await self.benchmark_cache()
            await self.benchmark_concurrency()
            await self.benchmark_memory()
            
            # 生成报告
            self.generate_report()
            
        finally:
            await self.teardown()
    
    def generate_report(self):
        """生成基准测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"benchmark_report_{timestamp}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "summary": {
                "fastest": min(self.results, key=lambda r: r.avg).name if self.results else None,
                "slowest": max(self.results, key=lambda r: r.avg).name if self.results else None
            }
        }
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 报告已保存：{report_file}")
        
        # 生成 Markdown 报告
        self.generate_markdown_report(timestamp)
    
    def generate_markdown_report(self, timestamp: str):
        """生成 Markdown 格式报告"""
        md_file = self.output_dir / f"benchmark_{timestamp}.md"
        
        lines = [
            "# Agent-Browser 性能基准测试报告",
            "",
            f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 测试结果汇总",
            "",
            "| 测试项目 |  iterations | 最小值 (ms) | 最大值 (ms) | 平均值 (ms) | 中位数 (ms) | P95 (ms) | 标准差 |",
            "|---------|------------|------------|------------|------------|------------|---------|--------|"
        ]
        
        for result in self.results:
            lines.append(
                f"| {result.name} | {result.iterations} | "
                f"{result.min:.3f} | {result.max:.3f} | "
                f"{result.avg:.3f} | {result.median:.3f} | "
                f"{result.p95:.3f} | {result.std_dev:.3f} |"
            )
        
        lines.extend([
            "",
            "## 性能分析",
            "",
            "### 导航性能",
            f"- 平均延迟：**{self._get_result('导航延迟').avg:.3f} ms**",
            f"- P95 延迟：**{self._get_result('导航延迟').p95:.3f} ms**",
            "",
            "### 快照性能",
            f"- 平均生成时间：**{self._get_result('快照生成').avg:.3f} ms**",
            f"- P95 延迟：**{self._get_result('快照生成').p95:.3f} ms**",
            "",
            "### 操作性能",
            f"- 点击延迟：**{self._get_result('点击操作').avg:.3f} ms**",
            f"- JS 执行：**{self._get_result('JavaScript 执行').avg:.3f} ms**",
            "",
            "### 缓存性能",
            f"- 读取延迟：**{self._get_result('缓存读取').avg:.3f} ms**",
            "",
            "## 优化建议",
            "",
            "基于测试结果，建议：",
            "1. 使用 Native CDP 模式获得最佳性能",
            "2. 启用缓存减少重复操作",
            "3. 使用并发处理批量任务",
            "4. 合理设置快照优化选项",
            ""
        ])
        
        with open(md_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        print(f"✅ Markdown 报告已保存：{md_file}")
    
    def _get_result(self, name: str) -> BenchmarkResult:
        """获取指定测试结果"""
        for result in self.results:
            if result.name == name:
                return result
        return BenchmarkResult(name=name, iterations=0)


# ==================== 运行基准测试 ====================

async def main():
    """主函数"""
    suite = BenchmarkSuite()
    await suite.run_all()


if __name__ == "__main__":
    asyncio.run(main())
