"""
代理配置模块
提供代理池管理和负载均衡功能
"""
import random
import json
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProxyConfig:
    """代理配置"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    weight: int = 1  # 权重
    last_used: float = 0  # 最后使用时间
    failure_count: int = 0  # 失败次数
    response_time: float = 0  # 响应时间
    country: Optional[str] = None  # 国家
    city: Optional[str] = None  # 城市
    is_anonymous: bool = False  # 是否匿名

class ProxyManager:
    """代理管理器"""

    def __init__(self, config_file: str = "proxy_config.json"):
        self.config_file = Path(config_file)
        self.proxies: List[ProxyConfig] = []
        self.banned_proxies: set() = set()  # 被封禁的代理
        self.load_config()

    def load_config(self):
        """加载代理配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    proxy_data = json.load(f)
                    self.proxies = [ProxyConfig(**proxy) for proxy in proxy_data]
                    logger.info(f"Loaded {len(self.proxies)} proxies from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load proxy config: {e}")
        else:
            logger.info(f"Proxy config file {self.config_file} not found, using empty proxy list")
            self._create_sample_config()

    def save_config(self):
        """保存代理配置"""
        try:
            proxy_data = [asdict(proxy) for proxy in self.proxies]
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(proxy_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.proxies)} proxies to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save proxy config: {e}")

    def _create_sample_config(self):
        """创建示例配置文件"""
        sample_proxies = [
            {
                "host": "proxy1.example.com",
                "port": 8080,
                "username": "user1",
                "password": "pass1",
                "protocol": "http",
                "weight": 2,
                "country": "US",
                "city": "New York",
                "is_anonymous": True
            },
            {
                "host": "proxy2.example.com",
                "port": 3128,
                "username": "user2",
                "password": "pass2",
                "protocol": "socks5",
                "weight": 1,
                "country": "SG",
                "city": "Singapore",
                "is_anonymous": True
            }
        ]

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(sample_proxies, f, ensure_ascii=False, indent=2)

    def add_proxy(self, proxy: ProxyConfig):
        """添加代理"""
        # 检查是否已存在
        existing = self._find_existing_proxy(proxy)
        if existing:
            logger.info(f"Proxy {proxy.host}:{proxy.port} already exists, updating")
            # 更新现有代理
            existing.weight = proxy.weight
            existing.country = proxy.country
            existing.city = proxy.city
        else:
            self.proxies.append(proxy)
            logger.info(f"Added new proxy: {proxy.host}:{proxy.port}")
            self.save_config()

    def remove_proxy(self, proxy_host: str, proxy_port: int):
        """移除代理"""
        self.proxies = [p for p in self.proxies if not (p.host == proxy_host and p.port == proxy_port)]
        self.banned_proxies.discard(f"{proxy_host}:{proxy_port}")
        self.save_config()

    def _find_existing_proxy(self, proxy: ProxyConfig) -> Optional[ProxyConfig]:
        """查找已存在的代理"""
        for p in self.proxies:
            if p.host == proxy.host and p.port == proxy.port:
                return p
        return None

    def get_proxy(self, domain: str = None) -> Optional[ProxyConfig]:
        """获取一个可用代理"""
        # 过滤被ban的代理
        available_proxies = [
            p for p in self.proxies
            if f"{p.host}:{p.port}" not in self.banned_proxies
        ]

        if not available_proxies:
            logger.warning("No available proxies")
            return None

        # 根据响应时间排序，优先选择响应快的
        sorted_proxies = sorted(
            available_proxies,
            key=lambda p: (p.response_time, p.failure_count)
        )

        # 前一半最好的代理
        best_proxies = sorted_proxies[:max(1, len(sorted_proxies)//2)]

        # 加权随机选择
        total_weight = sum(p.weight for p in best_proxies)
        if total_weight == 0:
            # 如果没有权重，平均选择
            return random.choice(best_proxies)

        r = random.randint(1, total_weight)
        current_weight = 0
        for proxy in best_proxies:
            current_weight += proxy.weight
            if r <= current_weight:
                return proxy

        return best_proxies[0]

    def report_failure(self, proxy: ProxyConfig, error_type: str):
        """报告代理失败"""
        proxy.failure_count += 1
        proxy.last_used = asyncio.get_event_loop().time()
        logger.warning(f"Proxy {proxy.host}:{proxy.port} failed ({error_type}), failure count: {proxy.failure_count}")

        # 如果失败次数过多，临时ban掉
        if proxy.failure_count >= 5:
            ban_key = f"{proxy.host}:{proxy.port}"
            self.banned_proxies.add(ban_key)
            logger.error(f"Proxy {ban_key} temporarily banned due to multiple failures")
            # 30分钟后解除ban
            asyncio.create_task(self._unban_proxy(ban_key))

    def report_success(self, proxy: ProxyConfig, response_time: float):
        """报告代理成功"""
        proxy.failure_count = max(0, proxy.failure_count - 1)  # 减少失败计数
        proxy.response_time = response_time
        proxy.last_used = asyncio.get_event_loop().time()
        logger.debug(f"Proxy {proxy.host}:{proxy.port} succeeded, response time: {response_time:.2f}s")

    async def _unban_proxy(self, ban_key: str, delay_minutes: int = 30):
        """解除代理ban"""
        await asyncio.sleep(delay_minutes * 60)
        self.banned_proxies.discard(ban_key)
        logger.info(f"Proxy {ban_key} unbanned after {delay_minutes} minutes")

    def get_statistics(self) -> Dict:
        """获取代理统计"""
        total_proxies = len(self.proxies)
        banned_count = len(self.banned_proxies)
        available_count = total_proxies - banned_count

        # 计算平均响应时间
        valid_proxies = [p for p in self.proxies if p.response_time > 0]
        avg_response_time = sum(p.response_time for p in valid_proxies) / len(valid_proxies) if valid_proxies else 0

        # 按国家统计
        country_stats = {}
        for proxy in self.proxies:
            country = proxy.country or "Unknown"
            if country not in country_stats:
                country_stats[country] = 0
            country_stats[country] += 1

        return {
            "total_proxies": total_proxies,
            "available_proxies": available_count,
            "banned_proxies": banned_count,
            "average_response_time": avg_response_time,
            "country_distribution": country_stats,
            "failure_rates": {
                f"{proxy.host}:{proxy.port}": proxy.failure_count
                for proxy in sorted(self.proxies, key=lambda p: p.failure_count, reverse=True)[:10]
            }
        }

    def clean_expired_proxies(self, max_age_days: int = 7):
        """清理过期代理"""
        import time
        current_time = time.time()
        cutoff_time = current_time - (max_age_days * 24 * 3600)

        expired_proxies = [
            proxy for proxy in self.proxies
            if proxy.last_used > 0 and proxy.last_used < cutoff_time
        ]

        if expired_proxies:
            self.proxies = [p for p in self.proxies if p not in expired_proxies]
            logger.info(f"Cleaned {len(expired_proxies)} expired proxies")
            self.save_config()

    def test_proxy(self, proxy: ProxyConfig, test_url: str = "http://httpbin.org/ip") -> bool:
        """测试代理是否可用"""
        import aiohttp
        import asyncio

        async def test():
            proxy_url = f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}" if proxy.username and proxy.password else f"{proxy.protocol}://{proxy.host}:{proxy.port}"

            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(test_url, proxy=proxy_url) as response:
                        if response.status == 200:
                            self.report_success(proxy, 0)
                            return True
                        else:
                            self.report_failure(proxy, f"HTTP {response.status}")
                            return False
            except Exception as e:
                self.report_failure(proxy, str(e))
                return False

        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(test())
        except Exception as e:
            logger.error(f"Proxy test failed: {e}")
            return False

# 免费代理源（示例）
FREE_PROXY_SOURCES = [
    # 免费代理网站（需要定期更新）
    "https://free-proxy-list.net/",
    "https://proxylist.geonode.com/",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
]

# 付费代理服务（示例）
PAID_PROXY_SERVICES = [
    {
        "name": "Luminati",
        "api_url": "https://luminati.io/api/",
        "supports_rotating": True,
        "supports_residential": True
    },
    {
        "name": "Smartproxy",
        "api_url": "https://dashboard.smartproxy.com/api/",
        "supports_rotating": True,
        "supports_residential": False
    },
    {
        "name": "Oxylabs",
        "api_url": "https://oxylabs.io/api/",
        "supports_rotating": True,
        "supports_residential": True
    },
]

# 使用示例
def main():
    # 创建代理管理器
    proxy_manager = ProxyManager()

    # 添加一些测试代理
    proxy_manager.add_proxy(ProxyConfig(
        host="1.2.3.4",
        port=8080,
        username="testuser",
        password="testpass",
        protocol="http",
        weight=2
    ))

    # 获取一个代理
    proxy = proxy_manager.get_proxy()
    if proxy:
        print(f"Selected proxy: {proxy.host}:{proxy.port}")
        print(f"Location: {proxy.country} - {proxy.city}")

    # 查看统计
    stats = proxy_manager.get_statistics()
    print(f"Proxy statistics: {stats}")

if __name__ == "__main__":
    main()