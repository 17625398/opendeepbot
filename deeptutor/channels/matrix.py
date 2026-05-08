"""Matrix Channel Integration

Matrix 聊天通道实现，基于 matrix-nio 库。

Features:
- Matrix 消息接收和发送
- 房间支持
- 加密消息支持
- 消息转发到 Agent
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from deeptutor.channels.base import BaseChannel, Message

logger = logging.getLogger(__name__)


@dataclass
class MatrixConfig:
    """Matrix 通道配置"""
    enabled: bool = False
    homeserver_url: str = "https://matrix.org"
    user_id: str = ""
    password: str = ""
    access_token: str = ""
    device_id: str = "DeepTutor"
    auto_join: bool = True
    encryption_enabled: bool = False


class MatrixChannel(BaseChannel):
    """Matrix 聊天通道"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "matrix"
        self.config = MatrixConfig(**config)
        self._connected = False
        self._client = None
        self._tasks: List[asyncio.Task] = []
    
    async def connect(self):
        """连接到 Matrix"""
        if self._connected:
            logger.warning("Matrix channel is already connected")
            return
        
        logger.info("Connecting to Matrix...")
        
        try:
            from nio import AsyncClient, LoginResponse
            
            self._client = AsyncClient(
                self.config.homeserver_url,
                self.config.user_id,
                device_id=self.config.device_id
            )
            
            # 登录
            if self.config.access_token:
                self._client.access_token = self.config.access_token
                self._client.user_id = self.config.user_id
                logger.info("Using existing access token")
            elif self.config.user_id and self.config.password:
                response = await self._client.login(self.config.password)
                if isinstance(response, LoginResponse):
                    logger.info(f"Matrix login successful: {self.config.user_id}")
                else:
                    logger.error(f"Matrix login failed: {response}")
                    return
            else:
                logger.error("Matrix configuration incomplete")
                return
            
            # 添加事件回调
            self._client.add_event_callback(self._on_message, "m.room.message")
            
            # 启动同步任务
            task = asyncio.create_task(self._sync_loop())
            self._tasks.append(task)
            
            self._connected = True
            logger.info("Matrix channel connected successfully")
            
        except ImportError:
            logger.error("matrix-nio is required for Matrix channel")
        except Exception as e:
            logger.error(f"Failed to connect to Matrix: {e}")
    
    async def _sync_loop(self):
        """Matrix 同步循环"""
        logger.info("Matrix sync loop started")
        
        while self._connected and self._client:
            try:
                await self._client.sync(timeout=30000)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Matrix sync error: {e}")
                await asyncio.sleep(5)
    
    async def _on_message(self, room, event):
        """处理消息事件"""
        try:
            from nio import RoomMessageText
            
            if isinstance(event, RoomMessageText):
                # 跳过自己发送的消息
                if event.sender == self._client.user_id:
                    return
                
                # 创建消息对象
                message = Message(
                    id=event.event_id,
                    text=event.body,
                    sender_id=event.sender,
                    sender_name=event.sender,
                    channel_type="matrix",
                    is_group=not room.is_private,
                    group_id=room.room_id,
                    raw={"room": room, "event": event}
                )
                
                # 发送到消息处理器
                if self._message_handler:
                    await self._message_handler(message)
                    
        except Exception as e:
            logger.error(f"Error processing Matrix message: {e}")
    
    async def disconnect(self):
        """断开连接"""
        logger.info("Disconnecting Matrix channel...")
        
        # 取消所有任务
        for task in self._tasks:
            task.cancel()
        
        # 注销客户端
        if self._client:
            try:
                await self._client.close()
            except Exception as e:
                logger.warning(f"Failed to close Matrix client: {e}")
        
        self._connected = False
        logger.info("Matrix channel disconnected")
    
    async def send_message(self, message: Message):
        """发送消息"""
        if not self._connected or not self._client:
            logger.warning("Matrix channel is not connected")
            return False
        
        try:
            room_id = message.group_id if message.is_group else message.recipient_id
            
            if not room_id:
                logger.error("No room ID specified")
                return False
            
            response = await self._client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": message.text}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Matrix message: {e}")
            return False
    
    async def send_room_message(self, room_id: str, text: str):
        """发送房间消息"""
        message = Message(
            id="",
            text=text,
            sender_id="",
            sender_name="",
            channel_type="matrix",
            is_group=True,
            group_id=room_id,
            recipient_id=room_id
        )
        return await self.send_message(message)
    
    async def send_private_message(self, user_id: str, text: str):
        """发送私聊消息"""
        message = Message(
            id="",
            text=text,
            sender_id="",
            sender_name="",
            channel_type="matrix",
            is_group=False,
            recipient_id=user_id
        )
        return await self.send_message(message)
    
    async def join_room(self, room_id_or_alias: str):
        """加入房间"""
        if not self._client:
            return False
        
        try:
            await self._client.join(room_id_or_alias)
            logger.info(f"Joined room: {room_id_or_alias}")
            return True
        except Exception as e:
            logger.error(f"Failed to join room: {e}")
            return False
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
