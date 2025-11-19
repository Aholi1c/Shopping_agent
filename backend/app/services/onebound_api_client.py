"""
万邦API客户端
用于调用万邦（Onebound）电商数据 API 获取商品信息
"""
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlencode

from ..core.config import settings

logger = logging.getLogger(__name__)


class OneboundAPIClient:
    """万邦 API 客户端封装"""

    def __init__(self) -> None:
        self.api_key = settings.onebound_api_key or "test_api_key"
        self.api_secret = settings.onebound_api_secret or ""
        self.base_url = settings.onebound_api_base_url
        self.timeout = aiohttp.ClientTimeout(total=30)

    # ---------------------- 内部工具方法 ---------------------- #

    def _normalize_platform(self, platform: str) -> str:
        """
        规范化平台标识到万邦要求的路径名.

        taobao -> taobao
        jd -> jd
        pdd -> pinduoduo
        """
        if not platform:
            return "taobao"
        platform = platform.lower()
        if platform in ["pdd", "pinduoduo"]:
            return "pinduoduo"
        return platform

    def _is_error_response(self, result: Dict[str, Any]) -> bool:
        """
        根据万邦文档判断响应是否为错误:

        成功: error_code == "0000" 且 error 为空字符串
        失败: error_code != "0000" 或 error 非空
        """
        if not isinstance(result, dict):
            return False

        error_code = str(result.get("error_code", "") or "").strip()
        error_msg = (result.get("error") or "").strip()

        if error_code and error_code != "0000":
            return True
        if error_msg:
            return True
        return False

    async def _make_request(
        self,
        platform: str,
        api_type: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        发送 API 请求

        Args:
            platform: 平台名称 (taobao, jd, pdd/pinduoduo)
            api_type: API 类型 (item_search, item_get 等)
            params: 业务参数
        """
        if params is None:
            params = {}

        normalized_platform = self._normalize_platform(platform)
        url = f"{self.base_url}/{normalized_platform}/{api_type}/"

        common_params = {
            "key": self.api_key,
            "secret": self.api_secret,
            # 万邦文档: cn/en/ru，默认 cn
            "lang": params.get("lang", "cn"),
            "result_type": params.get("result_type", "json"),
            "cache": params.get("cache", "yes"),
        }

        # 合并参数，业务参数优先
        all_params: Dict[str, Any] = {
            **common_params,
            **{k: v for k, v in params.items() if k not in ["lang", "result_type", "cache"]},
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                logger.info("请求万邦API: %s?%s", url, urlencode(all_params))
                async with session.get(url, params=all_params) as response:
                    if response.status == 200:
                        try:
                            return await response.json()
                        except Exception as e:
                            text = await response.text()
                            logger.error("万邦API JSON 解析失败: %s, text=%s", e, text[:500])
                            return {"error": f"JSON解析失败: {e}", "raw_text": text}
                    else:
                        error_text = await response.text()
                        logger.error("万邦API请求失败: %s - %s", response.status, error_text[:500])
                        return {
                            "error": f"API请求失败: {response.status}",
                            "detail": error_text,
                            "status": response.status,
                        }
        except aiohttp.ClientError as e:
            logger.error("万邦API网络请求错误: %s", e)
            return {"error": f"网络请求失败: {e}"}
        except Exception as e:
            logger.error("万邦API请求异常: %s", e)
            return {"error": f"请求异常: {e}"}

    # ---------------------- 对外能力：搜索 ---------------------- #

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
        seller_info: bool = True,
    ) -> Dict[str, Any]:
        """
        搜索商品（淘宝 / 京东 / 拼多多）
        """
        params: Dict[str, Any] = {
            "q": query,
            "page": page,
            "page_size": page_size,
        }

        # seller_info 参数在淘宝/JD 文档中出现，PDD 忽略也不会出错
        params["seller_info"] = "yes" if seller_info else "no"

        if start_price is not None:
            params["start_price"] = start_price
        if end_price is not None:
            params["end_price"] = end_price
        if sort != "default":
            params["sort"] = sort
        if category is not None:
            params["cat"] = category

        # tmall 使用专门的 item_search_tmall
        api_type = "item_search_tmall" if platform.lower() == "tmall" else "item_search"

        result = await self._make_request(platform, api_type, params)

        logger.debug(
            "万邦API原始响应类型: %s, keys: %s",
            type(result),
            list(result.keys()) if isinstance(result, dict) else "N/A",
        )

        if self._is_error_response(result):
            logger.error(
                "万邦API搜索错误: platform=%s, error_code=%s, error=%s, reason=%s",
                platform,
                result.get("error_code"),
                result.get("error"),
                result.get("reason"),
            )
            return result

        if isinstance(result, dict):
            return self._parse_search_results(result)

        logger.warning("无法识别万邦API响应格式，返回原始结果类型: %s", type(result))
        return result

    # ---------------------- 对外能力：详情/历史/相似 ---------------------- #

    async def get_product_details(
        self,
        product_id: str,
        platform: str = "taobao",
    ) -> Dict[str, Any]:
        """
        获取商品详情
        """
        params = {"num_iid": product_id}
        result = await self._make_request(platform, "item_get", params)

        if self._is_error_response(result):
            logger.error(
                "万邦API获取商品详情错误: platform=%s, num_iid=%s, error_code=%s, error=%s, reason=%s",
                platform,
                product_id,
                result.get("error_code"),
                result.get("error"),
                result.get("reason"),
            )
            return result

        if isinstance(result, dict):
            if "item" in result:
                return self._parse_product_details(result)
            data = result.get("data")
            if isinstance(data, dict) and "item" in data:
                return self._parse_product_details(data)

        return result

    async def get_product_history_price(
        self,
        product_id: str,
        platform: str = "taobao",
    ) -> Dict[str, Any]:
        """
        获取商品历史价格（万邦直接返回结构，上层自行解释）
        """
        params = {"num_iid": product_id}
        result = await self._make_request(platform, "item_history_price", params)
        return result

    async def search_similar_products(
        self,
        product_id: str,
        platform: str = "taobao",
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        搜索相似商品
        """
        params = {
            "num_iid": product_id,
            "page_size": limit,
        }

        result = await self._make_request(platform, "item_search_similar", params)

        if self._is_error_response(result):
            logger.error(
                "万邦API相似商品搜索错误: platform=%s, num_iid=%s, error_code=%s, error=%s, reason=%s",
                platform,
                product_id,
                result.get("error_code"),
                result.get("error"),
                result.get("reason"),
            )
            return result

        if isinstance(result, dict):
            return self._parse_search_results(result)

        return result

    # ---------------------- 解析与标准化 ---------------------- #

    def _parse_search_results(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析搜索结果为统一结构:
        {
            "products": [...],
            "total": int,
            "page": int,
            "page_size": int,
            "source": "onebound"
        }
        """
        try:
            items: List[Dict[str, Any]] = []

            # 方式1: 顶层 items 结构（淘宝 / JD / PDD）
            if "items" in api_response:
                items_data = api_response["items"]
                if isinstance(items_data, list):
                    items = items_data
                elif isinstance(items_data, dict):
                    if "item" in items_data:
                        item_obj = items_data["item"]
                        if isinstance(item_obj, list):
                            items = item_obj
                        elif isinstance(item_obj, dict):
                            items = [item_obj]
                    elif "items" in items_data:
                        inner = items_data["items"]
                        if isinstance(inner, list):
                            items = inner

            # 方式2: data.items
            if not items and "data" in api_response:
                data = api_response["data"]
                if isinstance(data, dict) and "items" in data:
                    items_data = data["items"]
                    if isinstance(items_data, list):
                        items = items_data
                    elif isinstance(items_data, dict) and "item" in items_data:
                        item_obj = items_data["item"]
                        if isinstance(item_obj, list):
                            items = item_obj
                        elif isinstance(item_obj, dict):
                            items = [item_obj]

            # 方式3: results / goods
            if not items:
                for key in ["results", "goods", "products"]:
                    if key in api_response:
                        raw = api_response[key]
                        if isinstance(raw, list):
                            items = raw
                        elif isinstance(raw, dict) and "items" in raw:
                            inner_items = raw["items"]
                            if isinstance(inner_items, list):
                                items = inner_items
                        break

            # 方式4: 直接是列表
            if not items and isinstance(api_response, list):
                items = api_response

            logger.debug("解析万邦搜索结果，共 %d 个商品项", len(items))

            products: List[Dict[str, Any]] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                try:
                    product = self._normalize_product_data(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning("解析单个商品失败: %s, 商品数据: %s", e, item)
                    continue

            # 页码信息
            page = 1
            page_size = len(products)
            items_meta = api_response.get("items")
            if isinstance(items_meta, dict):
                try:
                    page = int(items_meta.get("page", page))
                    page_size = int(items_meta.get("page_size", page_size))
                except Exception:
                    pass

            return {
                "products": products,
                "total": len(products),
                "page": page,
                "page_size": page_size,
                "source": "onebound",
            }
        except Exception as e:
            logger.error("解析搜索结果失败: %s", e)
            return {"error": f"解析失败: {e}", "raw_data": api_response}

    def _parse_product_details(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析商品详情
        """
        try:
            item = api_response.get("item", {})
            if not item and "data" in api_response:
                data = api_response["data"]
                if isinstance(data, dict):
                    item = data.get("item", {})

            if not item:
                return {"error": "未找到商品数据", "raw_data": api_response}

            product = self._normalize_product_data(item, detailed=True)
            if not product:
                return {"error": "标准化商品数据失败", "raw_data": api_response}
            return product
        except Exception as e:
            logger.error("解析商品详情失败: %s", e)
            return {"error": f"解析失败: {e}", "raw_data": api_response}

    def _normalize_product_data(
        self,
        item: Dict[str, Any],
        detailed: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        将万邦返回的商品结构标准化为内部统一结构
        """
        try:
            # 价格
            price = 0.0
            if "price" in item and item["price"] not in (None, ""):
                price = float(item["price"])
            elif "promotion_price" in item and item["promotion_price"] not in (None, ""):
                price = float(item["promotion_price"])
            elif "view_price" in item and item["view_price"] not in (None, ""):
                price = float(item["view_price"])
            elif "reserve_price" in item and item["reserve_price"] not in (None, ""):
                price = float(item["reserve_price"])

            # 原价
            original_price = price
            if "original_price" in item and item["original_price"] not in (None, ""):
                original_price = float(item["original_price"])
            elif "orginal_price" in item and item["orginal_price"] not in (None, ""):
                original_price = float(item["orginal_price"])

            # 商品 ID
            product_id = (
                item.get("num_iid")
                or item.get("nid")
                or item.get("item_id")
                or item.get("goods_id")
                or ""
            )

            # 标题
            title = item.get("title") or item.get("name") or ""

            # 图片
            image_url = ""
            if "pic_url" in item and item["pic_url"]:
                image_url = item["pic_url"]
            elif "pict_url" in item and item["pict_url"]:
                image_url = item["pict_url"]

            # 链接
            product_url = item.get("detail_url") or item.get("item_url") or ""

            # 店铺信息
            shop_name = item.get("nick") or item.get("shop_name") or ""
            shop_id = item.get("seller_id") or item.get("user_id") or ""

            # 销量
            sales_count = 0
            if "sales" in item and item["sales"] not in (None, ""):
                sales_count = int(item["sales"])
            elif "volume" in item and item["volume"] not in (None, ""):
                sales_count = int(item["volume"])

            # 评价数
            review_count = 0
            if "comment_count" in item and item["comment_count"] not in (None, ""):
                review_count = int(item["comment_count"])
            elif "rate_count" in item and item["rate_count"] not in (None, ""):
                review_count = int(item["rate_count"])
            elif "reviews" in item and item["reviews"] not in (None, ""):
                # JD 搜索示例中的 reviews
                try:
                    review_count = int(item["reviews"])
                except Exception:
                    review_count = 0

            # 评分
            rating = 0.0
            if "score" in item and item["score"] not in (None, ""):
                rating = float(item["score"])
            elif "rating" in item and item["rating"] not in (None, ""):
                rating = float(item["rating"])

            # 折扣
            discount_rate = 0.0
            if original_price and price and original_price > price:
                discount_rate = (original_price - price) / original_price

            product: Dict[str, Any] = {
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
                "source": "onebound",
            }

            if detailed:
                product.update(
                    {
                        "description": item.get("desc") or item.get("description") or "",
                        "category": item.get("cat_name") or "",
                        "category_id": item.get("cat_id") or "",
                        "brand": item.get("brand") or "",
                        "location": item.get("location") or "",
                        "post_fee": item.get("post_fee", 0),
                        "express_fee": item.get("express_fee", 0),
                        "ems_fee": item.get("ems_fee", 0),
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                    }
                )

            return product
        except Exception as e:
            logger.error("标准化商品数据失败: %s, item=%s", e, item)
            return None


# 创建全局实例
onebound_api_client = OneboundAPIClient()

