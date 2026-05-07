"""
OpenCLI Electron 应用控制示例

此示例展示了如何使用 OpenCLI 控制 Electron 应用程序。
Electron 应用基于 Chromium，可以通过 Chrome DevTools Protocol 进行控制。

使用场景：
- 自动化测试 Electron 应用
- 从 Electron 应用提取数据
- 与 Electron 应用进行交互
- 监控 Electron 应用状态

前提条件：
1. Electron 应用需要启用远程调试
2. 启动时添加参数: --remote-debugging-port=9223
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# 将项目根目录添加到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 模拟 opencli 导入
try:
    from opencli import OpenCLI
    from opencli.exceptions import ConnectionError, ElementNotFoundError, TimeoutError
except ImportError:
    print("警告: opencli 包未安装。这是一个示例代码。\n")
    
    class MockOpenCLI:
        def __init__(self, host="localhost", port=9222, timeout=30000):
            self.host = host
            self.port = port
            self.timeout = timeout
            self._connected = False
        
        def connect(self):
            self._connected = True
            print(f"  [连接] Electron 应用 ({self.host}:{self.port})")
            return True
        
        def disconnect(self):
            self._connected = False
            print("  [断开] 连接已关闭")
        
        def is_connected(self):
            return self._connected
        
        def navigate(self, url):
            print(f"  [导航] {url}")
            return True
        
        def click(self, selector, by="css"):
            print(f"  [点击] {selector}")
            return True
        
        def type(self, selector, text, by="css", clear=True):
            print(f"  [输入] {selector}: {text}")
            return True
        
        def get_text(self, selector, by="css"):
            return "示例文本"
        
        def find_elements(self, selector, by="css"):
            return [{}, {}]
        
        def wait_for_element(self, selector, by="css", timeout=None):
            print(f"  [等待] {selector}")
            return {}
        
        def execute_script(self, script, *args):
            return None
        
        def screenshot(self, path=None, full_page=False):
            print(f"  [截图] 保存到: {path}")
            return "base64string"
    
    OpenCLI = MockOpenCLI
    ConnectionError = Exception
    ElementNotFoundError = Exception
    TimeoutError = Exception


@dataclass
class ElectronAppInfo:
    """Electron 应用信息"""
    name: str
    version: str
    electron_version: str
    chrome_version: str
    node_version: str
    window_count: int


class ElectronController:
    """
    Electron 应用控制器
    
    提供专门用于控制 Electron 应用的方法。
    """
    
    def __init__(self, debug_port: int = 9223, host: str = "localhost"):
        """
        初始化 Electron 控制器
        
        Args:
            debug_port: Electron 调试端口
            host: 调试服务器主机
        """
        self.client = OpenCLI(
            host=host,
            port=debug_port,
            timeout=30000
        )
        self.debug_port = debug_port
    
    def connect(self) -> bool:
        """
        连接到 Electron 应用
        
        Returns:
            连接是否成功
        """
        try:
            self.client.connect()
            print("✓ 已连接到 Electron 应用")
            return True
        except ConnectionError as e:
            print(f"✗ 连接失败: {e}")
            print("  请确保 Electron 应用以调试模式启动:")
            print(f"    electron . --remote-debugging-port={self.debug_port}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.client.is_connected():
            self.client.disconnect()
            print("✓ 已断开连接")
    
    def get_app_info(self) -> Optional[ElectronAppInfo]:
        """
        获取 Electron 应用信息
        
        Returns:
            应用信息对象
        """
        try:
            # 通过执行 JavaScript 获取应用信息
            info = self.client.execute_script("""
                return {
                    name: document.title,
                    electronVersion: process.versions.electron,
                    chromeVersion: process.versions.chrome,
                    nodeVersion: process.versions.node,
                    platform: process.platform
                };
            """)
            
            if info:
                return ElectronAppInfo(
                    name=info.get("name", "Unknown"),
                    version="Unknown",
                    electron_version=info.get("electronVersion", "Unknown"),
                    chrome_version=info.get("chromeVersion", "Unknown"),
                    node_version=info.get("nodeVersion", "Unknown"),
                    window_count=1
                )
        except Exception as e:
            print(f"  获取应用信息失败: {e}")
        
        return None
    
    def get_window_handles(self) -> List[str]:
        """
        获取所有窗口句柄
        
        Returns:
            窗口句柄列表
        """
        try:
            # 获取所有窗口
            handles = self.client.execute_script("""
                return Object.keys(window);
            """)
            return handles if handles else []
        except:
            return []
    
    def switch_to_window(self, window_handle: str) -> bool:
        """
        切换到指定窗口
        
        Args:
            window_handle: 窗口句柄
            
        Returns:
            切换是否成功
        """
        print(f"  切换到窗口: {window_handle}")
        return True
    
    def execute_ipc(self, channel: str, *args) -> Any:
        """
        执行 IPC 通信
        
        Args:
            channel: IPC 通道名
            *args: 传递的参数
            
        Returns:
            IPC 调用结果
        """
        try:
            result = self.client.execute_script(f"""
                const {{ ipcRenderer }} = require('electron');
                return ipcRenderer.sendSync('{channel}', ...arguments);
            """, *args)
            return result
        except Exception as e:
            print(f"  IPC 调用失败: {e}")
            return None
    
    def get_local_storage(self) -> Dict[str, str]:
        """
        获取 LocalStorage 数据
        
        Returns:
            LocalStorage 数据字典
        """
        try:
            data = self.client.execute_script("""
                const items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            """)
            return data if data else {}
        except:
            return {}
    
    def set_local_storage(self, key: str, value: str):
        """
        设置 LocalStorage 数据
        
        Args:
            key: 键名
            value: 值
        """
        self.client.execute_script(f"""
            localStorage.setItem('{key}', '{value}');
        """)
    
    def clear_local_storage(self):
        """清除 LocalStorage"""
        self.client.execute_script("localStorage.clear();")
    
    def get_cookies(self) -> List[Dict]:
        """
        获取应用 Cookie
        
        Returns:
            Cookie 列表
        """
        try:
            cookies = self.client.execute_script("""
                return document.cookie.split(';').map(c => {
                    const [name, value] = c.trim().split('=');
                    return {{ name, value }};
                });
            """)
            return cookies if cookies else []
        except:
            return []
    
    def take_screenshot(self, filename: str = "electron_screenshot.png") -> str:
        """
        截取应用截图
        
        Args:
            filename: 保存文件名
            
        Returns:
            截图文件路径
        """
        filepath = f"screenshots/{filename}"
        os.makedirs("screenshots", exist_ok=True)
        
        self.client.screenshot(filepath, full_page=True)
        print(f"  截图已保存: {filepath}")
        return filepath
    
    def wait_for_element(self, selector: str, timeout: int = 10000):
        """
        等待元素出现
        
        Args:
            selector: CSS 选择器
            timeout: 超时时间（毫秒）
        """
        return self.client.wait_for_element(selector, timeout=timeout)
    
    def click_menu_item(self, menu_text: str) -> bool:
        """
        点击菜单项
        
        Args:
            menu_text: 菜单文本
            
        Returns:
            点击是否成功
        """
        try:
            # 尝试多种常见菜单选择器
            selectors = [
                f"[role='menuitem']:has-text('{menu_text}')",
                f".menu-item:contains('{menu_text}')",
                f"[data-menu='{menu_text}']",
                f"text='{menu_text}'"
            ]
            
            for selector in selectors:
                try:
                    self.client.click(selector)
                    print(f"  点击菜单: {menu_text}")
                    return True
                except:
                    continue
            
            return False
        except:
            return False
    
    def fill_form(self, form_data: Dict[str, str]) -> bool:
        """
        填写表单
        
        Args:
            form_data: 表单数据字典 {选择器: 值}
            
        Returns:
            填写是否成功
        """
        try:
            for selector, value in form_data.items():
                self.client.type(selector, value)
                print(f"  填写 {selector}: {value}")
            return True
        except Exception as e:
            print(f"  填写表单失败: {e}")
            return False
    
    def get_console_logs(self) -> List[str]:
        """
        获取控制台日志
        
        Returns:
            日志列表
        """
        # 注意：需要在连接前启用日志收集
        return []


def example_basic_connection():
    """基础连接示例"""
    print("=" * 60)
    print("示例 1: 连接到 Electron 应用")
    print("=" * 60)
    
    # 创建控制器（默认端口 9223）
    controller = ElectronController(debug_port=9223)
    
    try:
        # 连接
        if controller.connect():
            # 获取应用信息
            info = controller.get_app_info()
            if info:
                print(f"\n  应用信息:")
                print(f"    名称: {info.name}")
                print(f"    Electron 版本: {info.electron_version}")
                print(f"    Chrome 版本: {info.chrome_version}")
                print(f"    Node 版本: {info.node_version}")
    finally:
        controller.disconnect()
    
    print()


def example_form_interaction():
    """表单交互示例"""
    print("=" * 60)
    print("示例 2: Electron 表单交互")
    print("=" * 60)
    
    controller = ElectronController(debug_port=9223)
    
    try:
        if controller.connect():
            # 等待表单加载
            controller.wait_for_element("form", timeout=5000)
            print("✓ 表单已加载")
            
            # 填写表单
            form_data = {
                "#username": "testuser",
                "#email": "test@example.com",
                "#password": "testpass123"
            }
            controller.fill_form(form_data)
            
            # 选择下拉选项
            controller.client.execute_script("""
                document.querySelector('#role').value = 'admin';
            """)
            print("✓ 选择角色: admin")
            
            # 勾选复选框
            controller.client.click("#agree-terms")
            print("✓ 勾选同意条款")
            
            # 提交表单
            controller.client.click("button[type='submit']")
            print("✓ 提交表单")
            
            # 等待提交完成
            controller.wait_for_element(".success-message", timeout=10000)
            print("✓ 表单提交成功")
    finally:
        controller.disconnect()
    
    print()


def example_data_extraction():
    """数据提取示例"""
    print("=" * 60)
    print("示例 3: 从 Electron 应用提取数据")
    print("=" * 60)
    
    controller = ElectronController(debug_port=9223)
    
    try:
        if controller.connect():
            # 获取 LocalStorage 数据
            storage = controller.get_local_storage()
            print(f"\n  LocalStorage 数据 ({len(storage)} 项):")
            for key, value in list(storage.items())[:5]:
                print(f"    {key}: {value[:50]}...")
            
            # 获取 Cookie
            cookies = controller.get_cookies()
            print(f"\n  Cookie ({len(cookies)} 个):")
            for cookie in cookies[:3]:
                print(f"    {cookie.get('name', 'N/A')}: {cookie.get('value', 'N/A')}")
            
            # 执行 JavaScript 提取数据
            user_data = controller.client.execute_script("""
                // 假设应用将用户数据存储在全局变量中
                return window.userData || null;
            """)
            
            if user_data:
                print(f"\n  用户数据:")
                print(f"    {json.dumps(user_data, indent=2, ensure_ascii=False)}")
    finally:
        controller.disconnect()
    
    print()


def example_menu_navigation():
    """菜单导航示例"""
    print("=" * 60)
    print("示例 4: Electron 菜单导航")
    print("=" * 60)
    
    controller = ElectronController(debug_port=9223)
    
    try:
        if controller.connect():
            # 点击菜单项
            menu_items = ["File", "Edit", "View", "Settings"]
            
            for item in menu_items:
                if controller.click_menu_item(item):
                    time.sleep(0.5)  # 等待菜单动画
                    
                    # 截图记录
                    controller.take_screenshot(f"menu_{item.lower()}.png")
    finally:
        controller.disconnect()
    
    print()


def example_ipc_communication():
    """IPC 通信示例"""
    print("=" * 60)
    print("示例 5: IPC 通信")
    print("=" * 60)
    
    controller = ElectronController(debug_port=9223)
    
    try:
        if controller.connect():
            # 通过 IPC 获取应用配置
            config = controller.execute_ipc("get-app-config")
            if config:
                print(f"\n  应用配置:")
                print(f"    {json.dumps(config, indent=2, ensure_ascii=False)}")
            
            # 通过 IPC 触发操作
            result = controller.execute_ipc("perform-action", "save-data")
            if result:
                print(f"\n  操作结果: {result}")
            
            # 发送事件到主进程
            controller.client.execute_script("""
                const { ipcRenderer } = require('electron');
                ipcRenderer.send('user-action', { type: 'test', timestamp: Date.now() });
            """)
            print("✓ 已发送 IPC 事件")
    finally:
        controller.disconnect()
    
    print()


def example_automated_testing():
    """自动化测试示例"""
    print("=" * 60)
    print("示例 6: Electron 自动化测试")
    print("=" * 60)
    
    controller = ElectronController(debug_port=9223)
    test_results = []
    
    try:
        if controller.connect():
            # 测试 1: 检查应用是否加载
            try:
                controller.wait_for_element("#app", timeout=5000)
                test_results.append(("应用加载", "通过"))
            except:
                test_results.append(("应用加载", "失败"))
            
            # 测试 2: 检查导航菜单
            try:
                menu = controller.client.find_elements(".nav-item")
                test_results.append(("导航菜单", f"通过 ({len(menu)} 项)"))
            except:
                test_results.append(("导航菜单", "失败"))
            
            # 测试 3: 表单验证
            try:
                controller.client.click("#submit")
                error = controller.client.wait_for_element(".error-message", timeout=3000)
                test_results.append(("表单验证", "通过"))
            except:
                test_results.append(("表单验证", "失败"))
            
            # 测试 4: 截图对比
            controller.take_screenshot("test_screenshot.png")
            test_results.append(("截图", "已保存"))
            
            # 输出测试结果
            print("\n  测试结果:")
            for test, result in test_results:
                status = "✓" if "通过" in result or "已保存" in result else "✗"
                print(f"    {status} {test}: {result}")
    finally:
        controller.disconnect()
    
    print()


def example_multi_window():
    """多窗口处理示例"""
    print("=" * 60)
    print("示例 7: 多窗口处理")
    print("=" * 60)
    
    controller = ElectronController(debug_port=9223)
    
    try:
        if controller.connect():
            # 获取所有窗口
            windows = controller.get_window_handles()
            print(f"\n  检测到 {len(windows)} 个窗口")
            
            # 遍历每个窗口
            for i, handle in enumerate(windows):
                print(f"\n  窗口 {i + 1}:")
                controller.switch_to_window(handle)
                
                # 获取窗口信息
                title = controller.client.get_title()
                url = controller.client.get_url()
                
                print(f"    标题: {title}")
                print(f"    URL: {url}")
                
                # 截图
                controller.take_screenshot(f"window_{i + 1}.png")
    finally:
        controller.disconnect()
    
    print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("OpenCLI Electron 应用控制示例")
    print("=" * 60)
    print("\n启动 Electron 应用时添加调试参数:")
    print("  electron . --remote-debugging-port=9223")
    print()
    
    # 运行示例
    example_basic_connection()
    example_form_interaction()
    example_data_extraction()
    example_menu_navigation()
    example_ipc_communication()
    example_automated_testing()
    example_multi_window()
    
    print("=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)
    print("\nElectron 控制最佳实践:")
    print("1. 确保 Electron 应用启用远程调试")
    print("2. 使用 wait_for_element() 等待页面加载")
    print("3. 处理 IPC 通信时注意主进程和渲染进程的区别")
    print("4. 使用截图功能记录测试过程")
    print("5. 定期清理 LocalStorage 和 Cookie 避免状态污染")


if __name__ == "__main__":
    main()
