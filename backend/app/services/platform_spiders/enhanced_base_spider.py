"""
增强版基础爬虫模块
针对反爬虫问题的优化版本
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
from urllib.parse import urljoin, urlparse, quote
import hashlib
import json
import re

logger = logging.getLogger(__name__)

@dataclass
class ProxyConfig:
    """代理配置"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    weight: int = 1  # 权重，用于负载均衡

@dataclass
class EnhancedRequestConfig:
    """增强请求配置"""
    timeout: int = 30
    retry_count: int = 5
    retry_delay: float = 2.0
    use_proxy: bool = False
    delay_range: tuple = (3, 8)  # 增加延迟时间
    user_agent: Optional[str] = None
    use_real_browser: bool = True  # 使用真实浏览器UA

class EnhancedScraper:
    """增强版基础爬虫类"""

    def __init__(self, config: EnhancedRequestConfig = None):
        self.config = config or EnhancedRequestConfig()
        if FAKE_USERAGENT_AVAILABLE:
            try:
                self.ua = UserAgent(fallback='chrome')  # 优先使用Chrome UA
            except:
                self.ua = UserAgent()  # 如果fallback不支持，使用默认
        else:
            self.ua = UserAgent()  # 使用替代类
        self.session = None
        self.proxy_list: List[ProxyConfig] = []
        self.current_proxy_index = 0
        self.request_timestamps = {}  # 记录每个域名的请求时间
        self.domain_delays = {
            'jd.com': (5, 10),      # 京东5-10秒
            'taobao.com': (8, 15),   # 淘宝8-15秒
            'yangkeduo.com': (6, 12), # 拼多多6-12秒
        }

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
            limit=20,              # 减少并发连接数
            limit_per_host=5,       # 每个主机最多5个连接
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
            force_close=False,
            ssl=False  # 跳过SSL验证（某些反爬机制依赖此）
        )

        timeout = aiohttp.ClientTimeout(
            total=self.config.timeout,
            connect=10,
            sock_connect=10,
            sock_read=20
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self._get_enhanced_headers(),
            trust_env=True  # 使用环境变量中的代理设置
        )

    async def close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()

    def _get_enhanced_headers(self) -> Dict[str, str]:
        """获取增强的请求头"""
        # 生成更真实的User-Agent
        if self.config.use_real_browser:
            user_agent = self._generate_real_browser_ua()
        else:
            user_agent = self.config.user_agent or self.ua.random

        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive',
        }

        # 添加随机的一些额外头信息
        if random.random() > 0.5:
            headers['DNT'] = '1'
            headers['Save-Data'] = 'on'

        return headers

    def _generate_real_browser_ua(self) -> str:
        """生成更真实的浏览器UA"""
        browsers = [
            # Chrome
            lambda: f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(91, 120)}.0.{random.randint(0, 9)}.{random.randint(0, 999)} Safari/537.36",
            # Firefox
            lambda: f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{random.randint(91, 120)}.0) Gecko/20100101 Firefox/{random.randint(91, 120)}.0",
            # Edge
            lambda: f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(91, 120)}.0.{random.randint(0, 9)}.{random.randint(0, 999)} Safari/537.36 Edg/{random.randint(91, 120)}.0.{random.randint(0, 9)}.{random.randint(0, 999)}",
            # Safari
            lambda: f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(15, 17)}_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{random.randint(14, 17)}.{random.randint(0, 6)} Safari/605.1.15",
        ]

        return random.choice(browsers)()

    def add_proxy(self, proxy: ProxyConfig):
        """添加代理"""
        self.proxy_list.append(proxy)

    def add_proxies_from_list(self, proxy_configs: List[Dict]):
        """从列表批量添加代理"""
        for config in proxy_configs:
            proxy = ProxyConfig(
                host=config.get('host'),
                port=config.get('port'),
                username=config.get('username'),
                password=config.get('password'),
                protocol=config.get('protocol', 'http'),
                weight=config.get('weight', 1)
            )
            self.add_proxy(proxy)

    def get_next_proxy(self) -> Optional[ProxyConfig]:
        """获取下一个代理（加权随机选择）"""
        if not self.proxy_list:
            return None

        # 加权随机选择
        total_weight = sum(p.weight for p in self.proxy_list)
        if total_weight == 0:
            return None

        r = random.randint(1, total_weight)
        current_weight = 0
        for proxy in self.proxy_list:
            current_weight += proxy.weight
            if r <= current_weight:
                return proxy

        return self.proxy_list[0]

    def get_proxy_url(self, proxy: ProxyConfig) -> str:
        """获取代理URL"""
        if proxy.username and proxy.password:
            return f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
        return f"{proxy.protocol}://{proxy.host}:{proxy.port}"

    async def smart_delay(self, url: str):
        """智能延迟控制"""
        domain = urlparse(url).netloc

        # 获取该域名的延迟配置
        if domain in self.domain_delays:
            delay_min, delay_max = self.domain_delays[domain]
        else:
            delay_min, delay_max = self.config.delay_range

        # 检查最近的请求时间
        last_request_time = self.request_timestamps.get(domain, 0)
        current_time = time.time()

        # 如果距离上次请求时间太短，增加额外延迟
        if current_time - last_request_time < delay_min:
            extra_delay = delay_min - (current_time - last_request_time) + random.uniform(1, 3)
            logger.info(f"Domain {domain} rate limiting, adding extra delay: {extra_delay:.2f}s")
            await asyncio.sleep(extra_delay)

        # 基础随机延迟
        delay = random.uniform(delay_min, delay_max)
        logger.info(f"Smart delay for {domain}: {delay:.2f}s")
        await asyncio.sleep(delay)

        # 记录请求时间
        self.request_timestamps[domain] = time.time()

    async def fetch_page(self, url: str, **kwargs) -> Optional[str]:
        """获取页面内容"""
        # 先进行智能延迟
        await self.smart_delay(url)

        proxy = self.get_next_proxy() if self.config.use_proxy else None
        proxy_url = self.get_proxy_url(proxy) if proxy else None

        headers = self._get_enhanced_headers()
        headers.update(kwargs.get('headers', {}))

        # 添加随机Referer（如果有）
        if random.random() > 0.7 and 'Referer' not in headers:
            headers['Referer'] = self._generate_realistic_referer(url)

        # 记录尝试信息
        attempt_info = {
            'url': url,
            'proxy': proxy_url,
            'attempt': 0
        }

        for attempt in range(self.config.retry_count):
            attempt_info['attempt'] = attempt + 1
            try:
                logger.info(f"Attempt {attempt + 1}/{self.config.retry_count}: {url}")
                if proxy_url:
                    logger.info(f"Using proxy: {proxy_url}")

                async with self.session.get(
                    url,
                    headers=headers,
                    proxy=proxy_url,
                    ssl=False,
                    allow_redirects=True,  # 允许重定向
                    max_redirects=5,    # 最多5次重定向
                    timeout=aiohttp.ClientTimeout(total=30),
                    **{k: v for k, v in kwargs.items() if k != 'headers'}
                ) as response:
                    # 检查是否被重定向到验证码页面
                    if response is not None and self._is_anti_bot_page(response):
                        logger.warning(f"Anti-bot page detected: {url}")
                        if attempt < self.config.retry_count - 1:
                            # 遇到反爬，增加延迟重试
                            await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                            # 更换User-Agent和代理
                            headers['User-Agent'] = self._generate_real_browser_ua()
                            if self.config.use_proxy:
                                proxy = self.get_next_proxy()
                                proxy_url = self.get_proxy_url(proxy) if proxy else None
                        continue

                    if response is not None and response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        if 'text/html' in content_type:
                            content = await response.text()
                        elif 'application/json' in content_type:
                            try:
                                json_data = await response.json()
                                if json_data is not None:
                                    content = json.dumps(json_data, ensure_ascii=False)
                                else:
                                    content = await response.text()
                            except Exception as e:
                                logger.warning(f"JSON parsing failed for {url}: {e}")
                                content = await response.text()
                        else:
                            content = await response.text()

                        # 成功获取，记录信息
                        logger.info(f"Successfully fetched: {url} ({len(content)} chars)")
                        return content
                    elif response is not None and response.status == 404:
                        logger.warning(f"Page not found: {url}")
                        return None
                    elif response is not None and response.status >= 500:
                        logger.warning(f"Server error {response.status} for {url}")
                        if attempt < self.config.retry_count - 1:
                            await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                        continue
                    elif response is not None:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.config.retry_count - 1:
                    # 增加延迟时间
                    wait_time = self.config.retry_delay * (attempt + 1) + random.uniform(1, 3)
                    logger.info(f"Waiting {wait_time:.2f}s before retry...")
                    await asyncio.sleep(wait_time)
                    # 可能更换代理
                    if self.config.use_proxy:
                        proxy = self.get_next_proxy()
                        proxy_url = self.get_proxy_url(proxy) if proxy else None
                else:
                    logger.error(f"All attempts failed for {url}: {e}")
                    return None
            except Exception as e:
                import traceback
                logger.error(f"Unexpected error on attempt {attempt + 1} for {url}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(self.config.retry_delay)
                else:
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

    def _is_anti_bot_page(self, response) -> bool:
        """检测是否是反爬虫页面"""
        if response is None:
            return False
        # 检查常见的反爬虫页面特征
        content = getattr(response, 'text', '') or ''
        url = str(response.url)

        # 检查URL是否被重定向到风险检测页面
        anti_bot_patterns = [
            r'privatedomain/risk_handler',
            r'verification',
            r'captcha',
            r'robot',
            r'blocked',
            r'access.denied',
            r'security.check',
            r'anti.spider',
        ]

        for pattern in anti_bot_patterns:
            if re.search(pattern, url, re.IGNORECASE) or re.search(pattern, content, re.IGNORECASE):
                logger.warning(f"Anti-bot pattern detected: {pattern}")
                return True

        return False

    def _generate_realistic_referer(self, url: str) -> str:
        """生成合理的Referer"""
        domain = urlparse(url).netloc
        referer_patterns = [
            f"https://{domain}/",
            f"https://www.{domain}/search",
            f"https://{domain}/category/",
            f"https://www.google.com/search?q=shopping",
        ]
        return random.choice(referer_patterns)

    def parse_price(self, price_str: str) -> Optional[float]:
        """解析价格字符串"""
        if not price_str:
            return None

        # 移除货币符号和空格
        price_str = re.sub(r'[￥¥元,\s]', '', str(price_str))

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
        return re.sub(r'[<>:"/\\|?*]', '_', filename)[:255]

    async def fetch_multiple(self, urls: List[str], **kwargs) -> List[Optional[str]]:
        """并发获取多个页面"""
        semaphore = asyncio.Semaphore(3)  # 严格限制并发数

        async def fetch_one(url):
            async with semaphore:
                return await self.fetch_page(url, **kwargs)

        tasks = [fetch_one(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_platform_cookies(self, platform: str) -> Dict[str, str]:
        """获取特定平台的Cookie设置"""
        # 生成随机的cookie值以模拟真实用户
        import random
        import string
        import time

        def random_string(length=16):
            return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

        def random_timestamp():
            return str(int(time.time() * 1000))

        platform_cookies = {
            'jd': {
                'shshshfpa': random_string(32),  # 京东反爬虫相关
                'shshshfpb': random_string(32),
                'qrreferer': 'https://www.jd.com/',
                '__jda': f'{random.randint(1000000, 9999999)}.{random_timestamp()}.{random_timestamp()}.{random_timestamp()}.{random_timestamp()}',
                '__jdc': random_string(32),
                'thor': random_string(32),
                'shshshfp': random_timestamp(),
                'ipLoc-djd': '1-72-2799-0',  # 模拟地区
            },
            'taobao': {
                '_tb_token_': random_string(16),
                'cookie2': random_string(32),
                't': random_timestamp(),
                'unb': random_string(32),
                '_samesite_flag_': 'true',
                'cna': random_string(32),
                'isg': random_string(18),
                'uc3': f'lg2={random_string(32)}&nk2={random_string(32)}&id2={random_string(32)}',
                'track': random_string(32),
            },
            'pdd': {
                'webp': '1',
                'whtoken': random_string(32),
                'cookie2': random_string(32),
                't': random_timestamp(),
                'ua': random_string(32),
                'pdd_user_id': str(random.randint(100000000, 999999999)),
            }
        }
        return platform_cookies.get(platform.lower(), {})

    async def fetch_with_cookie(self, url: str, cookies: Dict[str, str] = None, **kwargs) -> Optional[str]:
        """使用Cookie获取页面"""
        headers = self._get_enhanced_headers()
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

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'proxy_count': len(self.proxy_list),
            'active_proxies': len([p for p in self.proxy_list if p.weight > 0]),
            'domain_requests': {domain: count for domain, count in self.request_timestamps.items()},
            'config': {
                'timeout': self.config.timeout,
                'retry_count': self.config.retry_count,
                'use_proxy': self.config.use_proxy,
                'delay_range': self.config.delay_range
            }
        }

class SmartRateLimiter:
    """智能速率限制器"""
    def __init__(self, domain_configs: Dict[str, tuple] = None):
        self.domain_configs = domain_configs or {
            'jd.com': (1, 10),      # 1次/10秒
            'taobao.com': (1, 15),   # 1次/15秒
            'yangkeduo.com': (1, 12), # 1次/12秒
            'default': (1, 5),        # 默认1次/5秒
        }
        self.request_history = {}

    async def acquire(self, domain: str):
        """获取请求许可"""
        # 获取该域名的配置
        config = self.domain_configs.get(domain, self.domain_configs['default'])
        max_calls, time_window = config

        current_time = time.time()
        history = self.request_history.get(domain, [])

        # 清理过期的请求记录
        history = [req_time for req_time in history if current_time - req_time < time_window]
        self.request_history[domain] = history

        # 检查是否超过限制
        if len(history) >= max_calls:
            oldest_request = min(history)
            wait_time = time_window - (current_time - oldest_request)
            if wait_time > 0:
                logger.info(f"Rate limiting {domain}, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

        # 记录本次请求
        self.request_history[domain].append(current_time)

# 示例代理配置
EXAMPLE_PROXIES = [
    {
        "host": "proxy1.example.com",
        "port": 8080,
        "username": "user1",
        "password": "pass1",
        "protocol": "http",
        "weight": 2
    },
    {
        "host": "proxy2.example.com",
        "port": 8080,
        "username": "user2",
        "password": "pass2",
        "protocol": "socks5",
        "weight": 1
    }
]

# 使用示例
async def main():
    # 配置爬虫
    config = RequestConfig(
        timeout=30,
        retry_count=5,
        use_proxy=True,
        delay_range=(5, 10)
    )

    async with EnhancedScraper(config) as scraper:
        # 添加代理
        scraper.add_proxies_from_list(EXAMPLE_PROXIES)

        # 获取页面
        content = await scraper.fetch_page("https://search.jd.com/Search?keyword=手机&enc=utf-8&page=1")
        if content:
            print(f"获取到内容，长度: {len(content)}")

if __name__ == "__main__":
    import random
    asyncio.run(main())