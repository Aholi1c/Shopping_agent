// 购物API服务
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8002';

// 平台类型枚举
export enum PlatformType {
  JD = 'jd',
  TAOBAO = 'taobao',
  PDD = 'pdd',
  XIAOHONGSHU = 'xiaohongshu',
  DOUYIN = 'douyin',
  OTHER = 'other'
}

// 商品接口
export interface Product {
  id: number;
  platform: PlatformType;
  product_id: string;
  title: string;
  description?: string;
  category?: string;
  brand?: string;
  price?: number;
  original_price?: number;
  discount_rate?: number;
  image_url?: string;
  product_url?: string;
  rating?: number;
  review_count?: number;
  sales_count?: number;
  stock_status?: string;
  created_at: string;
  updated_at: string;
  // 新增属性以支持UI显示
  is_hot?: boolean;
  is_recommended?: boolean;
  coupon_info?: string;
  shipping_info?: string;
  seller_info?: string;
  estimated_delivery?: string;
}

// 搜索请求接口
export interface SearchRequest {
  query: string;
  platforms?: PlatformType[];
  category?: string;
  price_min?: number;
  price_max?: number;
  sort_by?: string;
  page?: number;
  page_size?: number;
}

// 搜索响应接口
export interface SearchResponse {
  products: Product[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
  search_time: number;
}

// 推荐商品接口
export interface RecommendationItem {
  id: number;
  title: string;
  price: number;
  original_price?: number;
  platform: PlatformType;
  rating?: number;
  review_count?: number;
  image_url?: string;
  category: string;
  reason: string;
  confidence: number;
  match_score: number;
  tags: string[];
  discount_rate?: number;
  is_hot?: boolean;
  is_new?: boolean;
  limited_time?: boolean;
}

// 推荐响应接口
export interface RecommendationResponse {
  recommendations: RecommendationItem[];
  total_count: number;
  algorithm_type: string;
  user_id: number;
  generated_at: string;
}

// 分类接口
export interface Category {
  id: string;
  name: string;
  count?: number;
  hot?: boolean;
  subcategories?: Category[];
}

// 购物车商品接口
export interface CartItem {
  id: number;
  product: Product;
  quantity: number;
  selected: boolean;
  added_at: string;
  // 便捷属性，直接访问product的属性
  platform?: PlatformType;
  title?: string;
  price?: number;
  original_price?: number;
  image_url?: string;
  stock_status?: string;
  coupon_info?: string;
  shipping_info?: string;
  seller_info?: string;
  estimated_delivery?: string;
}

// 购物车响应接口
export interface CartResponse {
  items: CartItem[];
  total_amount: number;
  total_discount: number;
  final_amount: number;
  item_count: number;
  selected_count: number;
}

// API响应错误接口
export interface ApiError {
  detail: string;
  status_code?: number;
}

// HTTP请求工具函数
const apiRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const url = `${API_BASE_URL}${endpoint}`;

  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({ detail: '请求失败' }));
      throw new Error(error.detail || `HTTP错误: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API请求失败:', error);
    throw error;
  }
};

// 购物API服务类
export class ShoppingApiService {
  // 商品搜索
  static async searchProducts(request: SearchRequest): Promise<SearchResponse> {
    return apiRequest<SearchResponse>('/api/shopping/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // 获取商品详情
  static async getProductDetails(productId: number): Promise<Product> {
    return apiRequest<Product>(`/api/shopping/products/${productId}`);
  }

  // 获取相似商品
  static async getSimilarProducts(
    productId: number,
    platform: PlatformType,
    limit: number = 10
  ): Promise<{ products: Product[] }> {
    return apiRequest<{ products: Product[] }>(
      `/api/shopping/products/${productId}/similar?platform=${platform}&limit=${limit}`
    );
  }

  // 价格比较
  static async comparePrices(
    query: string,
    platforms: PlatformType[] = [PlatformType.JD, PlatformType.TAOBAO, PlatformType.PDD]
  ): Promise<any> {
    const params = new URLSearchParams({
      query,
      platforms: platforms.join(',')
    });
    return apiRequest<any>(`/api/shopping/price-comparison?${params}`);
  }

  // 获取最佳优惠
  static async getBestDeal(productId: number): Promise<any> {
    return apiRequest<any>('/api/shopping/best-deal', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId }),
    });
  }

  // 获取个性化推荐
  static async getRecommendations(
    userId: number,
    category?: string,
    limit: number = 20
  ): Promise<RecommendationResponse> {
    const params = new URLSearchParams({
      user_id: userId.toString(),
      limit: limit.toString()
    });
    if (category) {
      params.append('category', category);
    }
    return apiRequest<RecommendationResponse>(`/api/shopping/recommendations?${params}`);
  }

  // 获取商品分类统计
  static async getCategoryStats(): Promise<any> {
    return apiRequest<any>('/api/shopping/statistics');
  }

  // 获取热门搜索词
  static async getHotSearches(limit: number = 10): Promise<string[]> {
    // 模拟热门搜索词，实际应该从后端API获取
    return [
      'iPhone 15 Pro',
      'MacBook Air M2',
      '戴森吸尘器V15',
      'SK-II神仙水',
      'Nike运动鞋',
      'Sony耳机',
      '小米手机',
      '华为手表',
      '雅诗兰黛',
      '乐高玩具'
    ];
  }

  // 获取搜索建议
  static async getSearchSuggestions(query: string): Promise<string[]> {
    // 模拟搜索建议，实际应该从后端API获取
    if (!query.trim()) return [];

    const mockSuggestions = [
      `${query} 保护壳`,
      `${query} 配件`,
      `${query} 2024新款`,
      `${query} 官方旗舰店`,
      `${query} 优惠`
    ];

    return mockSuggestions.slice(0, 5);
  }

  // 获取购物车（模拟）
  static async getCart(userId: number): Promise<CartResponse> {
    // 模拟购物车数据，实际应该从后端API获取
    return {
      items: [],
      total_amount: 0,
      total_discount: 0,
      final_amount: 0,
      item_count: 0,
      selected_count: 0
    };
  }

  // 添加到购物车（模拟）
  static async addToCart(userId: number, productId: number, quantity: number = 1): Promise<void> {
    // 模拟添加到购物车，实际应该调用后端API
    console.log(`添加商品 ${productId} 到用户 ${userId} 的购物车，数量: ${quantity}`);
  }

  // 从购物车移除（模拟）
  static async removeFromCart(userId: number, itemId: number): Promise<void> {
    // 模拟从购物车移除，实际应该调用后端API
    console.log(`从用户 ${userId} 的购物车移除商品 ${itemId}`);
  }

  // 更新购物车商品数量（模拟）
  static async updateCartQuantity(userId: number, itemId: number, quantity: number): Promise<void> {
    // 模拟更新购物车数量，实际应该调用后端API
    console.log(`更新用户 ${userId} 购物车商品 ${itemId} 的数量为: ${quantity}`);
  }

  // 图片识别商品
  static async recognizeImage(imageUrl: string): Promise<any> {
    return apiRequest<any>('/api/shopping/image-recognition', {
      method: 'POST',
      body: JSON.stringify({ image_url: imageUrl }),
    });
  }

  // 以图搜图
  static async searchByImage(imageUrl: string, platforms?: PlatformType[]): Promise<SearchResponse> {
    return apiRequest<SearchResponse>('/api/shopping/image-search', {
      method: 'POST',
      body: JSON.stringify({
        image_url: imageUrl,
        platforms: platforms || [PlatformType.JD, PlatformType.TAOBAO, PlatformType.PDD]
      }),
    });
  }
}

export default ShoppingApiService;