#!/usr/bin/env python3
"""
DeepTutor 通道系统示例

演示如何使用多平台聊天通道：
- WebSocket 网关
- 通道管理器
- 消息处理
"""

import asyncio
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("channels_demo")


async def example_channel_manager():
    """示例 1: 通道管理器"""
    logger.info("=" * 60)
    logger.info("示例 1: 通道管理器")
    logger.info("=" * 60)
    
    from deeptutor.channels import ChannelManager
    
    # 创建通道管理器
    manager = ChannelManager({})
    
    # 列出可用通道
    logger.info(f"已注册通道: {manager.list_channels()}")
    
    # 注意：实际通道需要先初始化


async def example_websocket_channel():
    """示例 2: WebSocket 通道 (概念演示)"""
    logger.info("=" * 60)
    logger.info("示例 2: WebSocket 通道 (概念演示)")
    logger.info("=" * 60)
    
    logger.info("WebSocket 通道功能:")
    logger.info("1. 实时双向通信")
    logger.info("2. 支持多个客户端连接")
    logger.info("3. 可与 WebUI 集成")


async def example_message_routing():
    """示例 3: 消息路由"""
    logger.info("=" * 60)
    logger.info("示例 3: 消息路由")
    logger.info("=" * 60)
    
    logger.info("消息路由功能:")
    logger.info("1. 统一的消息处理接口")
    logger.info("2. 消息广播到多个通道")
    logger.info("3. 权限控制 (allow_from)")


async def example_health_check():
    """示例 4: 健康检查"""
    logger.info("=" * 60)
    logger.info("示例 4: 健康检查")
    logger.info("=" * 60)
    
    from deeptutor.channels import ChannelManager
    
    manager = ChannelManager({})
    
    # 注意：需要先初始化通道才能进行完整的健康检查
    logger.info("健康检查功能:")
    logger.info("1. 检查通道连接状态")
    logger.info("2. 获取统计信息")
    logger.info("3. 整体系统健康状况")


async def main():
    """运行所有示例"""
    logger.info("=" * 60)
    logger.info("DeepTutor 通道系统示例")
    logger.info("=" * 60)
    
    try:
        await example_channel_manager()
        print()
        
        await example_websocket_channel()
        print()
        
        await example_message_routing()
        print()
        
        await example_health_check()
        print()
        
        logger.info("=" * 60)
        logger.info("如何运行实际的通道网关:")
        logger.info("=" * 60)
        logger.info("1. 复制 .env.example 到 .env")
        logger.info("2. 配置需要的通道 (TELEGRAM_TOKEN, DISCORD_TOKEN, etc.)")
        logger.info("3. 运行: python scripts/start_channels.py")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"执行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())