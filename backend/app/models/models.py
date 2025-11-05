from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, JSON, LargeBinary, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String)  # "user" or "assistant"
    content = Column(Text)
    message_type = Column(String, default="text")  # "text", "image", "audio"
    media_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    model_name = Column(String, default="gpt-3.5-turbo")
    max_tokens = Column(Integer, default=2048)
    temperature = Column(Float, default=0.7)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

class FileUpload(Base):
    __tablename__ = "file_uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    original_name = Column(String)
    file_path = Column(String)
    file_type = Column(String)
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

# 记忆系统模型
class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    content = Column(Text)
    embedding = Column(LargeBinary)  # 向量存储
    memory_type = Column(String, default="episodic")  # "episodic", "semantic", "working"
    importance_score = Column(Float, default=0.0)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, nullable=True)  # 额外的元数据
    tags = Column(JSON, nullable=True)  # 标签系统

    user = relationship("User", backref="memories")

class MemoryIndex(Base):
    __tablename__ = "memory_indices"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"))
    index_type = Column(String)  # "semantic", "temporal", "importance"
    index_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class WorkingMemory(Base):
    __tablename__ = "working_memories"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    context_data = Column(JSON)  # 当前对话上下文
    short_term_memory = Column(JSON)  # 短期记忆数据
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

# RAG系统模型
class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    user = relationship("User", backref="knowledge_bases")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"))
    filename = Column(String)
    original_name = Column(String)
    file_path = Column(String)
    file_type = Column(String)
    content = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    knowledge_base = relationship("KnowledgeBase", backref="documents")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    content = Column(Text)
    embedding = Column(LargeBinary)
    chunk_index = Column(Integer)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", backref="chunks")

# 多Agent系统模型
class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text)
    agent_type = Column(String)  # "researcher", "analyst", "writer", "coordinator"
    capabilities = Column(JSON)  # Agent能力列表
    config = Column(JSON)  # Agent配置
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    session_id = Column(String, index=True)
    task_type = Column(String)  # "research", "analysis", "generation", "collaboration"
    task_data = Column(JSON)
    status = Column(String, default="pending")  # "pending", "running", "completed", "failed"
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    agent = relationship("Agent", backref="tasks")

class AgentCollaboration(Base):
    __tablename__ = "agent_collaborations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    collaboration_type = Column(String)  # "sequential", "parallel", "hierarchical"
    participants = Column(JSON)  # 参与的Agent列表
    workflow = Column(JSON)  # 协作流程定义
    status = Column(String, default="active")  # "active", "completed", "failed"
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

# 网购助手相关模型
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)  # 平台名称
    product_id = Column(String(100), nullable=False)  # 平台商品ID
    title = Column(String(500), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    brand = Column(String(100))
    price = Column(Float)
    original_price = Column(Float)
    discount_rate = Column(Float)
    image_url = Column(Text)
    product_url = Column(Text)
    rating = Column(Float)
    review_count = Column(Integer)
    sales_count = Column(Integer)
    stock_status = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint('platform', 'product_id', name='_platform_product_uc'),)

class ProductSpec(Base):
    __tablename__ = "product_specs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    spec_name = Column(String(100), nullable=False)
    spec_value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", backref="specs")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    discount_rate = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", backref="price_history")

class ProductReview(Base):
    __tablename__ = "product_reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    reviewer_name = Column(String(100))
    rating = Column(Float)
    content = Column(Text)
    is_verified = Column(Boolean, default=False)
    sentiment_score = Column(Float)
    authenticity_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", backref="reviews")

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    preference_type = Column(String(50), nullable=False)  # 'category', 'brand', 'price_range', 'feature'
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(Text)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="preferences")

class PurchaseHistory(Base):
    __tablename__ = "purchase_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    purchase_price = Column(Float)
    purchase_date = Column(DateTime)
    satisfaction_rating = Column(Float)
    feedback = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="purchase_history")
    product = relationship("Product", backref="purchase_history")

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    search_query = Column(Text, nullable=False)
    search_results_count = Column(Integer)
    click_through_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="search_history")

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)
    coupon_id = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    discount_type = Column(String(20))  # 'fixed', 'percentage', 'cashback'
    discount_value = Column(Float)
    min_purchase_amount = Column(Float)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    usage_limit = Column(Integer)
    usage_count = Column(Integer, default=0)
    terms = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint('platform', 'coupon_id', name='_platform_coupon_uc'),)

class CouponProduct(Base):
    __tablename__ = "coupon_products"

    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    coupon = relationship("Coupon", backref="products")
    product = relationship("Product", backref="coupons")

class CouponStrategy(Base):
    __tablename__ = "coupon_strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    strategy_data = Column(JSON)  # 优惠券组合策略
    max_discount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="coupon_strategies")
    product = relationship("Product", backref="coupon_strategies")

class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    image_url = Column(Text, nullable=False)
    image_hash = Column(String(64))
    features = Column(JSON)  # 图像特征向量
    quality_score = Column(Float)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", backref="images")

class ImageSimilarity(Base):
    __tablename__ = "image_similarities"

    id = Column(Integer, primary_key=True, index=True)
    source_image_id = Column(Integer, ForeignKey("product_images.id"))
    target_image_id = Column(Integer, ForeignKey("product_images.id"))
    similarity_score = Column(Float)
    similarity_type = Column(String(20))  # 'visual', 'semantic', 'overall'
    created_at = Column(DateTime, default=datetime.utcnow)

    source_image = relationship("ProductImage", foreign_keys=[source_image_id])
    target_image = relationship("ProductImage", foreign_keys=[target_image_id])

class ImageSearchHistory(Base):
    __tablename__ = "image_search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query_image_url = Column(Text)
    search_results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="image_search_history")

# 场景化推荐相关模型
class ScenarioTag(Base):
    __tablename__ = "scenario_tags"

    id = Column(Integer, primary_key=True, index=True)
    tag_name = Column(String(100), nullable=False, unique=True)
    tag_category = Column(String(50))  # "user_role", "environment", "purpose", "constraint"
    description = Column(Text)
    related_keywords = Column(JSON)  # 相关关键词列表
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserScenario(Base):
    __tablename__ = "user_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    scenario_description = Column(Text)
    extracted_tags = Column(JSON)  # 提取的场景标签
    context_data = Column(JSON)  # 场景上下文数据
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="scenarios")

class ProductScenarioMapping(Base):
    __tablename__ = "product_scenario_mappings"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    scenario_tag_id = Column(Integer, ForeignKey("scenario_tags.id"))
    match_score = Column(Float)  # 商品与场景的匹配分数
    reasoning = Column(Text)  # 匹配理由
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", backref="scenario_mappings")
    scenario_tag = relationship("ScenarioTag", backref="product_mappings")

class ScenarioKnowledge(Base):
    __tablename__ = "scenario_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    scenario_tag_id = Column(Integer, ForeignKey("scenario_tags.id"))
    knowledge_type = Column(String(50))  # "requirement", "recommendation", "standard"
    title = Column(String(200))
    content = Column(Text)
    source = Column(String(100))
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    scenario_tag = relationship("ScenarioTag", backref="knowledge")

# 用户行为分析相关模型
class UserBehavior(Base):
    __tablename__ = "user_behaviors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String(100))
    behavior_type = Column(String(50))  # "view", "click", "search", "compare", "add_to_cart", "purchase", "review"
    target_id = Column(Integer)  # 商品ID或其他目标ID
    target_type = Column(String(50))  # "product", "category", "brand"
    behavior_data = Column(JSON)  # 行为详情数据
    duration = Column(Float)  # 停留时间（秒）
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="behaviors")

class BehaviorPreferenceRule(Base):
    __tablename__ = "behavior_preference_rules"

    id = Column(Integer, primary_key=True, index=True)
    behavior_type = Column(String(50))
    behavior_pattern = Column(JSON)  # 行为模式描述
    preference_inference = Column(JSON)  # 推断的偏好
    confidence = Column(Float)
    weight = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserPreferenceModel(Base):
    __tablename__ = "user_preference_models"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    preference_dimension = Column(String(100))  # "price_sensitivity", "quality_focus", "brand_loyalty", "eco_friendly"
    current_weight = Column(Float, default=0.5)
    learning_rate = Column(Float, default=0.1)
    confidence = Column(Float, default=0.5)
    last_updated = Column(DateTime, default=datetime.utcnow)
    update_history = Column(JSON)  # 权重更新历史

    user = relationship("User", backref="preference_models")

class PreferenceFeedback(Base):
    __tablename__ = "preference_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recommendation_id = Column(String(100))
    action = Column(String(20))  # "click", "purchase", "ignore", "dislike"
    feedback_data = Column(JSON)
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="preference_feedback")

class UserInsightReport(Base):
    __tablename__ = "user_insight_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    report_type = Column(String(50))  # "weekly", "monthly", "preference_analysis"
    title = Column(String(200))
    content = Column(JSON)  # 报告内容
    key_insights = Column(JSON)  # 关键洞察
    recommendations = Column(JSON)  # 建议行动
    confidence_score = Column(Float)
    generated_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    user = relationship("User", backref="insight_reports")

class PotentialNeed(Base):
    __tablename__ = "potential_needs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    need_type = Column(String(100))  # "complementary", "upgrade", "alternative"
    trigger_product_id = Column(Integer, ForeignKey("products.id"))
    recommended_product_id = Column(Integer, ForeignKey("products.id"))
    reasoning = Column(Text)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="pending")  # "pending", "suggested", "accepted", "rejected"

    user = relationship("User", backref="potential_needs")
    trigger_product = relationship("Product", foreign_keys=[trigger_product_id], backref="triggered_needs")
    recommended_product = relationship("Product", foreign_keys=[recommended_product_id], backref="recommended_needs")

# 价格预测和促销优化相关模型
class PricePrediction(Base):
    __tablename__ = "price_predictions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    prediction_date = Column(DateTime)  # 预测的日期
    predicted_price = Column(Float)  # 预测价格
    confidence_lower = Column(Float)  # 置信区间下限
    confidence_upper = Column(Float)  # 置信区间上限
    prediction_model = Column(String(50))  # 使用的预测模型
    features_used = Column(JSON)  # 使用的特征
    accuracy_score = Column(Float)  # 历史准确率
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", backref="price_predictions")

class PromotionCalendar(Base):
    __tablename__ = "promotion_calendars"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50))  # 平台
    promotion_name = Column(String(100))  # 促销活动名称
    promotion_type = Column(String(50))  # "618", "双11", "春节", "日常"
    start_date = Column(DateTime)  # 开始时间
    end_date = Column(DateTime)  # 结束时间
    discount_rules = Column(JSON)  # 折扣规则
    minimum_threshold = Column(Float)  # 最低门槛
    maximum_discount = Column(Float)  # 最大折扣
    historical_effectiveness = Column(JSON)  # 历史效果数据
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    target_price = Column(Float)  # 目标价格
    alert_type = Column(String(20))  # "below", "above", "percentage_drop"
    threshold_value = Column(Float)  # 阈值
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime)
    notification_method = Column(String(20))  # "email", "app", "sms"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="price_alerts")
    product = relationship("Product", backref="price_alerts")

# 商品风险识别相关模型
class ProductRisk(Base):
    __tablename__ = "product_risks"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    risk_type = Column(String(50))  # "quality", "fake", "misleading", "service", "safety"
    risk_level = Column(String(20))  # "low", "medium", "high", "critical"
    risk_description = Column(Text)  # 风险描述
    evidence_sources = Column(JSON)  # 证据来源
    detection_method = Column(String(50))  # "complaint_analysis", "review_mining", "llm_analysis"
    confidence_score = Column(Float)
    mitigation_suggestions = Column(JSON)  # 规避建议
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", backref="risk_assessments")

class RiskKeywordLibrary(Base):
    __tablename__ = "risk_keyword_libraries"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100))  # 风险关键词
    risk_category = Column(String(50))  # 风险类别
    severity_score = Column(Float)  # 严重程度
    context_patterns = Column(JSON)  # 上下文模式
    frequency_weight = Column(Float)  # 频率权重
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ComplaintRecord(Base):
    __tablename__ = "complaint_records"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    source_platform = Column(String(50))  # 投诉来源平台
    complaint_type = Column(String(50))  # 投诉类型
    complaint_content = Column(Text)  # 投诉内容
    severity_level = Column(String(20))  # 严重程度
    complaint_date = Column(DateTime)  # 投诉日期
    resolution_status = Column(String(20))  # 解决状态
    verified = Column(Boolean, default=False)  # 是否已核实
    related_risks = Column(JSON)  # 相关风险
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", backref="complaint_records")

# 交互式决策工具相关模型
class UserDecisionWeights(Base):
    __tablename__ = "user_decision_weights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    decision_context = Column(String(100))  # 决策上下文
    weight_dimension = Column(String(50))  # 权重维度
    weight_value = Column(Float)  # 权重值 (0-1)
    priority_level = Column(Integer)  # 优先级
    is_active = Column(Boolean, default=True)
    last_adjusted = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="decision_weights")

class DecisionRecommendation(Base):
    __tablename__ = "decision_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String(100))  # 决策会话ID
    product_candidates = Column(JSON)  # 候选商品
    user_weights = Column(JSON)  # 用户权重设置
    recommendation_results = Column(JSON)  # 推荐结果
    explanation_details = Column(JSON)  # 解释详情
    optimization_algorithm = Column(String(50))  # 优化算法
    confidence_score = Column(Float)
    user_feedback = Column(String(20))  # "helpful", "neutral", "not_helpful"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="decision_recommendations")

class RecommendationExplanation(Base):
    __tablename__ = "recommendation_explanations"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("decision_recommendations.id"))
    product_a_id = Column(Integer, ForeignKey("products.id"))
    product_b_id = Column(Integer, ForeignKey("products.id"))
    comparison_dimension = Column(String(50))  # 比较维度
    advantage_reason = Column(Text)  # 优势原因
    quantitive_difference = Column(Float)  # 量化差异
    confidence_score = Column(Float)
    natural_language_explanation = Column(Text)  # 自然语言解释
    created_at = Column(DateTime, default=datetime.utcnow)

    recommendation = relationship("DecisionRecommendation", backref="explanations")
    product_a = relationship("Product", foreign_keys=[product_a_id])
    product_b = relationship("Product", foreign_keys=[product_b_id])