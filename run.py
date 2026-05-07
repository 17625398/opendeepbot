#!/usr/bin/env python3
"""DeepTutor 统一聊天系统入口

一键启动所有配置的聊天通道。
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from deeptutor.config import load_config, validate_config
from deeptutor.channels import (
    ChannelManager,
    TelegramChannel,
    DiscordChannel,
    WeChatChannel,
    FeishuChannel,
    SlackChannel,
    EmailChannel,
    WebSocketChannel,
)
from deeptutor.llm.providers import LLMProvider
from deeptutor.agents.agent_loop import AgentLoop

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("deeptutor.main")


async def main():
    """主函数"""
    print("=" * 60)
    print("        DeepTutor - 多平台 AI 助手")
    print("=" * 60)
    
    # 加载并验证配置
    print("\n[1/4] 加载配置...")
    config = load_config()
    
    if not validate_config(config):
        print("\n❌ 配置验证失败！请检查您的 .env 文件。")
        sys.exit(1)
    
    print("✅ 配置加载完成")
    
    # 初始化 LLM
    print("\n[2/4] 初始化 LLM...")
    try:
        llm_provider = LLMProvider.from_env()
        llm_client = llm_provider.get_client()
        print(f"✅ LLM 初始化完成: {config.llm.provider} / {config.llm.model}")
    except Exception as e:
        print(f"❌ LLM 初始化失败: {e}")
        sys.exit(1)
    
    # 初始化 Agent
    agent = AgentLoop(
        llm_client=llm_client,
        max_iterations=10,
        yolo_mode=False,
        track_cost=True
    )
    
    # 初始化通道管理器
    print("\n[3/4] 初始化通道...")
    channel_manager = ChannelManager(config)
    
    # 注册通道
    enabled_channels = []
    
    if config.channels.get("telegram", {}).get("enabled", False):
        try:
            telegram_config = config.channels["telegram"]
            channel_manager.register_channel(TelegramChannel(telegram_config))
            enabled_channels.append("📱 Telegram")
        except Exception as e:
            logger.warning(f"Telegram 初始化失败: {e}")
    
    if config.channels.get("discord", {}).get("enabled", False):
        try:
            discord_config = config.channels["discord"]
            channel_manager.register_channel(DiscordChannel(discord_config))
            enabled_channels.append("🎮 Discord")
        except Exception as e:
            logger.warning(f"Discord 初始化失败: {e}")
    
    if config.channels.get("wechat", {}).get("enabled", False):
        try:
            wechat_config = config.channels["wechat"]
            channel_manager.register_channel(WeChatChannel(wechat_config))
            enabled_channels.append("💬 WeChat")
        except Exception as e:
            logger.warning(f"WeChat 初始化失败: {e}")
    
    if config.channels.get("feishu", {}).get("enabled", False):
        try:
            feishu_config = config.channels["feishu"]
            channel_manager.register_channel(FeishuChannel(feishu_config))
            enabled_channels.append("📌 Feishu")
        except Exception as e:
            logger.warning(f"Feishu 初始化失败: {e}")
    
    if config.channels.get("slack", {}).get("enabled", False):
        try:
            slack_config = config.channels["slack"]
            channel_manager.register_channel(SlackChannel(slack_config))
            enabled_channels.append("🟦 Slack")
        except Exception as e:
            logger.warning(f"Slack 初始化失败: {e}")
    
    if config.channels.get("email", {}).get("enabled", False):
        try:
            email_config = config.channels["email"]
            channel_manager.register_channel(EmailChannel(email_config))
            enabled_channels.append("📧 Email")
        except Exception as e:
            logger.warning(f"Email 初始化失败: {e}")
    
    if config.channels.get("websocket", {}).get("enabled", True):
        try:
            websocket_config = config.channels["websocket"]
            channel_manager.register_channel(WebSocketChannel(websocket_config))
            enabled_channels.append("🔌 WebSocket")
        except Exception as e:
            logger.warning(f"WebSocket 初始化失败: {e}")
    
    if not enabled_channels:
        print("⚠️ 没有启用任何通道！")
        print("请在 .env 文件中启用至少一个通道。")
        sys.exit(1)
    
    print(f"✅ 已启用 {len(enabled_channels)} 个通道:")
    for channel in enabled_channels:
        print(f"   - {channel}")
    
    # 设置消息处理器
    async def handle_message(message):
        """处理来自所有通道的消息"""
        try:
            logger.info(f"📨 [{message['channel']}] {message['user_id']}: {message['message'][:50]}...")
            
            # 发送输入状态
            await channel_manager.send_typing(message['channel'], message['user_id'])
            
            # 调用 Agent 处理
            response = await agent.run(message['message'])
            
            # 发送回复
            await channel_manager.send_message(
                message['channel'],
                message['user_id'],
                response
            )
            
            logger.info(f"✅ [{message['channel']}] 回复已发送")
            
            # 记录成本
            cost_info = agent.get_cost_info()
            if cost_info:
                logger.info(f"💰 本次请求成本: ${cost_info.get('total_cost', 0):.4f}")
                
        except Exception as e:
            logger.error(f"❌ 处理消息时出错: {e}")
            error_msg = f"抱歉，我遇到了一个问题: {str(e)}"
            await channel_manager.send_message(
                message['channel'],
                message['user_id'],
                error_msg
            )
    
    channel_manager.set_message_handler(handle_message)
    
    # 启动所有通道
    print("\n[4/4] 启动通道...")
    try:
        await channel_manager.start()
    except Exception as e:
        logger.error(f"启动通道失败: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🚀 DeepTutor 已启动！")
    print("=" * 60)
    print("\n按 Ctrl+C 停止服务\n")
    
    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\n停止中...")
        await channel_manager.stop()
        print("👋 再见！")


if __name__ == "__main__":
    asyncio.run(main())
