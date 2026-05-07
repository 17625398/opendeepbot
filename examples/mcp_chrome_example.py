"""
MCP Chrome Integration Examples

This module demonstrates how to use MCP Chrome integration with DeepTutor.
"""

import asyncio
from typing import Dict, Any, List

from src.integrations.mcp.chrome import (
    MCPChromeClient,
    MCPChromeConfig,
    MCPChromeAdapter,
    ConnectionType,
)
from src.integrations.mcp.chrome.tools import (
    BrowserManagementTools,
    ScreenshotTools,
    NetworkTools,
    ContentAnalysisTools,
    InteractionTools,
    DataManagementTools,
)


async def basic_navigation_example():
    """
    Basic browser navigation example.
    
    Demonstrates:
    - Connecting to MCP Chrome Server
    - Navigating to a URL
    - Taking a screenshot
    - Extracting page content
    """
    print("=== Basic Navigation Example ===")
    
    config = MCPChromeConfig(
        connection_type=ConnectionType.STREAMABLE_HTTP,
        http_url="http://127.0.0.1:12306/mcp",
        timeout=30
    )
    
    async with MCPChromeAdapter(config) as adapter:
        print("Connected to MCP Chrome Server")
        
        print("\n1. Navigating to example.com...")
        result = await adapter.browser.navigate("https://example.com")
        print(f"   Navigation result: {result.success}")
        
        print("\n2. Taking a screenshot...")
        screenshot_data = await adapter.screenshot.capture(full_page=True)
        if screenshot_data:
            with open("example_screenshot.png", "wb") as f:
                f.write(screenshot_data)
            print("   Screenshot saved to example_screenshot.png")
        
        print("\n3. Extracting page content...")
        content = await adapter.content.get_content(format="text")
        print(f"   Page title: {content.get('title', 'N/A')}")
        print(f"   Content length: {len(content.get('content', ''))} characters")


async def semantic_search_example():
    """
    Semantic search across browser tabs example.
    
    Demonstrates:
    - Listing all open tabs
    - Performing semantic search across tabs
    - Finding relevant content
    """
    print("\n=== Semantic Search Example ===")
    
    config = MCPChromeConfig.from_env()
    
    async with MCPChromeAdapter(config) as adapter:
        print("Listing all tabs...")
        tabs = await adapter.browser.get_windows_and_tabs()
        print(f"Found {len(tabs.get('windows', []))} windows")
        
        print("\nPerforming semantic search for 'AI agent'...")
        results = await adapter.content.semantic_search(
            query="AI agent automation",
            top_k=5
        )
        
        print(f"\nFound {len(results)} relevant results:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.get('title', 'Untitled')}")
            print(f"     URL: {result.get('url', 'N/A')}")
            print(f"     Score: {result.get('score', 0):.2f}")


async def form_automation_example():
    """
    Form automation example.
    
    Demonstrates:
    - Navigating to a form page
    - Filling form fields
    - Clicking buttons
    - Handling form submission
    """
    print("\n=== Form Automation Example ===")
    
    config = MCPChromeConfig.from_env()
    
    async with MCPChromeAdapter(config) as adapter:
        print("Navigating to form page...")
        await adapter.browser.navigate("https://httpbin.org/forms/post")
        
        print("\nFilling form fields...")
        
        await adapter.interaction.fill(
            selector="input[name='custname']",
            value="Test User"
        )
        print("  - Filled customer name")
        
        await adapter.interaction.fill(
            selector="input[name='custtel']",
            value="1234567890"
        )
        print("  - Filled phone number")
        
        await adapter.interaction.fill(
            selector="input[name='custemail']",
            value="test@example.com"
        )
        print("  - Filled email")
        
        await adapter.interaction.fill(
            selector="textarea[name='comments']",
            value="This is an automated test submission."
        )
        print("  - Filled comments")
        
        print("\nSubmitting form...")
        await adapter.interaction.click("button[type='submit']")
        
        print("Waiting for response...")
        await asyncio.sleep(2)
        
        content = await adapter.content.get_content(format="text")
        print("Response received!")
        print(content.get('content', '')[:500])


async def network_monitoring_example():
    """
    Network monitoring example.
    
    Demonstrates:
    - Starting network capture
    - Performing actions that trigger network requests
    - Analyzing captured requests
    """
    print("\n=== Network Monitoring Example ===")
    
    config = MCPChromeConfig.from_env()
    
    async with MCPChromeAdapter(config) as adapter:
        print("Starting network debugger...")
        await adapter.network.start_debugger()
        
        print("Navigating and performing actions...")
        await adapter.browser.navigate("https://jsonplaceholder.typicode.com")
        await asyncio.sleep(2)
        
        print("Stopping network debugger and analyzing requests...")
        requests = await adapter.network.stop_debugger()
        
        print(f"\nCaptured {len(requests)} network requests:")
        for req in requests[:10]:
            print(f"  - {req.get('method', 'GET')} {req.get('url', 'N/A')}")
            if req.get('response_body'):
                print(f"    Response size: {len(req['response_body'])} bytes")


async def history_and_bookmarks_example():
    """
    History and bookmarks management example.
    
    Demonstrates:
    - Searching browser history
    - Managing bookmarks
    """
    print("\n=== History and Bookmarks Example ===")
    
    config = MCPChromeConfig.from_env()
    
    async with MCPChromeAdapter(config) as adapter:
        print("Searching browser history for 'github'...")
        history = await adapter.data.search_history(
            query="github",
            max_results=10
        )
        
        print(f"\nFound {len(history)} history items:")
        for item in history[:5]:
            print(f"  - {item.get('title', 'Untitled')}")
            print(f"    URL: {item.get('url', 'N/A')}")
            print(f"    Visited: {item.get('lastVisitTime', 'N/A')}")
        
        print("\nSearching bookmarks...")
        bookmarks = await adapter.data.search_bookmarks("AI")
        
        print(f"\nFound {len(bookmarks)} bookmarks:")
        for bm in bookmarks[:5]:
            print(f"  - {bm.get('title', 'Untitled')}")
            print(f"    URL: {bm.get('url', 'N/A')}")


async def pipeline_automation_example():
    """
    Pipeline automation example using OpenHarness integration.
    
    Demonstrates:
    - Creating a pipeline of browser actions
    - Executing the pipeline
    - Collecting results
    """
    print("\n=== Pipeline Automation Example ===")
    
    from src.integrations.mcp.chrome.adapter import (
        MCPChromePipelineIntegration,
        quick_automation
    )
    
    config = MCPChromeConfig.from_env()
    
    async with MCPChromeAdapter(config) as adapter:
        pipeline = MCPChromePipelineIntegration(adapter)
        
        steps = MCPChromePipelineIntegration.create_pipeline_steps(
            url="https://example.com",
            actions=[
                {"type": "screenshot", "options": {"full_page": True}},
                {"type": "extract", "options": {"format": "text"}},
            ]
        )
        
        print("Executing pipeline steps...")
        results = []
        for step in steps:
            if step.get("type") == "tool":
                result = await pipeline.execute_step(step)
                results.append(result)
                print(f"  - {step['tool']}: {'success' if result['success'] else 'failed'}")
        
        print(f"\nPipeline completed with {len(results)} results")


async def case_investigation_example():
    """
    Case investigation workflow example for law enforcement scenarios.
    
    Demonstrates:
    - Collecting evidence from web pages
    - Cross-tab content analysis
    - Network request analysis
    - Screenshot documentation
    """
    print("\n=== Case Investigation Example ===")
    
    config = MCPChromeConfig.from_env()
    
    async with MCPChromeAdapter(config) as adapter:
        target_url = "https://example.com"
        
        print(f"Investigating: {target_url}")
        
        await adapter.browser.navigate(target_url)
        
        print("\n1. Capturing page screenshot...")
        screenshot = await adapter.screenshot.capture(full_page=True)
        if screenshot:
            evidence_path = f"evidence_screenshot_{target_url.replace('://', '_').replace('/', '_')}.png"
            with open(evidence_path, "wb") as f:
                f.write(screenshot)
            print(f"   Saved: {evidence_path}")
        
        print("\n2. Extracting page content...")
        content = await adapter.content.get_content(
            format="markdown",
            include_metadata=True
        )
        
        evidence = {
            "url": target_url,
            "title": content.get("title"),
            "metadata": content.get("metadata"),
            "content": content.get("content"),
            "links": content.get("links", []),
            "timestamp": content.get("timestamp")
        }
        
        print(f"   Title: {evidence['title']}")
        print(f"   Content length: {len(evidence['content'] or '')} characters")
        print(f"   Links found: {len(evidence['links'])}")
        
        print("\n3. Capturing network activity...")
        await adapter.network.start_debugger()
        await asyncio.sleep(1)
        requests = await adapter.network.stop_debugger()
        
        api_calls = [
            r for r in requests
            if 'api' in r.get('url', '').lower()
        ]
        print(f"   Total requests: {len(requests)}")
        print(f"   API calls: {len(api_calls)}")
        
        print("\n4. Searching for related content across tabs...")
        related = await adapter.content.semantic_search(
            query="related information",
            top_k=5
        )
        print(f"   Found {len(related)} potentially related pages")
        
        print("\nInvestigation complete!")
        return evidence


async def main():
    """Run all examples."""
    print("=" * 60)
    print("MCP Chrome Integration Examples")
    print("=" * 60)
    
    try:
        await basic_navigation_example()
        await semantic_search_example()
        await form_automation_example()
        await network_monitoring_example()
        await history_and_bookmarks_example()
        await pipeline_automation_example()
        await case_investigation_example()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure MCP Chrome Server is running:")
        print("  1. Install: npm install -g mcp-chrome-bridge")
        print("  2. Load Chrome extension from GitHub releases")
        print("  3. Extension will start server on http://127.0.0.1:12306")


if __name__ == "__main__":
    asyncio.run(main())
