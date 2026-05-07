"""
OpenCLI 适配器使用示例

此示例展示了如何创建和使用适配器来简化特定网站的自动化操作。
适配器模式允许你将常用的网站操作封装成可重用的组件。

适配器优势：
- 代码复用：封装常用操作
- 易于维护：网站结构变化时只需修改适配器
- 更好的抽象：隐藏底层实现细节
- 可测试性：便于单元测试
"""

import os
import sys
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

# 将项目根目录添加到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 模拟 opencli 导入
try:
    from opencli import OpenCLI
    from opencli.exceptions import ConnectionError, ElementNotFoundError, TimeoutError
except ImportError:
    print("警告: opencli 包未安装。这是一个示例代码。\n")
    
    class MockOpenCLI:
        def __init__(self, **kwargs):
            self._connected = False
        
        def connect(self):
            self._connected = True
            return True
        
        def disconnect(self):
            self._connected = False
        
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
            return [{}, {}, {}]
        
        def wait_for_element(self, selector, by="css", timeout=None):
            print(f"  [等待] {selector}")
            return {}
        
        def execute_script(self, script, *args):
            return None
    
    OpenCLI = MockOpenCLI
    ConnectionError = Exception
    ElementNotFoundError = Exception
    TimeoutError = Exception


# ============================================================================
# 基础适配器类
# ============================================================================

class BaseAdapter(ABC):
    """
    OpenCLI 适配器基类
    
    所有特定网站的适配器都应该继承此类。
    """
    
    def __init__(self, client: OpenCLI):
        """
        初始化适配器
        
        Args:
            client: OpenCLI 客户端实例
        """
        self.client = client
        self.base_url = ""
        self._logged_in = False
    
    def navigate_to_base(self):
        """导航到基础 URL"""
        if self.base_url:
            self.client.navigate(self.base_url)
    
    @abstractmethod
    def login(self, username: str, password: str) -> bool:
        """
        登录方法（子类必须实现）
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            登录是否成功
        """
        pass
    
    def is_logged_in(self) -> bool:
        """
        检查是否已登录
        
        Returns:
            是否已登录
        """
        return self._logged_in
    
    def logout(self) -> bool:
        """
        登出
        
        Returns:
            登出是否成功
        """
        self._logged_in = False
        return True


# ============================================================================
# GitHub 适配器示例
# ============================================================================

class GitHubAdapter(BaseAdapter):
    """
    GitHub 适配器
    
    封装 GitHub 网站的常用操作。
    """
    
    def __init__(self, client: OpenCLI):
        super().__init__(client)
        self.base_url = "https://github.com"
    
    def login(self, username: str, password: str) -> bool:
        """
        登录 GitHub
        
        Args:
            username: GitHub 用户名或邮箱
            password: GitHub 密码
            
        Returns:
            登录是否成功
        """
        print(f"  正在登录 GitHub: {username}")
        
        # 导航到登录页面
        self.client.navigate(f"{self.base_url}/login")
        
        # 输入用户名
        self.client.type("#login_field", username)
        
        # 输入密码
        self.client.type("#password", password)
        
        # 点击登录按钮
        self.client.click("input[name='commit']")
        
        # 等待登录完成（检查头像是否存在）
        try:
            self.client.wait_for_element(".avatar", timeout=10000)
            self._logged_in = True
            print("  ✓ GitHub 登录成功")
            return True
        except TimeoutError:
            print("  ✗ GitHub 登录失败")
            return False
    
    def search_repositories(self, query: str) -> List[Dict[str, Any]]:
        """
        搜索仓库
        
        Args:
            query: 搜索关键词
            
        Returns:
            仓库列表
        """
        print(f"  搜索仓库: {query}")
        
        # 导航到搜索页面
        self.client.navigate(f"{self.base_url}/search?q={query}&type=repositories")
        
        # 等待结果加载
        self.client.wait_for_element(".repo-list", timeout=10000)
        
        # 获取仓库列表
        repos = []
        items = self.client.find_elements(".repo-list-item")
        
        for item in items[:10]:  # 只获取前 10 个
            try:
                name = self.client.get_text("a.v-align-middle")
                desc = self.client.get_text("p.col-12")
                
                repos.append({
                    "name": name,
                    "description": desc,
                    "url": f"{self.base_url}/{name}"
                })
            except:
                continue
        
        print(f"  ✓ 找到 {len(repos)} 个仓库")
        return repos
    
    def get_user_profile(self, username: str) -> Dict[str, Any]:
        """
        获取用户资料
        
        Args:
            username: GitHub 用户名
            
        Returns:
            用户信息字典
        """
        print(f"  获取用户资料: {username}")
        
        self.client.navigate(f"{self.base_url}/{username}")
        
        # 等待页面加载
        self.client.wait_for_element(".vcard-names", timeout=10000)
        
        profile = {}
        
        try:
            profile["name"] = self.client.get_text(".vcard-fullname")
        except:
            profile["name"] = ""
        
        try:
            profile["bio"] = self.client.get_text(".user-profile-bio")
        except:
            profile["bio"] = ""
        
        try:
            profile["location"] = self.client.get_text("[itemprop='homeLocation']")
        except:
            profile["location"] = ""
        
        print(f"  ✓ 获取资料成功: {profile.get('name', 'N/A')}")
        return profile


# ============================================================================
# 搜索引擎适配器示例
# ============================================================================

class SearchEngineAdapter(BaseAdapter):
    """
    通用搜索引擎适配器
    
    支持多个搜索引擎：Google、Bing、DuckDuckGo
    """
    
    ENGINES = {
        "google": "https://www.google.com",
        "bing": "https://www.bing.com",
        "duckduckgo": "https://duckduckgo.com"
    }
    
    def __init__(self, client: OpenCLI, engine: str = "google"):
        super().__init__(client)
        self.engine = engine.lower()
        self.base_url = self.ENGINES.get(self.engine, self.ENGINES["google"])
    
    def login(self, username: str, password: str) -> bool:
        """搜索引擎通常不需要登录"""
        print(f"  {self.engine} 不需要登录")
        return True
    
    def search(self, query: str) -> List[Dict[str, str]]:
        """
        执行搜索
        
        Args:
            query: 搜索关键词
            
        Returns:
            搜索结果列表
        """
        print(f"  在 {self.engine} 搜索: {query}")
        
        if self.engine == "google":
            return self._search_google(query)
        elif self.engine == "bing":
            return self._search_bing(query)
        elif self.engine == "duckduckgo":
            return self._search_duckduckgo(query)
        else:
            return []
    
    def _search_google(self, query: str) -> List[Dict[str, str]]:
        """Google 搜索实现"""
        self.client.navigate(f"{self.base_url}/search?q={query}")
        self.client.wait_for_element("#search", timeout=10000)
        
        results = []
        items = self.client.find_elements(".g")
        
        for item in items[:10]:
            try:
                title = self.client.get_text("h3")
                url = self.client.execute_script("""
                    return arguments[0].querySelector('a').href;
                "", item)
                
                results.append({
                    "title": title,
                    "url": url,
                    "engine": "google"
                })
            except:
                continue
        
        return results
    
    def _search_bing(self, query: str) -> List[Dict[str, str]]:
        """Bing 搜索实现"""
        self.client.navigate(f"{self.base_url}/search?q={query}")
        self.client.wait_for_element("#b_content", timeout=10000)
        
        results = []
        items = self.client.find_elements(".b_algo")
        
        for item in items[:10]:
            try:
                title = self.client.get_text("h2")
                url = self.client.get_text("cite")
                
                results.append({
                    "title": title,
                    "url": url,
                    "engine": "bing"
                })
            except:
                continue
        
        return results
    
    def _search_duckduckgo(self, query: str) -> List[Dict[str, str]]:
        """DuckDuckGo 搜索实现"""
        self.client.navigate(f"{self.base_url}/?q={query}")
        self.client.wait_for_element(".results", timeout=10000)
        
        results = []
        items = self.client.find_elements(".result")
        
        for item in items[:10]:
            try:
                title = self.client.get_text(".result__a")
                url = self.client.get_text(".result__url")
                
                results.append({
                    "title": title,
                    "url": url,
                    "engine": "duckduckgo"
                })
            except:
                continue
        
        return results


# ============================================================================
# 电商网站适配器示例
# ============================================================================

class ECommerceAdapter(BaseAdapter):
    """
    电商网站通用适配器
    
    可以扩展为特定网站的适配器（如 Amazon、淘宝等）
    """
    
    def __init__(self, client: OpenCLI, site: str = "generic"):
        super().__init__(client)
        self.site = site
        self.cart = []
    
    def login(self, username: str, password: str) -> bool:
        """登录电商网站"""
        print(f"  登录 {self.site}: {username}")
        # 具体实现取决于网站
        self._logged_in = True
        return True
    
    def search_products(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索商品
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            商品列表
        """
        print(f"  搜索商品: {keyword}")
        # 模拟返回商品数据
        return [
            {"name": f"{keyword} 商品 1", "price": 99.99, "rating": 4.5},
            {"name": f"{keyword} 商品 2", "price": 149.99, "rating": 4.2},
            {"name": f"{keyword} 商品 3", "price": 79.99, "rating": 4.8},
        ]
    
    def add_to_cart(self, product_id: str, quantity: int = 1) -> bool:
        """
        添加商品到购物车
        
        Args:
            product_id: 商品 ID
            quantity: 数量
            
        Returns:
            是否成功
        """
        print(f"  添加商品到购物车: {product_id} x {quantity}")
        self.cart.append({"product_id": product_id, "quantity": quantity})
        return True
    
    def get_cart_total(self) -> float:
        """
        获取购物车总价
        
        Returns:
            总价
        """
        # 模拟计算
        total = sum(item["quantity"] * 99.99 for item in self.cart)
        print(f"  购物车总价: ¥{total:.2f}")
        return total
    
    def checkout(self) -> bool:
        """结算购物车"""
        print(f"  结算购物车，共 {len(self.cart)} 件商品")
        self.cart = []
        return True


# ============================================================================
# 示例使用代码
# ============================================================================

def example_github_adapter():
    """GitHub 适配器示例"""
    print("=" * 60)
    print("示例 1: GitHub 适配器")
    print("=" * 60)
    
    client = OpenCLI()
    
    try:
        client.connect()
        
        # 创建 GitHub 适配器
        github = GitHubAdapter(client)
        
        # 登录
        github.login("your_username", "your_password")
        
        if github.is_logged_in():
            # 搜索仓库
            repos = github.search_repositories("machine learning")
            print(f"\n  搜索结果:")
            for repo in repos[:3]:
                print(f"    - {repo.get('name', 'N/A')}")
            
            # 获取用户资料
            profile = github.get_user_profile("torvalds")
            print(f"\n  用户资料:")
            print(f"    名称: {profile.get('name', 'N/A')}")
            print(f"    简介: {profile.get('bio', 'N/A')}")
        
    finally:
        if client.is_connected():
            client.disconnect()
    
    print()


def example_search_engine_adapter():
    """搜索引擎适配器示例"""
    print("=" * 60)
    print("示例 2: 搜索引擎适配器")
    print("=" * 60)
    
    client = OpenCLI()
    
    try:
        client.connect()
        
        # 创建搜索引擎适配器
        search = SearchEngineAdapter(client, engine="google")
        
        # 执行搜索
        results = search.search("OpenAI GPT-4")
        
        print(f"\n  搜索结果 ({len(results)} 条):")
        for i, result in enumerate(results[:5], 1):
            print(f"    {i}. {result.get('title', 'N/A')}")
            print(f"       {result.get('url', 'N/A')}")
        
    finally:
        if client.is_connected():
            client.disconnect()
    
    print()


def example_ecommerce_adapter():
    """电商适配器示例"""
    print("=" * 60)
    print("示例 3: 电商适配器")
    print("=" * 60)
    
    client = OpenCLI()
    
    try:
        client.connect()
        
        # 创建电商适配器
        shop = ECommerceAdapter(client, site="ExampleShop")
        
        # 登录
        shop.login("user@example.com", "password")
        
        # 搜索商品
        products = shop.search_products("无线耳机")
        print(f"\n  找到 {len(products)} 件商品:")
        for p in products:
            print(f"    - {p['name']}: ¥{p['price']} (评分: {p['rating']})")
        
        # 添加商品到购物车
        if products:
            shop.add_to_cart("PROD001", quantity=2)
            shop.add_to_cart("PROD002", quantity=1)
        
        # 查看购物车
        total = shop.get_cart_total()
        
        # 结算
        shop.checkout()
        
    finally:
        if client.is_connected():
            client.disconnect()
    
    print()


def example_adapter_composition():
    """适配器组合示例"""
    print("=" * 60)
    print("示例 4: 适配器组合")
    print("=" * 60)
    
    client = OpenCLI()
    
    try:
        client.connect()
        
        # 使用多个适配器协同工作
        print("\n  场景: 搜索 GitHub 项目，然后在搜索引擎中查找相关文档")
        
        # 1. 使用 GitHub 适配器搜索项目
        github = GitHubAdapter(client)
        repos = github.search_repositories("react")
        
        if repos:
            target_repo = repos[0]
            print(f"\n  找到项目: {target_repo.get('name', 'N/A')}")
            
            # 2. 使用搜索引擎适配器查找文档
            search = SearchEngineAdapter(client, engine="google")
            docs = search.search(f"{target_repo.get('name', '')} documentation tutorial")
            
            print(f"\n  相关文档 ({len(docs)} 条):")
            for doc in docs[:3]:
                print(f"    - {doc.get('title', 'N/A')}")
        
    finally:
        if client.is_connected():
            client.disconnect()
    
    print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("OpenCLI 适配器使用示例")
    print("=" * 60 + "\n")
    
    example_github_adapter()
    example_search_engine_adapter()
    example_ecommerce_adapter()
    example_adapter_composition()
    
    print("=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)
    print("\n适配器开发最佳实践:")
    print("1. 继承 BaseAdapter 基类")
    print("2. 实现 login() 抽象方法")
    print("3. 使用 wait_for_element() 等待页面加载")
    print("4. 封装常用操作为独立方法")
    print("5. 添加适当的错误处理")
    print("6. 为每个适配器编写单元测试")


if __name__ == "__main__":
    main()
