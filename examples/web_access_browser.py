"""
Web Access Skill - 浏览器自动化示例

本示例展示如何使用 Web Access Skill 的浏览器自动化功能：
- 基础页面获取
- 页面截图
- 元素交互（点击、输入、滚动）
- 表单填写
- 多步骤操作流程

运行前请确保：
1. 已安装 Playwright: pip install playwright
2. 已安装浏览器: playwright install chromium
3. 或已启动 Chrome 远程调试模式
"""

import asyncio
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional

# 尝试导入 WebAccessSkill
try:
    from src.skills.web_access import WebAccessSkill
except ImportError:
    print("警告: 无法导入 WebAccessSkill，使用模拟实现")
    
    class MockWebAccessSkill:
        def __init__(self):
            self.name = "WebAccessSkill (Mock)"
        
        async def execute(self, **kwargs):
            action = kwargs.get("action")
            
            if action == "fetch":
                return MockResult({
                    "success": True,
                    "data": {
                        "url": kwargs.get("url"),
                        "title": "Mock Page Title",
                        "content": "This is mock page content for demonstration...",
                        "method": "mock_fetch"
                    },
                    "channel_used": "fetch"
                })
            
            elif action == "browse":
                interactions = kwargs.get("interactions", [])
                interaction_results = []
                
                for interaction in interactions:
                    interaction_results.append({
                        "action": interaction.get("action"),
                        "selector": interaction.get("selector"),
                        "success": True
                    })
                
                return MockResult({
                    "success": True,
                    "data": {
                        "url": kwargs.get("url"),
                        "title": "Mock Page After Interactions",
                        "content": "Page content after mock interactions...",
                        "interactions": interaction_results,
                        "media": []
                    },
                    "channel_used": "browser"
                })
            
            return MockResult({"success": False, "error": "Unknown action"})
        
        def get_stats(self):
            return {"config": {"cdp": {"chrome_port": 9222}}}
    
    class MockResult:
        def __init__(self, data):
            self.success = data.get("success", False)
            self.data = data.get("data")
            self.error = data.get("error")
            self.channel_used = data.get("channel_used", "")
            self.execution_time = 0.5
    
    WebAccessSkill = MockWebAccessSkill


class BrowserExamples:
    """浏览器自动化示例类"""
    
    def __init__(self):
        self.skill = WebAccessSkill()
        self.screenshot_dir = Path("./screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
    
    async def example_1_basic_fetch(self):
        """
        示例 1: 基础页面获取
        
        展示如何获取网页内容
        """
        print("\n" + "="*60)
        print("示例 1: 基础页面获取")
        print("="*60)
        
        urls = [
            "https://example.com",
            "https://httpbin.org/html",
        ]
        
        for url in urls:
            print(f"\n🌐 获取页面: {url}")
            
            result = await self.skill.execute(
                action="fetch",
                url=url,
                extract_content=True
            )
            
            if result.success:
                data = result.data
                print(f"✅ 成功获取")
                print(f"📄 标题: {data.get('title', 'N/A')}")
                print(f"📊 内容长度: {len(data.get('content', ''))} 字符")
                print(f"🔧 使用方式: {data.get('method', 'unknown')}")
                print(f"⏱️  耗时: {result.execution_time:.2f}秒")
                
                # 显示内容预览
                content = data.get('content', '')
                if content:
                    preview = content[:200].replace('\n', ' ')
                    print(f"📝 内容预览: {preview}...")
            else:
                print(f"❌ 获取失败: {result.error}")
    
    async def example_2_forced_browser_fetch(self):
        """
        示例 2: 强制使用浏览器获取
        
        某些网站需要 JavaScript 渲染，强制使用浏览器模式
        """
        print("\n" + "="*60)
        print("示例 2: 强制使用浏览器获取")
        print("="*60)
        
        # 需要 JavaScript 渲染的页面示例
        urls = [
            "https://httpbin.org/html",
        ]
        
        for url in urls:
            print(f"\n🌐 强制浏览器模式获取: {url}")
            
            result = await self.skill.execute(
                action="fetch",
                url=url,
                use_browser=True,  # 强制使用浏览器
                extract_content=True,
                extract_media=True
            )
            
            if result.success:
                data = result.data
                print(f"✅ 成功获取 (浏览器模式)")
                print(f"📄 标题: {data.get('title', 'N/A')}")
                print(f"📊 内容长度: {len(data.get('content', ''))} 字符")
                
                # 显示媒体信息
                media = data.get('media', [])
                if media:
                    print(f"🖼️  发现媒体资源: {len(media)} 个")
                    for i, m in enumerate(media[:3], 1):
                        print(f"   {i}. {m.get('type', 'unknown')}: {m.get('src', 'N/A')[:50]}...")
            else:
                print(f"❌ 获取失败: {result.error}")
                print("💡 提示: 确保 Chrome 远程调试已启动")
                print("   命令: google-chrome --remote-debugging-port=9222")
    
    async def example_3_simple_interactions(self):
        """
        示例 3: 简单页面交互
        
        展示点击、滚动等基本操作
        """
        print("\n" + "="*60)
        print("示例 3: 简单页面交互")
        print("="*60)
        
        # 使用 httpbin 进行交互测试
        url = "https://httpbin.org/forms/post"
        
        print(f"\n🌐 页面交互演示: {url}")
        print("-" * 40)
        
        interactions = [
            {"action": "wait", "time": 2},  # 等待页面加载
            {"action": "scroll", "direction": "bottom"},  # 滚动到底部
            {"action": "wait", "time": 1},  # 等待滚动完成
        ]
        
        result = await self.skill.execute(
            action="browse",
            url=url,
            interactions=interactions,
            extract_content=True
        )
        
        if result.success:
            data = result.data
            print(f"✅ 交互完成")
            print(f"📄 页面标题: {data.get('title', 'N/A')}")
            
            # 显示交互结果
            interaction_results = data.get('interactions', [])
            print(f"\n🎮 交互操作记录:")
            for i, interaction in enumerate(interaction_results, 1):
                status = "✅" if interaction.get('success') else "❌"
                print(f"   {i}. {status} {interaction.get('action')}")
                if interaction.get('selector'):
                    print(f"      选择器: {interaction['selector']}")
            
            print(f"\n⏱️  总耗时: {result.execution_time:.2f}秒")
        else:
            print(f"❌ 交互失败: {result.error}")
    
    async def example_4_form_interaction(self):
        """
        示例 4: 表单填写和提交
        
        展示如何填写表单
        """
        print("\n" + "="*60)
        print("示例 4: 表单填写和提交")
        print("="*60)
        
        # httpbin 的表单测试页面
        url = "https://httpbin.org/forms/post"
        
        print(f"\n🌐 表单操作: {url}")
        print("-" * 40)
        print("📝 模拟表单填写流程:")
        
        # 表单填写交互
        interactions = [
            {"action": "wait", "time": 2},
            {
                "action": "type",
                "selector": "input[name='custname']",
                "value": "张三"
            },
            {
                "action": "type",
                "selector": "input[name='custtel']",
                "value": "13800138000"
            },
            {
                "action": "type",
                "selector": "input[name='custemail']",
                "value": "zhangsan@example.com"
            },
            {"action": "wait", "time": 1},
            {"action": "scroll", "direction": "bottom"},
            {"action": "wait", "time": 1},
        ]
        
        # 显示计划的操作
        for i, interaction in enumerate(interactions, 1):
            action = interaction.get('action')
            if action == "type":
                print(f"   {i}. 输入 '{interaction.get('value')}' 到 {interaction.get('selector')}")
            elif action == "wait":
                print(f"   {i}. 等待 {interaction.get('time')} 秒")
            elif action == "scroll":
                print(f"   {i}. 滚动到{interaction.get('direction')}")
        
        result = await self.skill.execute(
            action="browse",
            url=url,
            interactions=interactions,
            extract_content=True
        )
        
        if result.success:
            print(f"\n✅ 表单填写完成")
            data = result.data
            
            # 检查交互结果
            interaction_results = data.get('interactions', [])
            success_count = sum(1 for i in interaction_results if i.get('success'))
            print(f"📊 成功操作: {success_count}/{len(interaction_results)}")
            
            # 显示页面内容预览
            content = data.get('content', '')
            if content and 'zhangsan' in content.lower():
                print("✅ 表单内容已反映在页面中")
        else:
            print(f"❌ 表单操作失败: {result.error}")
    
    async def example_5_multi_step_workflow(self):
        """
        示例 5: 多步骤工作流程
        
        展示复杂的多步骤浏览器操作流程
        """
        print("\n" + "="*60)
        print("示例 5: 多步骤工作流程")
        print("="*60)
        
        url = "https://httpbin.org/html"
        
        print(f"\n🌐 多步骤流程演示: {url}")
        print("-" * 40)
        print("📋 流程步骤:")
        print("   1. 打开页面")
        print("   2. 等待加载")
        print("   3. 滚动到中部")
        print("   4. 等待渲染")
        print("   5. 滚动到底部")
        print("   6. 获取最终内容")
        
        interactions = [
            {"action": "wait", "time": 2},
            {"action": "scroll", "direction": "down", "amount": 500},
            {"action": "wait", "time": 1},
            {"action": "scroll", "direction": "bottom"},
            {"action": "wait", "time": 1},
        ]
        
        result = await self.skill.execute(
            action="browse",
            url=url,
            interactions=interactions,
            extract_content=True,
            extract_media=True
        )
        
        if result.success:
            data = result.data
            print(f"\n✅ 多步骤流程完成")
            print(f"📄 最终页面标题: {data.get('title', 'N/A')}")
            print(f"📊 内容长度: {len(data.get('content', ''))} 字符")
            
            # 流程统计
            interaction_results = data.get('interactions', [])
            print(f"\n📈 流程统计:")
            print(f"   - 总步骤: {len(interaction_results)}")
            print(f"   - 成功: {sum(1 for i in interaction_results if i.get('success'))}")
            print(f"   - 失败: {sum(1 for i in interaction_results if not i.get('success'))}")
            print(f"   - 总耗时: {result.execution_time:.2f}秒")
        else:
            print(f"❌ 流程失败: {result.error}")
    
    async def example_6_error_handling(self):
        """
        示例 6: 错误处理和重试
        
        展示如何处理浏览器操作中的错误
        """
        print("\n" + "="*60)
        print("示例 6: 错误处理和重试")
        print("="*60)
        
        # 测试无效选择器
        url = "https://example.com"
        
        print(f"\n🌐 错误处理演示: {url}")
        print("-" * 40)
        
        # 尝试点击不存在的元素
        interactions = [
            {"action": "wait", "time": 2},
            {"action": "click", "selector": "#non-existent-element"},
            {"action": "type", "selector": "#non-existent-input", "value": "test"},
        ]
        
        result = await self.skill.execute(
            action="browse",
            url=url,
            interactions=interactions,
            extract_content=True
        )
        
        if result.success:
            data = result.data
            interaction_results = data.get('interactions', [])
            
            print(f"📊 交互结果分析:")
            for i, interaction in enumerate(interaction_results, 1):
                action = interaction.get('action')
                success = interaction.get('success')
                selector = interaction.get('selector', 'N/A')
                
                status = "✅" if success else "❌"
                print(f"   {i}. {status} {action}")
                if selector != 'N/A':
                    print(f"      选择器: {selector}")
                if not success:
                    print(f"      💡 提示: 元素可能不存在或页面结构不同")
        else:
            print(f"❌ 操作失败: {result.error}")
        
        print("\n💡 最佳实践:")
        print("   1. 使用 wait 操作确保页面加载完成")
        print("   2. 检查选择器是否正确")
        print("   3. 处理可能的异常情况")
        print("   4. 添加适当的超时设置")
    
    def print_browser_config(self):
        """打印浏览器配置信息"""
        print("\n" + "="*60)
        print("浏览器配置信息")
        print("="*60)
        
        stats = self.skill.get_stats()
        config = stats.get('config', {})
        cdp_config = config.get('cdp', {})
        
        print(f"\n🔧 CDP 配置:")
        print(f"   - Chrome 主机: {cdp_config.get('chrome_host', 'localhost')}")
        print(f"   - Chrome 端口: {cdp_config.get('chrome_port', 9222)}")
        print(f"   - 默认超时: {cdp_config.get('default_timeout', 30)} 秒")
        print(f"   - 页面加载超时: {cdp_config.get('page_load_timeout', 60)} 秒")
        
        print(f"\n📁 截图保存目录:")
        print(f"   {self.screenshot_dir.absolute()}")
        
        print("\n💡 启动 Chrome 远程调试:")
        print("   macOS:")
        print("     /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\")
        print("       --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_dev")
        print("\n   Linux:")
        print("     google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_dev")
        print("\n   Windows:")
        print("     start chrome.exe --remote-debugging-port=9222 --user-data-dir=C:/chrome_dev")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("Web Access Skill - 浏览器自动化示例")
    print("="*60)
    
    examples = BrowserExamples()
    
    # 打印配置信息
    examples.print_browser_config()
    
    # 运行示例
    try:
        await examples.example_1_basic_fetch()
        await examples.example_2_forced_browser_fetch()
        await examples.example_3_simple_interactions()
        await examples.example_4_form_interaction()
        await examples.example_5_multi_step_workflow()
        await examples.example_6_error_handling()
        
    except Exception as e:
        print(f"\n❌ 运行示例时出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("示例运行完成!")
    print("="*60)
    print("\n💡 提示:")
    print("   - 浏览器自动化需要 Chrome 远程调试模式")
    print("   - 确保已启动 Chrome 并开启远程调试端口")
    print("   - 某些操作可能需要根据实际页面结构调整选择器")


if __name__ == "__main__":
    asyncio.run(main())
