"""
拼多多平台爬虫
专门用于抓取拼多多商品信息
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

class PDDScraper(EnhancedScraper):
    """拼多多爬虫类"""

    def __init__(self, config: EnhancedRequestConfig = None):
        super().__init__(config)
        self.base_url = "https://yangkeduo.com"
        self.search_url = "https://mobile.yangkeduo.com/search.html"
        self.product_url = "https://mobile.yangkeduo.com/goods.html"
        self.rate_limiter = SmartRateLimiter()  # 使用智能速率限制

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        """构建搜索URL"""
        encoded_keyword = quote(keyword)
        return f"{self.search_url}?search_key={encoded_keyword}&page={page}"

    def get_product_url(self, product_id: str) -> str:
        """构建商品详情URL"""
        return f"{self.product_url}?goods_id={product_id}"

    async def search_products(self, keyword: str, max_pages: int = 5) -> List[Dict]:
        """搜索商品"""
        all_products = []

        for page in range(1, max_pages + 1):
            # 智能延迟控制（继承自EnhancedScraper）
            await self.rate_limiter.acquire('mobile.yangkeduo.com')
            logger.info(f"搜索 {keyword} - 第{page}页")

            search_url = self.get_search_url(keyword, page)

            # 使用更安全的请求方式
            content = await self.fetch_with_cookie(
                search_url,
                cookies=self.get_platform_cookies('pdd')
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
            cookies=self.get_platform_cookies('pdd')
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

        # 查找商品列表
        product_items = []

        # 拼多多有多种商品列表结构
        product_items.extend(soup.find_all('div', class_='goods-item'))
        product_items.extend(soup.find_all('div', class_='item'))
        product_items.extend(soup.find_all('div', class_='product-item'))
        product_items.extend(soup.find_all('a', class_='goods-item-link'))

        # 去重
        unique_items = []
        seen_ids = set()
        for item in product_items:
            item_id = item.get('data-goods-id') or item.get('data-id') or item.get('id')
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
            product_id = item_element.get('data-goods-id') or \
                        item_element.get('data-id') or \
                        item_element.get('id')

            if not product_id:
                # 尝试从链接中提取
                link_element = item_element.find('a', href=True)
                if link_element:
                    href = link_element.get('href', '')
                    # 从URL中提取ID
                    id_match = re.search(r'goods[ _]?id[=:]([^\D]+)', href, re.IGNORECASE)
                    if id_match:
                        product_id = id_match.group(1)

            if not product_id:
                return None

            # 商品名称
            title_element = item_element.find('div', class_='goods-name') or \
                           item_element.find('div', class_='title') or \
                           item_element.find('span', class_='name') or \
                           item_element.find('a', title=True)

            if title_element:
                title = title_element.get('title') or title_element.get_text(strip=True)
            else:
                title = ''

            # 价格 - 拼多多通常有原价和拼单价
            price_element = item_element.find('div', class_='price') or \
                           item_element.find('span', class_='price') or \
                           item_element.find('div', class_='goods-price')

            price = None
            original_price = None

            if price_element:
                # 尝试提取当前价格
                current_price_el = price_element.find('span', class_='current') or \
                                  price_element.find('span', class_='red') or \
                                  price_element.find('em') or \
                                  price_element

                if current_price_el:
                    price = self.parse_price(current_price_el.get_text(strip=True))

                # 尝试提取原价
                original_price_el = price_element.find('span', class_='original') or \
                                   price_element.find('span', class_='market-price') or \
                                   price_element.find('del')

                if original_price_el:
                    original_price = self.parse_price(original_price_el.get_text(strip=True))

            # 销量信息
            sales_element = item_element.find('div', class_='sales') or \
                           item_element.find('span', class_='sales-num') or \
                           item_element.find('div', class_='sold')

            sales_count = 0
            if sales_element:
                sales_text = sales_element.get_text(strip=True)
                # 解析销量数字
                if '万' in sales_text:
                    match = re.search(r'([\d.]+)万', sales_text)
                    if match:
                        sales_count = int(float(match.group(1)) * 10000)
                else:
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
                    href = 'https://mobile.yangkeduo.com' + href
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

            # 拼团人数
            group_element = item_element.find('div', class_='group-num') or \
                          item_element.find('span', class_='group-count')
            group_count = 0
            if group_element:
                group_text = group_element.get_text(strip=True)
                group_match = re.search(r'(\d+)', group_text)
                if group_match:
                    group_count = int(group_match.group(1))

            return {
                'product_id': product_id,
                'title': title,
                'price': price,
                'original_price': original_price,
                'sales_count': sales_count,
                'group_count': group_count,
                'product_url': product_url,
                'image_url': image_url,
                'platform': 'pdd',
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
            'platform': 'pdd'
        }

        try:
            # 商品标题
            title_element = soup.find('h1') or soup.find('div', class_='goods-name') or \
                           soup.find('div', class_='title') or soup.find('title')
            if title_element:
                title_text = title_element.get_text(strip=True)
                # 清理标题中的平台名称
                title_text = title_text.replace('拼多多', '').replace(' - 拼多多', '').strip()
                product_details['title'] = title_text

            # 店铺信息
            shop_element = soup.find('div', class_='shop-name') or \
                           soup.find('div', class_='mall-name') or \
                           soup.find('span', class_='shop-name')
            if shop_element:
                shop_link = shop_element.find('a') if not shop_element.name == 'a' else shop_element
                product_details['shop_name'] = shop_link.get_text(strip=True) if shop_link else shop_element.get_text(strip=True)
            else:
                product_details['shop_name'] = ''

            # 价格信息
            price_element = soup.find('span', class_='current-price') or \
                           soup.find('div', class_='price-info') or \
                           soup.find('span', class_='price')

            if price_element:
                product_details['price'] = self.parse_price(price_element.get_text(strip=True))
            else:
                product_details['price'] = None

            # 原价
            original_element = soup.find('del') or \
                             soup.find('span', class_='original-price')
            if original_element:
                product_details['original_price'] = self.parse_price(original_element.get_text(strip=True))
            else:
                product_details['original_price'] = None

            # 商品描述
            desc_element = soup.find('div', class_='description') or \
                           soup.find('div', class_='detail-content') or \
                           soup.find('div', class_='goods-detail')

            if desc_element:
                # 清理脚本和广告
                for ad in desc_element.find_all(['script', 'iframe', 'ad']):
                    ad.decompose()
                product_details['description'] = desc_element.get_text(strip=True, separator=' ')
            else:
                product_details['description'] = ''

            # 商品参数
            params = {}
            param_element = soup.find('ul', class_='parameter-list') or \
                           soup.find('div', class_='attributes') or \
                           soup.find('table', class_='specs')

            if param_element:
                param_items = param_element.find_all('li') or param_element.find_all('tr') or \
                             param_element.find_all('div', class_='param-item')
                for item in param_items:
                    text = item.get_text(strip=True)
                    if '：' in text:
                        key, value = text.split('：', 1)
                        params[key.strip()] = value.strip()
                    elif ':' in text:
                        key, value = text.split(':', 1)
                        params[key.strip()] = value.strip()
                    elif text:
                        # 如果没有分隔符，作为参数名，值设为空
                        params[text.strip()] = ''

            product_details['parameters'] = params

            # 规格选择
            specs = {}
            spec_element = soup.find('div', class_='sku-list') or \
                           soup.find('div', class_='specs-container') or \
                           soup.find('div', class_='goods-specs')

            if spec_element:
                spec_groups = spec_element.find_all('div', class_='spec-group') or \
                             spec_element.find_all('ul', class_='sku-row')
                for group in spec_groups:
                    spec_name = group.find('span', class_='spec-name') or group.find('dt')
                    if spec_name:
                        spec_name_text = spec_name.get_text(strip=True)
                        spec_values = []
                        spec_items = group.find_all('li') or group.find_all('span', class_='spec-value')
                        for item in spec_items:
                            spec_text = item.get_text(strip=True)
                            if spec_text:
                                spec_values.append(spec_text)

                        if spec_values:
                            specs[spec_name_text] = spec_values

            product_details['specifications'] = specs

            # 商品图片
            images = []
            img_container = soup.find('ul', class_='goods-gallery') or \
                          soup.find('div', class_='image-list') or \
                          soup.find('div', class_='swiper-wrapper')

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

            # 销量信息
            sales_element = soup.find('div', class_='sales-info') or \
                           soup.find('span', class_='sales-count')
            if sales_element:
                sales_text = sales_element.get_text(strip=True)
                if '万' in sales_text:
                    match = re.search(r'([\d.]+)万', sales_text)
                    if match:
                        product_details['sales_count'] = int(float(match.group(1)) * 10000)
                else:
                    sales_match = re.search(r'(\d+)', sales_text)
                    if sales_match:
                        product_details['sales_count'] = int(sales_match.group(1))
            else:
                product_details['sales_count'] = 0

            # 店铺评分
            rating_element = soup.find('div', class_='shop-rating') or \
                            soup.find('span', class_='rating')
            if rating_element:
                rating_text = rating_element.get_text(strip=True)
                rating_match = re.search(r'([\d.]+)', rating_text)
                if rating_match:
                    product_details['shop_rating'] = float(rating_match.group(1))
                else:
                    product_details['shop_rating'] = None
            else:
                product_details['shop_rating'] = None

        except Exception as e:
            logger.error(f"解析商品详情失败 {product_id}: {e}")

        return product_details

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
            'pdd反爬',
            '拼多多反爬',
            '系统繁忙',
            '稍后重试',
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
    scraper = PDDScraper()

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