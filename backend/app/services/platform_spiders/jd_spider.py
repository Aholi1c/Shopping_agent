"""
京东平台爬虫
专门用于抓取京东商品信息
"""
import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, quote
from .enhanced_base_spider import EnhancedScraper, EnhancedRequestConfig, SmartRateLimiter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class JDScraper(EnhancedScraper):
    """京东爬虫类"""

    def __init__(self, config: EnhancedRequestConfig = None):
        super().__init__(config)
        self.base_url = "https://www.jd.com"
        self.search_url = "https://search.jd.com/Search"
        self.api_search_url = "https://api.m.jd.com/api"
        self.product_url = "https://item.jd.com"
        self.price_url = "https://p.3.cn/prices/mgets"
        self.rate_limiter = SmartRateLimiter()  # 使用智能速率限制

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        """构建搜索URL"""
        encoded_keyword = quote(keyword)
        # 使用更稳定的URL格式
        return f"https://search.jd.com/Search?keyword={encoded_keyword}&enc=utf-8&page={page}"

    def get_product_url(self, product_id: str) -> str:
        """构建商品详情URL"""
        return f"{self.product_url}/{product_id}.html"

    async def search_products(self, keyword: str, max_pages: int = 5) -> List[Dict]:
        """搜索商品"""
        all_products = []

        for page in range(1, max_pages + 1):
            # 智能延迟控制（继承自EnhancedScraper）
            await self.rate_limiter.acquire('search.jd.com')
            logger.info(f"搜索 {keyword} - 第{page}页")

            search_url = self.get_search_url(keyword, page)

            # 使用更安全的请求方式
            content = await self.fetch_with_cookie(
                search_url,
                cookies=self.get_platform_cookies('jd')
            )

            if not content:
                logger.warning(f"搜索页面获取失败: {search_url}")
                continue

            # 检查是否是反爬虫页面
            if self._is_anti_bot_page_content(content):
                logger.warning(f"检测到反爬虫页面，跳过第{page}页")
                # 遇到反爬，增加延迟
                await asyncio.sleep(random.uniform(30, 60))
                continue

            # 解析搜索结果
            products = await self._parse_search_results(content, keyword)
            if products:
                all_products.extend(products)
                logger.info(f"第{page}页找到 {len(products)} 个商品")
            else:
                logger.warning(f"第{page}页未解析到商品")

            # 智能延迟（EnhancedScraper会自动处理）
            if page < max_pages:
                # 在基础延迟上增加额外的随机延迟
                await asyncio.sleep(random.uniform(3, 8))

        return all_products

    async def get_product_details(self, product_id: str) -> Optional[Dict]:
        """获取商品详情"""
        await self.rate_limiter.acquire()

        product_url = self.get_product_url(product_id)
        content = await self.fetch_with_cookie(product_url)

        if not content:
            logger.warning(f"商品详情页面获取失败: {product_url}")
            return None

        # 解析商品详情
        product_data = await self._parse_product_details(content, product_id)

        # 获取价格信息
        if product_data:
            price_info = await self.get_product_price(product_id)
            product_data.update(price_info)

        return product_data

    async def get_product_price(self, product_id: str) -> Dict:
        """获取商品价格信息"""
        await self.rate_limiter.acquire()

        params = {
            'skuIds': f'J_{product_id}',
            'type': '1'
        }

        try:
            price_data = await self.fetch_json(self.price_url, params=params)
            if price_data and len(price_data) > 0:
                price_info = price_data[0]
                return {
                    'price': self.parse_price(price_info.get('p', '0')),
                    'original_price': self.parse_price(price_info.get('m', '0')),
                    'discount_price': self.parse_price(price_info.get('op', '0')),
                    'price_update_time': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"获取价格失败 {product_id}: {e}")

        return {
            'price': None,
            'original_price': None,
            'discount_price': None,
            'price_update_time': datetime.now().isoformat()
        }

    async def _parse_search_results(self, html_content: str, keyword: str) -> List[Dict]:
        """解析搜索结果页面"""
        from bs4 import BeautifulSoup
        import random

        products = []
        soup = BeautifulSoup(html_content, 'lxml')

        # 查找商品列表
        product_items = soup.find_all('div', class_='gl-item') or soup.find_all('li', class_='gl-item')

        for item in product_items[:20]:  # 限制每页最多20个商品
            try:
                product_data = self._extract_product_info(item, keyword)
                if product_data:
                    products.append(product_data)
            except Exception as e:
                logger.error(f"解析商品信息失败: {e}")
                continue

        return products

    def _extract_product_info(self, item_element, keyword: str) -> Optional[Dict]:
        """从商品元素中提取信息"""
        try:
            # 商品ID
            sku_element = item_element.get('data-sku', '') or item_element.find('a', class_='log')
            if isinstance(sku_element, str):
                product_id = sku_element
            else:
                product_id = sku_element.get('href', '').split('/')[-1].replace('.html', '') if sku_element else ''

            if not product_id:
                return None

            # 商品名称
            title_element = item_element.find('div', class_='p-name') or item_element.find('div', class_='p-name-type-2')
            if title_element:
                title_link = title_element.find('a', href=True)
                title = title_link.get_text(strip=True) if title_link else ''
            else:
                title = ''

            # 价格
            price_element = item_element.find('div', class_='p-price') or item_element.find('strong', class_='J_price')
            if price_element:
                price_text = price_element.find('i') or price_element.find('strong') or price_element
                price = self.parse_price(price_text.get_text(strip=True))
            else:
                price = None

            # 商店信息
            shop_element = item_element.find('div', class_='p-shop') or item_element.find('span', class_='J_im_icon')
            shop_name = shop_element.get_text(strip=True) if shop_element else ''

            # 评论数量
            comment_element = item_element.find('div', class_='p-commit') or item_element.find('strong', class_='comment')
            comment_count = self._parse_comment_count(comment_element.get_text(strip=True)) if comment_element else 0

            # 商品链接
            link_element = item_element.find('a', href=True)
            if link_element:
                href = link_element.get('href', '')
                if href.startswith('//'):
                    href = 'https:' + href
                product_url = href
            else:
                product_url = ''

            # 图片URL
            img_element = item_element.find('img', src=True)
            if img_element:
                img_src = img_element.get('src', '') or img_element.get('data-src', '') or img_element.get('data-lazy-img', '')
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                image_url = img_src
            else:
                image_url = ''

            return {
                'product_id': product_id,
                'title': title,
                'price': price,
                'shop_name': shop_name,
                'comment_count': comment_count,
                'product_url': product_url,
                'image_url': image_url,
                'platform': 'jd',
                'search_keyword': keyword,
                'crawl_time': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"提取商品信息失败: {e}")
            return None

    async def _parse_product_details(self, html_content: str, product_id: str) -> Dict:
        """解析商品详情页面"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, 'lxml')
        product_details = {
            'product_id': product_id,
            'platform': 'jd'
        }

        try:
            # 商品标题
            title_element = soup.find('div', class_='sku-name') or soup.find('h1')
            product_details['title'] = title_element.get_text(strip=True) if title_element else ''

            # 品牌信息
            brand_element = soup.find('ul', id='parameter-brand') or soup.find('div', class_='brand')
            if brand_element:
                brand_link = brand_element.find('a')
                product_details['brand'] = brand_link.get_text(strip=True) if brand_link else ''
            else:
                product_details['brand'] = ''

            # 商品参数
            params = {}
            param_element = soup.find('div', class_='parameter2') or soup.find('ul', id='detail')
            if param_element:
                param_items = param_element.find_all('li') or param_element.find_all('tr')
                for item in param_items:
                    text = item.get_text(strip=True)
                    if '：' in text:
                        key, value = text.split('：', 1)
                        params[key.strip()] = value.strip()
                    elif ':' in text:
                        key, value = text.split(':', 1)
                        params[key.strip()] = value.strip()

            product_details['parameters'] = params

            # 商品描述
            desc_element = soup.find('div', class_='product-intro') or soup.find('div', class_='detail-content')
            if desc_element:
                # 清理广告和无关内容
                for ad in desc_element.find_all(['script', 'iframe', 'ad']):
                    ad.decompose()
                product_details['description'] = desc_element.get_text(strip=True, separator=' ')
            else:
                product_details['description'] = ''

            # 规格选择
            specs = {}
            spec_element = soup.find('div', class_='choose-wrap') or soup.find('div', class_='spec-list')
            if spec_element:
                spec_items = spec_element.find_all('div', class_='li') or spec_element.find_all('li')
                for spec_item in spec_items:
                    spec_text = spec_item.get_text(strip=True)
                    if spec_text:
                        # 尝试解析规格名称和选项
                        if '：' in spec_text or ':' in spec_text:
                            spec_name = spec_item.find_previous(['dt', 'label'])
                            if spec_name:
                                spec_name = spec_name.get_text(strip=True)
                                specs[spec_name] = spec_text
                        else:
                            specs[f'spec_{len(specs)}'] = spec_text

            product_details['specifications'] = specs

        except Exception as e:
            logger.error(f"解析商品详情失败 {product_id}: {e}")

        return product_details

    def _parse_comment_count(self, comment_text: str) -> int:
        """解析评论数量"""
        if not comment_text:
            return 0

        # 移除 '+' 和其他非数字字符
        numbers = re.findall(r'\d+', comment_text)
        if numbers:
            try:
                return int(numbers[0])
            except ValueError:
                return 0
        return 0

    async def get_product_comments(self, product_id: str, page: int = 0) -> List[Dict]:
        """获取商品评论"""
        await self.rate_limiter.acquire()

        comment_url = f"https://club.jd.com/comment/productCommentSummaries.action"
        params = {
            'referenceIds': product_id,
            'callback': 'jQueryJSONPCallback'
        }

        try:
            response = await self.fetch_json(comment_url, params=params)
            if response and 'CommentsCount' in response:
                return self._parse_comment_data(response)
        except Exception as e:
            logger.error(f"获取评论失败 {product_id}: {e}")

        return []

    def _parse_comment_data(self, comment_data: Dict) -> List[Dict]:
        """解析评论数据"""
        comments = []
        try:
            if 'CommentsCount' in comment_data:
                comment_info = comment_data['CommentsCount']
                if isinstance(comment_info, list) and len(comment_info) > 0:
                    comment_count = comment_info[0]
                    comments.append({
                        'good_rate': comment_count.get('GoodRate', 0),
                        'good_count': comment_count.get('GoodCount', 0),
                        'general_count': comment_count.get('GeneralCount', 0),
                        'poor_count': comment_count.get('PoorCount', 0),
                        'comment_count': comment_count.get('CommentCountStr', 0),
                        'average_score': comment_count.get('AverageScore', 0)
                    })
        except Exception as e:
            logger.error(f"解析评论数据失败: {e}")

        return comments

    async def search_by_category(self, category_id: str, max_pages: int = 5) -> List[Dict]:
        """按分类搜索商品"""
        all_products = []

        for page in range(1, max_pages + 1):
            await self.rate_limiter.acquire()

            url = f"https://search.jd.com/Search?cid={category_id}&page={page}"
            content = await self.fetch_with_cookie(url)

            if content:
                products = await self._parse_search_results(content, f"category_{category_id}")
                all_products.extend(products)

                if page < max_pages:
                    await asyncio.sleep(random.uniform(2, 4))

        return all_products

    def _is_anti_bot_page_content(self, content: str) -> bool:
        """检测是否是反爬虫页面内容"""
        anti_bot_indicators = [
            '风险检测',
            '安全验证',
            '机器人验证',
            '验证码',
            'captcha',
            '访问异常',
            'risk_handler',
            'security_check',
            'anti_spider',
            'blocked',
            'forbidden',
            '403',
            '检测到异常访问',
            '请完成安全验证',
            '请输入验证码',
        ]

        content_lower = content.lower()
        for indicator in anti_bot_indicators:
            if indicator.lower() in content_lower:
                logger.warning(f"Anti-bot indicator found: {indicator}")
                return True

        return False

    def generate_product_hash(self, product_data: Dict) -> str:
        """生成商品哈希用于去重"""
        import hashlib
        hash_input = f"{product_data.get('product_id', '')}_{product_data.get('platform', '')}_{product_data.get('title', '')}"
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()

# 使用示例
async def main():
    scraper = JDScraper()

    # 搜索商品
    products = await scraper.search_products("手机", max_pages=2)
    print(f"搜索到 {len(products)} 个商品")

    # 获取商品详情
    if products:
        product_id = products[0]['product_id']
        details = await scraper.get_product_details(product_id)
        if details:
            print(f"商品详情: {details.get('title', 'Unknown')}")

if __name__ == "__main__":
    import random
    asyncio.run(main())