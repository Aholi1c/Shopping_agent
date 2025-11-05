# 完整电商助手Agent部署指南

## 📋 所需资源清单

### 🔑 API密钥要求

#### 核心必需 (至少选择一个)
- [x] **智谱AI BigModel** (推荐)
  - `BIGMODEL_API_KEY` - GLM-4.5文本模型
  - `BIGMODEL_VLM_API_KEY` - GLM-4.5V视觉模型
  - 成本：约￥100-500/月

#### 备选方案
- [ ] **OpenAI API**
  - `OPENAI_API_KEY`
  - 成本：约$20-100/月

#### 电商平台API (可选)
- [ ] **京东联盟API**
  - `JD_API_KEY` + `JD_API_SECRET`

- [ ] **淘宝客API**
  - `TAOBAO_API_KEY` + `TAOBAO_API_SECRET`

- [ ] **拼多多联盟API**
  - `PDD_API_KEY` + `PDD_API_SECRET`

### 💾 数据存储要求

#### 必需存储
- [x] **主数据库** (SQLite)
  - 位置：`./llm_agent.db`
  - 大小：1-10GB (初期)

- [x] **向量数据库** (FAISS)
  - 位置：`./vector_store`
  - 大小：100MB-5GB

- [x] **文件存储**
  - 位置：`./uploads`
  - 大小：1-50GB

#### 推荐存储
- [ ] **Redis缓存**
  - 用途：会话管理、缓存、任务队列
  - 大小：100MB-1GB

## 🚀 完整部署步骤

### 步骤1：环境准备
```bash
# 1. 系统要求
- macOS/Linux
- Python 3.9+
- 8GB+ RAM
- 50GB+ 磁盘空间

# 2. 安装依赖
cd /Users/xinyizhu/Downloads/cc-mirror/llm-agent
chmod +x start_agent.sh
./start_agent.sh
```

### 步骤2：API密钥配置
编辑 `backend/.env` 文件：

```bash
# 核心LLM配置 (必需)
BIGMODEL_API_KEY=your_bigmodel_api_key_here
BIGMODEL_VLM_API_KEY=your_bigmodel_vlm_api_key_here

# 备选配置 (可选)
OPENAI_API_KEY=your_openai_api_key_here

# 电商平台API (可选)
JD_API_KEY=your_jd_api_key
JD_API_SECRET=your_jd_api_secret
TAOBAO_API_KEY=your_taobao_api_key
TAOBAO_API_SECRET=your_taobao_api_secret
```

### 步骤3：数据库初始化
```bash
# 激活虚拟环境
cd backend
source ../venv/bin/activate

# 初始化数据库
python -c "
from app.core.database import engine
from app.models.models import Base
from app.models.ecommerce_models import Base as EcommerceBase
Base.metadata.create_all(bind=engine)
EcommerceBase.metadata.create_all(bind=engine)
print('数据库初始化完成')
"
```

### 步骤4：安装完整依赖
```bash
# 安装所有依赖
pip install -r requirements.txt

# 单独安装重要依赖
pip install zhipuai==2.1.5.20250825
pip install faiss-cpu==1.7.4
pip install sentence-transformers==2.2.2
pip install langchain==0.1.0
pip install celery==5.3.4
pip install redis==5.0.1
```

### 步骤5：启动服务
```bash
# 启动完整版服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 或使用后台启动
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &
```

### 步骤6：启动辅助服务 (可选)
```bash
# 启动Redis (如果使用)
redis-server --port 6379

# 启动Celery Worker (用于异步任务)
celery -A app.services.celery_config.celery_app worker --loglevel=info

# 启动Celery Beat (用于定时任务)
celery -A app.services.celery_config.celery_app beat --loglevel=info
```

## 📊 数据来源方案

### 方案1：仅使用LLM (最低成本)
- **优点**：成本低，部署简单
- **缺点**：数据准确性有限
- **适用**：个人使用，测试阶段

### 方案2：LLM + 网络爬虫 (推荐)
- **优点**：数据较准确，成本适中
- **缺点**：可能违反网站政策
- **适用**：小型商业使用

### 方案3：LLM + 官方API (最佳)
- **优点**：数据准确，合法合规
- **缺点**：成本较高
- **适用**：商业部署

## 🔧 功能模块启用状态

### ✅ 基础功能 (立即可用)
- [x] 基础聊天对话
- [x] 用户管理
- [x] 会话记忆
- [x] 健康检查

### ✅ 增强功能 (需要完整依赖)
- [x] 实时价格跟踪
- [x] 产品比较分析
- [x] 智能优惠券系统
- [x] 增强RAG搜索
- [x] 购物行为分析
- [x] 视觉搜索识别
- [x] 社交商务集成

### 🚀 高级功能 (需要额外配置)
- [ ] 实时数据同步
- [ ] 多语言支持
- [ ] 移动端适配
- [ ] 微信小程序
- [ ] 数据分析面板

## 📈 成本估算

### 开发阶段
- API成本：￥0-100/月
- 服务器成本：￥0/月 (本地部署)
- 总成本：￥0-100/月

### 生产阶段
- API成本：￥200-1000/月
- 服务器成本：￥100-500/月
- 电商平台API：￥0-500/月
- 总成本：￥300-2000/月

## 🎯 部署建议

### 个人开发者
1. 使用BigModel API
2. 本地SQLite数据库
3. 网络爬虫获取数据
4. 估计成本：￥100-300/月

### 小型企业
1. BigModel + OpenAI备用
2. PostgreSQL数据库
3. Redis缓存
4. 官方电商平台API
5. 估计成本：￥500-1500/月

### 中大型企业
1. 多LLM提供商
2. 云数据库集群
3. 完整API集成
4. 专业运维团队
5. 估计成本：￥2000-10000/月

## 🔍 监控和维护

### 性能监控
- API调用次数和成本
- 数据库查询性能
- 内存使用情况
- 响应时间统计

### 数据维护
- 定期清理过期数据
- 数据备份和恢复
- 索引优化
- 日志轮转

### 安全维护
- API密钥轮换
- 数据加密
- 访问控制
- 漏洞修复

---

## 📞 技术支持

如果在部署过程中遇到问题：
1. 检查日志文件：`server.log`
2. 验证API密钥配置
3. 确认网络连接
4. 查看错误信息和解决方案

**祝您的电商助手Agent部署成功！** 🎉