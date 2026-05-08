"""QQ Channel Integration

QQ 聊天通道实现，基于 Mirai 协议或其他 QQ 机器人框架。

Features:
- QQ 消息接收和发送
- 群聊和私聊支持
- 消息转发到 Agent
- 命令处理
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from deeptutor.channels.base import BaseChannel, Message

logger = logging.getLogger(__name__)


@dataclass
class QQConfig:
    """QQ 通道配置"""
    enabled: bool = False
    qq_number: str = ""
    password: str = ""
    bot_token: str = ""
    mirai_api_http_url: str = "http://localhost:8080"
    verify_key: str = ""
    auto_login: bool = True


class QQChannel(BaseChannel):
    """QQ 聊天通道"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "qq"
        self.config = QQConfig(**config)
        self._connected = False
        self._session_key = ""
        self._tasks: List[asyncio.Task] = []
    
    async def connect(self):
        """连接到 QQ"""
        if self._connected:
            logger.warning("QQ channel is already connected")
            return
        
        logger.info("Connecting to QQ...")
        
        try:
            # 尝试连接到 Mirai API HTTP
            if self.config.mirai_api_http_url and self.config.verify_key:
                await self._connect_mirai()
            else:
                logger.error("QQ configuration incomplete")
                return
            
            self._connected = True
            logger.info("QQ channel connected successfully")
            
            # 启动消息监听任务
            task = asyncio.create_task(self._message_listener())
            self._tasks.append(task)
            
        except Exception as e:
            logger.error(f"Failed to connect to QQ: {e}")
    
    async def _connect_mirai(self):
        """连接到 Mirai API HTTP"""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                # 验证连接
                response = await client.post(
                    f"{self.config.mirai_api_http_url}/verify",
                    json={"verifyKey": self.config.verify_key}
                )
                data = response.json()
                
                if "session" in data:
                    self._session_key = data["session"]
                    logger.info(f"Mirai session key obtained: {self._session_key[:10]}...")
                    
                    # 绑定 QQ 号
                    if self.config.qq_number:
                        await client.post(
                            f"{self.config.mirai_api_http_url}/bind",
                            json={"sessionKey": self._session_key, "qq": int(self.config.qq_number)}
                        )
                        logger.info(f"QQ {self.config.qq_number} bound successfully")
                else:
                    logger.error(f"Mirai verification failed: {data}")
                    
        except ImportError:
            logger.error("httpx is required for QQ channel")
        except Exception as e:
            logger.error(f"Mirai connection failed: {e}")
    
    async def disconnect(self):
        """断开连接"""
        logger.info("Disconnecting QQ channel...")
        
        # 取消所有任务
        for task in self._tasks:
            task.cancel()
        
        # 释放 Mirai 会话
        if self._session_key:
            try:
                import httpx
                
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{self.config.mirai_api_http_url}/release",
                        json={"sessionKey": self._session_key, "qq": int(self.config.qq_number)}
                    )
            except Exception as e:
                logger.warning(f"Failed to release Mirai session: {e}")
        
        self._connected = False
        logger.info("QQ channel disconnected")
    
    async def _message_listener(self):
        """监听 QQ 消息"""
        logger.info("QQ message listener started")
        
        while self._connected:
            try:
                await self._poll_messages()
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message listener: {e}")
                await asyncio.sleep(5)
    
    async def _poll_messages(self):
        """轮询消息"""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.mirai_api_http_url}/fetchMessage",
                    params={"sessionKey": self._session_key, "count": 10}
                )
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    for msg in data:
                        await self._process_message(msg)
                        
        except Exception as e:
            logger.debug(f"Error polling messages: {e}")
    
    async def _process_message(self, msg: Dict[str, Any]):
        """处理消息"""
        try:
            message_type = msg.get("type", "")
            sender = msg.get("sender", {})
            content = msg.get("messageChain", [])
            
            # 提取文本内容
            text = ""
            for part in content:
                if part.get("type") == "Plain":
                    text += part.get("text", "")
            
            if not text.strip():
                return
            
            # 创建消息对象
            message = Message(
                id=str(msg.get("id", "")),
                text=text,
                sender_id=str(sender.get("id", "")),
                sender_name=sender.get("nickname", ""),
                channel_type="qq",
                is_group=message_type == "GroupMessage",
                group_id=str(msg.get("group", {}).get("id", "")) if message_type == "GroupMessage" else "",
                raw=msg
            )
            
            # 发送到消息处理器
            if self._message_handler:
                await self._message_handler(message)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def send_message(self, message: Message):
        """发送消息"""
        if not self._connected:
            logger.warning("QQ channel is not connected")
            return False
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "sessionKey": self._session_key,
                    "target": int(message.recipient_id),
                    "messageChain": [{
                        "type": "Plain",
                        "text": message.text
                    }]
                }
                
                url = f"{self.config.mirai_api_http_url}/sendMessage"
                response = await client.post(url, json=payload)
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def send_group_message(self, group_id: str, text: str):
        """发送群消息"""
        message = Message(
            id="",
            text=text,
            sender_id="",
            sender_name="",
            channel_type="qq",
            is_group=True,
            group_id=group_id,
            recipient_id=group_id
        )
        return await self.send_message(message)
    
    async def send_private_message(self, user_id: str, text: str):
        """发送私聊消息"""
        message = Message(
            id="",
            text=text,
            sender_id="",
            sender_name="",
            channel_type="qq",
            is_group=False,
            recipient_id=user_id
        )
        return await self.send_message(message)
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
