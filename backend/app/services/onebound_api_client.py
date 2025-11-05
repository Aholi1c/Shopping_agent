"""
万邦API客户端
用于调用万邦（Onebound）电商数据API获取商品信息
"""
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlencode

from ..core.config import settings

logger = logging.getLogger(__name__)


class OneboundAPIClient:
    """万邦API客户端"""
    
    def __init__(self):
        self.api_key = settings.onebound_api_key or "test_api_key"  # 默认使用测试key
        self.api_secret = settings.onebound_api_secret or ""
        self.base_url = settings.onebound_api_base_url
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def _make_request(
        self, 
        platform: str, 
        api_type: str, 
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        发送API请求
        
        Args:
            platform: 平台名称 (taobao, jd, pdd等)
            api_type: API类型 (item_search, item_get等)
            params: 请求参数
            
        Returns:
            API响应数据
        """
        if params is None:
            params = {}
            
        # 构建URL
        url = f"{self.base_url}/{platform}/{api_type}/"
        
        # 添加通用参数
        common_params = {
            "key": self.api_key,
            "secret": self.api_secret,
            "lang": params.get("lang", "zh-CN"),  # 默认中文
            "result_type": params.get("result_type", "json"),  # 默认JSON格式
            "cache": params.get("cache", "yes"),  # 默认使用缓存
        }
        
        # 合并参数
        all_params = {**common_params, **{k: v for k, v in params.items() if k not in ["lang", "result_type", "cache"]}}
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                logger.info(f"请求万邦API: {url}?{urlencode(all_params)}")
                async with session.get(url, params=all_params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"万邦API请求失败: {response.status} - {error_text}")
                        return {"error": f"API请求失败: {response.status}", "detail": error_text}
                        
        except aiohttp.ClientError as e:
            logger.error(f"万邦API网络请求错误: {e}")
            return {"error": f"网络请求失败: {str(e)}"}
        except Exception as e:
            logger.error(f"万邦API请求异常: {e}")
            return {"error": f"请求异常: {str(e)}"}
    
    async def search_products(
        self, 
        query: str, 
        platform: str = "taobao",
        page: int = 1,
        page_size: int = 40,
        start_price: Optional[float] = None,
        end_price: Optional[float] = None,
        sort: str = "default",
        category: Optional[int] = None,
        seller_info: bool = True
    ) -> Dict[str, Any]:
        """
        搜索商品
        
        Args:
            query: 搜索关键字
            platform: 平台 (taobao, tmall, jd, pdd)
            page: 页码
            page_size: 每页数量
            start_price: 起始价格
            end_price: 结束价格
            sort: 排序方式 (default, bid, bid2, _bid2, _sale, _credit)
            category: 分类ID
            seller_info: 是否获取商家信息
            
        Returns:
            搜索结果
        """
        params = {
            "q": query,
            "page": page,
            "page_size": page_size,
            "seller_info": "yes" if seller_info else "no",
        }
        
        if start_price is not None:
            params["start_price"] = start_price
        if end_price is not None:
            params["end_price"] = end_price
        if sort != "default":
            params["sort"] = sort
        if category is not None:
            params["cat"] = category
            
        # 根据平台选择API类型
        if platform == "tmall":
            api_type = "item_search_tmall"
        else:
            api_type = "item_search"
            
        result = await self._make_request(platform, api_type, params)
        
        # 记录原始响应以便调试
        logger.debug(f"万邦API原始响应类型: {type(result)}, keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        # 转换结果格式
        if "error" in result:
            logger.error(f"万邦API返回错误: {result.get('error')}, 详情: {result.get('detail', '')}")
            return result
        
        # 尝试多种可能的响应格式
        if isinstance(result, dict):
            # 格式1: 直接包含items
            if "items" in result:
                logger.debug("使用items字段解析结果")
                return self._parse_search_results(result)
            
            # 格式2: 包含data.items
            if "data" in result and isinstance(result["data"], dict):
                if "items" in result["data"]:
                    logger.debug("使用data.items字段解析结果")
                    return self._parse_search_results(result)
                # 如果data本身就是列表
                elif isinstance(result["data"], list):
                    logger.debug("data是列表格式，直接解析")
                    return self._parse_search_results({"items": result["data"]})
            
            # 格式3: 可能在其他字段
            for key in ["products", "results", "goods"]:
                if key in result:
                    logger.debug(f"使用{key}字段解析结果")
                    return self._parse_search_results({"items": result[key]})
        
        # 如果都不匹配，记录并返回原始结果
        logger.warning(f"无法识别万邦API响应格式，返回原始结果: {type(result)}")
        return result
    
    async def get_product_details(
        self, 
        product_id: str, 
        platform: str = "taobao"
    ) -> Dict[str, Any]:
        """
        获取商品详情
        
        Args:
            product_id: 商品ID (num_iid)
            platform: 平台 (taobao, jd, pdd)
            
        Returns:
            商品详情
        """
        params = {
            "num_iid": product_id
        }
        
        result = await self._make_request(platform, "item_get", params)
        
        # 转换结果格式
        if "error" not in result and "item" in result:
            return self._parse_product_details(result)
        elif "error" not in result and "data" in result:
            if "item" in result["data"]:
                return self._parse_product_details(result)
            else:
                return result
        else:
            return result
    
    async def get_product_history_price(
        self, 
        product_id: str, 
        platform: str = "taobao"
    ) -> Dict[str, Any]:
        """
        获取商品历史价格
        
        Args:
            product_id: 商品ID
            platform: 平台
            
        Returns:
            历史价格数据
        """
        params = {
            "num_iid": product_id
        }
        
        result = await self._make_request(platform, "item_history_price", params)
        return result
    
    async def search_similar_products(
        self, 
        product_id: str, 
        platform: str = "taobao",
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        搜索相似商品
        
        Args:
            product_id: 商品ID
            platform: 平台
            limit: 返回数量
            
        Returns:
            相似商品列表
        """
        params = {
            "num_iid": product_id,
            "page_size": limit
        }
        
        result = await self._make_request(platform, "item_search_similar", params)
        
        if "error" not in result and "items" in result:
            return self._parse_search_results(result)
        else:
            return result
    
    def _parse_search_results(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析搜索结果
        
        Args:
            api_response: API响应数据
            
        Returns:
            标准化的搜索结果
        """
        try:
            # 获取items数据（可能在不同层级）
            items = []
            
            # 方式1: 直接包含items
            if "items" in api_response:
                items_data = api_response["items"]
                if isinstance(items_data, list):
                    items = items_data
                elif isinstance(items_data, dict) and "item" in items_data:
                    # 可能items是一个对象，包含item字段
                    item_obj = items_data["item"]
                    if isinstance(item_obj, list):
                        items = item_obj
                    elif isinstance(item_obj, dict):
                        items = [item_obj]
                elif isinstance(items_data, dict) and "list" in items_data:
                    items = items_data["list"]
            
            # 方式2: 在data.items中
            if not items and "data" in api_response:
                data = api_response["data"]
                if isinstance(data, dict):
                    if "items" in data:
                        items_data = data["items"]
                        if isinstance(items_data, list):
                            items = items_data
                        elif isinstance(items_data, dict) and "item" in items_data:
                            item_obj = items_data["item"]
                            if isinstance(item_obj, list):
                                items = item_obj
                            elif isinstance(item_obj, dict):
                                items = [item_obj]
                elif isinstance(data, list):
                    items = data
            
            # 方式3: 在results中
            if not items and "results" in api_response:
                results = api_response["results"]
                if isinstance(results, list):
                    items = results
                elif isinstance(results, dict) and "items" in results:
                    items = results["items"]
            
            # 方式4: 直接是列表
            if not items and isinstance(api_response, list):
                items = api_response
            
            logger.debug(f"解析到 {len(items)} 个商品项")
            
            products = []
            for item in items:
                try:
                    product = self._normalize_product_data(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"解析单个商品失败: {e}, 商品数据: {item}")
                    continue
            
            return {
                "products": products,
                "total": len(products),
                "page": api_response.get("page", api_response.get("data", {}).get("page", 1)),
                "page_size": len(products),
                "source": "onebound"
            }
            
        except Exception as e:
            logger.error(f"解析搜索结果失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.error(f"原始响应数据: {api_response}")
            return {"error": f"解析失败: {str(e)}", "raw_data": api_response}
    
    def _parse_product_details(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析商品详情
        
        Args:
            api_response: API响应数据
            
        Returns:
            标准化的商品详情
        """
        try:
            # 获取item数据
            item = api_response.get("item", {})
            if not item and "data" in api_response:
                item = api_response["data"].get("item", {})
            
            if not item:
                return {"error": "未找到商品数据", "raw_data": api_response}
            
            product = self._normalize_product_data(item, detailed=True)
            return product
            
        except Exception as e:
            logger.error(f"解析商品详情失败: {e}")
            return {"error": f"解析失败: {str(e)}", "raw_data": api_response}
    
    def _normalize_product_data(
        self, 
        item: Dict[str, Any], 
        detailed: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        标准化商品数据格式
        
        Args:
            item: 原始商品数据
            detailed: 是否包含详细信息
            
        Returns:
            标准化的商品数据
        """
        try:
            # 提取价格（可能有多种格式）
            price = 0.0
            if "price" in item:
                price = float(item["price"]) if item["price"] else 0.0
            elif "view_price" in item:
                price = float(item["view_price"]) if item["view_price"] else 0.0
            elif "reserve_price" in item:
                price = float(item["reserve_price"]) if item["reserve_price"] else 0.0
            
            # 提取原价
            original_price = price
            if "original_price" in item:
                original_price = float(item["original_price"]) if item["original_price"] else price
            elif "orginal_price" in item:  # 可能的拼写错误
                original_price = float(item["orginal_price"]) if item["orginal_price"] else price
            
            # 提取商品ID
            product_id = item.get("num_iid", item.get("nid", item.get("item_id", "")))
            
            # 提取标题
            title = item.get("title", item.get("name", ""))
            
            # 提取图片
            image_url = ""
            if "pic_url" in item:
                image_url = item["pic_url"]
            elif "pict_url" in item:
                image_url = item["pict_url"]
            elif "small_images" in item and item["small_images"]:
                image_url = item["small_images"].get("string", [""])[0] if isinstance(item["small_images"], dict) else item["small_images"][0]
            
            # 提取链接
            product_url = item.get("detail_url", item.get("item_url", ""))
            
            # 提取店铺信息
            shop_name = item.get("nick", item.get("shop_name", ""))
            shop_id = item.get("seller_id", item.get("user_id", ""))
            
            # 提取销量和评价
            sales_count = 0
            if "volume" in item:
                sales_count = int(item["volume"]) if item["volume"] else 0
            elif "sales" in item:
                sales_count = int(item["sales"]) if item["sales"] else 0
            
            review_count = 0
            if "comment_count" in item:
                review_count = int(item["comment_count"]) if item["comment_count"] else 0
            elif "rate_count" in item:
                review_count = int(item["rate_count"]) if item["rate_count"] else 0
            
            rating = 0.0
            if "score" in item:
                rating = float(item["score"]) if item["score"] else 0.0
            elif "rating" in item:
                rating = float(item["rating"]) if item["rating"] else 0.0
            
            # 计算折扣率
            discount_rate = 0.0
            if original_price > 0 and price < original_price:
                discount_rate = (original_price - price) / original_price
            
            # 构建标准化商品数据
            product = {
                "product_id": str(product_id),
                "title": title,
                "price": price,
                "original_price": original_price,
                "discount_rate": discount_rate,
                "image_url": image_url,
                "product_url": product_url,
                "shop_name": shop_name,
                "shop_id": str(shop_id) if shop_id else "",
                "sales_count": sales_count,
                "review_count": review_count,
                "rating": rating,
                "stock_status": "in_stock" if item.get("is_available", True) else "out_of_stock",
                "source": "onebound"
            }
            
            # 如果要求详细信息，添加额外字段
            if detailed:
                product.update({
                    "description": item.get("desc", item.get("description", "")),
                    "category": item.get("cat_name", ""),
                    "category_id": item.get("cat_id", ""),
                    "brand": item.get("brand", ""),
                    "location": item.get("location", ""),
                    "post_fee": item.get("post_fee", 0),
                    "express_fee": item.get("express_fee", 0),
                    "ems_fee": item.get("ems_fee", 0),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })
            
            return product
            
        except Exception as e:
            logger.error(f"标准化商品数据失败: {e}, item: {item}")
            return None


# 创建全局实例
onebound_api_client = OneboundAPIClient()

