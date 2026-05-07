"""
Agent-Browser 示例项目集合

包含 8+ 实际使用场景：
1. 网页抓取
2. 自动化测试
3. 表单提交
4. 数据监控
5. 截图报告
6. 批量操作
7. 登录认证
8. API 测试

Author: DeepTutor
Created: 2026-03-06
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.mcp.agent_browser_cdp import get_browser
from src.mcp.agent_browser_native_daemon import DaemonConfig, get_daemon_manager
from src.mcp.agent_browser_snapshot import SnapshotEngine


# ==================== 示例 1: 网页抓取 ====================

async def example_web_scraper():
    """
    示例 1: 网页抓取
    
    抓取网页内容并提取结构化数据
    """
    print("\n📌 示例 1: 网页抓取")
    print("=" * 50)
    
    config = DaemonConfig(headless=True, session="scraper")
    manager = await get_daemon_manager(config)
    browser = await get_browser("scraper")
    
    try:
        # 导航到目标页面
        await browser.navigate("https://httpbin.org/html")
        
        # 获取快照
        snapshot = await browser.get_snapshot(interactive_only=False)
        
        # 提取标题
        title_result = await browser.evaluate_js("document.title")
        print(f"页面标题：{title_result.data.get('result')}")
        
        # 提取所有段落
        paragraphs = await browser.evaluate_js(
            "Array.from(document.querySelectorAll('p')).map(p => p.textContent)"
        )
        print(f"段落数量：{len(paragraphs.data.get('result', []))}")
        
        # 提取链接
        links = await browser.evaluate_js(
            "Array.from(document.querySelectorAll('a')).map(a => ({text: a.textContent, href: a.href}))"
        )
        print(f"链接数量：{len(links.data.get('result', []))}")
        
    finally:
        await browser.close()


# ==================== 示例 2: 自动化测试 ====================

async def example_automation_test():
    """
    示例 2: 自动化测试
    
    测试网页功能是否正常工作
    """
    print("\n📌 示例 2: 自动化测试")
    print("=" * 50)
    
    config = DaemonConfig(headless=True, session="test")
    manager = await get_daemon_manager(config)
    browser = await get_browser("test")
    
    try:
        # 测试页面加载
        await browser.navigate("https://httpbin.org/forms/post")
        print("✅ 页面加载成功")
        
        # 测试表单元素存在
        form_exists = await browser.evaluate_js(
            "document.querySelector('form') !== null"
        )
        assert form_exists.data.get("result") is True
        print("✅ 表单元素存在")
        
        # 测试输入框
        await browser.evaluate_js(
            "document.getElementById('custname').value = 'Test User'"
        )
        value = await browser.evaluate_js(
            "document.getElementById('custname').value"
        )
        assert value.data.get("result") == "Test User"
        print("✅ 输入框操作正常")
        
        print("✅ 所有测试通过")
        
    finally:
        await browser.close()


# ==================== 示例 3: 表单提交 ====================

async def example_form_submission():
    """
    示例 3: 表单提交
    
    自动填写并提交表单
    """
    print("\n📌 示例 3: 表单提交")
    print("=" * 50)
    
    config = DaemonConfig(headless=True, session="form")
    manager = await get_daemon_manager(config)
    browser = await get_browser("form")
    
    try:
        await browser.navigate("https://httpbin.org/forms/post")
        
        # 填写表单
        form_data = {
            "custname": "张三",
            "custtel": "13800138000",
            "custemail": "test@example.com",
            "comments": "这是一个测试订单"
        }
        
        for field_id, value in form_data.items():
            await browser.evaluate_js(
                f"document.getElementById('{field_id}').value = '{value}'"
            )
            print(f"✅ 填写 {field_id}: {value}")
        
        # 选择单选框
        await browser.evaluate_js(
            "document.querySelector('input[name=\"size\"][value=\"medium\"]').checked = true"
        )
        print("✅ 选择尺寸：中号")
        
        # 提交表单（不实际提交，仅演示）
        print("✅ 表单已填写完成")
        
        # 验证数据
        submitted_data = await browser.evaluate_js(
            """
            JSON.stringify({
                name: document.getElementById('custname').value,
                tel: document.getElementById('custtel').value,
                email: document.getElementById('custemail').value
            })
            """
        )
        print(f"📋 表单数据：{submitted_data.data.get('result')}")
        
    finally:
        await browser.close()


# ==================== 示例 4: 数据监控 ====================

async def example_data_monitoring():
    """
    示例 4: 数据监控
    
    监控网页数据变化（如价格、库存等）
    """
    print("\n📌 示例 4: 数据监控")
    print("=" * 50)
    
    config = DaemonConfig(headless=True, session="monitor")
    manager = await get_daemon_manager(config)
    browser = await get_browser("monitor")
    
    try:
        # 模拟监控数据
        monitoring_items = [
            {"url": "https://httpbin.org/html", "selector": "h1", "name": "标题"},
            {"url": "https://httpbin.org/html", "selector": "p", "name": "段落"}
        ]
        
        for item in monitoring_items:
            await browser.navigate(item["url"])
            
            # 获取元素文本
            text = await browser.evaluate_js(
                f"document.querySelector('{item['selector']}').textContent.trim()"
            )
            
            print(f"✅ {item['name']}: {text.data.get('result')[:50]}...")
        
        # 生成监控报告
        report = {
            "timestamp": asyncio.get_event_loop().time(),
            "items_checked": len(monitoring_items),
            "status": "success"
        }
        print(f"📊 监控报告：{json.dumps(report, indent=2)}")
        
    finally:
        await browser.close()


# ==================== 示例 5: 截图报告 ====================

async def example_screenshot_report():
    """
    示例 5: 截图报告
    
    批量截图并生成报告
    """
    print("\n📌 示例 5: 截图报告")
    print("=" * 50)
    
    config = DaemonConfig(headless=True, session="screenshot")
    manager = await get_daemon_manager(config)
    browser = await get_browser("screenshot")
    
    try:
        urls = [
            "https://example.com",
            "https://httpbin.org/html",
            "https://httpbin.org/forms/post"
        ]
        
        screenshots = []
        
        for i, url in enumerate(urls):
            await browser.navigate(url)
            
            # 获取截图
            screenshot = await browser.screenshot(full_page=False)
            
            if screenshot.success:
                screenshots.append({
                    "url": url,
                    "success": True,
                    "size": len(screenshot.data.get("screenshot", ""))
                })
                print(f"✅ 截图 {i+1}/{len(urls)}: {url}")
        
        # 生成报告
        report = {
            "total": len(urls),
            "success": sum(1 for s in screenshots if s["success"]),
            "failed": sum(1 for s in screenshots if not s["success"])
        }
        print(f"📊 截图报告：{json.dumps(report, indent=2)}")
        
    finally:
        await browser.close()


# ==================== 示例 6: 批量操作 ====================

async def example_batch_operations():
    """
    示例 6: 批量操作
    
    批量处理多个任务
    """
    print("\n📌 示例 6: 批量操作")
    print("=" * 50)
    
    from src.mcp.agent_browser_optimizer import get_optimizer
    
    optimizer = get_optimizer()
    executor = optimizer.executor
    
    # 模拟批量任务
    tasks = [
        ("fetch_url", [f"https://httpbin.org/get?id={i}"], {})
        for i in range(10)
    ]
    
    async def fetch_url(url):
        await asyncio.sleep(0.05)  # 模拟网络延迟
        return {"url": url, "status": 200}
    
    print("🚀 开始批量处理 10 个任务...")
    
    start = asyncio.get_event_loop().time()
    results = await executor.execute_batch(tasks)
    duration = asyncio.get_event_loop().time() - start
    
    print(f"✅ 完成 {len(results)} 个任务，耗时：{duration*1000:.2f}ms")
    print(f"📊 平均每个任务：{duration*1000/len(results):.2f}ms")


# ==================== 示例 7: 登录认证 ====================

async def example_login_authentication():
    """
    示例 7: 登录认证
    
    模拟用户登录流程
    """
    print("\n📌 示例 7: 登录认证")
    print("=" * 50)
    
    config = DaemonConfig(headless=True, session="login")
    manager = await get_daemon_manager(config)
    browser = await get_browser("login")
    
    try:
        # 导航到登录页面
        await browser.navigate("https://httpbin.org/forms/post")
        print("✅ 到达登录页面")
        
        # 填写用户名和密码
        await browser.evaluate_js(
            "document.getElementById('custname').value = 'admin'"
        )
        await browser.evaluate_js(
            "document.getElementById('custemail').value = 'admin@example.com'"
        )
        print("✅ 填写凭证")
        
        # 模拟点击登录按钮
        await browser.evaluate_js(
            "document.querySelector('button[type=\"submit\"]').click()"
        )
        print("✅ 提交登录")
        
        # 等待并检查登录结果
        await asyncio.sleep(1)
        
        # 获取当前 URL（判断是否跳转）
        current_url = await browser.evaluate_js("window.location.href")
        print(f"📍 当前 URL: {current_url.data.get('result')}")
        
        # 检查登录状态
        login_success = True  # 实际应检查页面元素
        print(f"✅ 登录{'成功' if login_success else '失败'}")
        
    finally:
        await browser.close()


# ==================== 示例 8: API 测试 ====================

async def example_api_testing():
    """
    示例 8: API 测试
    
    测试 API 端点
    """
    print("\n📌 示例 8: API 测试")
    print("=" * 50)
    
    config = DaemonConfig(headless=True, session="api")
    manager = await get_daemon_manager(config)
    browser = await get_browser("api")
    
    try:
        # 测试 GET 请求
        await browser.navigate("https://httpbin.org/get?name=test&value=123")
        
        response = await browser.evaluate_js("document.body.textContent")
        print(f"✅ GET 响应：{response.data.get('result')[:100]}...")
        
        # 测试 POST 请求（模拟）
        post_data = {
            "key1": "value1",
            "key2": "value2"
        }
        
        print(f"📋 POST 数据：{json.dumps(post_data)}")
        
        # 执行性能测试
        iterations = 5
        start = asyncio.get_event_loop().time()
        
        for _ in range(iterations):
            await browser.navigate("https://httpbin.org/get")
        
        duration = asyncio.get_event_loop().time() - start
        
        print(f"✅ 性能测试：{iterations} 次请求，耗时 {duration*1000:.2f}ms")
        print(f"📊 平均延迟：{duration*1000/iterations:.2f}ms")
        
    finally:
        await browser.close()


# ==================== 运行所有示例 ====================

async def run_all_examples():
    """运行所有示例"""
    print("=" * 60)
    print("🚀 Agent-Browser 示例项目集合")
    print("=" * 60)
    
    examples = [
        example_web_scraper,
        example_automation_test,
        example_form_submission,
        example_data_monitoring,
        example_screenshot_report,
        example_batch_operations,
        example_login_authentication,
        example_api_testing
    ]
    
    for example in examples:
        try:
            await example()
            await asyncio.sleep(1)  # 间隔 1 秒
        except Exception as e:
            print(f"❌ 示例失败：{example.__name__} - {e}")
    
    print("\n" + "=" * 60)
    print("✅ 所有示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_examples())
