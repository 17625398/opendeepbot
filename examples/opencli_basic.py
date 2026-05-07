"""
OpenCLI 基础使用示例

此示例展示了 OpenCLI 的基本功能：
- 连接到 Chrome 浏览器
- 导航到网页
- 查找和交互元素
- 获取页面信息
- 截图

前提条件：
1. 安装 OpenCLI: npm install -g @jackwener/opencli
2. 以调试模式启动 Chrome:
   Windows: "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
   Linux: google-chrome --remote-debugging-port=9222
   macOS: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
"""

import os
import sys

# 将项目根目录添加到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 注意：实际使用时需要安装 opencli Python 包
# pip install opencli
try:
    from opencli import OpenCLI
    from opencli.exceptions import ConnectionError, ElementNotFoundError, TimeoutError
except ImportError:
    print("警告: opencli 包未安装。这是一个示例代码，展示如何使用 API。")
    print("安装命令: pip install opencli")
    
    # 创建模拟类用于演示
    class MockOpenCLI:
        def __init__(self, host="localhost", port=9222, timeout=30000):
            self.host = host
            self.port = port
            self.timeout = timeout
            self._connected = False
        
        def connect(self):
            print(f"[模拟] 连接到 Chrome ({self.host}:{self.port})")
            self._connected = True
            return True
        
        def disconnect(self):
            print("[模拟] 断开连接")
            self._connected = False
        
        def is_connected(self):
            return self._connected
        
        def navigate(self, url, wait_until="networkidle"):
            print(f"[模拟] 导航到: {url}")
            return True
        
        def find_element(self, selector, by="css"):
            print(f"[模拟] 查找元素: {selector} (by={by})")
            return {"selector": selector}
        
        def click(self, selector, by="css"):
            print(f"[模拟] 点击元素: {selector}")
            return True
        
        def type(self, selector, text, by="css", clear=True):
            print(f"[模拟] 在 {selector} 输入: {text}")
            return True
        
        def get_text(self, selector, by="css"):
            print(f"[模拟] 获取 {selector} 的文本")
            return "示例文本"
        
        def get_page_content(self):
            print("[模拟] 获取页面内容")
            return "<html><body>示例页面内容</body></html>"
        
        def get_page_text(self):
            print("[模拟] 获取页面纯文本")
            return "示例页面纯文本内容"
        
        def get_url(self):
            return "https://example.com"
        
        def get_title(self):
            return "示例页面标题"
        
        def screenshot(self, path=None, full_page=False):
            print(f"[模拟] 截图保存到: {path}")
            return "base64encodedstring"
        
        def execute_script(self, script, *args):
            print(f"[模拟] 执行脚本: {script[:50]}...")
            return None
        
        def wait_for_element(self, selector, by="css", timeout=None):
            print(f"[模拟] 等待元素: {selector}")
            return {"selector": selector}
    
    OpenCLI = MockOpenCLI
    ConnectionError = Exception
    ElementNotFoundError = Exception
    TimeoutError = Exception


def example_basic_navigation():
    """基础导航示例"""
    print("=" * 50)
    print("示例 1: 基础导航")
    print("=" * 50)
    
    client = OpenCLI(
        host="localhost",
        port=9222,
        timeout=30000
    )
    
    try:
        # 连接到 Chrome
        client.connect()
        print("✓ 已连接到 Chrome")
        
        # 导航到网页
        client.navigate("https://example.com")
        print("✓ 导航到 example.com")
        
        # 获取页面信息
        url = client.get_url()
        title = client.get_title()
        print(f"  URL: {url}")
        print(f"  标题: {title}")
        
    except ConnectionError as e:
        print(f"✗ 连接失败: {e}")
    finally:
        if client.is_connected():
            client.disconnect()
            print("✓ 已断开连接")
    
    print()


def example_element_interaction():
    """元素交互示例"""
    print("=" * 50)
    print("示例 2: 元素交互")
    print("=" * 50)
    
    client = OpenCLI()
    
    try:
        client.connect()
        
        # 导航到登录页面（示例）
        client.navigate("https://example.com/login")
        
        # 等待页面加载
        client.wait_for_element("form", timeout=10000)
        print("✓ 页面已加载")
        
        # 输入用户名
        client.type("#username", "testuser")
        print("✓ 输入用户名")
        
        # 输入密码
        client.type("#password", "testpass")
        print("✓ 输入密码")
        
        # 点击登录按钮
        client.click("button[type='submit']")
        print("✓ 点击登录按钮")
        
        # 等待登录完成
        client.wait_for_element(".dashboard", timeout=10000)
        print("✓ 登录成功")
        
    except ElementNotFoundError as e:
        print(f"✗ 元素未找到: {e}")
    except TimeoutError as e:
        print(f"✗ 操作超时: {e}")
    finally:
        if client.is_connected():
            client.disconnect()
    
    print()


def example_page_content():
    """页面内容获取示例"""
    print("=" * 50)
    print("示例 3: 页面内容获取")
    print("=" * 50)
    
    client = OpenCLI()
    
    try:
        client.connect()
        client.navigate("https://example.com")
        
        # 获取 HTML 内容
        html = client.get_page_content()
        print(f"✓ HTML 内容长度: {len(html)} 字符")
        
        # 获取纯文本内容
        text = client.get_page_text()
        print(f"✓ 纯文本内容长度: {len(text)} 字符")
        print(f"  前 100 字符: {text[:100]}...")
        
        # 获取特定元素文本
        try:
            heading_text = client.get_text("h1")
            print(f"✓ H1 标题: {heading_text}")
        except:
            print("  未找到 H1 标题")
        
    finally:
        if client.is_connected():
            client.disconnect()
    
    print()


def example_javascript_execution():
    """JavaScript 执行示例"""
    print("=" * 50)
    print("示例 4: JavaScript 执行")
    print("=" * 50)
    
    client = OpenCLI()
    
    try:
        client.connect()
        client.navigate("https://example.com")
        
        # 获取页面标题
        title = client.execute_script("return document.title;")
        print(f"✓ 页面标题: {title}")
        
        # 获取页面高度
        height = client.execute_script("return document.body.scrollHeight;")
        print(f"✓ 页面高度: {height}")
        
        # 滚动到页面底部
        client.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("✓ 滚动到页面底部")
        
        # 获取所有链接
        links = client.execute_script("""
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.textContent.trim(),
                href: a.href
            }));
        """)
        print(f"✓ 找到 {len(links)} 个链接")
        for link in links[:3]:  # 只显示前 3 个
            print(f"  - {link.get('text', 'N/A')}: {link.get('href', 'N/A')}")
        
    finally:
        if client.is_connected():
            client.disconnect()
    
    print()


def example_screenshot():
    """截图示例"""
    print("=" * 50)
    print("示例 5: 截图")
    print("=" * 50)
    
    client = OpenCLI()
    
    try:
        client.connect()
        client.navigate("https://example.com")
        
        # 创建截图目录
        screenshot_dir = "screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # 截取可见区域
        client.screenshot(f"{screenshot_dir}/visible.png")
        print(f"✓ 已保存可见区域截图: {screenshot_dir}/visible.png")
        
        # 截取整个页面
        client.screenshot(f"{screenshot_dir}/fullpage.png", full_page=True)
        print(f"✓ 已保存完整页面截图: {screenshot_dir}/fullpage.png")
        
        # 截取特定元素
        try:
            client.screenshot(f"{screenshot_dir}/header.png", selector="header")
            print(f"✓ 已保存页眉截图: {screenshot_dir}/header.png")
        except:
            print("  未找到 header 元素")
        
    finally:
        if client.is_connected():
            client.disconnect()
    
    print()


def example_form_handling():
    """表单处理示例"""
    print("=" * 50)
    print("示例 6: 表单处理")
    print("=" * 50)
    
    client = OpenCLI()
    
    try:
        client.connect()
        client.navigate("https://example.com/form")
        
        # 填写文本输入
        client.type("#name", "张三")
        print("✓ 填写姓名")
        
        client.type("#email", "zhangsan@example.com")
        print("✓ 填写邮箱")
        
        # 选择下拉选项
        try:
            client.execute_script("""
                document.querySelector('#country').value = 'cn';
            """)
            print("✓ 选择国家")
        except:
            print("  选择国家失败")
        
        # 勾选复选框
        client.execute_script("""
            document.querySelector('#agree').checked = true;
        """)
        print("✓ 勾选同意条款")
        
        # 提交表单
        client.click("button[type='submit']")
        print("✓ 提交表单")
        
        # 等待提交完成
        client.wait_for_element(".success-message", timeout=10000)
        print("✓ 表单提交成功")
        
    finally:
        if client.is_connected():
            client.disconnect()
    
    print()


def main():
    """主函数：运行所有示例"""
    print("\n" + "=" * 50)
    print("OpenCLI 基础使用示例")
    print("=" * 50 + "\n")
    
    # 运行各个示例
    example_basic_navigation()
    example_element_interaction()
    example_page_content()
    example_javascript_execution()
    example_screenshot()
    example_form_handling()
    
    print("=" * 50)
    print("所有示例运行完成！")
    print("=" * 50)
    print("\n提示:")
    print("1. 确保 Chrome 以调试模式运行")
    print("2. 安装 opencli: pip install opencli")
    print("3. 查看文档: docs/OPENCLI-INTEGRATION.md")
    print("4. 查看 API 文档: docs/OPENCLI-API.md")


if __name__ == "__main__":
    main()
