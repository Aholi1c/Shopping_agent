export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  message_type: 'text' | 'image' | 'audio' | 'video';
  media_url?: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  user_id?: number;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ChatRequest {
  message: string;
  conversation_id?: number;
  message_type?: 'text' | 'image' | 'audio' | 'video';
  media_url?: string;
  model?: string;
  max_tokens?: number;
  temperature?: number;
}

export interface ChatResponse {
  response: string;
  conversation_id: number;
  message_id: number;
  model_used: string;
  tokens_used?: number;
}

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface MediaFile {
  id: number;
  filename: string;
  original_name: string;
  file_type: string;
  file_size: number;
  file_url: string;
  uploaded_at: string;
}

export interface VoiceSettings {
  voice: string;
  rate: number;
  pitch: number;
  volume: number;
}

export interface AppSettings {
  theme: 'light' | 'dark';
  language: 'en' | 'zh';
  fontSize: number;
  voiceSettings: VoiceSettings;
}

// 记忆系统相关类型
export interface Memory {
  id: number;
  content: string;
  memory_type: 'episodic' | 'semantic' | 'working';
  importance_score: number;
  access_count: number;
  last_accessed: string;
  created_at: string;
  metadata?: Record<string, any>;
  tags?: string[];
}

export interface WorkingMemory {
  context_data: Record<string, any>;
  short_term_memory: Record<string, any>;
  expires_at?: string;
}

// RAG系统相关类型
export interface KnowledgeBase {
  id: number;
  name: string;
  description?: string;
  user_id?: number;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: number;
  knowledge_base_id: number;
  filename: string;
  original_name: string;
  file_type: string;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface RAGSearchResult {
  content: string;
  document_id: number;
  chunk_index: number;
  score: number;
  metadata?: Record<string, any>;
}

// 多Agent系统相关类型
export interface Agent {
  id: number;
  name: string;
  description: string;
  agent_type: 'researcher' | 'analyst' | 'writer' | 'coordinator' | 'specialist';
  capabilities: string[];
  config: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentTask {
  id: number;
  task_id: string;
  agent_id: number;
  session_id: string;
  task_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  task_data: Record<string, any>;
  result?: Record<string, any>;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface AgentCollaboration {
  id: number;
  session_id: string;
  collaboration_type: 'sequential' | 'parallel' | 'hierarchical';
  participants: number[];
  workflow: Record<string, any>;
  status: string;
  result?: Record<string, any>;
  created_at: string;
  completed_at?: string;
}

// 增强的聊天类型
export interface EnhancedChatRequest {
  message: string;
  conversation_id?: number;
  message_type?: 'text' | 'image' | 'audio' | 'video';
  media_url?: string;
  model?: string;
  max_tokens?: number;
  temperature?: number;
  // 新增功能
  use_memory?: boolean;
  use_rag?: boolean;
  knowledge_base_ids?: number[];
  agent_collaboration?: boolean;
  collaboration_type?: 'sequential' | 'parallel' | 'hierarchical';
  agents?: number[];
}

export interface EnhancedChatResponse {
  response: string;
  conversation_id: number;
  message_id: number;
  model_used: string;
  tokens_used?: number;
  // 新增信息
  memory_used: boolean;
  rag_results?: RAGSearchResult[];
  agent_collaboration?: Record<string, any>;
  processing_time?: number;
}

// 平台类型
export enum PlatformType {
  JD = 'jd',
  TAOBAO = 'taobao',
  PDD = 'pdd',
  XIAOHONGSHU = 'xiaohongshu',
  DOUYIN = 'douyin',
  OTHER = 'other'
}

// 协作类型
export type CollaborationType = 'sequential' | 'parallel' | 'hierarchical';

// 功能开关类型
export interface FeatureToggle {
  useMemory: boolean;
  useRAG: boolean;
  useAgentCollaboration: boolean;
  selectedKnowledgeBases: number[];
  selectedAgents: number[];
  collaborationType: CollaborationType;
}