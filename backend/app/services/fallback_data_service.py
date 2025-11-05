"""
备用数据源服务
当网络爬虫和API都失败时，提供模拟数据
"""
import random
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class FallbackDataService:
    """备用数据服务"""

    def __init__(self):
        # 模拟商品数据库
        self.mock_products = {
            '手机': [
                {
                    'product_id': 'mock_phone_001',
                    'title': 'iPhone 15 Pro Max 256GB',
                    'platform': 'mock',
                    'price': 9999.0,
                    'original_price': 10999.0,
                    'shop_name': '苹果官方旗舰店',
                    'sales_count': 12580,
                    'rating': 4.8,
                    'product_url': 'https://example.com/iphone15pro',
                    'image_url': 'https://example.com/images/iphone15.jpg',
                    'description': '苹果最新旗舰手机，配备A17 Pro芯片，钛金属设计，支持USB-C接口',
                    'search_keyword': '手机',
                    'crawl_time': datetime.now().isoformat()
                },
                {
                    'product_id': 'mock_phone_002',
                    'title': '小米14 Ultra 徕卡影像',
                    'platform': 'mock',
                    'price': 6999.0,
                    'original_price': 7999.0,
                    'shop_name': '小米官方旗舰店',
                    'sales_count': 8920,
                    'rating': 4.6,
                    'product_url': 'https://example.com/mi14ultra',
                    'image_url': 'https://example.com/images/mi14.jpg',
                    'description': '徕卡光学联合研发，专业影像旗舰',
                    'search_keyword': '手机',
                    'crawl_time': datetime.now().isoformat()
                }
            ],
            '笔记本电脑': [
                {
                    'product_id': 'mock_laptop_001',
                    'title': 'MacBook Air M3 13英寸 8GB+256GB',
                    'platform': 'mock',
                    'price': 8999.0,
                    'original_price': 9999.0,
                    'shop_name': '苹果官方旗舰店',
                    'sales_count': 4560,
                    'rating': 4.9,
                    'product_url': 'https://example.com/macbookairm3',
                    'image_url': 'https://example.com/images/macbookair.jpg',
                    'description': '全新M3芯片，轻薄便携，续航出色',
                    'search_keyword': '笔记本电脑',
                    'crawl_time': datetime.now().isoformat()
                }
            ]
        }

    def get_fallback_products(self, keyword: str, count: int = 10) -> List[Dict]:
        """获取备用商品数据"""
        logger.info(f"使用备用数据源搜索: {keyword}")

        # 尝试匹配关键词
        matched_products = []

        # 完全匹配
        if keyword in self.mock_products:
            matched_products = self.mock_products[keyword]
        # 部分匹配
        else:
            for search_key, products in self.mock_products.items():
                if keyword in search_key or search_key in keyword:
                    matched_products.extend(products)

        if matched_products:
            # 随机选择并返回指定数量的商品
            selected_products = random.sample(
                matched_products,
                min(count, len(matched_products))
            )

            # 为每个商品添加一些随机变化
            for product in selected_products:
                product = product.copy()
                # 随机价格波动
                if product.get('price'):
                    product['price'] *= random.uniform(0.95, 1.05)
                if product.get('original_price'):
                    product['original_price'] *= random.uniform(0.95, 1.05)
                # 更新时间戳
                product['crawl_time'] = datetime.now().isoformat()
                # 添加备用数据标记
                product['is_fallback_data'] = True
                matched_products.append(product)

            return selected_products

        # 如果没有匹配的商品，生成通用商品
        return self._generate_generic_products(keyword, count)

    def _generate_generic_products(self, keyword: str, count: int) -> List[Dict]:
        """生成通用商品数据"""
        logger.info(f"生成通用商品数据: {keyword}")

        generic_products = []
        shop_names = ['官方旗舰店', '品牌专卖店', '授权经销商', '海外购专营店']

        for i in range(count):
            product = {
                'product_id': f'generic_{hash(keyword)}_{i}',
                'title': f'{keyword} - 商品{i+1}',
                'platform': 'mock',
                'price': random.randint(100, 10000),
                'original_price': random.randint(120, 12000),
                'shop_name': random.choice(shop_names),
                'sales_count': random.randint(100, 5000),
                'rating': round(random.uniform(3.5, 5.0), 1),
                'product_url': f'https://example.com/product/{hash(keyword)}_{i}',
                'image_url': f'https://example.com/images/{hash(keyword)}_{i}.jpg',
                'description': f'高品质{keyword}，满足您的需求',
                'search_keyword': keyword,
                'crawl_time': datetime.now().isoformat(),
                'is_fallback_data': True,
                'is_generated': True
            }
            generic_products.append(product)

        return generic_products

    def get_fallback_product_details(self, product_id: str) -> Optional[Dict]:
        """获取备用商品详情"""
        logger.info(f"获取备用商品详情: {product_id}")

        # 在模拟数据中查找
        for products in self.mock_products.values():
            for product in products:
                if product['product_id'] == product_id:
                    details = product.copy()
                    details['crawl_time'] = datetime.now().isoformat()
                    details['is_fallback_data'] = True

                    # 添加详细规格
                    details['specifications'] = {
                        '品牌': '模拟品牌',
                        '型号': '模拟型号',
                        '颜色': '多种颜色可选',
                        '材质': '优质材料',
                        '保修': '一年保修'
                    }

                    # 添加参数
                    details['parameters'] = {
                        '生产日期': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                        '产地': '中国制造',
                        '重量': '标准重量',
                        '尺寸': '标准尺寸'
                    }

                    return details

        # 生成通用商品详情
        return self._generate_generic_product_details(product_id)

    def _generate_generic_product_details(self, product_id: str) -> Optional[Dict]:
        """生成通用商品详情"""
        return {
            'product_id': product_id,
            'title': f'商品详情 - {product_id}',
            'platform': 'mock',
            'price': random.randint(100, 10000),
            'original_price': random.randint(120, 12000),
            'shop_name': '模拟店铺',
            'description': '这是一个高质量的模拟商品，满足您的各种需求。',
            'specifications': {
                '品牌': '知名品牌',
                '型号': '标准型号',
                '颜色': '多种选择',
                '材质': '优质材料'
            },
            'parameters': {
                '生产日期': datetime.now().strftime('%Y-%m-%d'),
                '产地': '中国制造',
                '保修': '一年保修'
            },
            'images': [
                f'https://example.com/images/{product_id}_1.jpg',
                f'https://example.com/images/{product_id}_2.jpg',
                f'https://example.com/images/{product_id}_3.jpg'
            ],
            'crawl_time': datetime.now().isoformat(),
            'is_fallback_data': True,
            'is_generated': True
        }

    def get_statistics(self) -> Dict:
        """获取备用数据源统计信息"""
        return {
            'total_mock_products': sum(len(products) for products in self.mock_products.values()),
            'available_keywords': list(self.mock_products.keys()),
            'fallback_data_enabled': True,
            'generated_data_available': True
        }

    def add_mock_product(self, keyword: str, product: Dict):
        """添加模拟商品数据"""
        if keyword not in self.mock_products:
            self.mock_products[keyword] = []

        product['is_mock'] = True
        self.mock_products[keyword].append(product)
        logger.info(f"添加模拟商品: {keyword} - {product.get('title', 'Unknown')}")

# 全局实例
fallback_data_service = FallbackDataService()

# 使用示例
def main():
    service = FallbackDataService()

    # 搜索商品
    products = service.get_fallback_products("手机", count=3)
    print(f"获取到 {len(products)} 个备用商品")

    # 获取商品详情
    if products:
        details = service.get_fallback_product_details(products[0]['product_id'])
        if details:
            print(f"商品详情: {details.get('title', 'Unknown')}")

    # 获取统计信息
    stats = service.get_statistics()
    print(f"备用数据统计: {stats}")

if __name__ == "__main__":
    main()