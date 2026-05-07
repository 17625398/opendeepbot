"""DeepTutor Channels Gateway

Starts all configured chat channels and connects them to the agent.
"""

import asyncio
import logging
import os
from typing import Dict

from deeptutor.channels import (
    ChannelManager,
    TelegramChannel,
    DiscordChannel,
    WebSocketChannel,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("channels.gateway")


def load_config() -> Dict:
    """Load channel configuration from environment variables"""
    return {
        "telegram": {
            "enabled": os.environ.get("TELEGRAM_ENABLED", "false").lower() == "true",
            "token": os.environ.get("TELEGRAM_TOKEN"),
            "name": "telegram"
        },
        "discord": {
            "enabled": os.environ.get("DISCORD_ENABLED", "false").lower() == "true",
            "token": os.environ.get("DISCORD_TOKEN"),
            "prefix": os.environ.get("DISCORD_PREFIX", "!"),
            "name": "discord"
        },
        "websocket": {
            "enabled": os.environ.get("WEBSOCKET_ENABLED", "true").lower() == "true",
            "host": os.environ.get("WEBSOCKET_HOST", "localhost"),
            "port": int(os.environ.get("WEBSOCKET_PORT", "8765")),
            "name": "websocket"
        }
    }


async def main():
    """Main entry point for channels gateway"""
    logger.info("Starting DeepTutor Channels Gateway...")
    
    # Load configuration
    config = load_config()
    logger.info(f"Loaded config: {list(config.keys())}")
    
    # Create channel manager
    channel_manager = ChannelManager(config)
    
    # Register channels
    if config["telegram"]["enabled"]:
        channel_manager.register_channel(TelegramChannel(config["telegram"]))
    
    if config["discord"]["enabled"]:
        channel_manager.register_channel(DiscordChannel(config["discord"]))
    
    if config["websocket"]["enabled"]:
        channel_manager.register_channel(WebSocketChannel(config["websocket"]))
    
    # Set message handler
    async def handle_message(message: Dict):
        """Handle incoming messages from any channel"""
        logger.info(f"Received message from {message['channel']}: "
                    f"user={message['user_id']}, message={message['message'][:50]}...")
        
        # Here you would connect to the agent and get a response
        # For now, just log the message
        channel_name = message["channel"]
        user_id = message["user_id"]
        
        # Example: Send a response back
        response = f"Received your message: {message['message'][:30]}..."
        await channel_manager.send_message(channel_name, user_id, response)
    
    channel_manager.set_message_handler(handle_message)
    
    # Start channels
    await channel_manager.start()
    
    # Keep running
    logger.info("Channels gateway started. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Shutting down channels gateway...")
        await channel_manager.stop()


if __name__ == "__main__":
    asyncio.run(main())