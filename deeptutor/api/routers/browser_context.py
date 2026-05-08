"""
浏览器上下文API路由
用于接收和管理来自浏览器扩展的上下文数据
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["browser-context"])


class BrowserContext(BaseModel):
    """浏览器上下文数据模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    selected_text: Optional[str] = None
    source_type: str = Field(..., pattern="^(page|selection|document)$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BrowserContextCreate(BaseModel):
    """创建浏览器上下文请求"""
    url: str
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    selected_text: Optional[str] = None
    source_type: str = "page"
    metadata: Optional[Dict] = Field(default_factory=dict)


class BrowserContextResponse(BaseModel):
    """浏览器上下文响应"""
    success: bool
    data: Optional[BrowserContext] = None
    message: str = ""


# 内存存储（生产环境建议使用 Redis 或数据库）
_context_store: Dict[str, BrowserContext] = {}
_context_history: List[BrowserContext] = []

# 配置
MAX_HISTORY_SIZE = 50
CONTEXT_EXPIRY_HOURS = 24


def _cleanup_expired_contexts():
    """清理过期的上下文"""
    now = datetime.utcnow()
    expired_ids = [
        ctx_id for ctx_id, ctx in _context_store.items()
        if now - ctx.timestamp > timedelta(hours=CONTEXT_EXPIRY_HOURS)
    ]
    for ctx_id in expired_ids:
        del _context_store[ctx_id]


def _add_to_history(context: BrowserContext):
    """添加到历史记录"""
    global _context_history
    
    # 检查是否已存在相同 URL 的记录
    existing_index = None
    for i, ctx in enumerate(_context_history):
        if ctx.url == context.url:
            existing_index = i
            break
    
    if existing_index is not None:
        # 更新现有记录
        _context_history[existing_index] = context
    else:
        # 添加新记录
        _context_history.insert(0, context)
    
    # 限制历史记录大小
    if len(_context_history) > MAX_HISTORY_SIZE:
        _context_history = _context_history[:MAX_HISTORY_SIZE]


def get_browser_context_record(context_id: str) -> Optional[BrowserContext]:
    """供其他路由读取指定上下文。"""
    context = _context_store.get(context_id)
    if not context:
        return None
    if datetime.utcnow() - context.timestamp > timedelta(hours=CONTEXT_EXPIRY_HOURS):
        return None
    return context


def get_latest_browser_context_record() -> Optional[BrowserContext]:
    """供其他模块读取最近上下文。"""
    if not _context_history:
        return None
    latest_context = _context_history[0]
    if datetime.utcnow() - latest_context.timestamp > timedelta(hours=CONTEXT_EXPIRY_HOURS):
        return None
    return latest_context


@router.post("", response_model=BrowserContextResponse)
async def create_browser_context(
    context_data: BrowserContextCreate,
    background_tasks: BackgroundTasks
):
    """
    创建浏览器上下文
    
    接收来自浏览器扩展的上下文数据并存储
    """
    try:
        # 清理过期数据
        background_tasks.add_task(_cleanup_expired_contexts)
        
        # 创建上下文对象
        context = BrowserContext(**context_data.dict())
        
        # 存储到内存
        _context_store[context.id] = context
        
        # 添加到历史记录
        _add_to_history(context)
        
        return BrowserContextResponse(
            success=True,
            data=context,
            message="上下文创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建上下文失败: {str(e)}")


@router.get("", response_model=BrowserContextResponse)
async def get_current_context():
    """
    获取当前上下文
    
    返回最近创建的浏览器上下文
    """
    if not _context_history:
        return BrowserContextResponse(
            success=False,
            message="暂无浏览器上下文"
        )
    
    # 返回最新的上下文
    latest_context = _context_history[0]
    
    # 检查是否过期
    if datetime.utcnow() - latest_context.timestamp > timedelta(hours=CONTEXT_EXPIRY_HOURS):
        return BrowserContextResponse(
            success=False,
            message="上下文已过期"
        )
    
    return BrowserContextResponse(
        success=True,
        data=latest_context,
        message="获取上下文成功"
    )


# 健康检查端点 (must be before /{context_id} to avoid path param match)
@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "context_count": len(_context_store),
        "history_count": len(_context_history)
    }


@router.get("/history", response_model=List[BrowserContext])
async def get_context_history(limit: int = 10):
    """
    获取上下文历史记录
    
    Args:
        limit: 返回记录数量，默认10条
    """
    # 清理过期记录
    now = datetime.utcnow()
    valid_history = [
        ctx for ctx in _context_history
        if now - ctx.timestamp <= timedelta(hours=CONTEXT_EXPIRY_HOURS)
    ]
    
    return valid_history[:limit]


@router.get("/{context_id}", response_model=BrowserContextResponse)
async def get_context_by_id(context_id: str):
    """
    根据ID获取上下文
    """
    context = _context_store.get(context_id)
    
    if not context:
        raise HTTPException(status_code=404, detail="上下文不存在")
    
    # 检查是否过期
    if datetime.utcnow() - context.timestamp > timedelta(hours=CONTEXT_EXPIRY_HOURS):
        raise HTTPException(status_code=410, detail="上下文已过期")
    
    return BrowserContextResponse(
        success=True,
        data=context,
        message="获取上下文成功"
    )


@router.delete("", response_model=BrowserContextResponse)
async def clear_current_context():
    """
    清除当前上下文
    
    清除最近创建的浏览器上下文
    """
    if _context_history:
        latest_context = _context_history.pop(0)
        if latest_context.id in _context_store:
            del _context_store[latest_context.id]
        
        return BrowserContextResponse(
            success=True,
            message="上下文已清除"
        )
    
    return BrowserContextResponse(
        success=False,
        message="暂无上下文需要清除"
    )


@router.delete("/{context_id}", response_model=BrowserContextResponse)
async def delete_context(context_id: str):
    """
    删除指定上下文
    """
    if context_id not in _context_store:
        raise HTTPException(status_code=404, detail="上下文不存在")
    
    del _context_store[context_id]
    
    # 同时从历史记录中移除
    global _context_history
    _context_history = [ctx for ctx in _context_history if ctx.id != context_id]
    
    return BrowserContextResponse(
        success=True,
        message="上下文已删除"
    )


@router.get("/history", response_model=List[BrowserContext])
async def get_context_history(limit: int = 10):
    """
    获取上下文历史记录
    
    Args:
        limit: 返回记录数量，默认10条
    """
    # 清理过期记录
    now = datetime.utcnow()
    valid_history = [
        ctx for ctx in _context_history
        if now - ctx.timestamp <= timedelta(hours=CONTEXT_EXPIRY_HOURS)
    ]
    
    return valid_history[:limit]


@router.post("/selection", response_model=BrowserContextResponse)
async def create_selection_context(selection_data: dict):
    """
    创建选区上下文
    
    专门用于接收选中文本
    """
    try:
        context_data = BrowserContextCreate(
            url=selection_data.get("url", ""),
            title=selection_data.get("title", "选区内容"),
            selected_text=selection_data.get("text", ""),
            source_type="selection",
            metadata=selection_data.get("metadata", {})
        )
        
        context = BrowserContext(**context_data.dict())
        _context_store[context.id] = context
        _add_to_history(context)
        
        return BrowserContextResponse(
            success=True,
            data=context,
            message="选区上下文创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建选区上下文失败: {str(e)}")


