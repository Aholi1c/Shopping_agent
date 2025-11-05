export enum PlatformType {
  JD = 'jd',
  TAOBAO = 'taobao',
  PDD = 'pdd',
  XIAOHONGSHU = 'xiaohongshu',
  DOUYIN = 'douyin',
  OTHER = 'other'
}

export enum DiscountType {
  FIXED = 'fixed',
  PERCENTAGE = 'percentage',
  CASHBACK = 'cashback'
}

export enum SimilarityType {
  VISUAL = 'visual',
  SEMANTIC = 'semantic',
  OVERALL = 'overall'
}

export interface ProductCreate {
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
}

export interface ProductResponse {
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
}

export interface ProductSpecResponse {
  id: number;
  product_id: number;
  spec_name: string;
  spec_value: string;
  created_at: string;
}

export interface ProductSearchRequest {
  query: string;
  platforms: PlatformType[];
  category?: string;
  price_min?: number;
  price_max?: number;
  sort_by: string;
  page: number;
  page_size: number;
}

export interface ProductSearchResponse {
  products: ProductResponse[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
  search_time: number;
}

export interface PriceHistoryResponse {
  id: number;
  product_id: number;
  price: number;
  original_price?: number;
  discount_rate?: number;
  timestamp: string;
}

export interface ProductReviewResponse {
  id: number;
  product_id: number;
  reviewer_name?: string;
  rating?: number;
  content?: string;
  is_verified: boolean;
  sentiment_score?: number;
  authenticity_score?: number;
  created_at: string;
}

export interface UserPreferenceResponse {
  id: number;
  user_id: number;
  preference_type: string;
  preference_key: string;
  preference_value: string;
  weight: number;
  created_at: string;
  updated_at: string;
}

export interface CouponResponse {
  id: number;
  platform: PlatformType;
  coupon_id: string;
  title: string;
  description?: string;
  discount_type: DiscountType;
  discount_value: number;
  min_purchase_amount?: number;
  start_date?: string;
  end_date?: string;
  usage_limit?: number;
  usage_count: number;
  terms?: string;
  created_at: string;
}

export interface BestDealRequest {
  product_id: number;
  user_id?: number;
  quantity: number;
}

export interface BestDealResponse {
  product_id: number;
  best_price: number;
  original_price: number;
  total_discount: number;
  recommended_coupons: CouponResponse[];
  savings_amount: number;
  final_price: number;
  strategy_description: string;
}

export interface ImageRecognitionRequest {
  image_url: string;
  platform?: PlatformType;
}

export interface ImageRecognitionResponse {
  product_info?: ProductResponse;
  confidence: number;
  description: string;
  similar_products: ProductResponse[];
}

export interface ImageSearchRequest {
  image_url: string;
  platforms: PlatformType[];
  similarity_threshold: number;
  limit: number;
}

export interface ImageSearchResponse {
  query_image: string;
  results: ProductResponse[];
  similarity_scores: number[];
  search_time: number;
}

export interface SimilarProductRequest {
  product_id: number;
  platform: PlatformType;
  limit: number;
  include_visual: boolean;
  include_semantic: boolean;
}

export interface SimilarProductResponse {
  source_product: ProductResponse;
  similar_products: ProductResponse[];
  similarity_scores: number[];
  similarity_types: string[];
}

export interface RecommendationRequest {
  user_id: number;
  category?: string;
  limit: number;
  include_reasons: boolean;
}

export interface RecommendationResponse {
  user_id: number;
  recommendations: ProductResponse[];
  reasons: string[];
  score: number[];
}

export interface PurchaseAnalysisRequest {
  user_id: number;
  days: number;
}

export interface PurchaseAnalysisResponse {
  user_id: number;
  total_purchases: number;
  total_amount: number;
  average_satisfaction: number;
  favorite_categories: string[];
  favorite_brands: string[];
  price_preference: {
    min: number;
    max: number;
    avg: number;
  };
  purchase_trends: Array<{
    date: string;
    count: number;
    amount: number;
  }>;
}

// API 服务类型
export interface ShoppingAPIService {
  searchProducts(request: ProductSearchRequest, userId?: number): Promise<ProductSearchResponse>;
  getProductDetails(productId: number): Promise<ProductResponse>;
  getPriceHistory(productId: number, days?: number): Promise<PriceHistoryResponse[]>;
  compareProducts(productIds: number[]): Promise<any>;
  recognizeProductImage(request: ImageRecognitionRequest, userId?: number): Promise<ImageRecognitionResponse>;
  searchByImage(request: ImageSearchRequest, userId?: number): Promise<ImageSearchResponse>;
  getSimilarProducts(productId: number, platform: PlatformType, limit?: number): Promise<SimilarProductResponse>;
  getBestDeal(request: BestDealRequest): Promise<BestDealResponse>;
  getUserRecommendations(request: RecommendationRequest): Promise<RecommendationResponse>;
  getUserPurchaseAnalysis(request: PurchaseAnalysisRequest): Promise<PurchaseAnalysisResponse>;
  comparePrices(query: string, platforms?: PlatformType[]): Promise<any>;
  getUserCouponStatistics(userId: number): Promise<any>;
  getPriceAlerts(userId: number, thresholdPercent?: number): Promise<any>;
}