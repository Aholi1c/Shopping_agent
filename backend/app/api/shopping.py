from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
# Form暂时移除，因为python-multipart安装有问题
# from fastapi import Form
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from ..core.database import get_db
from ..core.config import settings
from ..models.schemas import (
    ProductSearchRequest, ProductSearchResponse, ProductResponse,
    ProductCreate, ProductSpecCreate, ProductSpecResponse,
    ImageRecognitionRequest, ImageRecognitionResponse,
    ImageSearchRequest, ImageSearchResponse,
    SimilarProductRequest, SimilarProductResponse,
    BestDealRequest, BestDealResponse,
    RecommendationRequest, RecommendationResponse,
    PurchaseAnalysisRequest, PurchaseAnalysisResponse,
    CouponCreate, CouponResponse,
    PlatformType, DiscountType
)
from ..services.shopping_service import ShoppingService
from ..services.image_service import ImageService
from ..services.price_service import PriceService
from ..services.llm_service import LLMService
from ..services.memory_service import MemoryService
from ..services.media_service import MediaService
from ..services.scenario_service import scenario_service
from ..services.reinforcement_learning_service import rl_service

logger = logging.getLogger(__name__)
router = APIRouter()

# 依赖注入
def get_shopping_service(db: Session = Depends(get_db)) -> ShoppingService:
    llm_service = LLMService()
    memory_service = MemoryService(db)
    media_service = MediaService()
    return ShoppingService(db, llm_service, memory_service, media_service)

def get_image_service(db: Session = Depends(get_db)) -> ImageService:
    llm_service = LLMService()
    shopping_service = get_shopping_service(db)
    return ImageService(db, llm_service, shopping_service)

def get_price_service(db: Session = Depends(get_db)) -> PriceService:
    llm_service = LLMService()
    shopping_service = get_shopping_service(db)
    return PriceService(db, llm_service, shopping_service)

# 商品搜索和检索
@router.post("/search", response_model=ProductSearchResponse)
async def search_products(
    request: ProductSearchRequest,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """多平台商品搜索"""
    try:
        shopping_service = get_shopping_service(db)
        return await shopping_service.search_products(request, user_id)
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail="搜索商品失败")

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product_details(
    product_id: int,
    db: Session = Depends(get_db)
):
    """获取商品详情"""
    try:
        shopping_service = get_shopping_service(db)
        product = await shopping_service.get_product_details(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product details: {e}")
        raise HTTPException(status_code=500, detail="获取商品详情失败")

@router.get("/products/{product_id}/price-history")
async def get_price_history(
    product_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """获取价格历史"""
    try:
        shopping_service = get_shopping_service(db)
        return await shopping_service.get_price_history(product_id, days)
    except Exception as e:
        logger.error(f"Error getting price history: {e}")
        raise HTTPException(status_code=500, detail="获取价格历史失败")

@router.post("/compare")
async def compare_products(
    product_ids: List[int],
    db: Session = Depends(get_db)
):
    """商品对比"""
    try:
        if len(product_ids) < 2:
            raise HTTPException(status_code=400, detail="至少需要选择2个商品进行对比")

        shopping_service = get_shopping_service(db)
        return await shopping_service.compare_products(product_ids)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing products: {e}")
        raise HTTPException(status_code=500, detail="商品对比失败")

@router.post("/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """创建商品"""
    try:
        shopping_service = get_shopping_service(db)
        return await shopping_service.create_product(product)
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail="创建商品失败")

# 图片识别和搜索
@router.post("/image-recognition", response_model=ImageRecognitionResponse)
async def recognize_product_image(
    request: ImageRecognitionRequest,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """商品图片识别"""
    try:
        image_service = get_image_service(db)
        return await image_service.recognize_product(request, user_id)
    except Exception as e:
        logger.error(f"Error in image recognition: {e}")
        raise HTTPException(status_code=500, detail="图片识别失败")

@router.post("/image-search", response_model=ImageSearchResponse)
async def search_by_image(
    request: ImageSearchRequest,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """以图搜图"""
    try:
        image_service = get_image_service(db)
        return await image_service.search_by_image(request, user_id)
    except Exception as e:
        logger.error(f"Error in image search: {e}")
        raise HTTPException(status_code=500, detail="图片搜索失败")

@router.get("/products/{product_id}/similar", response_model=SimilarProductResponse)
async def get_similar_products(
    product_id: int,
    platform: PlatformType,
    limit: int = 10,
    include_visual: bool = True,
    include_semantic: bool = True,
    db: Session = Depends(get_db)
):
    """获取相似商品"""
    try:
        request = SimilarProductRequest(
            product_id=product_id,
            platform=platform,
            limit=limit,
            include_visual=include_visual,
            include_semantic=include_semantic
        )
        image_service = get_image_service(db)
        return await image_service.get_similar_products(request)
    except Exception as e:
        logger.error(f"Error getting similar products: {e}")
        raise HTTPException(status_code=500, detail="获取相似商品失败")

@router.post("/upload-image-features")
async def upload_image_features(
    product_id: int,
    image_url: str,
    db: Session = Depends(get_db)
):
    """上传图片并提取特征"""
    try:
        image_service = get_image_service(db)
        success = await image_service.extract_image_features(image_url, product_id)
        if success:
            return {"message": "图片特征提取成功", "product_id": product_id}
        else:
            raise HTTPException(status_code=500, detail="图片特征提取失败")
    except Exception as e:
        logger.error(f"Error uploading image features: {e}")
        raise HTTPException(status_code=500, detail="上传图片特征失败")

# 商品分析
@router.post("/product-analysis")
async def analyze_product(
    product_data: Dict[str, Any],
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """商品分析（基于商品信息）"""
    try:
        from ..services.llm_service import get_llm_service
        from ..services.price_service import PriceService
        from ..services.risk_detection_service import RiskDetectionService
        
        llm_service = get_llm_service()
        price_service = get_price_service(db)
        risk_service = RiskDetectionService(db, llm_service)
        
        # 提取商品信息（支持多种字段名）
        product_name = product_data.get('name') or product_data.get('title') or product_data.get('product_name') or ''
        product_price = float(product_data.get('price', 0)) or 0
        product_currency = product_data.get('currency', 'CNY')  # 默认人民币
        product_platform = product_data.get('platform', '')
        product_id = product_data.get('productId') or product_data.get('product_id') or product_data.get('id') or ''
        product_image = product_data.get('image') or product_data.get('image_url') or ''
        product_url = product_data.get('url') or ''
        product_description = product_data.get('description') or ''
        product_parameters = product_data.get('parameters') or {}
        
        # 货币符号映射
        currency_symbols = {
            'CNY': '¥',
            'HKD': 'HK$',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': 'JP¥',
            'AUD': 'A$'
        }
        currency_symbol = currency_symbols.get(product_currency, '¥')
        
        logger.info(f"开始分析商品: {product_name}, 价格: {currency_symbol}{product_price} ({product_currency}), 平台: {product_platform}")
        
        # 验证必要的商品信息
        if not product_name:
            raise HTTPException(status_code=400, detail="商品名称不能为空，请确保在商品详情页面")
        
        # 验证LLM服务是否可用
        if not llm_service:
            raise HTTPException(status_code=500, detail="LLM服务未初始化，请检查配置")
        
        # 1. 价格分析
        price_analysis = {}
        if product_name:
            try:
                # 使用价格服务进行多平台价格比较
                # PriceService.compare_prices需要query字符串和platforms列表
                try:
                    price_comparison = await price_service.compare_prices(
                        query=product_name, 
                        platforms=[PlatformType.JD, PlatformType.TAOBAO, PlatformType.PDD]
                    )
                    
                    # 确保price_comparison是字典
                    if not isinstance(price_comparison, dict):
                        logger.warning(f"price_comparison is not a dict: {type(price_comparison)}")
                        price_comparison = {}
                    
                    # 计算节省潜力
                    comparison = price_comparison.get("comparison", {})
                    savings_potential = 0
                    min_prices = []
                    
                    if comparison:
                        # 找到最低价格
                        for product_key, data in comparison.items():
                            if isinstance(data, dict) and "min_price" in data:
                                min_prices.append(data["min_price"])
                        
                        if min_prices:
                            lowest_price = min(min_prices)
                            if product_price > 0 and product_price > lowest_price:
                                savings_potential = product_price - lowest_price
                    
                    price_analysis = {
                        "current_price": product_price,
                        "platform": product_platform,
                        "comparison": comparison,
                        "savings_potential": savings_potential,
                        "lowest_found_price": min(min_prices) if min_prices else None,
                        "total_comparisons": len(comparison),
                        "status": "success" if comparison else "no_comparison"
                    }
                except AttributeError as ae:
                    # 捕获属性错误
                    logger.error(f"Price comparison attribute error: {ae}")
                    price_analysis = {
                        "error": f"价格比较服务错误: {str(ae)}",
                        "current_price": product_price,
                        "platform": product_platform,
                        "status": "service_error"
                    }
            except Exception as e:
                logger.error(f"Price analysis error: {e}")
                import traceback
                logger.error(traceback.format_exc())
                price_analysis = {
                    "error": str(e),
                    "current_price": product_price,
                    "platform": product_platform,
                    "status": "error"
                }
        
        # 2. 风险评估
        risk_analysis = {}
        if product_name:
            try:
                # 构建临时产品数据用于风险分析
                temp_product_data = {
                    "name": product_name,
                    "price": product_price,
                    "platform": product_platform
                }
                risk_analysis = await risk_service.analyze_product_risks_by_data(temp_product_data)
            except Exception as e:
                logger.error(f"Risk analysis error: {e}")
                risk_analysis = {"error": str(e)}
        
        # 3. 使用LLM生成综合分析
        # 构建商品详细信息文本
        product_details_text = f"商品名称: {product_name}\n当前价格: {currency_symbol}{product_price} ({product_currency})\n平台: {product_platform}"
        
        if product_description:
            product_details_text += f"\n\n商品描述:\n{product_description[:1000]}"  # 限制长度避免token过多
        
        if product_parameters:
            params_text = "\n".join([f"{k}: {v}" for k, v in list(product_parameters.items())[:20]])  # 最多20个参数
            product_details_text += f"\n\n商品参数:\n{params_text}"
        
        # 构建价格对比文本（注意货币单位）
        price_comparison_text = ""
        if price_analysis.get("comparison"):
            price_comparison_text = "\n\n其他平台价格对比（注意：以下价格均为人民币CNY，如果当前商品是其他货币，请提醒用户注意汇率转换）:\n"
            for platform, data in price_analysis.get("comparison", {}).items():
                if isinstance(data, dict):
                    if "min_price" in data:
                        price_comparison_text += f"- {platform}: ¥{data.get('min_price', 0)}\n"
        
        analysis_prompt = f"""
        请对以下商品进行全面分析：

        {product_details_text}
        
        价格分析结果: {price_analysis}
        {price_comparison_text}
        风险评估结果: {risk_analysis}
        
        重要提示：
        - 当前商品价格使用货币: {product_currency} ({currency_symbol})
        - 如果商品价格是HKD（港币），请提醒用户注意汇率转换（1 HKD ≈ 0.92 CNY）
        - 如果商品价格是USD（美元），请提醒用户注意汇率转换（1 USD ≈ 7.2 CNY）
        - 价格对比数据来自数据库，均为人民币（CNY）价格
        
        请提供：
        1. 商品概述和特点（基于商品描述和参数信息）
        2. 价格合理性分析（注意货币单位，如需转换请说明）
        3. 与其他平台的价格对比（明确标注货币单位，如有汇率转换请说明）
        4. 风险评估和建议
        5. 购买建议（立即购买/等待降价/谨慎考虑）
        6. 需要注意的事项（特别提醒货币和汇率问题）
        
        请用清晰、专业的语言进行分析，帮助用户做出明智的购买决策。
        如果提供了商品描述，请结合描述信息进行更准确的分析。
        """
        
        # 调用LLM生成分析
        try:
            logger.info("调用LLM生成综合分析...")
            llm_response = await llm_service.chat_completion([
                {"role": "system", "content": "你是一个专业的购物助手，擅长分析商品的价格、质量和风险。"},
                {"role": "user", "content": analysis_prompt}
            ])
            
            # 处理不同的响应格式
            if isinstance(llm_response, dict):
                comprehensive_analysis = llm_response.get("content") or llm_response.get("message") or llm_response.get("text") or ""
            elif isinstance(llm_response, str):
                comprehensive_analysis = llm_response
            else:
                comprehensive_analysis = str(llm_response)
            
            if not comprehensive_analysis:
                logger.warning("LLM返回的分析内容为空")
                comprehensive_analysis = "分析完成，但未生成详细报告。请检查LLM服务配置。"
            
            logger.info(f"LLM分析完成，生成了 {len(comprehensive_analysis)} 字符的分析内容")
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            comprehensive_analysis = f"LLM分析失败: {str(e)}。请检查LLM服务配置（当前使用: {settings.llm_provider}）"
        
        return {
            "success": True,
            "data": {
                "product_name": product_name,
                "product_price": product_price,
                "platform": product_platform,
                "comprehensive_analysis": comprehensive_analysis,
                "price_analysis": price_analysis,
                "risk_analysis": risk_analysis,
                "recommendation": {
                    "action": "consider",  # consider, buy_now, wait, avoid
                    "confidence": 0.7,
                    "reason": "基于价格和风险分析的综合建议"
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing product: {e}")
        raise HTTPException(status_code=500, detail=f"商品分析失败: {str(e)}")

# 价格对比和优惠计算
class PriceComparisonRequest(BaseModel):
    """价格对比请求"""
    query: str = Field(..., description="商品名称或搜索关键词")
    platforms: Optional[List[str]] = Field(None, description="平台列表，如 ['jd', 'taobao', 'pdd']")

@router.post("/price-comparison")
async def compare_prices(
    request: PriceComparisonRequest,
    db: Session = Depends(get_db)
):
    """多平台价格对比 - 使用万邦API获取商品数据"""
    try:
        query = request.query
        platforms_param = request.platforms
        
        if not query:
            raise HTTPException(status_code=400, detail="缺少必需参数: query")
        
        # 转换平台名称到PlatformType枚举
        from ..models.schemas import PlatformType
        platform_list = []
        if platforms_param:
            platform_map = {
                'jd': PlatformType.JD,
                'taobao': PlatformType.TAOBAO,
                'tmall': PlatformType.TAOBAO,  # 天猫也是淘宝平台
                'pdd': PlatformType.PDD,
            }
            for p in platforms_param:
                p_lower = p.lower()
                if p_lower in platform_map:
                    platform_list.append(platform_map[p_lower])
        
        # 如果没有指定平台，使用默认值
        if not platform_list:
            platform_list = [PlatformType.JD, PlatformType.TAOBAO, PlatformType.PDD]
        
        logger.info(f"开始价格对比，商品: {query}, 平台: {platform_list}")
        
        price_service = get_price_service(db)
        result = await price_service.compare_prices(query, platform_list)
        
        # 确保返回格式一致
        if isinstance(result, dict):
            # 检查是否有错误
            if "error" in result:
                logger.warning(f"Price comparison returned error: {result.get('error')}")
                # 如果只是警告性错误（如没有找到结果），仍然返回结果
                if result.get("total_products", 0) == 0:
                    return {
                        "query": query,
                        "comparison": {},
                        "total_products": 0,
                        "search_time": 0,
                        "message": "未找到商品，请尝试使用更具体的关键词。如果配置了万邦API，请检查API密钥是否正确。",
                        "error": result.get("error")
                    }
            
            # 检查comparison是否为空
            comparison = result.get("comparison", {})
            if not comparison or len(comparison) == 0:
                total_products = result.get("total_products", 0)
                if total_products > 0:
                    # 有商品但没有分组，可能是分组逻辑的问题
                    logger.warning(f"找到 {total_products} 个商品，但分组后没有结果")
                    return {
                        "query": query,
                        "comparison": {},
                        "total_products": total_products,
                        "search_time": result.get("search_time", 0),
                        "message": f"找到 {total_products} 个商品，但无法进行价格对比。请尝试使用更具体的关键词。",
                        "data_source": result.get("data_source", "unknown")
                    }
                else:
                    return {
                        "query": query,
                        "comparison": {},
                        "total_products": 0,
                        "search_time": 0,
                        "message": "未找到价格比较结果。请确保已上传商品数据到数据库，或尝试使用更具体的关键词。",
                        "data_source": result.get("data_source", "unknown")
                    }
        
        logger.info(f"价格对比完成，找到 {result.get('total_products', 0)} 个商品，{len(result.get('comparison', {}))} 个商品组")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing prices: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"价格对比失败: {str(e)}")

@router.get("/products/{product_id}/price-tracking")
async def track_price_changes(
    product_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """价格变化追踪"""
    try:
        price_service = get_price_service(db)
        return await price_service.track_price_changes(product_id, days)
    except Exception as e:
        logger.error(f"Error tracking price changes: {e}")
        raise HTTPException(status_code=500, detail="价格追踪失败")

@router.post("/best-deal", response_model=BestDealResponse)
async def get_best_deal(
    request: BestDealRequest,
    db: Session = Depends(get_db)
):
    """获取最佳优惠方案"""
    try:
        price_service = get_price_service(db)
        return await price_service.get_best_deal(request)
    except Exception as e:
        logger.error(f"Error getting best deal: {e}")
        raise HTTPException(status_code=500, detail="获取优惠方案失败")

# 优惠券管理
@router.post("/coupons", response_model=CouponResponse)
async def create_coupon(
    coupon: CouponCreate,
    db: Session = Depends(get_db)
):
    """创建优惠券"""
    try:
        price_service = get_price_service(db)
        return await price_service.create_coupon(coupon.dict())
    except Exception as e:
        logger.error(f"Error creating coupon: {e}")
        raise HTTPException(status_code=500, detail="创建优惠券失败")

@router.get("/coupons")
async def get_coupons(
    platform: Optional[PlatformType] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """查询可用优惠券"""
    try:
        from ..models.models import Coupon
        query = db.query(Coupon)

        if platform:
            query = query.filter(Coupon.platform == platform)

        current_time = datetime.now()
        query = query.filter(
            db.or_(
                Coupon.end_date.is_(None),
                Coupon.end_date > current_time
            )
        )

        coupons = query.all()
        return [CouponResponse.from_orm(coupon) for coupon in coupons]
    except Exception as e:
        logger.error(f"Error getting coupons: {e}")
        raise HTTPException(status_code=500, detail="获取优惠券失败")

# 用户个性化功能
@router.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    user_id: int,
    category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """个性化推荐"""
    try:
        request = RecommendationRequest(
            user_id=user_id,
            category=category,
            limit=limit
        )
        shopping_service = get_shopping_service(db)
        return await shopping_service.get_user_recommendations(request)
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="获取推荐失败")

@router.get("/users/{user_id}/purchase-analysis", response_model=PurchaseAnalysisResponse)
async def get_purchase_analysis(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """用户购买行为分析"""
    try:
        request = PurchaseAnalysisRequest(
            user_id=user_id,
            days=days
        )
        shopping_service = get_shopping_service(db)
        return await shopping_service.analyze_purchase_behavior(request)
    except Exception as e:
        logger.error(f"Error analyzing purchase behavior: {e}")
        raise HTTPException(status_code=500, detail="分析购买行为失败")

@router.get("/users/{user_id}/coupon-statistics")
async def get_user_coupon_statistics(
    user_id: int,
    db: Session = Depends(get_db)
):
    """用户优惠券统计"""
    try:
        price_service = get_price_service(db)
        return await price_service.get_user_coupon_statistics(user_id)
    except Exception as e:
        logger.error(f"Error getting user coupon statistics: {e}")
        raise HTTPException(status_code=500, detail="获取优惠券统计失败")

@router.get("/users/{user_id}/price-alerts")
async def get_price_alerts(
    user_id: int,
    threshold_percent: float = 10.0,
    db: Session = Depends(get_db)
):
    """价格提醒"""
    try:
        price_service = get_price_service(db)
        return await price_service.get_price_alerts(user_id, threshold_percent)
    except Exception as e:
        logger.error(f"Error getting price alerts: {e}")
        raise HTTPException(status_code=500, detail="获取价格提醒失败")

# 商品规格管理
@router.post("/products/{product_id}/specs", response_model=ProductSpecResponse)
async def add_product_spec(
    product_id: int,
    spec: ProductSpecCreate,
    db: Session = Depends(get_db)
):
    """添加商品规格"""
    try:
        from ..models.models import ProductSpec

        # 验证商品存在
        from ..models.models import Product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")

        # 创建规格
        product_spec = ProductSpec(
            product_id=product_id,
            spec_name=spec.spec_name,
            spec_value=spec.spec_value
        )
        db.add(product_spec)
        db.commit()
        db.refresh(product_spec)

        return ProductSpecResponse.from_orm(product_spec)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding product spec: {e}")
        raise HTTPException(status_code=500, detail="添加商品规格失败")

@router.get("/products/{product_id}/specs")
async def get_product_specs(
    product_id: int,
    db: Session = Depends(get_db)
):
    """获取商品规格"""
    try:
        from ..models.models import ProductSpec
        specs = db.query(ProductSpec).filter(ProductSpec.product_id == product_id).all()
        return [ProductSpecResponse.from_orm(spec) for spec in specs]
    except Exception as e:
        logger.error(f"Error getting product specs: {e}")
        raise HTTPException(status_code=500, detail="获取商品规格失败")

# 系统管理功能
@router.get("/statistics")
async def get_shopping_statistics(
    db: Session = Depends(get_db)
):
    """获取购物助手统计信息"""
    try:
        from ..models.models import Product, PriceHistory, UserPreference, ImageSearchHistory

        stats = {
            "total_products": db.query(Product).count(),
            "total_price_records": db.query(PriceHistory).count(),
            "total_user_preferences": db.query(UserPreference).count(),
            "total_image_searches": db.query(ImageSearchHistory).count(),
            "platform_distribution": {},
            "category_distribution": {}
        }

        # 平台分布
        platforms = db.query(Product.platform, func.count(Product.id)).group_by(Product.platform).all()
        stats["platform_distribution"] = {platform: count for platform, count in platforms}

        # 类别分布
        categories = db.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
        stats["category_distribution"] = {category: count for category, count in categories if category}

        return stats
    except Exception as e:
        logger.error(f"Error getting shopping statistics: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")

@router.post("/update-image-similarity-index")
async def update_image_similarity_index(
    db: Session = Depends(get_db)
):
    """更新图片相似度索引"""
    try:
        image_service = get_image_service(db)
        await image_service.update_image_similarity_index()
        return {"message": "图片相似度索引更新成功"}
    except Exception as e:
        logger.error(f"Error updating image similarity index: {e}")
        raise HTTPException(status_code=500, detail="更新图片相似度索引失败")

@router.get("/image-statistics")
async def get_image_statistics(
    db: Session = Depends(get_db)
):
    """获取图片统计信息"""
    try:
        image_service = get_image_service(db)
        return await image_service.get_image_statistics()
    except Exception as e:
        logger.error(f"Error getting image statistics: {e}")
        raise HTTPException(status_code=500, detail="获取图片统计信息失败")

# 场景化推荐相关API
@router.post("/scenario/parse")
async def parse_user_scenario(
    user_input: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """解析用户场景"""
    try:
        result = await scenario_service.parse_scenario_from_input(user_input, user_id)
        return result
    except Exception as e:
        logger.error(f"Error parsing scenario: {e}")
        raise HTTPException(status_code=500, detail="场景解析失败")

@router.get("/scenario/recommendations")
async def get_scenario_recommendations(
    user_id: int,
    scenario_id: int,
    query: str = "",
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """基于场景获取推荐"""
    try:
        recommendations = await scenario_service.get_scenario_based_recommendations(
            user_id, scenario_id, query, limit
        )
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Error getting scenario recommendations: {e}")
        raise HTTPException(status_code=500, detail="场景推荐失败")

@router.get("/scenario/knowledge/{scenario_id}")
async def get_scenario_knowledge(
    scenario_id: int,
    db: Session = Depends(get_db)
):
    """获取场景相关知识"""
    try:
        knowledge = await scenario_service.enrich_scenario_with_knowledge(scenario_id)
        return knowledge
    except Exception as e:
        logger.error(f"Error getting scenario knowledge: {e}")
        raise HTTPException(status_code=500, detail="获取场景知识失败")

@router.post("/behavior/track")
async def track_user_behavior(
    user_id: int,
    behavior_type: str,
    behavior_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """记录用户行为"""
    try:
        success = await scenario_service.track_user_behavior(user_id, behavior_type, behavior_data)
        if success:
            return {"message": "行为记录成功"}
        else:
            raise HTTPException(status_code=500, detail="行为记录失败")
    except Exception as e:
        logger.error(f"Error tracking behavior: {e}")
        raise HTTPException(status_code=500, detail="行为追踪失败")

@router.get("/potential-needs/{user_id}")
async def get_potential_needs(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取用户潜在需求"""
    try:
        needs = await scenario_service.discover_potential_needs(user_id)
        return {"potential_needs": needs}
    except Exception as e:
        logger.error(f"Error discovering potential needs: {e}")
        raise HTTPException(status_code=500, detail="潜在需求发现失败")

@router.get("/user-insight/{user_id}")
async def get_user_insight_report(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取用户洞察报告"""
    try:
        report = await scenario_service.generate_user_insight_report(user_id)
        return report
    except Exception as e:
        logger.error(f"Error generating user insight report: {e}")
        raise HTTPException(status_code=500, detail="用户洞察报告生成失败")

# 强化学习相关API
@router.post("/preference/update")
async def update_preference_model(
    user_id: int,
    feedback_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """更新偏好模型"""
    try:
        success = await rl_service.update_preference_model(user_id, feedback_data)
        if success:
            return {"message": "偏好模型更新成功"}
        else:
            raise HTTPException(status_code=500, detail="偏好模型更新失败")
    except Exception as e:
        logger.error(f"Error updating preference model: {e}")
        raise HTTPException(status_code=500, detail="偏好模型更新失败")

@router.get("/optimization/report/{user_id}")
async def get_optimization_report(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取优化报告"""
    try:
        report = await rl_service.get_optimization_report(user_id)
        return report
    except Exception as e:
        logger.error(f"Error getting optimization report: {e}")
        raise HTTPException(status_code=500, detail="优化报告获取失败")

# 场景标签管理
@router.get("/scenario/tags")
async def get_scenario_tags(
    category: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取场景标签"""
    try:
        from ..models.models import ScenarioTag
        query = db.query(ScenarioTag)

        if category:
            query = query.filter(ScenarioTag.tag_category == category)

        tags = query.order_by(desc(ScenarioTag.usage_count)).limit(limit).all()
        return {"tags": tags}
    except Exception as e:
        logger.error(f"Error getting scenario tags: {e}")
        raise HTTPException(status_code=500, detail="获取场景标签失败")

@router.post("/scenario/products/{product_id}/map")
async def map_product_to_scenario(
    product_id: int,
    scenario_tag: str,
    match_score: float,
    db: Session = Depends(get_db)
):
    """映射商品到场景"""
    try:
        from ..models.models import ProductScenarioMapping

        # 验证商品存在
        from ..models.models import Product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")

        # 创建映射
        mapping = ProductScenarioMapping(
            product_id=product_id,
            scenario_tag=scenario_tag,
            match_score=match_score
        )
        db.add(mapping)
        db.commit()

        return {"message": "场景映射成功", "mapping_id": mapping.id}
    except Exception as e:
        logger.error(f"Error mapping product to scenario: {e}")
        raise HTTPException(status_code=500, detail="场景映射失败")

# 用户行为分析
@router.get("/behavior/analysis/{user_id}")
async def analyze_user_behavior(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """分析用户行为"""
    try:
        from datetime import datetime, timedelta
        from ..models.models import UserBehavior

        # 获取用户行为
        behaviors = db.query(UserBehavior).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.timestamp >= datetime.now() - timedelta(days=days)
        ).all()

        # 分析行为模式
        behavior_stats = {}
        category_stats = {}

        for behavior in behaviors:
            behavior_type = behavior.behavior_type
            behavior_stats[behavior_type] = behavior_stats.get(behavior_type, 0) + 1

            try:
                import json
                behavior_data = json.loads(behavior.behavior_data)
                category = behavior_data.get('category')
                if category:
                    category_stats[category] = category_stats.get(category, 0) + 1
            except:
                continue

        return {
            "total_behaviors": len(behaviors),
            "behavior_stats": behavior_stats,
            "category_stats": category_stats,
            "analysis_period_days": days
        }
    except Exception as e:
        logger.error(f"Error analyzing user behavior: {e}")
        raise HTTPException(status_code=500, detail="用户行为分析失败")

# 知识库管理
@router.post("/scenario/knowledge")
async def add_scenario_knowledge(
    scenario_type: str,
    knowledge_title: str,
    knowledge_content: str,
    source_type: str = "manual",
    confidence_score: float = 0.8,
    db: Session = Depends(get_db)
):
    """添加场景知识"""
    try:
        from ..models.models import ScenarioKnowledge

        knowledge = ScenarioKnowledge(
            scenario_type=scenario_type,
            knowledge_title=knowledge_title,
            knowledge_content=knowledge_content,
            source_type=source_type,
            confidence_score=confidence_score
        )
        db.add(knowledge)
        db.commit()
        db.refresh(knowledge)

        return {"message": "知识添加成功", "knowledge_id": knowledge.id}
    except Exception as e:
        logger.error(f"Error adding scenario knowledge: {e}")
        raise HTTPException(status_code=500, detail="场景知识添加失败")

@router.get("/scenario/knowledge")
async def get_scenario_knowledge_base(
    scenario_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取场景知识库"""
    try:
        from ..models.models import ScenarioKnowledge
        query = db.query(ScenarioKnowledge)

        if scenario_type:
            query = query.filter(ScenarioKnowledge.scenario_type == scenario_type)

        knowledge_list = query.order_by(desc(ScenarioKnowledge.confidence_score)).limit(limit).all()
        return {"knowledge_base": knowledge_list}
    except Exception as e:
        logger.error(f"Error getting scenario knowledge base: {e}")
        raise HTTPException(status_code=500, detail="获取场景知识库失败")