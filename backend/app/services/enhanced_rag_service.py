"""
增强RAG服务 - 多源数据集成
支持多种数据源的智能检索和增强生成
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple, Union
import os
import json
import asyncio
import aiohttp
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False
    feedparser = None
    print("⚠️  feedparser未安装，RSS功能将不可用。请运行: pip install feedparser")
from datetime import datetime, timedelta
import logging
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    BeautifulSoup = None
    print("⚠️  beautifulsoup4未安装，HTML解析功能将不可用。请运行: pip install beautifulsoup4")
import re
from .rag_service import RAGService, DocumentProcessor
from ..models.models import KnowledgeBase, Document, DocumentChunk
from ..models.ecommerce_models import Product, ProductReview, PriceHistory
from ..core.config import settings
from ..services.llm_service import LLMService
from ..services.vector_service import vector_service
import pandas as pd
import requests
from urllib.parse import urljoin, urlparse
import hashlib

logger = logging.getLogger(__name__)

class DataSource:
    """数据源基类"""
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_active = config.get("is_active", True)
        self.update_frequency = config.get("update_frequency", "daily")
        self.last_updated = config.get("last_updated")

    async def fetch_data(self) -> List[Dict[str, Any]]:
        """获取数据 - 子类需要实现"""
        raise NotImplementedError

    def process_data(self, raw_data: Any) -> List[Dict[str, Any]]:
        """处理原始数据 - 子类需要实现"""
        raise NotImplementedError

    async def update_data(self) -> List[Dict[str, Any]]:
        """更新数据"""
        if not self.is_active:
            return []

        # 检查是否需要更新
        if self._should_update():
            raw_data = await self.fetch_data()
            processed_data = self.process_data(raw_data)
            self.last_updated = datetime.utcnow()
            return processed_data
        return []

    def _should_update(self) -> bool:
        """检查是否需要更新"""
        if not self.last_updated:
            return True

        now = datetime.utcnow()
        if self.update_frequency == "hourly":
            return (now - self.last_updated) >= timedelta(hours=1)
        elif self.update_frequency == "daily":
            return (now - self.last_updated) >= timedelta(days=1)
        elif self.update_frequency == "weekly":
            return (now - self.last_updated) >= timedelta(weeks=1)
        elif self.update_frequency == "monthly":
            return (now - self.last_updated) >= timedelta(days=30)

        return False

class RSSDataSource(DataSource):
    """RSS数据源"""
    def __init__(self, config: Dict[str, Any]):
        super().__init__("rss", config)
        self.feed_urls = config.get("feed_urls", [])
        self.max_articles = config.get("max_articles", 50)

    async def fetch_data(self) -> List[Dict[str, Any]]:
        """获取RSS数据"""
        articles = []

        for feed_url in self.feed_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(feed_url, timeout=30) as response:
                        if response.status == 200:
                            content = await response.text()
                            if not FEEDPARSER_AVAILABLE or not feedparser:
                                logger.warning(f"feedparser未安装，无法解析RSS源: {feed_url}")
                                continue
                            feed = feedparser.parse(content)

                            for entry in feed.entries[:self.max_articles]:
                                articles.append({
                                    "title": entry.get("title", ""),
                                    "link": entry.get("link", ""),
                                    "summary": entry.get("summary", ""),
                                    "published": entry.get("published", ""),
                                    "content": self._extract_content(entry),
                                    "source": feed_url,
                                    "source_type": "rss"
                                })
            except Exception as e:
                logger.error(f"Error fetching RSS from {feed_url}: {e}")

        return articles

    def process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理RSS数据"""
        processed_data = []

        for article in raw_data:
            # 清理和标准化数据
            processed_article = {
                "title": self._clean_text(article["title"]),
                "content": self._clean_text(article["content"]),
                "url": article["link"],
                "publish_date": self._parse_date(article["published"]),
                "source": article["source"],
                "source_type": "rss",
                "hash": self._generate_hash(article["link"]),
                "metadata": {
                    "summary": self._clean_text(article["summary"]),
                    "extracted_at": datetime.utcnow().isoformat()
                }
            }
            processed_data.append(processed_article)

        return processed_data

    def _extract_content(self, entry) -> str:
        """提取文章内容"""
        content = ""
        if hasattr(entry, 'content'):
            content = entry.content[0].value if entry.content else ""
        elif hasattr(entry, 'summary'):
            content = entry.summary

        # 移除HTML标签
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            content = soup.get_text()

        return content

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""

        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def _parse_date(self, date_str: str) -> Optional[str]:
        """解析日期"""
        if not date_str:
            return None

        try:
            # 简单的日期解析
            if not FEEDPARSER_AVAILABLE or not feedparser:
                return None
            parsed = feedparser._parse_date(date_str)
            if parsed:
                return datetime(*parsed[:6]).isoformat()
        except:
            pass

        return None

    def _generate_hash(self, url: str) -> str:
        """生成URL哈希"""
        return hashlib.md5(url.encode()).hexdigest()

class WebCrawlerDataSource(DataSource):
    """网页爬虫数据源"""
    def __init__(self, config: Dict[str, Any]):
        super().__init__("web_crawler", config)
        self.base_urls = config.get("base_urls", [])
        self.max_pages = config.get("max_pages", 100)
        self.max_depth = config.get("max_depth", 2)
        self.include_patterns = config.get("include_patterns", [])
        self.exclude_patterns = config.get("exclude_patterns", [])

    async def fetch_data(self) -> List[Dict[str, Any]]:
        """爬取网页数据"""
        pages = []
        visited_urls = set()

        for base_url in self.base_urls:
            pages.extend(await self._crawl_url(base_url, visited_urls, depth=0))

        return pages

    async def _crawl_url(self, url: str, visited_urls: set, depth: int) -> List[Dict[str, Any]]:
        """递归爬取URL"""
        if depth > self.max_depth or url in visited_urls or len(visited_urls) >= self.max_pages:
            return []

        visited_urls.add(url)

        # 检查URL模式
        if not self._should_crawl_url(url):
            return []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()

                        page_data = {
                            "url": url,
                            "title": self._extract_title(content),
                            "content": self._extract_content(content),
                            "links": self._extract_links(content, url),
                            "depth": depth,
                            "source_type": "web_crawler",
                            "crawled_at": datetime.utcnow().isoformat()
                        }

                        result = [page_data]

                        # 递归爬取链接
                        if depth < self.max_depth:
                            for link in page_data["links"][:5]:  # 限制每个页面的链接数
                                result.extend(await self._crawl_url(link, visited_urls, depth + 1))

                        return result
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")

        return []

    def process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理爬取数据"""
        processed_data = []

        for page in raw_data:
            processed_page = {
                "title": self._clean_text(page["title"]),
                "content": self._clean_text(page["content"]),
                "url": page["url"],
                "source_type": "web_crawler",
                "hash": self._generate_hash(page["url"]),
                "metadata": {
                    "depth": page["depth"],
                    "crawled_at": page["crawled_at"],
                    "links_count": len(page["links"])
                }
            }
            processed_data.append(processed_page)

        return processed_data

    def _should_crawl_url(self, url: str) -> bool:
        """检查是否应该爬取该URL"""
        # 检查包含模式
        if self.include_patterns:
            if not any(re.search(pattern, url) for pattern in self.include_patterns):
                return False

        # 检查排除模式
        if self.exclude_patterns:
            if any(re.search(pattern, url) for pattern in self.exclude_patterns):
                return False

        return True

    def _extract_title(self, html: str) -> str:
        """提取页面标题"""
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('title')
        return title.get_text() if title else ""

    def _extract_content(self, html: str) -> str:
        """提取页面内容"""
        soup = BeautifulSoup(html, 'html.parser')

        # 移除不需要的元素
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()

        # 提取主要内容
        content = soup.get_text()
        return content

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """提取链接"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)

            # 只处理同一域名的链接
            if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                links.append(absolute_url)

        return links

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()

    def _generate_hash(self, url: str) -> str:
        """生成URL哈希"""
        return hashlib.md5(url.encode()).hexdigest()

class APIDataSource(DataSource):
    """API数据源"""
    def __init__(self, config: Dict[str, Any]):
        super().__init__("api", config)
        self.api_url = config.get("api_url")
        self.api_key = config.get("api_key")
        self.headers = config.get("headers", {})
        self.params = config.get("params", {})
        self.data_path = config.get("data_path", "")  # JSON数据路径

    async def fetch_data(self) -> List[Dict[str, Any]]:
        """获取API数据"""
        try:
            headers = self.headers.copy()
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_url,
                    headers=headers,
                    params=self.params,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # 提取指定路径的数据
                        if self.data_path:
                            for key in self.data_path.split('.'):
                                data = data.get(key, [])

                        return data if isinstance(data, list) else [data]
        except Exception as e:
            logger.error(f"Error fetching API data from {self.api_url}: {e}")

        return []

    def process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理API数据"""
        processed_data = []

        for item in raw_data:
            processed_item = {
                "content": json.dumps(item, ensure_ascii=False),
                "source_type": "api",
                "source_url": self.api_url,
                "hash": self._generate_hash(json.dumps(item, sort_keys=True)),
                "metadata": {
                    "extracted_at": datetime.utcnow().isoformat(),
                    "data_path": self.data_path
                }
            }
            processed_data.append(processed_item)

        return processed_data

    def _generate_hash(self, data: str) -> str:
        """生成数据哈希"""
        return hashlib.md5(data.encode()).hexdigest()

class DatabaseDataSource(DataSource):
    """数据库数据源"""
    def __init__(self, config: Dict[str, Any]):
        super().__init__("database", config)
        self.query = config.get("query", "")
        self.table_name = config.get("table_name", "")
        self.db = None

    async def fetch_data(self, db: Session) -> List[Dict[str, Any]]:
        """从数据库获取数据"""
        try:
            if self.query:
                result = db.execute(self.query).fetchall()
            elif self.table_name:
                result = db.execute(f"SELECT * FROM {self.table_name}").fetchall()
            else:
                return []

            # 转换为字典列表
            columns = result[0].keys() if result else []
            data = [dict(zip(columns, row)) for row in result]

            return data
        except Exception as e:
            logger.error(f"Error fetching database data: {e}")
            return []

    def process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理数据库数据"""
        processed_data = []

        for item in raw_data:
            processed_item = {
                "content": json.dumps(item, ensure_ascii=False),
                "source_type": "database",
                "table_name": self.table_name,
                "hash": self._generate_hash(json.dumps(item, sort_keys=True)),
                "metadata": {
                    "extracted_at": datetime.utcnow().isoformat(),
                    "query": self.query
                }
            }
            processed_data.append(processed_item)

        return processed_data

    def _generate_hash(self, data: str) -> str:
        """生成数据哈希"""
        return hashlib.md5(data.encode()).hexdigest()

class EnhancedRAGService(RAGService):
    """增强RAG服务 - 多源数据集成"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.data_sources = {}
        self.llm_service = LLMService()
        self._initialize_data_sources()

    def _initialize_data_sources(self):
        """初始化数据源"""
        from ..core.config import settings
        import json
        
        # 这里可以从配置文件或数据库加载配置
        config = {
            "rss": {
                "is_active": False,  # 默认关闭，优先使用MCP
                "update_frequency": "daily",
                "feed_urls": [
                    "https://example.com/feed1.rss",
                    "https://example.com/feed2.rss"
                ],
                "max_articles": 50
            },
            "web_crawler": {
                "is_active": False,  # 默认关闭，避免过度爬取
                "update_frequency": "weekly",
                "base_urls": ["https://example.com"],
                "max_pages": 100,
                "max_depth": 2
            },
            "api": {
                "is_active": False,  # 默认关闭，优先使用MCP
                "update_frequency": "hourly",
                "api_url": "https://api.example.com/data",
                "api_key": "your_api_key",
                "data_path": "results.items"
            }
        }

        # 初始化MCP数据源（如果启用）
        if settings.mcp_enabled and settings.mcp_base_url:
            try:
                from .mcp_service import MCPService, MCPDataSource
                
                mcp_service = MCPService(
                    base_url=settings.mcp_base_url,
                    api_key=settings.mcp_api_key,
                    timeout=settings.mcp_timeout
                )
                
                resource_filters = {}
                if settings.mcp_resource_filters:
                    try:
                        resource_filters = json.loads(settings.mcp_resource_filters)
                    except:
                        pass
                
                mcp_config = {
                    "name": "mcp",
                    "resource_filters": resource_filters,
                    "content_format": settings.mcp_content_format,
                    "max_items": settings.mcp_max_items,
                    "update_frequency": "hourly"
                }
                
                self.data_sources["mcp"] = MCPDataSource(mcp_service, mcp_config)
                logger.info("MCP数据源已初始化")
            except Exception as e:
                logger.error(f"初始化MCP数据源失败: {e}")

        # 初始化其他数据源（仅在MCP未启用时使用）
        if not settings.mcp_enabled:
            if config["rss"]["is_active"]:
                self.data_sources["rss"] = RSSDataSource(config["rss"])

            if config["web_crawler"]["is_active"]:
                self.data_sources["web_crawler"] = WebCrawlerDataSource(config["web_crawler"])

            if config["api"]["is_active"]:
                self.data_sources["api"] = APIDataSource(config["api"])

    async def update_all_sources(self) -> Dict[str, Any]:
        """更新所有数据源"""
        update_results = {}

        for source_name, source in self.data_sources.items():
            try:
                data = await source.update_data()

                # 将数据存储到知识库
                if data:
                    await self._store_source_data(source_name, data)

                update_results[source_name] = {
                    "success": True,
                    "items_processed": len(data),
                    "last_updated": source.last_updated.isoformat() if source.last_updated else None
                }

            except Exception as e:
                logger.error(f"Error updating source {source_name}: {e}")
                update_results[source_name] = {
                    "success": False,
                    "error": str(e)
                }

        return update_results

    async def _store_source_data(self, source_name: str, data: List[Dict[str, Any]]):
        """存储数据源数据到知识库"""
        # 创建或获取专用知识库
        kb_name = f"auto_{source_name}_kb"
        knowledge_base = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.name == kb_name
        ).first()

        if not knowledge_base:
            knowledge_base = KnowledgeBase(
                name=kb_name,
                description=f"自动生成的{source_name}数据源知识库",
                user_id=0  # 系统用户
            )
            self.db.add(knowledge_base)
            self.db.commit()
            self.db.refresh(knowledge_base)

        # 为每个数据项创建文档
        for item in data:
            # 检查是否已存在（通过哈希）
            existing_doc = self.db.query(Document).filter(
                Document.metadata.contains({"hash": item["hash"]})
            ).first()

            if existing_doc:
                continue

            # 创建文档
            document = Document(
                knowledge_base_id=knowledge_base.id,
                filename=f"{source_name}_{item['hash']}.txt",
                original_name=item.get("title", f"{source_name}_data"),
                file_path="",
                file_type="txt",
                content=item["content"],
                chunk_count=0,
                metadata={
                    "source": source_name,
                    "hash": item["hash"],
                    **item.get("metadata", {})
                }
            )

            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            # 分块和索引
            chunks = self.document_processor.split_text_into_chunks(item["content"])

            for i, chunk_content in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document.id,
                    content=chunk_content,
                    chunk_index=i,
                    metadata={
                        "source": source_name,
                        "hash": item["hash"],
                        "document_name": item.get("title", ""),
                        **item.get("metadata", {})
                    }
                )

                self.db.add(chunk)
                self.db.commit()
                self.db.refresh(chunk)

                # 添加到向量索引
                await asyncio.to_thread(
                    vector_service.add_document_chunk_embedding,
                    chunk.id, chunk_content, self.db
                )

            # 更新文档块计数
            document.chunk_count = len(chunks)
            self.db.commit()

    async def search_all_sources(self, query: str, limit: int = 10,
                               source_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """搜索所有数据源"""
        all_results = []

        # 获取要搜索的知识库ID
        kb_ids = []
        for source_name in self.data_sources.keys():
            if source_filter and source_name not in source_filter:
                continue

            kb_name = f"auto_{source_name}_kb"
            kb = self.db.query(KnowledgeBase).filter(
                KnowledgeBase.name == kb_name
            ).first()

            if kb:
                kb_ids.append(kb.id)

        # 使用向量搜索
        if kb_ids:
            search_results = vector_service.search_similar_documents(
                query=query,
                limit=limit,
                threshold=0.5,
                knowledge_base_ids=kb_ids,
                db=self.db
            )

            all_results.extend(search_results)

        # 按分数排序
        all_results.sort(key=lambda x: x["score"], reverse=True)

        return all_results[:limit]

    async def generate_cross_source_response(self, query: str,
                                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成跨数据源的增强响应"""
        # 搜索所有数据源
        search_results = await self.search_all_sources(query, limit=15)

        # 按数据源分组结果
        source_results = {}
        for result in search_results:
            source = result.get("metadata", {}).get("source", "unknown")
            if source not in source_results:
                source_results[source] = []
            source_results[source].append(result)

        # 生成跨数据源分析
        cross_source_analysis = await self._analyze_cross_source_results(query, source_results)

        # 构建增强的RAG提示
        context_text = ""
        for source, results in source_results.items():
            context_text += f"\n=== {source.upper()} 数据源 ===\n"
            for i, result in enumerate(results[:3], 1):  # 每个源限制前3个结果
                context_text += f"[{source}-{i}] {result['content']}\n\n"

        rag_prompt = f"""
        你是一个具备多源数据分析能力的智能助手。基于以下来自不同数据源的信息，请对用户问题进行全面分析。

        用户问题: {query}

        来自多个数据源的信息:
        {context_text}

        跨数据源分析:
        {cross_source_analysis}

        请提供:
        1. 综合分析结果
        2. 各数据源的信息价值评估
        3. 信息的一致性和差异分析
        4. 最终的建议或答案

        请引用具体的数据源，格式为 [数据源-编号]。
        """

        # 生成响应
        response = await self.llm_service.generate_response(rag_prompt)

        return {
            "response": response,
            "cross_source_analysis": cross_source_analysis,
            "sources_used": len(source_results),
            "source_breakdown": {source: len(results) for source, results in source_results.items()},
            "total_results": len(search_results),
            "context_used": context_text
        }

    async def _analyze_cross_source_results(self, query: str,
                                          source_results: Dict[str, List[Dict]]) -> str:
        """分析跨数据源结果"""
        analysis_prompt = f"""
        分析来自多个数据源的搜索结果，提供跨源洞察：

        查询: {query}

        各数据源结果数量: {json.dumps({k: len(v) for k, v in source_results.items()}, ensure_ascii=False)}

        请分析：
        1. 哪些数据源提供了最相关的信息？
        2. 不同数据源之间是否存在信息互补？
        3. 是否发现信息冲突或差异？
        4. 建议如何综合这些信息？

        返回简洁的分析报告。
        """

        try:
            analysis = await self.llm_service.generate_response(analysis_prompt)
            return analysis
        except Exception as e:
            logger.error(f"Error in cross-source analysis: {e}")
            return "跨数据源分析暂时不可用。"

    async def get_source_statistics(self) -> Dict[str, Any]:
        """获取数据源统计信息"""
        stats = {
            "data_sources": {},
            "total_documents": 0,
            "total_chunks": 0,
            "last_updates": {}
        }

        for source_name, source in self.data_sources.items():
            # 获取对应知识库的统计
            kb_name = f"auto_{source_name}_kb"
            kb = self.db.query(KnowledgeBase).filter(
                KnowledgeBase.name == kb_name
            ).first()

            if kb:
                kb_stats = await self.get_knowledge_base_stats(kb.id)
                source_stats = {
                    "is_active": source.is_active,
                    "update_frequency": source.update_frequency,
                    "last_updated": source.last_updated.isoformat() if source.last_updated else None,
                    "documents": kb_stats.get("document_count", 0),
                    "chunks": kb_stats.get("chunk_count", 0),
                    "document_types": kb_stats.get("document_types", {})
                }

                stats["data_sources"][source_name] = source_stats
                stats["total_documents"] += source_stats["documents"]
                stats["total_chunks"] += source_stats["chunks"]

            stats["last_updates"][source_name] = source.last_updated.isoformat() if source.last_updated else None

        return stats

    async def cleanup_old_source_data(self, days_threshold: int = 30):
        """清理旧的源数据"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        for source_name in self.data_sources.keys():
            kb_name = f"auto_{source_name}_kb"
            kb = self.db.query(KnowledgeBase).filter(
                KnowledgeBase.name == kb_name
            ).first()

            if kb:
                # 删除过期的文档
                old_documents = self.db.query(Document).filter(
                    Document.knowledge_base_id == kb.id,
                    Document.created_at < cutoff_date
                ).all()

                for doc in old_documents:
                    await self.delete_document(doc.id)

                logger.info(f"Cleaned up {len(old_documents)} old documents from {source_name}")

# 创建增强RAG服务实例
def get_enhanced_rag_service(db: Session) -> EnhancedRAGService:
    return EnhancedRAGService(db)