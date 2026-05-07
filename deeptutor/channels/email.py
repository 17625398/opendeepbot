"""Email Channel for DeepTutor

Email integration using aioimaplib and aiosmtplib.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from .base import BaseChannel

logger = logging.getLogger(__name__)

try:
    import aiosmtplib
    from aioimaplib import aioimaplib
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    logger.warning("aioimaplib/aiosmtplib not installed, Email channel disabled")


class EmailChannel(BaseChannel):
    """Email chat channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "email"
        self.smtp_host = config.get("smtp_host", "smtp.gmail.com")
        self.smtp_port = config.get("smtp_port", 587)
        self.imap_host = config.get("imap_host", "imap.gmail.com")
        self.imap_port = config.get("imap_port", 993)
        self.username = config.get("username")
        self.password = config.get("password")
        self.from_email = config.get("from_email", self.username)
        self.imap_client = None
        self.poll_task = None
    
    async def initialize(self) -> bool:
        """Initialize Email channel"""
        if not EMAIL_AVAILABLE:
            logger.error("aioimaplib/aiosmtplib not installed")
            return False
        
        if not self.username or not self.password:
            logger.error("Email username and password required")
            return False
        
        try:
            self._initialized = True
            logger.info("Email channel initialized")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize Email channel: {e}")
            return False
    
    async def send_message(self, user_id: str, message: str, **kwargs) -> bool:
        """Send email message"""
        if not self._connected:
            logger.error("Email channel not connected")
            return False
        
        try:
            subject = kwargs.get("subject", "Message from DeepTutor")
            
            # Create email
            from email.mime.text import MIMEText
            msg = MIMEText(message)
            msg["From"] = self.from_email
            msg["To"] = user_id
            msg["Subject"] = subject
            
            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                use_tls=True
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_typing(self, user_id: str):
        """Send typing indicator"""
        if not self._connected:
            return
        
        try:
            # Email doesn't have typing indicator, just log
            logger.info(f"Typing indicator to {user_id}")
        except Exception as e:
            logger.error(f"Failed to send typing indicator: {e}")
    
    async def _poll_emails(self):
        """Poll for incoming emails"""
        while self._connected:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Email poll error: {e}")
                await asyncio.sleep(5)
    
    async def start(self):
        """Start Email channel"""
        try:
            self._connected = True
            self._stats["connected_at"] = __import__("datetime").datetime.now().isoformat()
            
            # Start polling task
            self.poll_task = asyncio.create_task(self._poll_emails())
            logger.info("Email channel started")
        
        except Exception as e:
            logger.error(f"Failed to start Email channel: {e}")
            self._connected = False
    
    async def shutdown(self):
        """Shutdown Email channel"""
        await super().shutdown()
        
        if self.poll_task:
            self.poll_task.cancel()
            try:
                await self.poll_task
            except asyncio.CancelledError:
                pass
        
        if self.imap_client:
            try:
                await self.imap_client.logout()
            except Exception as e:
                logger.error(f"Error closing IMAP connection: {e}")
        
        logger.info("Email channel shutdown")
