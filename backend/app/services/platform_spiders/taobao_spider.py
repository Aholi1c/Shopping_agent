"""
淘宝平台爬虫
专门用于抓取淘宝商品信息
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

class TaobaoScraper(EnhancedScraper):
    """淘宝爬虫类"""

    def __init__(self, config: EnhancedRequestConfig = None):
        super().__init__(config)
        self.base_url = "https://www.taobao.com"
        self.search_url = "https://s.taobao.com/search"
        self.product_url = "https://item.taobao.com/item.htm"
        self.rate_limiter = SmartRateLimiter()  # 使用智能速率限制

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        """构建搜索URL"""
        encoded_keyword = quote(keyword)
        start = (page - 1) * 44  # 每页44个商品
        return f"{self.search_url}?q={encoded_keyword}&s={start}"

    def get_product_url(self, product_id: str) -> str:
        """构建商品详情URL"""
        return f"{self.product_url}?id={product_id}"

    async def search_products(self, keyword: str, max_pages: int = 5) -> List[Dict]:
        """搜索商品"""
        all_products = []

        for page in range(1, max_pages + 1):
            # 智能延迟控制（继承自EnhancedScraper）
            await self.rate_limiter.acquire('s.taobao.com')
            logger.info(f"搜索 {keyword} - 第{page}页")

            search_url = self.get_search_url(keyword, page)

            # 使用更安全的请求方式
            content = await self.fetch_with_cookie(
                search_url,
                cookies=self.get_platform_cookies('taobao')
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
        content = await self.fetch_with_cookie(
            product_url,
            cookies=self.get_platform_cookies('taobao')
        )

        if not content:
            logger.warning(f"商品详情页面获取失败: {product_url}")
            return None

        # 检查是否是反爬虫页面
        if self._is_anti_bot_page_content(content):
            logger.warning(f"检测到反爬虫页面，跳过商品详情: {product_id}")
            return None

        # 解析商品详情
        product_data = await self._parse_product_details(content, product_id)
        return product_data

    async def _parse_search_results(self, html_content: str, keyword: str) -> List[Dict]:
        """解析搜索结果页面"""
        from bs4 import BeautifulSoup
        import random

        products = []
        soup = BeautifulSoup(html_content, 'lxml')

        # 查找商品列表 - 淘宝的HTML结构比较复杂
        # 尝试多种选择器
        product_items = []

        # 方法1: 使用data-api属性
        product_items.extend(soup.find_all('div', attrs={'data-id': True}))

        # 方法2: 使用商品项类名
        product_items.extend(soup.find_all('div', class_='item'))
        product_items.extend(soup.find_all('div', class_='Product--main'))
        product_items.extend(soup.find_all('div', class_='Card--doubleCard'))

        # 方法3: 使用J_TGoodsData类
        product_items.extend(soup.find_all('div', class_='J_TGoodsData'))

        # 去重
        unique_items = []
        seen_ids = set()
        for item in product_items:
            item_id = item.get('data-id') or item.get('id')
            if item_id and item_id not in seen_ids:
                unique_items.append(item)
                seen_ids.add(item_id)

        for item in unique_items[:20]:  # 限制每页最多20个商品
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
            product_id = item_element.get('data-id') or item_element.get('id')
            if not product_id:
                # 尝试从链接中提取
                link_element = item_element.find('a', href=True)
                if link_element:
                    href = link_element.get('href', '')
                    # 从URL中提取ID
                    id_match = re.search(r'id=(\d+)', href)
                    if id_match:
                        product_id = id_match.group(1)

            if not product_id:
                return None

            # 商品名称
            title_element = item_element.find('a', class_='productTitle') or \
                           item_element.find('div', class_='title') or \
                           item_element.find('a', title=True)

            if title_element:
                title = title_element.get('title') or title_element.get_text(strip=True)
            else:
                title = ''

            # 价格 - 淘宝的价格结构比较复杂
            price_element = item_element.find('div', class_='price') or \
                           item_element.find('span', class_='price') or \
                           item_element.find('div', class_='priceWrap')

            price = None
            if price_element:
                # 尝试多种价格选择器
                price_text = price_element.find('span', class_='g_price') or \
                           price_element.find('span', class_='priceInt') or \
                           price_element.find('strong') or \
                           price_element.find('em')

                if price_text:
                    price = self.parse_price(price_text.get_text(strip=True))
                else:
                    price = self.parse_price(price_element.get_text(strip=True))

            # 商店信息
            shop_element = item_element.find('div', class_='shop') or \
                          item_element.find('span', class_='shopname') or \
                          item_element.find('a', class_='shopname')
            shop_name = shop_element.get_text(strip=True) if shop_element else ''

            # 销量信息
            sales_element = item_element.find('div', class_='sale') or \
                           item_element.find('span', class_='sale-count') or \
                           item_element.find('div', class_='deal-cnt')

            sales_count = 0
            if sales_element:
                sales_text = sales_element.get_text(strip=True)
                # 解析销量数字
                sales_match = re.search(r'(\d+)', sales_text)
                if sales_match:
                    sales_count = int(sales_match.group(1))

            # 商品链接
            link_element = item_element.find('a', href=True)
            if link_element:
                href = link_element.get('href', '')
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = 'https://item.taobao.com' + href
                product_url = href
            else:
                product_url = self.get_product_url(product_id)

            # 图片URL
            img_element = item_element.find('img', src=True) or \
                          item_element.find('img', attrs={'data-src': True})
            if img_element:
                img_src = img_element.get('src') or \
                         img_element.get('data-src') or \
                         img_element.get('data-lazy-img')
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                elif img_src.startswith('/'):
                    img_src = 'https:' + img_src
                image_url = img_src
            else:
                image_url = ''

            # 地点信息
            location_element = item_element.find('div', class_='location') or \
                             item_element.find('span', class_='loc')
            location = location_element.get_text(strip=True) if location_element else ''

            return {
                'product_id': product_id,
                'title': title,
                'price': price,
                'shop_name': shop_name,
                'sales_count': sales_count,
                'location': location,
                'product_url': product_url,
                'image_url': image_url,
                'platform': 'taobao',
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
            'platform': 'taobao'
        }

        try:
            # 商品标题
            title_element = soup.find('h1') or soup.find('div', class_='tb-main-title')
            if title_element:
                product_details['title'] = title_element.get_text(strip=True)
            else:
                # 尝试从页面标题获取
                title_element = soup.find('title')
                product_details['title'] = title_element.get_text(strip=True).replace(' - 淘宝网', '') if title_element else ''

            # 店铺信息
            shop_element = soup.find('div', class_='tb-shop-name') or \
                           soup.find('a', class_='slogo') or \
                           soup.find('div', class_='shop-name')
            if shop_element:
                shop_link = shop_element.find('a') if not shop_element.name == 'a' else shop_element
                product_details['shop_name'] = shop_link.get_text(strip=True) if shop_link else shop_element.get_text(strip=True)

                # 店铺链接
                shop_url = shop_link.get('href') if shop_link else shop_element.get('href')
                if shop_url and shop_url.startswith('//'):
                    shop_url = 'https:' + shop_url
                product_details['shop_url'] = shop_url
            else:
                product_details['shop_name'] = ''
                product_details['shop_url'] = ''

            # 价格信息
            price_element = soup.find('span', class_='tb-rmb-num') or \
                           soup.find('em', class_='tb-rmb-num') or \
                           soup.find('div', class_='tb-price')

            if price_element:
                product_details['price'] = self.parse_price(price_element.get_text(strip=True))
            else:
                product_details['price'] = None

            # 商品描述
            desc_element = soup.find('div', id='description') or \
                           soup.find('div', class_='tb-detail-hd') or \
                           soup.find('div', class_='tb-content')

            if desc_element:
                # 清理脚本和广告
                for ad in desc_element.find_all(['script', 'iframe', 'ad']):
                    ad.decompose()
                product_details['description'] = desc_element.get_text(strip=True, separator=' ')
            else:
                product_details['description'] = ''

            # 商品参数
            params = {}
            param_element = soup.find('ul', id='J_AttrUL') or \
                           soup.find('div', class_='tb-prop-list') or \
                           soup.find('div', class_='attributes-list')

            if param_element:
                param_items = param_element.find_all('li')
                for item in param_items:
                    text = item.get_text(strip=True)
                    if '：' in text:
                        key, value = text.split('：', 1)
                        params[key.strip()] = value.strip()
                    elif ':' in text:
                        key, value = text.split(':', 1)
                        params[key.strip()] = value.strip()

            product_details['parameters'] = params

            # 规格选择
            specs = {}
            spec_element = soup.find('div', class_='tb-skin') or \
                           soup.find('div', class_='tb-prop') or \
                           soup.find('div', class_='tb-sku')

            if spec_element:
                spec_groups = spec_element.find_all('dl')
                for group in spec_groups:
                    spec_name = group.find('dt')
                    if spec_name:
                        spec_name_text = spec_name.get_text(strip=True)
                        spec_values = []
                        spec_items = group.find_all('li') or group.find_all('a')
                        for item in spec_items:
                            spec_text = item.get_text(strip=True)
                            if spec_text:
                                spec_values.append(spec_text)

                        if spec_values:
                            specs[spec_name_text] = spec_values

            product_details['specifications'] = specs

            # 商品图片
            images = []
            img_container = soup.find('ul', id='J_UlThumb') or \
                          soup.find('div', class_='tb-pic') or \
                          soup.find('div', class_='tb-gallery')

            if img_container:
                img_elements = img_container.find_all('img')
                for img in img_elements:
                    img_src = img.get('src') or img.get('data-src')
                    if img_src and ('.jpg' in img_src or '.png' in img_src):
                        if img_src.startswith('//'):
                            img_src = 'https:' + img_src
                        elif img_src.startswith('/'):
                            img_src = 'https:' + img_src
                        images.append(img_src)

            product_details['images'] = images[:10]  # 最多保存10张图片

            # 卖家信息
            seller_element = soup.find('div', class_='tb-seller-info') or \
                            soup.find('div', class_='tb-shop-rate')
            if seller_element:
                seller_info = {}
                rate_items = seller_element.find_all('span', class_='tb-rate')
                for rate in rate_items:
                    rate_text = rate.get_text(strip=True)
                    if '%' in rate_text:
                        seller_info['positive_rate'] = rate_text

                product_details['seller_info'] = seller_info

        except Exception as e:
            logger.error(f"解析商品详情失败 {product_id}: {e}")

        return product_details

    async def get_shop_info(self, shop_name: str) -> Optional[Dict]:
        """获取店铺信息"""
        # 这里可以实现店铺信息抓取
        pass

    async def search_by_category(self, category_id: str, max_pages: int = 5) -> List[Dict]:
        """按分类搜索商品"""
        all_products = []

        for page in range(1, max_pages + 1):
            await self.rate_limiter.acquire()

            url = f"https://s.taobao.com/search?q=&cat={category_id}&s={(page-1)*44}"
            content = await self.fetch_with_cookie(url)

            if content:
                products = await self._parse_search_results(content, f"category_{category_id}")
                all_products.extend(products)

                if page < max_pages:
                    await asyncio.sleep(random.uniform(3, 5))

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
            '访问过于频繁',
            '限流',
            '流量控制',
            'taobao反爬',
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
    scraper = TaobaoScraper()

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