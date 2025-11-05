# LLM Agent 智能购物助手前端

基于React + TypeScript构建的现代化前端应用，为增强多模态LLM Agent提供直观的用户界面，特别集成了智能购物助手功能。

## ✨ 功能特性

### 🎯 核心功能
- 💬 **智能对话**: 实时WebSocket连接，支持多轮对话
- 🖼️ **多模态交互**: 图像上传、语音输入、多格式输出
- 🎤 **语音交互**: 语音识别和语音合成支持
- 📱 **响应式设计**: 适配桌面、平板、手机等多种设备

### 🛒 智能购物助手 (v2.1.0)
- 📈 **价格预测**: 可视化价格趋势图表和购买建议
- 🛡️ **风险分析**: 多维度风险评分和详细报告
- 🎯 **决策工具**: 交互式权重调整和实时推荐
- 🔍 **商品搜索**: 多平台商品搜索和比价
- 📊 **数据可视化**: Chart.js驱动的动态图表

### 🧠 增强功能
- 🧠 **记忆管理**: 可视化记忆系统界面
- 📚 **知识库**: 文档上传和管理界面
- 🤖 **多Agent协作**: Agent协作状态监控
- 🌐 **多语言**: 中英文界面切换

## 🛠️ 技术栈

### 核心框架
- **React 19.1.1** - 现代化UI框架
- **TypeScript 4.9.5** - 类型安全的JavaScript
- **Tailwind CSS 4.1.13** - 实用优先的CSS框架

### 状态管理与数据
- **React Hooks** - 内置状态管理
- **Axios 1.12.2** - HTTP客户端
- **WebSocket API** - 实时通信
- **Chart.js** - 数据可视化

### 开发工具
- **React Scripts 5.0.1** - 构建工具链
- **ESLint** - 代码质量检查
- **Prettier** - 代码格式化
- **Jest & Testing Library** - 单元测试

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/           # React组件
│   │   ├── ChatInterface.tsx        # 聊天界面
│   │   ├── FeaturePanel.tsx          # 功能面板
│   │   ├── ConversationList.tsx     # 对话列表
│   │   ├── MemoryPanel.tsx          # 记忆管理
│   │   ├── RAGPanel.tsx             # RAG知识库
│   │   ├── AgentPanel.tsx           # Agent协作
│   │   ├── PricePrediction.tsx      # 价格预测组件
│   │   ├── RiskAnalysis.tsx         # 风险分析组件
│   │   ├── DecisionTool.tsx         # 决策工具组件
│   │   └── ShoppingAssistant.tsx    # 购物助手主界面
│   ├── services/            # 服务层
│   │   ├── api.ts                  # API服务
│   │   ├── websocket.ts            # WebSocket服务
│   │   ├── llmService.ts            # LLM服务
│   │   └── shoppingService.ts       # 购物助手服务
│   ├── types/               # TypeScript类型定义
│   │   ├── api.ts                  # API相关类型
│   │   ├── chat.ts                 # 聊天相关类型
│   │   ├── shopping.ts             # 购物助手类型
│   │   └── common.ts               # 通用类型
│   ├── hooks/               # 自定义Hooks
│   │   ├── useWebSocket.ts          # WebSocket Hook
│   │   ├── useChat.ts               # 聊天Hook
│   │   ├── useMemory.ts            # 记忆Hook
│   │   └── useShopping.ts          # 购物助手Hook
│   ├── utils/               # 工具函数
│   │   ├── helpers.ts              # 辅助函数
│   │   ├── constants.ts            # 常量定义
│   │   └── formatters.ts           # 格式化函数
│   ├── styles/              # 样式文件
│   │   ├── global.css              # 全局样式
│   │   └── components/             # 组件样式
│   ├── App.tsx              # 主应用组件
│   ├── index.tsx            # 应用入口
│   └── react-app-env.d.ts    # React环境类型
├── public/                   # 静态资源
│   ├── index.html           # HTML模板
│   ├── favicon.ico          # 网站图标
│   └── manifest.json        # PWA配置
├── package.json             # 依赖配置
├── tsconfig.json           # TypeScript配置
├── tailwind.config.js      # Tailwind配置
└── .env.local             # 环境变量
```

## 🚀 快速开始

### 环境要求
- Node.js 16+
- npm 或 yarn

### 安装步骤

1. **安装依赖**
```bash
cd frontend
npm install
```

2. **环境配置**
```bash
# 复制环境变量模板
cp .env.example .env.local

# 编辑环境变量
vim .env.local
```

3. **启动开发服务器**
```bash
npm start
```

4. **访问应用**
打开浏览器访问: http://localhost:3000

### 环境变量配置

创建 `.env.local` 文件：

```env
# API配置
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

# 应用配置
REACT_APP_ENVIRONMENT=development
REACT_APP_VERSION=2.1.0

# 可选配置
REACT_APP_ENABLE_ANALYTICS=false
REACT_APP_DEBUG_MODE=true
```

## 🎨 组件使用指南

### 聊天界面组件
```tsx
import ChatInterface from './components/ChatInterface';

function App() {
  return (
    <ChatInterface
      onSendMessage={handleSendMessage}
      onFileUpload={handleFileUpload}
      onVoiceInput={handleVoiceInput}
    />
  );
}
```

### 购物助手组件
```tsx
import ShoppingAssistant from './components/ShoppingAssistant';

function App() {
  return (
    <ShoppingAssistant
      onProductSearch={handleSearch}
      onPriceAnalysis={handleAnalysis}
      onRiskAssessment={handleRisk}
    />
  );
}
```

### 价格预测组件
```tsx
import PricePrediction from './components/PricePrediction';

function App() {
  return (
    <PricePrediction
      productId="123"
      predictionDays={30}
      onPredictionUpdate={handleUpdate}
    />
  );
}
```

## 🔧 开发指南

### 添加新组件

1. **创建组件文件**
```tsx
// src/components/NewComponent.tsx
import React from 'react';

interface NewComponentProps {
  title: string;
  onAction?: () => void;
}

const NewComponent: React.FC<NewComponentProps> = ({ title, onAction }) => {
  return (
    <div className="new-component">
      <h2>{title}</h2>
      <button onClick={onAction}>Action</button>
    </div>
  );
};

export default NewComponent;
```

2. **添加类型定义**
```ts
// src/types/components.ts
export interface NewComponentProps {
  title: string;
  onAction?: () => void;
}
```

3. **使用组件**
```tsx
import NewComponent from './components/NewComponent';

<NewComponent
  title="Hello World"
  onAction={() => console.log('Action clicked')}
/>
```

### 样式开发

使用Tailwind CSS进行样式开发：

```tsx
// 响应式设计
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {/* 内容 */}
  </div>
</div>

// 主题色彩
<div className="bg-primary-500 text-white hover:bg-primary-600 transition-colors">
  {/* 按钮样式 */}
</div>
```

### API集成

使用Axios进行API调用：

```ts
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  timeout: 10000,
});

export const chatAPI = {
  sendMessage: async (message: string) => {
    const response = await api.post('/api/chat/send', { message });
    return response.data;
  },

  getHistory: async () => {
    const response = await api.get('/api/chat/history');
    return response.data;
  },
};
```

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
npm test

# 监听模式运行测试
npm test -- --watch

# 生成测试覆盖率报告
npm test -- --coverage
```

### 编写测试用例
```tsx
// src/components/__tests__/ChatInterface.test.tsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ChatInterface from '../ChatInterface';

test('renders chat interface correctly', () => {
  render(<ChatInterface />);

  expect(screen.getByPlaceholderText('输入消息...')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '发送' })).toBeInTheDocument();
});

test('sends message when send button is clicked', () => {
  const mockOnSend = jest.fn();
  render(<ChatInterface onSendMessage={mockOnSend} />);

  fireEvent.change(screen.getByPlaceholderText('输入消息...'), {
    target: { value: 'Hello' }
  });
  fireEvent.click(screen.getByRole('button', { name: '发送' }));

  expect(mockOnSend).toHaveBeenCalledWith('Hello');
});
```

## 📦 构建与部署

### 生产构建
```bash
# 构建生产版本
npm run build

# 预览构建结果
npm run build && serve -s build
```

### 环境配置

**生产环境 (.env.production):**
```env
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_WS_URL=wss://api.yourdomain.com
REACT_APP_ENVIRONMENT=production
REACT_APP_ENABLE_ANALYTICS=true
```

### Docker部署
```dockerfile
# Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🔍 调试与优化

### 开发调试
```bash
# 启动调试模式
npm start

# 使用React Developer Tools
# 在浏览器中安装React DevTools扩展
```

### 性能优化
```tsx
// 使用React.memo优化组件渲染
const OptimizedComponent = React.memo(({ data }) => {
  return <div>{data.map(item => <Item key={item.id} item={item} />)}</div>;
});

// 使用useMemo和useCallback优化
const ExpensiveComponent = ({ items, onItemSelect }) => {
  const processedItems = useMemo(() => {
    return items.map(processItem);
  }, [items]);

  const handleSelect = useCallback((item) => {
    onItemSelect(item);
  }, [onItemSelect]);

  return (
    <div>
      {processedItems.map(item => (
        <Item key={item.id} item={item} onSelect={handleSelect} />
      ))}
    </div>
  );
};
```

## 🐛 常见问题

### 1. 构建失败
```bash
# 清理缓存重新安装
rm -rf node_modules package-lock.json
npm install

# 检查TypeScript错误
npm run type-check
```

### 2. WebSocket连接问题
```tsx
// 检查WebSocket配置
const ws = new WebSocket(process.env.REACT_APP_WS_URL);

// 添加错误处理
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  // 尝试重连
  setTimeout(() => connectWebSocket(), 5000);
};
```

### 3. API调用失败
```ts
// 添加请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 添加响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    // 处理错误
    return Promise.reject(error);
  }
);
```

## 📚 相关文档

- [后端API文档](../backend/docs/API.md)
- [部署指南](../docs/DEPLOYMENT.md)
- [配置指南](../SETUP.md)
- [项目更新日志](../CHANGELOG.md)

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

MIT License

---

*最后更新：2024-09-25*