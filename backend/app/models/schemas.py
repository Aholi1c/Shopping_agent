from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"

class UserRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class UserCreate(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    conversation_id: int
    role: UserRole
    content: str
    message_type: MessageType = MessageType.TEXT
    media_url: Optional[str] = None

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: UserRole
    content: str
    message_type: MessageType
    media_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"
    user_id: Optional[int] = None

class ConversationResponse(BaseModel):
    id: int
    user_id: Optional[int]
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    message_type: MessageType = MessageType.TEXT
    media_url: Optional[str] = None
    model: str = "glm-4-0520"  # 默认使用GLM-4模型，适配BigModel配置
    max_tokens: int = 2048
    temperature: float = 0.7
    use_memory: bool = True  # 默认启用记忆功能
    use_rag: bool = False  # 默认不启用RAG，除非明确指定

class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    message_id: int
    model_used: str
    tokens_used: Optional[Dict[str, int]] = None

class SpeechRequest(BaseModel):
    text: str
    language: str = "en"
    voice: Optional[str] = None

class SpeechResponse(BaseModel):
    audio_url: str
    duration: Optional[float] = None

class TranscriptionRequest(BaseModel):
    audio_url: str
    language: Optional[str] = None

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: Optional[float] = None

class ImageAnalysisRequest(BaseModel):
    image_url: str
    prompt: Optional[str] = "Describe this image in detail."

class ImageAnalysisResponse(BaseModel):
    analysis: str
    description: str
    tags: Optional[List[str]] = None

class AgentConfig(BaseModel):
    model_name: str = "gpt-3.5-turbo"
    max_tokens: int = 2048
    temperature: float = 0.7
    system_prompt: Optional[str] = None

class AgentSessionCreate(BaseModel):
    config: AgentConfig
    user_id: Optional[int] = None

class AgentSessionResponse(BaseModel):
    session_id: str
    config: AgentConfig
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

class FileUploadResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    file_type: str
    file_size: int
    file_url: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# 记忆系统schemas
class MemoryType(str, Enum):
    EPISODIC = "episodic"  # 情景记忆
    SEMANTIC = "semantic"  # 语义记忆
    WORKING = "working"    # 工作记忆

class MemoryCreate(BaseModel):
    content: str
    memory_type: MemoryType = MemoryType.EPISODIC
    importance_score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    user_id: Optional[int] = None

class MemoryResponse(BaseModel):
    id: int
    content: str
    memory_type: MemoryType
    importance_score: float
    access_count: int
    last_accessed: datetime
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

    class Config:
        from_attributes = True

class MemorySearchRequest(BaseModel):
    query: str
    memory_type: Optional[MemoryType] = None
    limit: int = 10
    threshold: float = 0.7
    user_id: Optional[int] = None

class WorkingMemoryUpdate(BaseModel):
    session_id: str
    context_data: Optional[Dict[str, Any]] = None
    short_term_memory: Optional[Dict[str, Any]] = None
    expires_in: Optional[int] = None  # 过期时间（秒）

# RAG系统schemas
class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    user_id: Optional[int] = None

class KnowledgeBaseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    user_id: Optional[int]
    document_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentUploadRequest(BaseModel):
    knowledge_base_id: int
    file_path: str
    chunk_size: int = 1000
    chunk_overlap: int = 200

class DocumentResponse(BaseModel):
    id: int
    knowledge_base_id: int
    filename: str
    original_name: str
    file_type: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RAGSearchRequest(BaseModel):
    query: str
    knowledge_base_ids: List[int] = []
    limit: int = 5
    threshold: float = 0.7
    filters: Optional[Dict[str, Any]] = None

class RAGSearchResult(BaseModel):
    content: str
    document_id: int
    chunk_index: int
    score: float
    metadata: Optional[Dict[str, Any]] = None

# 多Agent系统schemas
class AgentType(str, Enum):
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"

class AgentCreate(BaseModel):
    name: str
    description: str
    agent_type: AgentType
    capabilities: List[str]
    config: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    id: int
    name: str
    description: str
    agent_type: AgentType
    capabilities: List[str]
    config: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskCreate(BaseModel):
    agent_id: int
    session_id: str
    task_type: str
    task_data: Dict[str, Any]
    priority: int = 0

class TaskResponse(BaseModel):
    id: int
    task_id: str
    agent_id: int
    session_id: str
    task_type: str
    status: TaskStatus
    task_data: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class CollaborationType(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"

class AgentCollaborationCreate(BaseModel):
    session_id: str
    collaboration_type: CollaborationType
    participants: List[int]  # Agent IDs
    workflow: Dict[str, Any]
    task_data: Dict[str, Any]

class AgentCollaborationResponse(BaseModel):
    id: int
    session_id: str
    collaboration_type: CollaborationType
    participants: List[Dict[str, Any]]
    workflow: Dict[str, Any]
    status: str
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

# 增强的聊天请求
class EnhancedChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    message_type: MessageType = MessageType.TEXT
    media_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 2048
    temperature: float = 0.7
    # 新增功能
    use_memory: bool = True
    use_rag: bool = True
    knowledge_base_ids: Optional[List[int]] = None
    agent_collaboration: bool = False
    collaboration_type: Optional[CollaborationType] = None
    agents: Optional[List[int]] = None

class EnhancedChatResponse(BaseModel):
    response: str
    conversation_id: int
    message_id: int
    model_used: str
    tokens_used: Optional[Dict[str, int]] = None
    # 新增信息
    memory_used: bool = False
    rag_results: Optional[List[RAGSearchResult]] = None
    agent_collaboration: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None

# 网购助手相关schemas
class PlatformType(str, Enum):
    JD = "jd"
    TAOBAO = "taobao"
    PDD = "pdd"
    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"
    OTHER = "other"

class DiscountType(str, Enum):
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    CASHBACK = "cashback"

class SimilarityType(str, Enum):
    VISUAL = "visual"
    SEMANTIC = "semantic"
    OVERALL = "overall"

class ProductCreate(BaseModel):
    platform: PlatformType
    product_id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    discount_rate: Optional[float] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    sales_count: Optional[int] = None
    stock_status: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    platform: PlatformType
    product_id: str
    title: str
    description: Optional[str]
    category: Optional[str]
    brand: Optional[str]
    price: Optional[float]
    original_price: Optional[float]
    discount_rate: Optional[float]
    image_url: Optional[str]
    product_url: Optional[str]
    rating: Optional[float]
    review_count: Optional[int]
    sales_count: Optional[int]
    stock_status: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductSpecCreate(BaseModel):
    product_id: int
    spec_name: str
    spec_value: str

class ProductSpecResponse(BaseModel):
    id: int
    product_id: int
    spec_name: str
    spec_value: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProductSearchRequest(BaseModel):
    query: str
    platforms: List[PlatformType] = [PlatformType.JD, PlatformType.TAOBAO, PlatformType.PDD]
    category: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    sort_by: str = "relevance"
    page: int = 1
    page_size: int = 20

class ProductSearchResponse(BaseModel):
    products: List[ProductResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    search_time: float

class PriceHistoryResponse(BaseModel):
    id: int
    product_id: int
    price: float
    original_price: Optional[float]
    discount_rate: Optional[float]
    timestamp: datetime

    class Config:
        from_attributes = True

class ProductReviewCreate(BaseModel):
    product_id: int
    reviewer_name: Optional[str] = None
    rating: Optional[float] = None
    content: Optional[str] = None
    is_verified: bool = False

class ProductReviewResponse(BaseModel):
    id: int
    product_id: int
    reviewer_name: Optional[str]
    rating: Optional[float]
    content: Optional[str]
    is_verified: bool
    sentiment_score: Optional[float]
    authenticity_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

class UserPreferenceCreate(BaseModel):
    user_id: int
    preference_type: str
    preference_key: str
    preference_value: str
    weight: float = 1.0

class UserPreferenceResponse(BaseModel):
    id: int
    user_id: int
    preference_type: str
    preference_key: str
    preference_value: str
    weight: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CouponCreate(BaseModel):
    platform: PlatformType
    coupon_id: str
    title: str
    description: Optional[str] = None
    discount_type: DiscountType
    discount_value: float
    min_purchase_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    usage_limit: Optional[int] = None
    terms: Optional[str] = None

class CouponResponse(BaseModel):
    id: int
    platform: PlatformType
    coupon_id: str
    title: str
    description: Optional[str]
    discount_type: DiscountType
    discount_value: float
    min_purchase_amount: Optional[float]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    usage_limit: Optional[int]
    usage_count: int
    terms: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class BestDealRequest(BaseModel):
    product_id: int
    user_id: Optional[int] = None
    quantity: int = 1

class BestDealResponse(BaseModel):
    product_id: int
    best_price: float
    original_price: float
    total_discount: float
    recommended_coupons: List[CouponResponse]
    savings_amount: float
    final_price: float
    strategy_description: str

class ImageRecognitionRequest(BaseModel):
    image_url: str
    platform: Optional[PlatformType] = None

class ImageRecognitionResponse(BaseModel):
    product_info: Optional[ProductResponse] = None
    confidence: float
    description: str
    similar_products: List[ProductResponse] = []

class ImageSearchRequest(BaseModel):
    image_url: str
    platforms: List[PlatformType] = [PlatformType.JD, PlatformType.TAOBAO, PlatformType.PDD]
    similarity_threshold: float = 0.7
    limit: int = 10

class ImageSearchResponse(BaseModel):
    query_image: str
    results: List[ProductResponse]
    similarity_scores: List[float]
    search_time: float

class SimilarProductRequest(BaseModel):
    product_id: int
    platform: PlatformType
    limit: int = 10
    include_visual: bool = True
    include_semantic: bool = True

class SimilarProductResponse(BaseModel):
    source_product: ProductResponse
    similar_products: List[ProductResponse]
    similarity_scores: List[float]
    similarity_types: List[str]

class RecommendationRequest(BaseModel):
    user_id: int
    category: Optional[str] = None
    limit: int = 20
    include_reasons: bool = True

class RecommendationResponse(BaseModel):
    user_id: int
    recommendations: List[ProductResponse]
    reasons: List[str] = []
    score: List[float] = []

class PurchaseAnalysisRequest(BaseModel):
    user_id: int
    days: int = 30

class PurchaseAnalysisResponse(BaseModel):
    user_id: int
    total_purchases: int
    total_amount: float
    average_satisfaction: float
    favorite_categories: List[str]
    favorite_brands: List[str]
    price_preference: Dict[str, float]
    purchase_trends: List[Dict[str, Any]]

# MCP (Model Context Protocol) Schemas
class MCPResourceResponse(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None
    uri: Optional[str] = None
    metadata: Dict[str, Any] = {}

class MCPSearchRequest(BaseModel):
    query: str
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None

class MCPSearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    count: int

class MCPToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class MCPToolResponse(BaseModel):
    tool_name: str
    result: Dict[str, Any]