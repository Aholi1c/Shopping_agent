"""
网络爬虫服务
统一管理各平台的数据获取任务
"""
import asyncio
import logging
import random
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import hashlib
from pathlib import Path
import aiohttp
import pandas as pd

from .platform_spiders.jd_spider import JDScraper
from .platform_spiders.taobao_spider import TaobaoScraper
from .platform_spiders.pdd_spider import PDDScraper
from .platform_spiders.enhanced_base_spider import EnhancedRequestConfig
from ..config.proxy_config import ProxyManager, ProxyConfig

logger = logging.getLogger(__name__)

class WebScraperService:
    """网络爬虫服务主类"""

    def __init__(self):
        # 创建增强请求配置
        self.request_config = EnhancedRequestConfig(
            timeout=30,
            retry_count=5,
            use_proxy=True,
            delay_range=(3, 8),
            use_real_browser=True
        )

        # 初始化代理管理器
        self.proxy_manager = ProxyManager()

        # 创建爬虫实例
        self.scrapers = {
            'jd': JDScraper(config=self.request_config),
            'taobao': TaobaoScraper(config=self.request_config),
            'pdd': PDDScraper(config=self.request_config),
        }
        self.crawl_queue = asyncio.Queue()
        self.results_cache = {}
        self.cache_ttl = 3600  # 缓存1小时
        self.is_running = False
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'products_found': 0,
            'platform_stats': {}
        }

    async def start(self):
        """启动爬虫服务"""
        if self.is_running:
            return

        self.is_running = True
        logger.info("Web Scraper Service started")

        # 初始化代理池
        await self._initialize_proxies()

        # 启动消费者任务
        asyncio.create_task(self._process_queue())

    async def stop(self):
        """停止爬虫服务"""
        self.is_running = False
        logger.info("Web Scraper Service stopped")

    async def search_products(self,
                            keyword: str,
                            platforms: List[str] = None,
                            max_pages: int = 3,
                            force_refresh: bool = False) -> Dict[str, List[Dict]]:
        """跨平台商品搜索"""
        if platforms is None:
            platforms = ['jd', 'taobao', 'pdd']

        # 检查缓存
        cache_key = self._generate_cache_key('search', keyword, platforms, max_pages)
        if not force_refresh and cache_key in self.results_cache:
            cached_result = self.results_cache[cache_key]
            if self._is_cache_valid(cached_result):
                logger.info(f"返回缓存结果: {cache_key}")
                return cached_result['data']

        results = {}
        tasks = []

        # 并发搜索各平台
        for platform in platforms:
            if platform in self.scrapers:
                task = self._search_platform(platform, keyword, max_pages)
                tasks.append(task)

        # 等待所有搜索完成
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        for i, result in enumerate(platform_results):
            platform = platforms[i]
            if isinstance(result, Exception):
                logger.error(f"{platform} 搜索失败: {result}")
                results[platform] = []
            else:
                results[platform] = result

        # 缓存结果
        self.results_cache[cache_key] = {
            'data': results,
            'timestamp': datetime.now().timestamp(),
            'keyword': keyword,
            'platforms': platforms,
            'total_products': sum(len(products) for products in results.values())
        }

        # 更新统计信息
        total_products = sum(len(products) for products in results.values())
        self.stats['total_requests'] += 1
        self.stats['products_found'] += total_products

        return results

    async def get_product_details(self,
                                product_id: str,
                                platform: str,
                                force_refresh: bool = False) -> Optional[Dict]:
        """获取商品详情"""
        if platform not in self.scrapers:
            logger.error(f"不支持的平台: {platform}")
            return None

        # 检查缓存
        cache_key = self._generate_cache_key('details', product_id, platform)
        if not force_refresh and cache_key in self.results_cache:
            cached_result = self.results_cache[cache_key]
            if self._is_cache_valid(cached_result):
                logger.info(f"返回缓存的商品详情: {product_id}")
                return cached_result['data']

        try:
            scraper = self.scrapers[platform]
            details = await scraper.get_product_details(product_id)

            if details:
                # 缓存结果
                self.results_cache[cache_key] = {
                    'data': details,
                    'timestamp': datetime.now().timestamp(),
                    'product_id': product_id,
                    'platform': platform
                }

                self.stats['successful_requests'] += 1
            else:
                self.stats['failed_requests'] += 1

            return details

        except Exception as e:
            logger.error(f"获取商品详情失败 {platform}:{product_id}: {e}")
            self.stats['failed_requests'] += 1
            return None

    async def batch_get_product_details(self,
                                       product_ids: List[Dict[str, str]],
                                       max_concurrent: int = 5) -> List[Optional[Dict]]:
        """批量获取商品详情"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def get_one_detail(item):
            async with semaphore:
                return await self.get_product_details(
                    item['product_id'],
                    item['platform']
                )

        tasks = [get_one_detail(item) for item in product_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [result if not isinstance(result, Exception) else None for result in results]

    async def get_price_history(self,
                               product_id: str,
                               platform: str,
                               days: int = 30) -> List[Dict]:
        """获取价格历史"""
        # 这里可以实现价格历史记录功能
        # 目前返回模拟数据
        return []

    async def compare_prices(self,
                           keyword: str,
                           platforms: List[str] = None) -> List[Dict]:
        """跨平台价格比较"""
        if platforms is None:
            platforms = ['jd', 'taobao', 'pdd']

        search_results = await self.search_products(keyword, platforms, max_pages=2)
        comparison_data = []

        for platform, products in search_results.items():
            for product in products:
                if product.get('price'):
                    comparison_data.append({
                        'platform': platform,
                        'product_id': product.get('product_id'),
                        'title': product.get('title'),
                        'price': product.get('price'),
                        'shop_name': product.get('shop_name'),
                        'product_url': product.get('product_url'),
                        'image_url': product.get('image_url'),
                        'crawl_time': product.get('crawl_time')
                    })

        # 按价格排序
        comparison_data.sort(key=lambda x: x['price'] or float('inf'))

        return comparison_data

    async def monitor_price_changes(self,
                                 products: List[Dict[str, str]],
                                 check_interval: int = 3600) -> None:
        """价格变化监控"""
        while True:
            try:
                logger.info(f"开始检查 {len(products)} 个商品的价格变化")

                for product in products:
                    current_details = await self.get_product_details(
                        product['product_id'],
                        product['platform'],
                        force_refresh=True
                    )

                    if current_details and current_details.get('price'):
                        current_price = current_details['price']
                        old_price = product.get('price')

                        if old_price and current_price != old_price:
                            logger.info(f"价格变化: {product['title']} {old_price} -> {current_price}")
                            # 这里可以触发价格变化通知

                            # 更新产品价格
                            product['price'] = current_price
                            product['last_updated'] = datetime.now().isoformat()

                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"价格监控错误: {e}")
                await asyncio.sleep(60)  # 错误后等待1分钟再重试

    async def export_data(self,
                        data: Union[List[Dict], Dict],
                        format: str = 'csv',
                        filename: str = None) -> str:
        """导出数据到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_data_{timestamp}.{format}"

        if isinstance(data, dict):
            # 如果是分平台的数据，合并
            flattened_data = []
            for platform, products in data.items():
                for product in products:
                    product['platform'] = platform
                    flattened_data.append(product)
            data = flattened_data

        try:
            df = pd.DataFrame(data)

            if format.lower() == 'csv':
                df.to_csv(filename, index=False, encoding='utf-8-sig')
            elif format.lower() == 'json':
                df.to_json(filename, orient='records', ensure_ascii=False, indent=2)
            elif format.lower() == 'excel':
                df.to_excel(filename, index=False)
            else:
                raise ValueError(f"不支持的导出格式: {format}")

            logger.info(f"数据已导出到: {filename}")
            return filename

        except Exception as e:
            logger.error(f"数据导出失败: {e}")
            raise

    async def _search_platform(self,
                              platform: str,
                              keyword: str,
                              max_pages: int) -> List[Dict]:
        """在指定平台搜索商品"""
        try:
            scraper = self.scrapers[platform]
            products = await scraper.search_products(keyword, max_pages)

            logger.info(f"{platform} 搜索 '{keyword}' 找到 {len(products)} 个商品")
            return products

        except Exception as e:
            logger.error(f"{platform} 搜索失败: {e}")
            raise

    async def _process_queue(self):
        """处理队列任务"""
        while self.is_running:
            try:
                task = await asyncio.wait_for(
                    self.crawl_queue.get(),
                    timeout=1.0
                )
                await self._execute_task(task)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"队列处理错误: {e}")

    async def _execute_task(self, task: Dict):
        """执行单个爬取任务"""
        try:
            task_type = task.get('type')
            if task_type == 'search':
                await self.search_products(**task['kwargs'])
            elif task_type == 'details':
                await self.get_product_details(**task['kwargs'])
            elif task_type == 'monitor':
                await self.monitor_price_changes(**task['kwargs'])

        except Exception as e:
            logger.error(f"任务执行失败: {e}")

    def _generate_cache_key(self, *args) -> str:
        """生成缓存键"""
        key_string = '_'.join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()

    def _is_cache_valid(self, cached_item: Dict) -> bool:
        """检查缓存是否有效"""
        if not cached_item:
            return False

        timestamp = cached_item.get('timestamp', 0)
        current_time = datetime.now().timestamp()
        return (current_time - timestamp) < self.cache_ttl

    async def _initialize_proxies(self):
        """初始化代理池"""
        # 添加一些示例代理
        sample_proxies = [
            ProxyConfig(
                host="proxy1.example.com",
                port=8080,
                username="user1",
                password="pass1",
                protocol="http",
                weight=2,
                country="US"
            ),
            ProxyConfig(
                host="proxy2.example.com",
                port=3128,
                username="user2",
                password="pass2",
                protocol="socks5",
                weight=1,
                country="SG"
            )
        ]

        for proxy in sample_proxies:
            self.proxy_manager.add_proxy(proxy)

        logger.info(f"初始化代理池，共 {len(self.proxy_manager.proxies)} 个代理")

    def add_proxy(self, proxy: ProxyConfig):
        """添加代理"""
        self.proxy_manager.add_proxy(proxy)

        # 更新所有爬虫的代理池
        for scraper in self.scrapers.values():
            scraper.add_proxy(proxy)

    def refresh_proxies(self):
        """刷新代理池"""
        self.proxy_manager.clean_expired_proxies()
        stats = self.proxy_manager.get_statistics()
        logger.info(f"代理池刷新: {stats}")

    async def get_proxy_for_domain(self, domain: str) -> Optional[ProxyConfig]:
        """获取指定域名的代理"""
        return self.proxy_manager.get_proxy(domain)

    def report_proxy_success(self, proxy: ProxyConfig, response_time: float):
        """报告代理成功"""
        self.proxy_manager.report_success(proxy, response_time)

    def report_proxy_failure(self, proxy: ProxyConfig, error_type: str):
        """报告代理失败"""
        self.proxy_manager.report_failure(proxy, error_type)

    def get_statistics(self) -> Dict:
        """获取爬虫统计信息"""
        proxy_stats = self.proxy_manager.get_statistics()
        return {
            **self.stats,
            'cache_size': len(self.results_cache),
            'is_running': self.is_running,
            'supported_platforms': list(self.scrapers.keys()),
            'proxy_stats': proxy_stats
        }

    def clear_cache(self):
        """清理缓存"""
        self.results_cache.clear()
        logger.info("缓存已清理")

    async def cleanup_old_cache(self, max_age_hours: int = 24):
        """清理过期缓存"""
        current_time = datetime.now().timestamp()
        max_age = max_age_hours * 3600

        expired_keys = []
        for key, cached_item in self.results_cache.items():
            if current_time - cached_item.get('timestamp', 0) > max_age:
                expired_keys.append(key)

        for key in expired_keys:
            del self.results_cache[key]

        logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")

    def add_to_queue(self, task: Dict):
        """添加任务到队列"""
        self.crawl_queue.put_nowait(task)
        self.stats['total_requests'] += 1

    async def scheduled_crawl(self,
                             keyword: str,
                             platforms: List[str],
                             interval_hours: int = 6):
        """定时爬取任务"""
        while self.is_running:
            try:
                logger.info(f"执行定时爬取: {keyword} on {platforms}")
                await self.search_products(keyword, platforms, force_refresh=True)

                # 等待下一次爬取
                await asyncio.sleep(interval_hours * 3600)

            except Exception as e:
                logger.error(f"定时爬取错误: {e}")
                await asyncio.sleep(300)  # 错误后等待5分钟

# 全局实例
web_scraper_service = WebScraperService()

# 使用示例
async def main():
    service = WebScraperService()
    await service.start()

    try:
        # 跨平台搜索
        results = await service.search_products("手机", ['jd', 'taobao', 'pdd'], max_pages=2)
        for platform, products in results.items():
            print(f"{platform}: {len(products)} 个商品")

        # 价格比较
        comparison = await service.compare_prices("笔记本电脑")
        print(f"找到 {len(comparison)} 个价格比较结果")

        # 批量获取详情
        if comparison:
            product_ids = [{'product_id': p['product_id'], 'platform': p['platform']}
                          for p in comparison[:5]]
            details = await service.batch_get_product_details(product_ids)
            print(f"获取到 {len([d for d in details if d])} 个商品详情")

        # 获取统计信息
        stats = service.get_statistics()
        print(f"爬虫统计: {stats}")

    finally:
        await service.stop()

if __name__ == "__main__":
    import random
    asyncio.run(main())