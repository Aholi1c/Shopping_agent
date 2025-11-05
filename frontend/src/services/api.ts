import axios from 'axios';
import {
  Message, Conversation, ChatRequest, ChatResponse, MediaFile,
  EnhancedChatRequest, KnowledgeBase,
  Agent, AgentTask, AgentCollaboration
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const chatAPI = {
  // Send chat message
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post('/api/chat/chat', request);
    return response.data;
  },

  // Send chat message with file upload
  sendMessageWithFile: async (formData: FormData): Promise<ChatResponse> => {
    const response = await api.post('/api/chat/chat/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Get conversations
  getConversations: async (userId?: number, limit = 50): Promise<Conversation[]> => {
    const params = userId ? { user_id: userId, limit } : { limit };
    const response = await api.get('/api/chat/conversations', { params });
    return response.data;
  },

  // Get conversation by ID
  getConversation: async (conversationId: number): Promise<Conversation> => {
    const response = await api.get(`/api/chat/conversations/${conversationId}`);
    return response.data;
  },

  // Create new conversation
  createConversation: async (title = 'New Conversation'): Promise<Conversation> => {
    const response = await api.post('/api/chat/conversations', { title });
    return response.data;
  },

  // Delete conversation
  deleteConversation: async (conversationId: number): Promise<void> => {
    await api.delete(`/api/chat/conversations/${conversationId}`);
  },

  // Get conversation messages
  getConversationMessages: async (conversationId: number): Promise<Message[]> => {
    const response = await api.get(`/api/chat/conversations/${conversationId}/messages`);
    return response.data;
  },

  // Upload file
  uploadFile: async (file: File): Promise<MediaFile> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/api/chat/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export const mediaAPI = {
  // Transcribe audio
  transcribeAudio: async (audioUrl: string, language?: string) => {
    const response = await api.post('/api/media/transcribe', {
      audio_url: audioUrl,
      language,
    });
    return response.data;
  },

  // Transcribe uploaded audio
  transcribeUploadedAudio: async (file: File, language?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (language) {
      formData.append('language', language);
    }

    const response = await api.post('/api/media/transcribe/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Text to speech
  textToSpeech: async (text: string, voice?: string) => {
    const response = await api.post('/api/media/speech', {
      text,
      voice,
    });
    return response.data;
  },

  // Analyze image
  analyzeImage: async (imageUrl: string, prompt?: string) => {
    const response = await api.post('/api/media/analyze-image', {
      image_url: imageUrl,
      prompt,
    });
    return response.data;
  },

  // Analyze uploaded image
  analyzeUploadedImage: async (file: File, prompt?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (prompt) {
      formData.append('prompt', prompt);
    }

    const response = await api.post('/api/media/analyze-image/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// 记忆系统API
export const memoryAPI = {
  // 创建记忆
  createMemory: async (memoryData: any) => {
    const response = await api.post('/api/memory/memories', memoryData);
    return response.data;
  },

  // 搜索记忆
  searchMemories: async (query: string, options?: any) => {
    const params = new URLSearchParams({ query, ...options });
    const response = await api.get(`/api/memory/memories/search?${params}`);
    return response.data;
  },

  // 获取工作记忆
  getWorkingMemory: async (sessionId: string) => {
    const response = await api.get(`/api/memory/working-memory/${sessionId}`);
    return response.data;
  },

  // 更新工作记忆
  updateWorkingMemory: async (sessionId: string, data: any) => {
    const response = await api.put(`/api/memory/working-memory/${sessionId}`, data);
    return response.data;
  },

  // 整合记忆
  consolidateMemories: async (userId?: number) => {
    const params = userId ? `?user_id=${userId}` : '';
    const response = await api.post(`/api/memory/memories/consolidate${params}`);
    return response.data;
  },
};

// RAG系统API
export const ragAPI = {
  // 创建知识库
  createKnowledgeBase: async (kbData: any) => {
    const response = await api.post('/api/rag/knowledge-bases', kbData);
    return response.data;
  },

  // 获取知识库列表
  getKnowledgeBases: async (userId?: number) => {
    const params = userId ? `?user_id=${userId}` : '';
    const response = await api.get(`/api/rag/knowledge-bases${params}`);
    return response.data;
  },

  // 上传文档到知识库
  uploadDocument: async (kbId: number, file: File, options?: Record<string, any>) => {
    const formData = new FormData();
    formData.append('file', file);
    if (options) {
      Object.entries(options).forEach(([key, value]) => {
        formData.append(key, String(value));
      });
    }

    const response = await api.post(`/api/rag/knowledge-bases/${kbId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 搜索知识库
  searchKnowledgeBase: async (searchData: any) => {
    const response = await api.post('/api/rag/knowledge-bases/search', searchData);
    return response.data;
  },

  // 生成RAG响应
  generateRAGResponse: async (query: string, options?: Record<string, any>) => {
    const formData = new FormData();
    formData.append('query', query);
    if (options) {
      Object.entries(options).forEach(([key, value]) => {
        formData.append(key, String(value));
      });
    }

    const response = await api.post('/api/rag/knowledge-bases/generate-response', formData);
    return response.data;
  },

  // 获取知识库统计
  getKnowledgeBaseStats: async (kbId: number) => {
    const response = await api.get(`/api/rag/knowledge-bases/${kbId}/stats`);
    return response.data;
  },
};

// 多Agent系统API
export const agentAPI = {
  // 获取活跃Agent列表
  getActiveAgents: async () => {
    const response = await api.get('/api/agents');
    return response.data;
  },

  // 创建Agent任务
  createAgentTask: async (taskData: any) => {
    const response = await api.post('/api/agents/tasks', taskData);
    return response.data;
  },

  // 获取会话任务
  getSessionTasks: async (sessionId: string, limit?: number) => {
    const params = limit ? `?limit=${limit}` : '';
    const response = await api.get(`/api/agents/tasks/${sessionId}${params}`);
    return response.data;
  },

  // 获取任务状态
  getTaskStatus: async (taskId: number) => {
    const response = await api.get(`/api/agents/tasks/${taskId}`);
    return response.data;
  },

  // 创建Agent协作
  createAgentCollaboration: async (collabData: any) => {
    const response = await api.post('/api/agents/collaborations', collabData);
    return response.data;
  },

  // 获取协作状态
  getCollaborationStatus: async (collabId: number) => {
    const response = await api.get(`/api/agents/collaborations/${collabId}`);
    return response.data;
  },

  // 获取会话协作列表
  getSessionCollaborations: async (sessionId: string) => {
    const response = await api.get(`/api/agents/collaborations/session/${sessionId}`);
    return response.data;
  },
};

// 增强的聊天API
export const enhancedChatAPI = {
  // 发送增强聊天消息
  sendEnhancedMessage: async (request: EnhancedChatRequest) => {
    const response = await api.post('/api/chat/enhanced', request);
    return response.data;
  },

  // 从对话提取记忆
  extractConversationMemory: async (conversationId: number, userId?: number) => {
    const params = userId ? `?user_id=${userId}` : '';
    const response = await api.post(`/api/chat/extract-memory${params}`, {
      conversation_id: conversationId
    });
    return response.data;
  },
};

export default api;