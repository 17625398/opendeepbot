"""WebSocket Channel for DeepTutor

WebSocket server for real-time bidirectional communication with WebUI.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Set

import websockets
from websockets import WebSocketServerProtocol

from .base import BaseChannel

logger = logging.getLogger(__name__)


class WebSocketChannel(BaseChannel):
    """WebSocket chat channel for WebUI connections"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "websocket"
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 8765)
        self.server: Optional[websockets.WebSocketServer] = None
        self.clients: Set[WebSocketServerProtocol] = set()
        self.client_info: Dict[str, Dict[str, Any]] = {}  # client_id -> info
        self._server_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """Initialize WebSocket channel"""
        try:
            self._initialized = True
            logger.info("WebSocket channel initialized")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket channel: {e}")
            return False
    
    async def _handle_client(self, websocket: WebSocketServerProtocol):
        """Handle a single WebSocket client connection"""
        client_id = id(websocket)
        self.clients.add(websocket)
        self.client_info[client_id] = {
            "connected_at": __import__("datetime").datetime.now().isoformat(),
            "user_id": None,
            "channel": None
        }
        
        logger.info(f"WebSocket client connected: {client_id}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(client_id, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON message from client {client_id}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling WebSocket client {client_id}: {e}")
        finally:
            self.clients.discard(websocket)
            del self.client_info[client_id]
    
    async def _process_message(self, client_id: int, data: Dict[str, Any]):
        """Process incoming message from WebSocket client"""
        message_type = data.get("type", "message")
        user_id = data.get("user_id", str(client_id))
        content = data.get("content", "")
        
        # Store user_id if provided
        if user_id:
            self.client_info[client_id]["user_id"] = user_id
        
        if message_type == "message":
            await self._handle_incoming_message(user_id, content, client_id=client_id)
        elif message_type == "auth":
            await self._handle_auth(client_id, data)
        elif message_type == "ping":
            await self._handle_ping(client_id)
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def _handle_auth(self, client_id: int, data: Dict[str, Any]):
        """Handle authentication message"""
        token = data.get("token")
        if token:
            self.client_info[client_id]["token"] = token
            # In real implementation, verify token and set user_id
    
    async def _handle_ping(self, client_id: int):
        """Handle ping message"""
        for websocket in self.clients:
            if id(websocket) == client_id:
                try:
                    await websocket.send(json.dumps({"type": "pong"}))
                except Exception as e:
                    logger.error(f"Failed to send pong to client {client_id}: {e}")
    
    async def send_message(self, user_id: str, message: str, **kwargs) -> bool:
        """Send message to WebSocket clients"""
        data = {
            "type": "message",
            "user_id": user_id,
            "content": message,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            **kwargs
        }
        
        message_json = json.dumps(data)
        sent_count = 0
        
        # If user_id is specified, try to find specific client
        if user_id and user_id != "broadcast":
            for client_id, info in self.client_info.items():
                if info.get("user_id") == user_id:
                    for websocket in self.clients:
                        if id(websocket) == client_id:
                            try:
                                await websocket.send(message_json)
                                sent_count += 1
                            except Exception as e:
                                logger.error(f"Failed to send to client {client_id}: {e}")
        else:
            # Broadcast to all clients
            for websocket in self.clients:
                try:
                    await websocket.send(message_json)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to broadcast to client: {e}")
        
        return sent_count > 0
    
    async def send_typing(self, user_id: str):
        """Send typing indicator"""
        data = {
            "type": "typing",
            "user_id": user_id,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
        
        message_json = json.dumps(data)
        
        for client_id, info in self.client_info.items():
            if not user_id or info.get("user_id") == user_id:
                for websocket in self.clients:
                    if id(websocket) == client_id:
                        try:
                            await websocket.send(message_json)
                        except Exception as e:
                            logger.error(f"Failed to send typing: {e}")
    
    async def start(self):
        """Start WebSocket server"""
        try:
            self.server = await websockets.serve(
                self._handle_client,
                self.host,
                self.port
            )
            
            self._connected = True
            self._stats["connected_at"] = __import__("datetime").datetime.now().isoformat()
            
            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
            
            # Keep server running
            self._server_task = asyncio.create_task(
                self.server.wait_closed()
            )
        
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            self._connected = False
    
    async def shutdown(self):
        """Shutdown WebSocket channel"""
        await super().shutdown()
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        if self._server_task:
            self._server_task.cancel()
        
        # Close all client connections
        for websocket in self.clients:
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Failed to close client connection: {e}")
        
        self.clients.clear()
        self.client_info.clear()
        
        logger.info("WebSocket channel shutdown")
    
    def get_client_count(self) -> int:
        """Get number of connected clients"""
        return len(self.clients)