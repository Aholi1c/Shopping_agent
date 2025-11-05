"""
视觉搜索和商品识别服务
支持图像搜索、商品识别和视觉推荐
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple, Union, TYPE_CHECKING
import os
import json
import logging
from datetime import datetime
import aiohttp
import asyncio
from io import BytesIO
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None
    ImageFont = None
    print("⚠️  PIL未安装，视觉搜索功能将不可用。请运行: pip install Pillow")

if TYPE_CHECKING:
    from PIL import Image as PILImage
else:
    PILImage = Image

import base64
import numpy as np
from ..models.models import KnowledgeBase, Document, DocumentChunk
from ..models.ecommerce_models import Product, ProductImage
from ..services.llm_service import LLMService
from ..services.vector_service import vector_service
from ..core.config import settings

logger = logging.getLogger(__name__)

class VisualSearchEngine:
    """视觉搜索引擎"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.supported_formats = ['jpg', 'jpeg', 'png', 'webp', 'bmp']
        self.max_image_size = 10 * 1024 * 1024  # 10MB

    async def search_by_image(self, image_data: bytes, search_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """通过图像搜索商品"""
        try:
            # 验证图像
            validation_result = self._validate_image(image_data)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"]
                }

            # 预处理图像
            processed_image = await self._preprocess_image(image_data)

            # 提取图像特征
            image_features = await self._extract_image_features(processed_image)

            # 生成图像描述
            image_description = await self._generate_image_description(processed_image)

            # 搜索相似商品
            similar_products = await self._search_similar_products(image_features, image_description, search_options)

            # 生成视觉分析
            visual_analysis = await self._generate_visual_analysis(processed_image, image_description)

            return {
                "success": True,
                "data": {
                    "image_features": image_features,
                    "image_description": image_description,
                    "similar_products": similar_products,
                    "visual_analysis": visual_analysis,
                    "search_options": search_options or {}
                }
            }

        except Exception as e:
            logger.error(f"Error in visual search: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _validate_image(self, image_data: bytes) -> Dict[str, Any]:
        """验证图像"""
        try:
            # 检查文件大小
            if len(image_data) > self.max_image_size:
                return {
                    "valid": False,
                    "error": f"Image size exceeds maximum limit of {self.max_image_size // (1024*1024)}MB"
                }

            # 检查图像格式
            try:
                img = Image.open(BytesIO(image_data))
                format_lower = img.format.lower() if img.format else ""
                if format_lower not in self.supported_formats:
                    return {
                        "valid": False,
                        "error": f"Unsupported image format. Supported formats: {', '.join(self.supported_formats)}"
                    }

                # 检查图像是否损坏
                img.verify()
                return {
                    "valid": True,
                    "format": format_lower,
                    "size": img.size,
                    "mode": img.mode
                }

            except Exception as e:
                return {
                    "valid": False,
                    "error": f"Invalid or corrupted image: {str(e)}"
                }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Error validating image: {str(e)}"
            }

    async def _preprocess_image(self, image_data: bytes) -> "PILImage.Image":
        """预处理图像"""
        try:
            # 打开图像
            img = Image.open(BytesIO(image_data))

            # 转换为RGB模式
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 调整大小
            max_size = 800
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                if PIL_AVAILABLE and Image:
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                else:
                    img = img.resize(new_size)

            return img

        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise

    async def _extract_image_features(self, image: "PILImage.Image") -> Dict[str, Any]:
        """提取图像特征"""
        try:
            # 转换为numpy数组
            img_array = np.array(image)

            # 计算基本统计特征
            features = {
                "color_histogram": self._calculate_color_histogram(img_array),
                "edge_density": self._calculate_edge_density(img_array),
                "texture_features": self._calculate_texture_features(img_array),
                "shape_features": self._calculate_shape_features(img_array),
                "dominant_colors": self._get_dominant_colors(img_array)
            }

            return features

        except Exception as e:
            logger.error(f"Error extracting image features: {e}")
            raise

    def _calculate_color_histogram(self, img_array: np.ndarray) -> Dict[str, List[int]]:
        """计算颜色直方图"""
        try:
            # 计算RGB通道直方图
            hist_r = np.histogram(img_array[:, :, 0], bins=256, range=(0, 256))[0]
            hist_g = np.histogram(img_array[:, :, 1], bins=256, range=(0, 256))[0]
            hist_b = np.histogram(img_array[:, :, 2], bins=256, range=(0, 256))[0]

            return {
                "red": hist_r.tolist(),
                "green": hist_g.tolist(),
                "blue": hist_b.tolist()
            }

        except Exception as e:
            logger.error(f"Error calculating color histogram: {e}")
            return {"red": [], "green": [], "blue": []}

    def _calculate_edge_density(self, img_array: np.ndarray) -> float:
        """计算边缘密度"""
        try:
            # 简单的边缘检测（Sobel算子）
            gray = np.mean(img_array, axis=2)
            sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
            sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])

            # 应用Sobel算子
            edges_x = np.abs(np.convolve(gray.flatten(), sobel_x.flatten(), mode='same'))
            edges_y = np.abs(np.convolve(gray.flatten(), sobel_y.flatten(), mode='same'))
            edges = edges_x + edges_y

            # 计算边缘密度
            edge_threshold = np.mean(edges) + np.std(edges)
            edge_pixels = np.sum(edges > edge_threshold)
            total_pixels = len(edges)

            return float(edge_pixels / total_pixels)

        except Exception as e:
            logger.error(f"Error calculating edge density: {e}")
            return 0.0

    def _calculate_texture_features(self, img_array: np.ndarray) -> Dict[str, float]:
        """计算纹理特征"""
        try:
            gray = np.mean(img_array, axis=2)

            # 计算局部二值模式（简化版本）
            height, width = gray.shape
            lbp_values = []

            for i in range(1, height - 1):
                for j in range(1, width - 1):
                    center = gray[i, j]
                    neighbors = [
                        gray[i-1, j-1], gray[i-1, j], gray[i-1, j+1],
                        gray[i, j+1], gray[i+1, j+1], gray[i+1, j],
                        gray[i+1, j-1], gray[i, j-1]
                    ]

                    binary = [1 if n > center else 0 for n in neighbors]
                    lbp = sum([bit * (2 ** i) for i, bit in enumerate(binary)])
                    lbp_values.append(lbp)

            # 计算LBP直方图
            lbp_hist, _ = np.histogram(lbp_values, bins=256, range=(0, 256))

            return {
                "lbp_uniformity": float(np.sum(lbp_hist ** 2) / (len(lbp_values) ** 2)),
                "lbp_entropy": float(-np.sum((lbp_hist / len(lbp_values)) * np.log2(lbp_hist / len(lbp_values) + 1e-10)))
            }

        except Exception as e:
            logger.error(f"Error calculating texture features: {e}")
            return {"lbp_uniformity": 0.0, "lbp_entropy": 0.0}

    def _calculate_shape_features(self, img_array: np.ndarray) -> Dict[str, float]:
        """计算形状特征"""
        try:
            # 计算图像的长宽比
            height, width = img_array.shape[:2]
            aspect_ratio = float(width / height)

            # 计算图像的紧凑度
            total_pixels = height * width
            perimeter = 2 * (height + width)
            compactness = float(total_pixels / (perimeter ** 2))

            return {
                "aspect_ratio": aspect_ratio,
                "compactness": compactness
            }

        except Exception as e:
            logger.error(f"Error calculating shape features: {e}")
            return {"aspect_ratio": 1.0, "compactness": 0.0}

    def _get_dominant_colors(self, img_array: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """获取主要颜色"""
        try:
            # 简化的K-means聚类
            pixels = img_array.reshape(-1, 3)
            np.random.shuffle(pixels)

            # 随机选择初始聚类中心
            centers = pixels[:k]

            # 迭代优化
            for _ in range(10):
                # 计算距离
                distances = np.sqrt(((pixels[:, np.newaxis] - centers) ** 2).sum(axis=2))
                labels = np.argmin(distances, axis=1)

                # 更新中心
                new_centers = np.array([pixels[labels == i].mean(axis=0) for i in range(k)])

                if np.allclose(centers, new_centers):
                    break

                centers = new_centers

            # 返回主要颜色
            dominant_colors = []
            for center in centers:
                dominant_colors.append({
                    "r": int(center[0]),
                    "g": int(center[1]),
                    "b": int(center[2]),
                    "hex": f"#{int(center[0]):02x}{int(center[1]):02x}{int(center[2]):02x}"
                })

            return dominant_colors

        except Exception as e:
            logger.error(f"Error getting dominant colors: {e}")
            return []

    async def _generate_image_description(self, image: "PILImage.Image") -> str:
        """生成图像描述"""
        try:
            # 将图像转换为base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            # 使用LLM生成描述
            prompt = f"""
            请详细描述这张商品图像的内容。包括：

            1. 商品的类型和类别
            2. 主要颜色和外观特征
            3. 材质和质感
            4. 风格和设计特点
            5. 可能的品牌特征
            6. 适合的使用场景

            图像数据（base64）: {img_base64[:1000]}...

            请用中文进行专业、准确的描述。
            """

            description = await self.llm_service.generate_response(prompt)
            return description

        except Exception as e:
            logger.error(f"Error generating image description: {e}")
            return "无法生成图像描述"

    async def _search_similar_products(self, image_features: Dict[str, Any], image_description: str,
                                     search_options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索相似商品"""
        try:
            # 构建搜索查询
            search_query = self._build_search_query_from_image(image_features, image_description)

            # 在商品数据库中搜索
            products = self._search_products_by_features(image_features, search_options)

            # 对搜索结果进行排序和评分
            ranked_products = self._rank_products_by_similarity(products, image_features, image_description)

            return ranked_products[:10]  # 返回前10个结果

        except Exception as e:
            logger.error(f"Error searching similar products: {e}")
            return []

    def _build_search_query_from_image(self, image_features: Dict[str, Any], image_description: str) -> str:
        """从图像特征构建搜索查询"""
        try:
            # 结合图像描述和特征生成搜索词
            query_terms = []

            # 从图像描述中提取关键词
            if image_description:
                query_terms.append(image_description)

            # 从颜色特征中添加颜色信息
            dominant_colors = image_features.get("dominant_colors", [])
            if dominant_colors:
                color_names = []
                for color in dominant_colors[:3]:  # 使用前3个主要颜色
                    hex_color = color.get("hex", "")
                    # 简单的颜色名称映射
                    if hex_color.startswith("#FF"):
                        color_names.append("红色")
                    elif hex_color.startswith("#00FF"):
                        color_names.append("绿色")
                    elif hex_color.startswith("#0000FF"):
                        color_names.append("蓝色")
                    elif all(c > 200 for c in [color["r"], color["g"], color["b"]]):
                        color_names.append("白色")
                    elif all(c < 100 for c in [color["r"], color["g"], color["b"]]):
                        color_names.append("黑色")

                if color_names:
                    query_terms.append("颜色：" + "、".join(color_names))

            return " ".join(query_terms)

        except Exception as e:
            logger.error(f"Error building search query: {e}")
            return image_description or ""

    def _search_products_by_features(self, image_features: Dict[str, Any], search_options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """根据图像特征搜索商品"""
        try:
            # 构建查询
            query = self.db.query(Product)

            # 应用过滤条件
            if search_options:
                if search_options.get("category"):
                    query = query.filter(Product.category == search_options["category"])
                if search_options.get("brand"):
                    query = query.filter(Product.brand == search_options["brand"])
                if search_options.get("price_range"):
                    min_price, max_price = search_options["price_range"]
                    query = query.filter(Product.price.between(min_price, max_price))

            # 获取商品列表
            products = query.limit(50).all()

            # 转换为字典格式
            product_list = []
            for product in products:
                product_data = {
                    "product_id": product.product_id,
                    "name": product.name,
                    "brand": product.brand,
                    "category": product.category,
                    "price": product.price,
                    "image_url": product.image_url,
                    "description": product.meta_data.get("description", "") if product.meta_data else ""
                }
                product_list.append(product_data)

            return product_list

        except Exception as e:
            logger.error(f"Error searching products by features: {e}")
            return []

    def _rank_products_by_similarity(self, products: List[Dict[str, Any]], image_features: Dict[str, Any],
                                  image_description: str) -> List[Dict[str, Any]]:
        """根据相似度对商品进行排序"""
        try:
            ranked_products = []

            for product in products:
                # 计算相似度分数
                similarity_score = self._calculate_similarity_score(product, image_features, image_description)

                # 添加分数信息
                product_with_score = product.copy()
                product_with_score["similarity_score"] = similarity_score
                product_with_score["match_reasons"] = self._get_match_reasons(product, image_features, image_description)

                ranked_products.append(product_with_score)

            # 按相似度分数排序
            ranked_products.sort(key=lambda x: x["similarity_score"], reverse=True)

            return ranked_products

        except Exception as e:
            logger.error(f"Error ranking products by similarity: {e}")
            return products

    def _calculate_similarity_score(self, product: Dict[str, Any], image_features: Dict[str, Any],
                                  image_description: str) -> float:
        """计算相似度分数"""
        try:
            score = 0.0

            # 基于类别匹配
            if image_description and product.get("category"):
                if product["category"] in image_description:
                    score += 0.3

            # 基于品牌匹配
            if image_description and product.get("brand"):
                if product["brand"] in image_description:
                    score += 0.2

            # 基于价格范围
            if product.get("price"):
                price = product["price"]
                if price < 100:
                    score += 0.1
                elif price < 500:
                    score += 0.2
                else:
                    score += 0.15

            # 基于描述匹配
            if image_description and product.get("description"):
                # 简单的文本相似度
                desc_score = self._calculate_text_similarity(image_description, product["description"])
                score += desc_score * 0.3

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"Error calculating similarity score: {e}")
            return 0.0

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        try:
            # 简单的词汇重叠相似度
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())

            intersection = words1.intersection(words2)
            union = words1.union(words2)

            if len(union) == 0:
                return 0.0

            return len(intersection) / len(union)

        except Exception as e:
            logger.error(f"Error calculating text similarity: {e}")
            return 0.0

    def _get_match_reasons(self, product: Dict[str, Any], image_features: Dict[str, Any],
                          image_description: str) -> List[str]:
        """获取匹配原因"""
        reasons = []

        try:
            # 类别匹配
            if image_description and product.get("category"):
                if product["category"] in image_description:
                    reasons.append(f"类别匹配：{product['category']}")

            # 品牌匹配
            if image_description and product.get("brand"):
                if product["brand"] in image_description:
                    reasons.append(f"品牌匹配：{product['brand']}")

            # 价格区间
            if product.get("price"):
                price = product["price"]
                if price < 100:
                    reasons.append("价格区间：低价商品")
                elif price < 500:
                    reasons.append("价格区间：中等价位")
                else:
                    reasons.append("价格区间：高端商品")

            # 外观特征
            dominant_colors = image_features.get("dominant_colors", [])
            if dominant_colors:
                reasons.append("颜色特征匹配")

        except Exception as e:
            logger.error(f"Error getting match reasons: {e}")

        return reasons[:3]  # 返回前3个原因

    async def _generate_visual_analysis(self, image: "PILImage.Image", image_description: str) -> Dict[str, Any]:
        """生成视觉分析"""
        try:
            # 分析图像质量
            quality_analysis = self._analyze_image_quality(image)

            # 分析商品特征
            product_analysis = await self._analyze_product_features(image_description)

            # 生成推荐标签
            recommended_tags = await self._generate_recommended_tags(image_description)

            return {
                "quality_analysis": quality_analysis,
                "product_analysis": product_analysis,
                "recommended_tags": recommended_tags,
                "image_metadata": {
                    "size": image.size,
                    "mode": image.mode,
                    "format": image.format
                }
            }

        except Exception as e:
            logger.error(f"Error generating visual analysis: {e}")
            return {}

    def _analyze_image_quality(self, image: "PILImage.Image") -> Dict[str, Any]:
        """分析图像质量"""
        try:
            # 计算图像质量指标
            img_array = np.array(image)

            # 计算亮度
            brightness = np.mean(img_array)

            # 计算对比度
            contrast = np.std(img_array)

            # 计算清晰度（基于边缘密度）
            edge_density = self._calculate_edge_density(img_array)

            return {
                "brightness": float(brightness),
                "contrast": float(contrast),
                "sharpness": float(edge_density),
                "quality_score": min(100.0, (brightness / 255 * 30 + contrast / 128 * 40 + edge_density * 30))
            }

        except Exception as e:
            logger.error(f"Error analyzing image quality: {e}")
            return {"brightness": 0, "contrast": 0, "sharpness": 0, "quality_score": 0}

    async def _analyze_product_features(self, image_description: str) -> Dict[str, Any]:
        """分析商品特征"""
        try:
            # 使用LLM分析商品特征
            prompt = f"""
            基于以下图像描述，分析商品的关键特征：

            图像描述：{image_description}

            请分析：
            1. 商品类型和用途
            2. 主要材质
            3. 设计风格
            4. 目标用户群体
            5. 适用场景
            6. 季节性特征

            返回JSON格式的分析结果。
            """

            analysis = await self.llm_service.generate_response(prompt)

            try:
                # 尝试解析JSON
                return json.loads(analysis)
            except:
                # 如果不是JSON，返回文本
                return {"analysis": analysis}

        except Exception as e:
            logger.error(f"Error analyzing product features: {e}")
            return {}

    async def _generate_recommended_tags(self, image_description: str) -> List[str]:
        """生成推荐标签"""
        try:
            # 使用LLM生成标签
            prompt = f"""
            基于以下图像描述，生成适合的标签：

            图像描述：{image_description}

            请生成5-10个相关的标签，包括：
            - 商品类别
            - 风格特征
            - 适用场景
            - 材质特征
            - 颜色特征

            标签用中文，用逗号分隔。
            """

            response = await self.llm_service.generate_response(prompt)

            # 解析标签
            tags = [tag.strip() for tag in response.split(",") if tag.strip()]
            return tags[:10]  # 限制标签数量

        except Exception as e:
            logger.error(f"Error generating recommended tags: {e}")
            return []

    async def recognize_product(self, image_data: bytes) -> Dict[str, Any]:
        """商品识别"""
        try:
            # 执行视觉搜索
            search_result = await self.search_by_image(image_data)

            if not search_result["success"]:
                return search_result

            # 如果找到高相似度的商品，返回识别结果
            similar_products = search_result["data"].get("similar_products", [])

            if similar_products:
                top_product = similar_products[0]
                if top_product["similarity_score"] > 0.7:  # 高相似度阈值
                    return {
                        "success": True,
                        "data": {
                            "recognized": True,
                            "product": top_product,
                            "confidence": top_product["similarity_score"],
                            "image_analysis": search_result["data"].get("visual_analysis", {}),
                            "alternative_matches": similar_products[1:4]  # 前3个替代匹配
                        }
                    }

            # 如果没有找到高相似度商品，返回一般识别结果
            return {
                "success": True,
                "data": {
                    "recognized": False,
                    "similar_products": similar_products[:5],
                    "image_analysis": search_result["data"].get("visual_analysis", {}),
                    "suggestions": [
                        "尝试调整图像角度和光线",
                        "确保商品主体清晰可见",
                        "使用更高质量的图像"
                    ]
                }
            }

        except Exception as e:
            logger.error(f"Error in product recognition: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_visual_search_index(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建视觉搜索索引"""
        try:
            # 为商品创建视觉特征索引
            indexed_products = []

            for product in products:
                # 如果商品有图像URL，下载并提取特征
                if product.get("image_url"):
                    try:
                        # 下载图像
                        async with aiohttp.ClientSession() as session:
                            async with session.get(product["image_url"]) as response:
                                if response.status == 200:
                                    image_data = await response.read()

                                    # 提取特征
                                    features = await self._extract_image_features_from_data(image_data)

                                    # 添加到索引
                                    indexed_product = product.copy()
                                    indexed_product["visual_features"] = features
                                    indexed_products.append(indexed_product)

                    except Exception as e:
                        logger.warning(f"Error processing image for product {product.get('product_id')}: {e}")

            return {
                "success": True,
                "data": {
                    "indexed_products": len(indexed_products),
                    "total_products": len(products),
                    "indexing_completed": datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error creating visual search index: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _extract_image_features_from_data(self, image_data: bytes) -> Dict[str, Any]:
        """从图像数据提取特征"""
        try:
            # 预处理图像
            image = await self._preprocess_image(image_data)

            # 提取特征
            features = await self._extract_image_features(image)

            return features

        except Exception as e:
            logger.error(f"Error extracting features from image data: {e}")
            return {}

    async def get_visual_search_statistics(self) -> Dict[str, Any]:
        """获取视觉搜索统计信息"""
        try:
            # 获取基本统计信息
            total_products = self.db.query(Product).count()
            products_with_images = self.db.query(Product).filter(
                Product.image_url.isnot(None)
            ).count()

            # 获取类别分布
            categories = self.db.query(Product.category).distinct().all()
            category_distribution = {}
            for category in categories:
                count = self.db.query(Product).filter(
                    Product.category == category[0]
                ).count()
                category_distribution[category[0]] = count

            return {
                "success": True,
                "data": {
                    "total_products": total_products,
                    "products_with_images": products_with_images,
                    "coverage_rate": round(products_with_images / total_products * 100, 2) if total_products > 0 else 0,
                    "category_distribution": category_distribution,
                    "supported_formats": self.supported_formats,
                    "max_image_size_mb": self.max_image_size // (1024 * 1024)
                }
            }

        except Exception as e:
            logger.error(f"Error getting visual search statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# 全局视觉搜索服务实例
def get_visual_search_service(db: Session) -> VisualSearchEngine:
    return VisualSearchEngine(db)