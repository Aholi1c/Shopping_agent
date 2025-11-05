"""
商品数据管理API
用于上传、管理静态商品数据库
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import json
import csv
import io

from ..core.database import get_db
from ..models.models import Product, ProductSpec, PriceHistory
from ..models.schemas import PlatformType

logger = logging.getLogger(__name__)

router = APIRouter()

class ProductUploadItem(BaseModel):
    """单个商品上传项"""
    platform: str = Field(..., description="平台名称: jd, taobao, pdd, amazon等")
    product_id: str = Field(..., description="平台商品ID")
    title: str = Field(..., description="商品标题")
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    price: float = Field(..., description="当前价格")
    original_price: Optional[float] = None
    discount_rate: Optional[float] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    sales_count: Optional[int] = None
    stock_status: Optional[str] = None
    specs: Optional[Dict[str, str]] = None  # 商品规格参数

class ProductUploadRequest(BaseModel):
    """批量商品上传请求"""
    products: List[ProductUploadItem] = Field(..., description="商品列表")

class ProductUpdateRequest(BaseModel):
    """商品更新请求"""
    title: Optional[str] = None
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

@router.post("/products/upload", summary="批量上传商品数据")
async def upload_products(
    request: ProductUploadRequest,
    db: Session = Depends(get_db)
):
    """
    批量上传商品数据到数据库
    
    示例：
    ```json
    {
      "products": [
        {
          "platform": "jd",
          "product_id": "123456",
          "title": "iPhone 15 Pro",
          "price": 7999.0,
          "category": "手机",
          "brand": "Apple"
        }
      ]
    }
    ```
    """
    try:
        success_count = 0
        error_count = 0
        errors = []
        
        for product_data in request.products:
            try:
                # 检查商品是否已存在
                existing_product = db.query(Product).filter(
                    Product.platform == product_data.platform,
                    Product.product_id == product_data.product_id
                ).first()
                
                if existing_product:
                    # 更新现有商品
                    existing_product.title = product_data.title
                    existing_product.description = product_data.description
                    existing_product.category = product_data.category
                    existing_product.brand = product_data.brand
                    existing_product.price = product_data.price
                    existing_product.original_price = product_data.original_price or product_data.price
                    existing_product.discount_rate = product_data.discount_rate or 0.0
                    existing_product.image_url = product_data.image_url
                    existing_product.product_url = product_data.product_url
                    existing_product.rating = product_data.rating
                    existing_product.review_count = product_data.review_count
                    existing_product.sales_count = product_data.sales_count
                    existing_product.stock_status = product_data.stock_status
                    existing_product.updated_at = datetime.utcnow()
                    
                    product = existing_product
                    logger.info(f"更新商品: {product_data.platform}/{product_data.product_id}")
                else:
                    # 创建新商品
                    product = Product(
                        platform=product_data.platform,
                        product_id=product_data.product_id,
                        title=product_data.title,
                        description=product_data.description,
                        category=product_data.category,
                        brand=product_data.brand,
                        price=product_data.price,
                        original_price=product_data.original_price or product_data.price,
                        discount_rate=product_data.discount_rate or 0.0,
                        image_url=product_data.image_url,
                        product_url=product_data.product_url,
                        rating=product_data.rating,
                        review_count=product_data.review_count,
                        sales_count=product_data.sales_count,
                        stock_status=product_data.stock_status or "有货"
                    )
                    db.add(product)
                    db.flush()  # 获取product.id
                    logger.info(f"创建商品: {product_data.platform}/{product_data.product_id}")
                
                # 保存商品规格
                if product_data.specs:
                    # 删除旧规格
                    db.query(ProductSpec).filter(ProductSpec.product_id == product.id).delete()
                    
                    # 添加新规格
                    for spec_name, spec_value in product_data.specs.items():
                        spec = ProductSpec(
                            product_id=product.id,
                            spec_name=spec_name,
                            spec_value=str(spec_value)
                        )
                        db.add(spec)
                
                # 记录价格历史
                if product.price:
                    price_history = PriceHistory(
                        product_id=product.id,
                        price=product.price,
                        original_price=product.original_price,
                        discount_rate=product.discount_rate,
                        timestamp=datetime.utcnow()
                    )
                    db.add(price_history)
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                error_msg = f"商品 {product_data.platform}/{product_data.product_id}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"成功上传 {success_count} 个商品，失败 {error_count} 个",
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[:10]  # 只返回前10个错误
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"批量上传商品失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")

# 暂时注释掉文件上传功能，避免multipart依赖问题
# 用户可以通过 /products/upload 端点使用JSON body上传数据
# @router.post("/products/upload/json", summary="从JSON文件上传商品数据")
# async def upload_products_from_json(
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
#     """
#     从JSON文件批量上传商品数据
#     """
#     pass

# @router.post("/products/upload/csv", summary="从CSV文件上传商品数据")
# async def upload_products_from_csv(
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
#     """
#     从CSV文件批量上传商品数据
#     """
#     pass

@router.get("/products", summary="查询商品列表")
async def list_products(
    platform: Optional[str] = Query(None, description="平台过滤"),
    category: Optional[str] = Query(None, description="类别过滤"),
    brand: Optional[str] = Query(None, description="品牌过滤"),
    keyword: Optional[str] = Query(None, description="关键词搜索（标题）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """查询商品列表，支持过滤和分页"""
    try:
        query = db.query(Product)
        
        # 应用过滤条件
        if platform:
            query = query.filter(Product.platform == platform)
        if category:
            query = query.filter(Product.category == category)
        if brand:
            query = query.filter(Product.brand == brand)
        if keyword:
            query = query.filter(Product.title.contains(keyword))
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        products = query.order_by(Product.created_at.desc()).offset(offset).limit(page_size).all()
        
        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "products": [
                {
                    "id": p.id,
                    "platform": p.platform,
                    "product_id": p.product_id,
                    "title": p.title,
                    "price": p.price,
                    "category": p.category,
                    "brand": p.brand,
                    "rating": p.rating,
                    "review_count": p.review_count,
                    "image_url": p.image_url,
                    "product_url": p.product_url,
                    "created_at": p.created_at.isoformat(),
                    "updated_at": p.updated_at.isoformat()
                }
                for p in products
            ]
        }
        
    except Exception as e:
        logger.error(f"查询商品列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.get("/products/{product_id}", summary="获取商品详情")
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """获取单个商品详情"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        
        # 获取商品规格
        specs = db.query(ProductSpec).filter(ProductSpec.product_id == product.id).all()
        specs_dict = {spec.spec_name: spec.spec_value for spec in specs}
        
        # 获取价格历史
        price_history = db.query(PriceHistory).filter(
            PriceHistory.product_id == product.id
        ).order_by(PriceHistory.timestamp.desc()).limit(30).all()
        
        return {
            "success": True,
            "product": {
                "id": product.id,
                "platform": product.platform,
                "product_id": product.product_id,
                "title": product.title,
                "description": product.description,
                "category": product.category,
                "brand": product.brand,
                "price": product.price,
                "original_price": product.original_price,
                "discount_rate": product.discount_rate,
                "image_url": product.image_url,
                "product_url": product.product_url,
                "rating": product.rating,
                "review_count": product.review_count,
                "sales_count": product.sales_count,
                "stock_status": product.stock_status,
                "specs": specs_dict,
                "price_history": [
                    {
                        "price": ph.price,
                        "timestamp": ph.timestamp.isoformat()
                    }
                    for ph in price_history
                ],
                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取商品详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.put("/products/{product_id}", summary="更新商品信息")
async def update_product(
    product_id: int,
    request: ProductUpdateRequest,
    db: Session = Depends(get_db)
):
    """更新商品信息"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        
        # 更新字段
        update_data = request.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(product, key, value)
        
        product.updated_at = datetime.utcnow()
        
        # 如果价格变化，记录价格历史
        if 'price' in update_data:
            price_history = PriceHistory(
                product_id=product.id,
                price=product.price,
                original_price=product.original_price,
                discount_rate=product.discount_rate,
                timestamp=datetime.utcnow()
            )
            db.add(price_history)
        
        db.commit()
        
        return {
            "success": True,
            "message": "商品更新成功",
            "product_id": product_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新商品失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/products/{product_id}", summary="删除商品")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """删除商品"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        
        # 删除关联数据
        db.query(ProductSpec).filter(ProductSpec.product_id == product.id).delete()
        db.query(PriceHistory).filter(PriceHistory.product_id == product.id).delete()
        
        # 删除商品
        db.delete(product)
        db.commit()
        
        return {
            "success": True,
            "message": "商品删除成功",
            "product_id": product_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除商品失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.get("/products/stats", summary="获取商品统计信息")
async def get_product_stats(
    db: Session = Depends(get_db)
):
    """获取商品数据库统计信息"""
    try:
        total_products = db.query(Product).count()
        
        # 按平台统计
        platform_stats = db.query(
            Product.platform,
            func.count(Product.id).label('count')
        ).group_by(Product.platform).all()
        
        # 按类别统计
        category_stats = db.query(
            Product.category,
            func.count(Product.id).label('count')
        ).filter(Product.category.isnot(None)).group_by(Product.category).limit(10).all()
        
        return {
            "success": True,
            "total_products": total_products,
            "platform_distribution": {platform: count for platform, count in platform_stats},
            "category_distribution": {category: count for category, count in category_stats if category}
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

