"""
基础爬虫模块
提供通用的爬虫功能和反反爬机制
"""
import asyncio
import random
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
try:
    from fake_useragent import UserAgent
    FAKE_USERAGENT_AVAILABLE = True
except ImportError:
    FAKE_USERAGENT_AVAILABLE = False
    print("⚠️  fake-useragent未安装，将使用默认User-Agent。请运行: pip install fake-useragent")
    # 创建一个简单的UserAgent替代类
    class UserAgent:
        def __init__(self):
            pass
        def __getitem__(self, key):
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        def random(self):
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
import aiohttp
import logging
from urllib.parse import urljoin, urlparse
import hashlib
import json

logger = logging.getLogger(__name__)

@dataclass
class ProxyConfig:
    """代理配置"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"

@dataclass
class RequestConfig:
    """请求配置"""
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    use_proxy: bool = False
    delay_range: tuple = (1, 3)  # 随机延迟范围(秒)
    user_agent: Optional[str] = None

class BaseScraper:
    """基础爬虫类"""

    def __init__(self, config: RequestConfig = None):
        self.config = config or RequestConfig()
        self.ua = UserAgent()
        self.session = None
        self.proxy_list: List[ProxyConfig] = []
        self.current_proxy_index = 0

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_session()

    async def start_session(self):
        """启动HTTP会话"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )

        timeout = aiohttp.ClientTimeout(total=self.config.timeout)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self._get_default_headers()
        )

    async def close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()

    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        return {
            'User-Agent': self.config.user_agent or self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

    def add_proxy(self, proxy: ProxyConfig):
        """添加代理"""
        self.proxy_list.append(proxy)

    def get_next_proxy(self) -> Optional[ProxyConfig]:
        """获取下一个代理"""
        if not self.proxy_list:
            return None

        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy

    def get_proxy_url(self, proxy: ProxyConfig) -> str:
        """获取代理URL"""
        if proxy.username and proxy.password:
            return f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
        return f"{proxy.protocol}://{proxy.host}:{proxy.port}"

    async def random_delay(self):
        """随机延迟"""
        if self.config.delay_range:
            delay = random.uniform(*self.config.delay_range)
            await asyncio.sleep(delay)

    async def fetch_page(self, url: str, **kwargs) -> Optional[str]:
        """获取页面内容"""
        proxy = self.get_next_proxy() if self.config.use_proxy else None
        proxy_url = self.get_proxy_url(proxy) if proxy else None

        headers = self._get_default_headers()
        headers.update(kwargs.get('headers', {}))

        for attempt in range(self.config.retry_count):
            try:
                await self.random_delay()

                async with self.session.get(
                    url,
                    headers=headers,
                    proxy=proxy_url,
                    ssl=False,
                    **{k: v for k, v in kwargs.items() if k != 'headers'}
                ) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        if 'text/html' in content_type:
                            return await response.text()
                        elif 'application/json' in content_type:
                            return json.dumps(await response.json(), ensure_ascii=False)
                        else:
                            return await response.text()
                    elif response.status == 404:
                        logger.warning(f"Page not found: {url}")
                        return None
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        if response.status >= 500:
                            await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                            continue
                        else:
                            return None

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    logger.error(f"All attempts failed for {url}")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return None

        return None

    async def fetch_json(self, url: str, **kwargs) -> Optional[Dict]:
        """获取JSON数据"""
        content = await self.fetch_page(url, **kwargs)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from {url}: {e}")
                return None
        return None

    def parse_price(self, price_str: str) -> Optional[float]:
        """解析价格字符串"""
        import re

        if not price_str:
            return None

        # 移除货币符号和空格
        price_str = re.sub(r'[^\d.]', '', str(price_str))

        try:
            return float(price_str) if price_str else None
        except ValueError:
            return None

    def generate_content_hash(self, content: str) -> str:
        """生成内容哈希用于去重"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def is_valid_url(self, url: str) -> bool:
        """验证URL是否有效"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def sanitize_filename(self, filename: str) -> str:
        """清理文件名"""
        import re
        # 移除或替换无效字符
        return re.sub(r'[<>:"/\\|?*]', '_', filename)[:255]

    async def fetch_multiple(self, urls: List[str], **kwargs) -> List[Optional[str]]:
        """并发获取多个页面"""
        semaphore = asyncio.Semaphore(10)  # 限制并发数

        async def fetch_one(url):
            async with semaphore:
                return await self.fetch_page(url, **kwargs)

        tasks = [fetch_one(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_platform_cookies(self, platform: str) -> Dict[str, str]:
        """获取特定平台的Cookie设置"""
        platform_cookies = {
            'jd': {
                'shshshfpa': '',  # 京东反爬虫相关
                'shshshfpb': '',
                'qrreferer': '',
            },
            'taobao': {
                '_tb_token_': '',
                'cookie2': '',
                't': '',
                'unb': '',
            },
            'pdd': {
                'webp': '1',
                'whtoken': '',
            }
        }
        return platform_cookies.get(platform.lower(), {})

    async def fetch_with_cookie(self, url: str, cookies: Dict[str, str] = None, **kwargs) -> Optional[str]:
        """使用Cookie获取页面"""
        headers = self._get_default_headers()
        if cookies:
            cookie_header = '; '.join([f"{k}={v}" for k, v in cookies.items()])
            headers['Cookie'] = cookie_header

        return await self.fetch_page(url, headers=headers, **kwargs)

    def setup_logging(self, level: str = 'INFO'):
        """设置日志"""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)

class RateLimiter:
    """速率限制器"""

    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.lock = asyncio.Lock()

    async def acquire(self):
        """获取许可"""
        async with self.lock:
            now = time.time()
            # 清理过期的调用记录
            self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]

            if len(self.calls) >= self.max_calls:
                sleep_time = self.time_window - (now - self.calls[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

            self.calls.append(now)

# 使用示例
async def main():
    # 配置爬虫
    config = RequestConfig(
        timeout=30,
        retry_count=3,
        use_proxy=False,
        delay_range=(1, 3)
    )

    async with BaseScraper(config) as scraper:
        # 获取页面
        content = await scraper.fetch_page("https://example.com")
        if content:
            print(f"获取到内容，长度: {len(content)}")

        # 获取JSON数据
        data = await scraper.fetch_json("https://api.example.com/data")
        if data:
            print(f"获取到JSON数据: {len(data)} 条记录")

if __name__ == "__main__":
    asyncio.run(main())