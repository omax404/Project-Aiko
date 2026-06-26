"""core/api/schemas.py
Pydantic models for all API request/response validation.
Zero breaking changes — these validate inputs but don't change the data structure.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum

class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"

class ChatRequest(BaseModel):
    """Validate /api/chat requests."""
    message: str = Field(..., min_length=1, max_length=10000, description="User message text")
    user_id: str = Field(default="user", min_length=1, max_length=256, description="User identifier")
    attachments: List[str] = Field(default=[], description="List of attachment URLs")
    
    @validator('message')
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v.strip()

class SettingsUpdate(BaseModel):
    """Validate /api/settings POST requests."""
    llm: Optional[Dict[str, Any]] = None
    tts: Optional[Dict[str, Any]] = None
    persona: Optional[Dict[str, Any]] = None
    plugins: Optional[Dict[str, Any]] = None
    vision: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"  # Allow unknown keys for forward compatibility

class SessionRename(BaseModel):
    """Validate /api/sessions/rename requests."""
    id: str = Field(..., min_length=1, max_length=256, description="Session ID")
    name: str = Field(..., min_length=1, max_length=128, description="New session name")

class SessionPin(BaseModel):
    """Validate /api/sessions/pin requests."""
    id: str = Field(..., min_length=1, max_length=256, description="Session ID to pin")

class SessionDelete(BaseModel):
    """Validate /api/sessions DELETE requests."""
    id: str = Field(..., min_length=1, max_length=256, description="Session ID to delete")

class HistoryQuery(BaseModel):
    """Validate /api/history query parameters."""
    uid: Optional[str] = Field(default="user", min_length=1, max_length=256)
    id: Optional[str] = Field(default=None, min_length=1, max_length=256)

class UploadResponse(BaseModel):
    """Response model for /api/upload."""
    status: str
    filename: str
    url: str
    type: str

class LatexRenderRequest(BaseModel):
    """Validate /api/latex/render requests."""
    snippet: str = Field(..., min_length=1, max_length=5000, description="LaTeX snippet to render")
    
    @validator('snippet')
    def snippet_not_empty(cls, v):
        if not v.strip():
            raise ValueError("LaTeX snippet cannot be empty")
        return v.strip()

class RelationshipResponse(BaseModel):
    """Response model for /api/relationship."""
    affection: int = Field(..., ge=0, le=1000)
    level: str
    trust: int = Field(..., ge=0, le=100)

class HealthResponse(BaseModel):
    """Response model for /health."""
    status: str
    timestamp: str
    bridges: Dict[str, str]
    llm_provider: str

class StatusResponse(BaseModel):
    """Response model for /status."""
    status: str
    hub_name: str
    metrics: Dict[str, Any]
    rag_available: bool

class WSChatMessage(BaseModel):
    """Validate WebSocket chat messages."""
    type: str = Field(..., pattern="^(chat|speak|branch|ping|system|listen|vts_sync)$")
    text: Optional[str] = Field(default=None, max_length=10000)
    user_id: Optional[str] = Field(default=None, max_length=256)
    session_id: Optional[str] = Field(default=None, max_length=256)
    attachments: Optional[List[str]] = Field(default=[])
    emotion: Optional[str] = Field(default=None, max_length=32)
    message_id: Optional[str] = Field(default=None, max_length=256)
    action: Optional[str] = Field(default=None)
    state: Optional[bool] = None
    interval: Optional[int] = Field(default=None, ge=10, le=3600)

class SessionCreate(BaseModel):
    """Validate /api/sessions/create requests."""
    id: str = Field(..., min_length=1, max_length=256, description="Session ID")
    title: str = Field(default="New Conversation", min_length=1, max_length=128, description="Session title")

