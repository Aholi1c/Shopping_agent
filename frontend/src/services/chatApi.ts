// 智能对话API服务
const CHAT_API_BASE_URL = process.env.REACT_APP_CHAT_API_URL || 'http://localhost:8004';

// 聊天请求接口
export interface ChatRequest {
  message: string;
  user_id?: number;
  session_id?: string;
}

// 聊天响应接口
export interface ChatResponse {
  response: string;
  timestamp: string;
  session_id: string;
  user_id: number;
}

// 对话历史项接口
export interface ChatHistoryItem {
  user_message: string;
  bot_response: string;
  timestamp: string;
  user_id: number;
}

// 对话历史响应接口
export interface ChatHistoryResponse {
  session_id: string;
  history: ChatHistoryItem[];
  total_messages?: number;
  message?: string;
}

class ChatApiService {
  // 发送消息
  static async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${CHAT_API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: request.message,
        user_id: request.user_id || 1,
        session_id: request.session_id || 'default'
      }),
    });

    if (!response.ok) {
      throw new Error(`聊天API错误: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // 获取对话历史
  static async getChatHistory(sessionId: string): Promise<ChatHistoryResponse> {
    const response = await fetch(`${CHAT_API_BASE_URL}/api/chat/history/${sessionId}`);

    if (!response.ok) {
      throw new Error(`获取对话历史错误: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // 清除对话历史
  static async clearChatHistory(sessionId: string): Promise<{ message: string; session_id: string }> {
    const response = await fetch(`${CHAT_API_BASE_URL}/api/chat/history/${sessionId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`清除对话历史错误: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // 检查聊天服务健康状态
  static async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${CHAT_API_BASE_URL}/health`);

    if (!response.ok) {
      throw new Error(`聊天服务健康检查失败: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }
}

export default ChatApiService;