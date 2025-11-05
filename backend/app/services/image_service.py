import asyncio
import json
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    print("⚠️  PIL未安装，图像处理功能将不可用。请运行: pip install Pillow")
import io
import requests
import hashlib

from ..models.models import (
    Product, ProductImage, ImageSimilarity, ImageSearchHistory,
    User, ProductSpec
)
from ..models.schemas import (
    ImageRecognitionRequest, ImageRecognitionResponse,
    ImageSearchRequest, ImageSearchResponse,
    SimilarProductRequest, SimilarProductResponse,
    ProductResponse, SimilarityType
)
from ..core.config import settings
from .llm_service import LLMService
from .shopping_service import ShoppingService

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self, db: Session, llm_service: LLMService, shopping_service: ShoppingService):
        self.db = db
        self.llm_service = llm_service
        self.shopping_service = shopping_service

        # 相似度权重
        self.similarity_weights = {
            SimilarityType.VISUAL: 0.4,
            SimilarityType.SEMANTIC: 0.3,
            SimilarityType.OVERALL: 1.0
        }

    async def recognize_product(self, request: ImageRecognitionRequest, user_id: Optional[int] = None) -> ImageRecognitionResponse:
        """商品图片识别"""
        try:
            # 1. 下载和处理图片
            image_features, image_hash = await self._process_image(request.image_url)

            # 2. 使用LLM进行商品识别
            recognition_result = await self._recognize_with_llm(request.image_url)

            # 3. 查找相似商品
            similar_products = await self._find_similar_by_image(image_features, request.platform)

            # 4. 记录搜索历史
            if user_id:
                await self._record_image_search(user_id, request.image_url, similar_products)

            return ImageRecognitionResponse(
                product_info=recognition_result.get("product_info"),
                confidence=recognition_result.get("confidence", 0.0),
                description=recognition_result.get("description", ""),
                similar_products=similar_products
            )

        except Exception as e:
            logger.error(f"Error in image recognition: {e}")
            return ImageRecognitionResponse(
                confidence=0.0,
                description="图片识别失败",
                similar_products=[]
            )

    async def search_by_image(self, request: ImageSearchRequest, user_id: Optional[int] = None) -> ImageSearchResponse:
        """以图搜图"""
        try:
            start_time = datetime.now()

            # 1. 处理查询图片
            query_features, query_hash = await self._process_image(request.image_url)

            # 2. 在数据库中查找相似图片
            similar_images = await self._find_similar_images(query_features, request.similarity_threshold)

            # 3. 获取对应的商品信息
            product_ids = list(set([img.product_id for img in similar_images if img.product_id]))
            products = self.db.query(Product).filter(Product.id.in_(product_ids)).all()

            # 4. 按相似度排序
            product_scores = {}
            for img in similar_images:
                if img.product_id in product_scores:
                    product_scores[img.product_id] = max(product_scores[img.product_id], img.similarity_score)
                else:
                    product_scores[img.product_id] = img.similarity_score

            sorted_products = sorted(products, key=lambda p: product_scores.get(p.id, 0), reverse=True)
            response_products = [ProductResponse.from_orm(p) for p in sorted_products[:request.limit]]
            similarity_scores = [product_scores.get(p.id, 0) for p in sorted_products[:request.limit]]

            # 5. 记录搜索历史
            if user_id:
                await self._record_image_search(user_id, request.image_url, response_products)

            search_time = (datetime.now() - start_time).total_seconds()

            return ImageSearchResponse(
                query_image=request.image_url,
                results=response_products,
                similarity_scores=similarity_scores,
                search_time=search_time
            )

        except Exception as e:
            logger.error(f"Error in image search: {e}")
            return ImageSearchResponse(
                query_image=request.image_url,
                results=[],
                similarity_scores=[],
                search_time=0.0
            )

    async def get_similar_products(self, request: SimilarProductRequest) -> SimilarProductResponse:
        """获取相似商品"""
        try:
            # 获取源商品
            source_product = self.db.query(Product).filter(Product.id == request.product_id).first()
            if not source_product:
                raise ValueError("Product not found")

            similar_products = []
            similarity_scores = []
            similarity_types = []

            if request.include_visual:
                # 基于视觉特征的相似度
                visual_similar = await self._find_visual_similar_products(source_product, request.limit)
                similar_products.extend(visual_similar)
                similarity_scores.extend([0.8] * len(visual_similar))  # 假设视觉相似度为0.8
                similarity_types.extend(["visual"] * len(visual_similar))

            if request.include_semantic:
                # 基于语义特征的相似度
                semantic_similar = await self._find_semantic_similar_products(source_product, request.limit)
                similar_products.extend(semantic_similar)
                similarity_scores.extend([0.6] * len(semantic_similar))  # 假设语义相似度为0.6
                similarity_types.extend(["semantic"] * len(semantic_similar))

            # 去重并按相似度排序
            seen_products = set()
            final_products = []
            final_scores = []
            final_types = []

            for product, score, sim_type in zip(similar_products, similarity_scores, similarity_types):
                if product.id not in seen_products and product.id != source_product.id:
                    seen_products.add(product.id)
                    final_products.append(product)
                    final_scores.append(score)
                    final_types.append(sim_type)

            # 按分数排序
            sorted_data = sorted(zip(final_products, final_scores, final_types),
                               key=lambda x: x[1], reverse=True)

            return SimilarProductResponse(
                source_product=ProductResponse.from_orm(source_product),
                similar_products=[ProductResponse.from_orm(p) for p, _, _ in sorted_data[:request.limit]],
                similarity_scores=[s for _, s, _ in sorted_data[:request.limit]],
                similarity_types=[t for _, _, t in sorted_data[:request.limit]]
            )

        except Exception as e:
            logger.error(f"Error getting similar products: {e}")
            return SimilarProductResponse(
                source_product=ProductResponse.from_orm(source_product) if 'source_product' in locals() else None,
                similar_products=[],
                similarity_scores=[],
                similarity_types=[]
            )

    async def _process_image(self, image_url: str) -> Tuple[List[float], str]:
        """处理图片并提取特征"""
        try:
            # 下载图片
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # 计算图片哈希
            image_hash = hashlib.md5(response.content).hexdigest()

            # 使用PIL处理图片
            if not PIL_AVAILABLE or not Image:
                raise ValueError("PIL未安装，无法处理图像")
            image = Image.open(io.BytesIO(response.content))

            # 这里可以集成实际的图像特征提取模型
            # 目前使用简化的特征提取方法
            features = self._extract_simple_features(image)

            return features, image_hash

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            # 返回默认特征
            return [0.0] * 512, hashlib.md5(b"default").hexdigest()

    def _extract_simple_features(self, image) -> List[float]:
        """提取简化的图像特征"""
        # 这里是一个简化的特征提取方法
        # 实际项目中应该使用预训练的CNN模型（如ResNet、VGG等）

        # 调整图片大小
        image = image.resize((224, 224))

        # 转换为RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # 获取像素值并归一化
        pixels = list(image.getdata())
        normalized_pixels = [(r/255.0, g/255.0, b/255.0) for r, g, b in pixels]

        # 简单的统计特征
        features = []
        for i in range(3):  # RGB三个通道
            channel_values = [pixel[i] for pixel in normalized_pixels]
            features.extend([
                np.mean(channel_values),
                np.std(channel_values),
                np.percentile(channel_values, 25),
                np.percentile(channel_values, 75)
            ])

        # 如果特征不足512维，用0填充
        while len(features) < 512:
            features.append(0.0)

        return features[:512]

    async def _recognize_with_llm(self, image_url: str) -> Dict:
        """使用LLM进行商品识别"""
        try:
            # 构建识别提示
            prompt = f"""
            请分析这张商品图片，识别出以下信息：
            图片URL: {image_url}

            请提供：
            1. 商品类型和名称
            2. 品牌（如果可见）
            3. 主要特征和规格
            4. 颜色和外观描述
            5. 估计的价格区间
            6. 置信度评分（0-1）

            请以JSON格式返回：
            {{
                "product_info": {{
                    "title": "商品名称",
                    "category": "商品类别",
                    "brand": "品牌",
                    "estimated_price": {{"min": 100, "max": 500}},
                    "key_features": ["特征1", "特征2"]
                }},
                "description": "详细描述",
                "confidence": 0.85
            }}
            """

            # 使用视觉模型进行识别
            response = await self.llm_service.analyze_image(image_url, prompt)

            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # 如果返回的不是JSON，尝试解析文本
                return {
                    "product_info": None,
                    "description": response,
                    "confidence": 0.5
                }

        except Exception as e:
            logger.error(f"Error in LLM recognition: {e}")
            return {
                "product_info": None,
                "description": "识别失败",
                "confidence": 0.0
            }

    async def _find_similar_by_image(self, image_features: List[float], platform: Optional[str] = None) -> List[ProductResponse]:
        """根据图像特征查找相似商品"""
        try:
            # 获取所有商品图片
            query = self.db.query(ProductImage).join(Product)
            if platform:
                query = query.filter(Product.platform == platform)

            product_images = query.all()

            # 计算相似度
            similar_products = []
            for img in product_images:
                if img.features:
                    similarity = self._calculate_cosine_similarity(image_features, img.features)
                    if similarity > 0.6:  # 相似度阈值
                        if img.product:
                            similar_products.append((img.product, similarity))

            # 按相似度排序
            similar_products.sort(key=lambda x: x[1], reverse=True)

            return [ProductResponse.from_orm(product) for product, _ in similar_products[:10]]

        except Exception as e:
            logger.error(f"Error finding similar products by image: {e}")
            return []

    def _calculate_cosine_similarity(self, features1: List[float], features2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            vec1 = np.array(features1)
            vec2 = np.array(features2)

            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)

        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    async def _find_similar_images(self, query_features: List[float], threshold: float = 0.7) -> List[ImageSimilarity]:
        """在数据库中查找相似图片"""
        try:
            # 获取所有图片特征
            all_images = self.db.query(ProductImage).filter(ProductImage.features.isnot(None)).all()

            similar_images = []
            for img in all_images:
                similarity = self._calculate_cosine_similarity(query_features, img.features)
                if similarity >= threshold:
                    similar_images.append(img)

            # 按相似度排序
            similar_images.sort(key=lambda x: self._calculate_cosine_similarity(query_features, x.features), reverse=True)

            return similar_images

        except Exception as e:
            logger.error(f"Error finding similar images: {e}")
            return []

    async def _find_visual_similar_products(self, source_product: Product, limit: int = 10) -> List[Product]:
        """基于视觉特征查找相似商品"""
        try:
            # 获取源商品的主图特征
            primary_image = self.db.query(ProductImage).filter(
                and_(
                    ProductImage.product_id == source_product.id,
                    ProductImage.is_primary == True
                )
            ).first()

            if not primary_image or not primary_image.features:
                return []

            # 查找视觉相似的商品
            similar_products = []
            all_images = self.db.query(ProductImage).join(Product).filter(
                and_(
                    ProductImage.features.isnot(None),
                    Product.id != source_product.id
                )
            ).all()

            for img in all_images:
                similarity = self._calculate_cosine_similarity(primary_image.features, img.features)
                if similarity > 0.6:  # 视觉相似度阈值
                    if img.product:
                        similar_products.append((img.product, similarity))

            # 按相似度排序
            similar_products.sort(key=lambda x: x[1], reverse=True)

            return [product for product, _ in similar_products[:limit]]

        except Exception as e:
            logger.error(f"Error finding visual similar products: {e}")
            return []

    async def _find_semantic_similar_products(self, source_product: Product, limit: int = 10) -> List[Product]:
        """基于语义特征查找相似商品"""
        try:
            # 使用文本相似度
            query = self.db.query(Product).filter(
                and_(
                    Product.id != source_product.id,
                    or_(
                        Product.category == source_product.category,
                        Product.brand == source_product.brand,
                        Product.title.contains(source_product.title.split()[0] if source_product.title else "")
                    )
                )
            )

            # 如果有类别，优先考虑相同类别
            if source_product.category:
                query = query.order_by(
                    func.case(
                        [(Product.category == source_product.category, 1)],
                        else_=0
                    ).desc()
                )

            products = query.limit(limit).all()
            return products

        except Exception as e:
            logger.error(f"Error finding semantic similar products: {e}")
            return []

    async def _record_image_search(self, user_id: int, image_url: str, results: List[Any]):
        """记录图片搜索历史"""
        try:
            search_history = ImageSearchHistory(
                user_id=user_id,
                query_image_url=image_url,
                search_results={"results": len(results)}
            )
            self.db.add(search_history)
            self.db.commit()

        except Exception as e:
            logger.error(f"Error recording image search: {e}")

    async def extract_image_features(self, image_url: str, product_id: int) -> bool:
        """提取图片特征并保存到数据库"""
        try:
            # 处理图片
            features, image_hash = await self._process_image(image_url)

            # 检查是否已存在
            existing_image = self.db.query(ProductImage).filter(
                and_(
                    ProductImage.product_id == product_id,
                    ProductImage.image_url == image_url
                )
            ).first()

            if existing_image:
                # 更新现有记录
                existing_image.features = features
                existing_image.image_hash = image_hash
                existing_image.quality_score = self._calculate_image_quality(features)
            else:
                # 创建新记录
                product_image = ProductImage(
                    product_id=product_id,
                    image_url=image_url,
                    image_hash=image_hash,
                    features=features,
                    quality_score=self._calculate_image_quality(features),
                    is_primary=False
                )
                self.db.add(product_image)

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error extracting image features: {e}")
            return False

    def _calculate_image_quality(self, features: List[float]) -> float:
        """计算图片质量分数"""
        try:
            # 基于特征向量的一些简单统计来评估图片质量
            feature_array = np.array(features)

            # 计算特征的标准差（反映图片的复杂度）
            std_dev = np.std(feature_array)

            # 计算特征的熵（反映图片的信息量）
            hist, _ = np.histogram(feature_array, bins=50)
            hist = hist / np.sum(hist)
            entropy = -np.sum(hist * np.log(hist + 1e-10))

            # 综合评分（标准化到0-1）
            quality_score = min((std_dev * 10 + entropy) / 2, 1.0)

            return quality_score

        except Exception as e:
            logger.error(f"Error calculating image quality: {e}")
            return 0.5

    async def update_image_similarity_index(self):
        """更新图片相似度索引"""
        try:
            # 获取所有有特征的图片
            all_images = self.db.query(ProductImage).filter(
                ProductImage.features.isnot(None)
            ).all()

            # 清除旧的相似度记录
            self.db.query(ImageSimilarity).delete()
            self.db.commit()

            # 计算新的相似度
            batch_size = 100
            for i in range(0, len(all_images), batch_size):
                batch = all_images[i:i + batch_size]

                for j, img1 in enumerate(batch):
                    for k, img2 in enumerate(batch[j+1:], j+1):
                        similarity = self._calculate_cosine_similarity(img1.features, img2.features)

                        if similarity > 0.5:  # 只保存有意义的相似度
                            # 创建双向记录
                            sim_record1 = ImageSimilarity(
                                source_image_id=img1.id,
                                target_image_id=img2.id,
                                similarity_score=similarity,
                                similarity_type=SimilarityType.VISUAL
                            )
                            sim_record2 = ImageSimilarity(
                                source_image_id=img2.id,
                                target_image_id=img1.id,
                                similarity_score=similarity,
                                similarity_type=SimilarityType.VISUAL
                            )
                            self.db.add(sim_record1)
                            self.db.add(sim_record2)

                # 批量提交
                if i % (batch_size * 10) == 0:
                    self.db.commit()

            self.db.commit()
            logger.info("Image similarity index updated successfully")

        except Exception as e:
            logger.error(f"Error updating image similarity index: {e}")
            self.db.rollback()

    async def get_image_statistics(self) -> Dict:
        """获取图片统计信息"""
        try:
            total_images = self.db.query(ProductImage).count()
            images_with_features = self.db.query(ProductImage).filter(
                ProductImage.features.isnot(None)
            ).count()

            avg_quality = self.db.query(func.avg(ProductImage.quality_score)).scalar() or 0

            # 相似度分布
            similarities = self.db.query(ImageSimilarity).all()
            similarity_distribution = {
                "high": len([s for s in similarities if s.similarity_score > 0.8]),
                "medium": len([s for s in similarities if 0.6 <= s.similarity_score <= 0.8]),
                "low": len([s for s in similarities if s.similarity_score < 0.6])
            }

            return {
                "total_images": total_images,
                "images_with_features": images_with_features,
                "feature_coverage": images_with_features / total_images if total_images > 0 else 0,
                "average_quality": avg_quality,
                "similarity_distribution": similarity_distribution,
                "total_similarities": len(similarities)
            }

        except Exception as e:
            logger.error(f"Error getting image statistics: {e}")
            return {}