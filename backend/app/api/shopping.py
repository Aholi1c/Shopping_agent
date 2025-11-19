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
    """Multi-platform product search"""
    try:
        shopping_service = get_shopping_service(db)
        return await shopping_service.search_products(request, user_id)
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail="Failed to search products")

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product_details(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get product details"""
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
        raise HTTPException(status_code=500, detail="Failed to get product details")

@router.get("/products/{product_id}/price-history")
async def get_price_history(
    product_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get price history"""
    try:
        shopping_service = get_shopping_service(db)
        return await shopping_service.get_price_history(product_id, days)
    except Exception as e:
        logger.error(f"Error getting price history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get price history")

@router.post("/compare")
async def compare_products(
    product_ids: List[int],
    db: Session = Depends(get_db)
):
    """Compare products"""
    try:
        if len(product_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 products are required for comparison")

        shopping_service = get_shopping_service(db)
        return await shopping_service.compare_products(product_ids)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing products: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare products")

@router.post("/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """Create product"""
    try:
        shopping_service = get_shopping_service(db)
        return await shopping_service.create_product(product)
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail="Failed to create product")

# 图片识别和搜索
@router.post("/image-recognition", response_model=ImageRecognitionResponse)
async def recognize_product_image(
    request: ImageRecognitionRequest,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Product image recognition"""
    try:
        image_service = get_image_service(db)
        return await image_service.recognize_product(request, user_id)
    except Exception as e:
        logger.error(f"Error in image recognition: {e}")
        raise HTTPException(status_code=500, detail="Image recognition failed")

@router.post("/image-search", response_model=ImageSearchResponse)
async def search_by_image(
    request: ImageSearchRequest,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Search by image"""
    try:
        image_service = get_image_service(db)
        return await image_service.search_by_image(request, user_id)
    except Exception as e:
        logger.error(f"Error in image search: {e}")
        raise HTTPException(status_code=500, detail="Image search failed")

@router.get("/products/{product_id}/similar", response_model=SimilarProductResponse)
async def get_similar_products(
    product_id: int,
    platform: PlatformType,
    limit: int = 10,
    include_visual: bool = True,
    include_semantic: bool = True,
    db: Session = Depends(get_db)
):
    """Get similar products"""
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
        raise HTTPException(status_code=500, detail="Failed to get similar products")

@router.post("/upload-image-features")
async def upload_image_features(
    product_id: int,
    image_url: str,
    db: Session = Depends(get_db)
):
    """Upload image and extract features"""
    try:
        image_service = get_image_service(db)
        success = await image_service.extract_image_features(image_url, product_id)
        if success:
            return {"message": "Image feature extraction successful", "product_id": product_id}
        else:
            raise HTTPException(status_code=500, detail="Image feature extraction failed")
    except Exception as e:
        logger.error(f"Error uploading image features: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image features")

# 商品分析
@router.post("/product-analysis")
async def analyze_product(
    product_data: Dict[str, Any],
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Product analysis (based on product information)"""
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
        product_currency = product_data.get('currency') or product_data.get('currency_code') or 'CNY'  # 默认人民币
        
        # ⚠️ CRITICAL: If currency is missing, try to infer from URL
        if product_currency == 'CNY' and product_data.get('url'):
            url = product_data.get('url', '').lower()
            if 'amazon.com' in url and 'amazon.cn' not in url and 'amazon.co.uk' not in url and 'amazon.com.hk' not in url:
                product_currency = 'USD'
                logger.warning(f"Currency not provided, inferred USD from URL: {url}")
            elif 'amazon.com.hk' in url or 'amazon.hk' in url:
                product_currency = 'HKD'
                logger.warning(f"Currency not provided, inferred HKD from URL: {url}")
            elif 'amazon.cn' in url:
                product_currency = 'CNY'
            elif '.hk' in url:
                product_currency = 'HKD'
                logger.warning(f"Currency not provided, inferred HKD from URL: {url}")
        
        # Log currency information for debugging
        logger.info(f"Product currency: {product_currency}, Price: {product_price}, URL: {product_data.get('url', 'N/A')}")
        
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
        
        # 货币转换汇率（转换为CNY）
        exchange_rates = {
            'CNY': 1.0,
            'HKD': 0.92,  # 1 HKD = 0.92 CNY
            'USD': 7.2,   # 1 USD = 7.2 CNY
            'EUR': 7.8,   # 1 EUR = 7.8 CNY
            'GBP': 9.1,   # 1 GBP = 9.1 CNY
            'JPY': 0.048, # 1 JPY = 0.048 CNY
            'AUD': 4.8,   # 1 AUD = 4.8 CNY
            'SGD': 5.3,   # 1 SGD = 5.3 CNY
            'CAD': 5.3    # 1 CAD = 5.3 CNY
        }
        
        # 将当前商品价格转换为CNY（用于与数据库中的价格比较）
        exchange_rate = exchange_rates.get(product_currency, 1.0)
        product_price_cny = product_price * exchange_rate
        
        logger.info(f"Starting product analysis: {product_name}, Price: {currency_symbol}{product_price} ({product_currency}), Converted to CNY: ¥{product_price_cny:.2f}, Platform: {product_platform}")
        
        # 验证必要的商品信息
        if not product_name:
            raise HTTPException(status_code=400, detail="Product name cannot be empty, please ensure you are on a product detail page")
        
        # 验证LLM服务是否可用
        if not llm_service:
            raise HTTPException(status_code=500, detail="LLM service not initialized, please check configuration")
        
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
                    
                    # 计算节省潜力（使用CNY价格进行比较）
                    comparison = price_comparison.get("comparison", {})
                    savings_potential = 0
                    savings_potential_original = 0  # 原始货币的节省
                    min_prices = []
                    
                    if comparison:
                        # 找到最低价格（数据库中的价格都是CNY）
                        for product_key, data in comparison.items():
                            if isinstance(data, dict) and "min_price" in data:
                                min_prices.append(data["min_price"])
                        
                        if min_prices:
                            lowest_price_cny = min(min_prices)
                            # 使用CNY价格进行比较
                            if product_price_cny > 0 and product_price_cny > lowest_price_cny:
                                savings_potential = product_price_cny - lowest_price_cny
                                # 转换为原始货币的节省金额
                                savings_potential_original = savings_potential / exchange_rate
                    
                    price_analysis = {
                        "current_price": product_price,
                        "current_price_cny": product_price_cny,  # 转换为CNY后的价格
                        "currency": product_currency,
                        "exchange_rate": exchange_rate,
                        "platform": product_platform,
                        "comparison": comparison,
                        "savings_potential": savings_potential,  # CNY节省金额
                        "savings_potential_original": savings_potential_original,  # 原始货币节省金额
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
        
        # 3. Use LLM to generate comprehensive analysis
        # Build product details text
        product_details_text = f"Product Name: {product_name}\nCurrent Price: {currency_symbol}{product_price} ({product_currency})\nPlatform: {product_platform}"
        
        if product_description:
            product_details_text += f"\n\nProduct Description:\n{product_description[:1000]}"  # Limit length to avoid too many tokens
        
        if product_parameters:
            params_text = "\n".join([f"{k}: {v}" for k, v in list(product_parameters.items())[:20]])  # Max 20 parameters
            product_details_text += f"\n\nProduct Parameters:\n{params_text}"
        
        # Build price comparison text (note currency units and conversion)
        price_comparison_text = ""
        if price_analysis.get("comparison"):
            current_price_cny = price_analysis.get("current_price_cny", product_price_cny)
            price_comparison_text = f"\n\nPrice Comparison on Other Platforms:\n"
            price_comparison_text += f"- Current Product: {currency_symbol}{product_price} ({product_currency}) = ¥{current_price_cny:.2f} (CNY)\n"
            price_comparison_text += f"- Exchange Rate: 1 {product_currency} = {exchange_rate} CNY\n"
            price_comparison_text += f"- All comparison prices below are in CNY (Chinese Yuan):\n"
            
            for platform, data in price_analysis.get("comparison", {}).items():
                if isinstance(data, dict):
                    if "min_price" in data:
                        min_price = data.get('min_price', 0)
                        price_comparison_text += f"  - {platform}: ¥{min_price:.2f}"
                        # 显示价格差异
                        if current_price_cny > 0:
                            diff = current_price_cny - min_price
                            diff_percent = (diff / current_price_cny) * 100
                            if diff > 0:
                                price_comparison_text += f" (Saves ¥{diff:.2f}, {diff_percent:.1f}% cheaper)"
                            elif diff < 0:
                                price_comparison_text += f" (More expensive by ¥{abs(diff):.2f})"
                        price_comparison_text += "\n"
            
            # 显示最低价格和节省潜力
            if price_analysis.get("lowest_found_price"):
                lowest_price = price_analysis.get("lowest_found_price")
                savings = price_analysis.get("savings_potential", 0)
                if savings > 0:
                    savings_original = price_analysis.get("savings_potential_original", 0)
                    price_comparison_text += f"\n- Lowest Price Found: ¥{lowest_price:.2f} (CNY)\n"
                    price_comparison_text += f"- Potential Savings: {currency_symbol}{savings_original:.2f} ({product_currency}) = ¥{savings:.2f} (CNY)\n"
        
        analysis_prompt = f"""
        Please provide a comprehensive analysis of the following product:

        {product_details_text}
        
        Price Analysis Results: {price_analysis}
        {price_comparison_text}
        Risk Assessment Results: {risk_analysis}
        
        ⚠️ CRITICAL: CURRENCY UNIT REQUIREMENTS ⚠️
        - PRIMARY CURRENCY: The product price is {currency_symbol}{product_price} in {product_currency}
        - You MUST analyze prices primarily using {product_currency} ({currency_symbol})
        - When discussing the current product, ALWAYS use {product_currency} as the primary unit
        - CNY conversion (¥{product_price_cny:.2f}) is ONLY for comparing with other platforms
        - Exchange rate: 1 {product_currency} = {exchange_rate} CNY
        - Database comparison prices are in CNY, but your main analysis should focus on {product_currency}
        
        Please provide your analysis following these requirements:
        
        1. Product overview and features (based on product description and parameter information)
           - Focus on product quality, features, and specifications
        
        2. Price reasonableness analysis (PRIMARY: Use {product_currency}):
           - Start with: "The current price is {currency_symbol}{product_price} ({product_currency})"
           - Analyze if this price is reasonable for this product in {product_currency}
           - Compare with typical market prices for similar products (mention if you're converting from CNY for reference)
           - Example format: "At {currency_symbol}{product_price} ({product_currency}), this product is [reasonable/expensive/cheap] compared to similar items in the market"
        
        3. Price comparison with other platforms:
           - Current product: {currency_symbol}{product_price} ({product_currency}) = ¥{product_price_cny:.2f} (CNY, converted)
           - Other platforms: All prices shown in CNY
           - Clearly state: "Compared to other platforms (prices in CNY), this product at {currency_symbol}{product_price} ({product_currency}) is..."
           - Show savings in BOTH currencies if applicable: {currency_symbol}[amount] ({product_currency}) / ¥[amount] (CNY)
        
        4. Risk assessment and recommendations
           - Consider product quality, seller reputation, shipping, etc.
        
        5. Purchase recommendation (buy now / wait for price drop / consider carefully)
           - Base recommendation on {product_currency} price primarily
        
        6. Important considerations:
           - REMINDER: The actual purchase price will be in {product_currency} ({currency_symbol}{product_price})
           - Exchange rate: 1 {product_currency} = {exchange_rate} CNY
           - If comparing with CNY prices, always mention the conversion
        
        ⚠️ REMEMBER: Your analysis should primarily use {product_currency} ({currency_symbol}). CNY is only for platform comparison.
        
        Please use clear and professional language. Always clearly label currency units ({product_currency} vs CNY) to avoid confusion.
        If product description is provided, please incorporate it for more accurate analysis.
        """
        
        # 调用LLM生成分析
        try:
            logger.info(f"Calling LLM to generate comprehensive analysis... Currency: {product_currency}, Price: {currency_symbol}{product_price}")
            
            # 构建系统提示词，强调货币单位
            system_prompt = f"""You are a professional shopping assistant, skilled at analyzing product prices, quality, and risks.

🚨 CRITICAL CURRENCY INSTRUCTIONS - READ CAREFULLY 🚨
The product you are analyzing has the following price information:
- PRICE: {currency_symbol}{product_price}
- CURRENCY: {product_currency}
- This is NOT CNY (Chinese Yuan) unless explicitly stated as CNY

YOU MUST:
1. ALWAYS use {product_currency} ({currency_symbol}) as the PRIMARY currency in your analysis
2. NEVER assume the price is in CNY unless the currency is explicitly CNY
3. When you see {currency_symbol}{product_price}, this means {product_price} {product_currency}, NOT {product_price} CNY
4. If the currency is USD, $115 means 115 US Dollars, NOT 115 Chinese Yuan
5. If the currency is HKD, HK$115 means 115 Hong Kong Dollars, NOT 115 Chinese Yuan

CORRECT Examples:
- For USD: "The product costs $115 (USD)" ✅
- For USD: "At $115 (USD), this is equivalent to approximately ¥828 (CNY) for comparison" ✅
- For HKD: "The product costs HK$115 (HKD)" ✅

WRONG Examples (DO NOT DO THIS):
- "The product costs ¥115" ❌ WRONG if currency is USD
- "The price is 115 yuan" ❌ WRONG if currency is USD
- "At 115 CNY" ❌ WRONG if currency is USD

Remember: The user will pay {currency_symbol}{product_price} in {product_currency}. Your analysis must reflect this."""
            
            llm_response = await llm_service.chat_completion([
                {"role": "system", "content": system_prompt},
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
                logger.warning("LLM returned empty analysis content")
                comprehensive_analysis = "Analysis completed but no detailed report generated. Please check LLM service configuration."
            
            logger.info(f"LLM analysis completed, generated {len(comprehensive_analysis)} characters of analysis content")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            comprehensive_analysis = f"LLM analysis failed: {str(e)}. Please check LLM service configuration (currently using: {settings.llm_provider})"
        
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
                    "reason": "Comprehensive recommendation based on price and risk analysis"
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing product: {e}")
        raise HTTPException(status_code=500, detail=f"Product analysis failed: {str(e)}")

# 价格对比和优惠计算
class PriceComparisonRequest(BaseModel):
    """Price comparison request"""
    query: str = Field(..., description="Product name or search keywords")
    platforms: Optional[List[str]] = Field(None, description="Platform list, e.g. ['jd', 'taobao', 'pdd']")

@router.post("/price-comparison")
async def compare_prices(
    request: PriceComparisonRequest,
    db: Session = Depends(get_db)
):
    """Multi-platform price comparison - uses database data (from products_data.json)"""
    try:
        query = request.query
        platforms_param = request.platforms
        
        if not query:
            raise HTTPException(status_code=400, detail="Missing required parameter: query")
        
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
                        "message": "Product not found, please try using more specific keywords. If Onebound API is configured, please check if the API key is correct.",
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
                        "message": f"Found {total_products} products, but unable to perform price comparison. Please try using more specific keywords.",
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