/**
 * API Client for Browser Extension
 * 与后端API通信的客户端
 */

const API_BASE_URL = 'http://localhost:8000';

class APIClient {
  constructor(baseUrl = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async getConfig() {
    const result = await chrome.storage.sync.get(['config']);
    return result.config || { apiUrl: this.baseUrl };
  }

  async request(endpoint, options = {}) {
    const config = await this.getConfig();
    const url = `${config.apiUrl || this.baseUrl}${endpoint}`;
    
    const defaultOptions = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    };
    
    const mergedOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers,
      },
    };
    
    // 如果是FormData，不要设置Content-Type，让浏览器自动设置
    if (mergedOptions.body instanceof FormData) {
      delete mergedOptions.headers['Content-Type'];
    } else if (mergedOptions.body && typeof mergedOptions.body === 'object') {
      mergedOptions.body = JSON.stringify(mergedOptions.body);
    }
    
    try {
      const response = await fetch(url, mergedOptions);
      
      if (!response.ok) {
        // 尝试获取详细的错误信息
        let errorMessage = `API request failed: ${response.statusText} (${response.status})`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          // 如果无法解析JSON，尝试读取文本
          try {
            const errorText = await response.text();
            if (errorText) {
              errorMessage = errorText.substring(0, 200);
            }
          } catch (e2) {
            // 忽略解析错误
          }
        }
        throw new Error(errorMessage);
      }
      
      // 检查响应内容类型
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        // 如果不是JSON，返回文本
        const text = await response.text();
        try {
          return JSON.parse(text);
        } catch (e) {
          return { message: text };
        }
      }
    } catch (error) {
      console.error('API request error:', error);
      // 提供更友好的错误信息
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        throw new Error('无法连接到服务器。请确保后端服务正在运行在 http://localhost:8000');
      }
      throw error;
    }
  }

  // 聊天相关API
  async sendChatMessage(message, conversationId = null, options = {}) {
    return this.request('/api/chat/chat', {
      method: 'POST',
      body: {
        message,
        conversation_id: conversationId,
        message_type: options.message_type || 'text',
        model: options.model || 'glm-4-0520',
        use_memory: options.use_memory !== undefined ? options.use_memory : true,  // 默认启用记忆
        use_rag: options.use_rag !== undefined ? options.use_rag : false,
        max_tokens: options.max_tokens,
        temperature: options.temperature,
      },
    });
  }

  async sendEnhancedChat(request) {
    return this.request('/api/chat/enhanced', {
      method: 'POST',
      body: request,
    });
  }

  // 购物相关API
  async searchProduct(query, platforms = []) {
    return this.request('/api/shopping/search', {
      method: 'POST',
      body: {
        query,
        platforms,
      },
    });
  }

  async analyzeProduct(productData) {
    return this.request('/api/shopping/product-analysis', {
      method: 'POST',
      body: productData,
    });
  }

  async comparePrices(productName, platforms = ['jd', 'taobao', 'pdd']) {
    // 使用shopping API的价格对比功能，它会使用万邦API
    return this.request('/api/shopping/price-comparison', {
      method: 'POST',
      body: {
        query: productName,
        platforms: platforms.map(p => {
          // 转换平台名称格式
          const platformMap = {
            'jd': 'jd',
            'taobao': 'taobao',
            'pdd': 'pdd',
            'jd.com': 'jd',
            'taobao.com': 'taobao',
            'pdd.com': 'pdd'
          };
          return platformMap[p.toLowerCase()] || p;
        }),
      },
    });
  }

  async trackPrice(productId, targetPrice = null) {
    return this.request('/api/price-tracker/track', {
      method: 'POST',
      body: {
        product_id: productId,
        target_price: targetPrice,
      },
    });
  }

  async getPriceHistory(productId, days = 30) {
    return this.request(`/api/price-tracker/history/${productId}?days=${days}`);
  }

  async predictPrice(productId) {
    return this.request(`/api/ecommerce/products/${productId}/price-prediction`);
  }

  async analyzeRisk(productId) {
    return this.request(`/api/ecommerce/products/${productId}/risk-analysis`);
  }

  // 商品推荐
  async getRecommendations(userId, options = {}) {
    return this.request('/api/comparison/recommendations', {
      method: 'POST',
      body: {
        user_id: userId,
        ...options,
      },
    });
  }

  // 视觉搜索
  async visualSearch(imageData) {
    const formData = new FormData();
    formData.append('image', imageData);
    
    return this.request('/api/visual-search/search', {
      method: 'POST',
      body: formData,
      headers: {}, // 让浏览器自动设置Content-Type
    });
  }

  // 健康检查
  async healthCheck() {
    return this.request('/health');
  }
}

// 导出API客户端实例
const apiClient = new APIClient();

// 如果在浏览器环境中，将其挂载到window
if (typeof window !== 'undefined') {
  window.apiClient = apiClient;
}

// 如果在CommonJS环境中
if (typeof module !== 'undefined' && module.exports) {
  module.exports = apiClient;
}

