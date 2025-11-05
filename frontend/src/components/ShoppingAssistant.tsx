import React, { useState, useEffect } from 'react';
import { Button } from 'antd';
import { PlatformType } from '../types';
import { ProductResponse, CouponResponse } from '../types/shopping';
import { PricePrediction } from './PricePrediction';
import { RiskAnalysis } from './RiskAnalysis';
import { DecisionTool } from './DecisionTool';
import ModernShoppingAssistant from './shopping/ModernShoppingAssistant';

interface ShoppingAssistantProps {
  userId?: number;
}

export const ShoppingAssistant: React.FC<ShoppingAssistantProps> = ({ userId = 1 }) => {
  const [activeTab, setActiveTab] = useState<'search' | 'image' | 'compare' | 'deals' | 'scenario' | 'insights' | 'prediction' | 'risk' | 'decision'>('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<ProductResponse[]>([]);
  const [selectedProducts, setSelectedProducts] = useState<ProductResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [platforms, setPlatforms] = useState<PlatformType[]>([PlatformType.JD, PlatformType.TAOBAO, PlatformType.PDD]);
  const [priceComparison, setPriceComparison] = useState<any>(null);
  const [imageUrl, setImageUrl] = useState('');
  const [imageResults, setImageResults] = useState<any>(null);
  const [useModernDesign, setUseModernDesign] = useState(true);

  // 场景化推荐相关状态
  const [scenarioInput, setScenarioInput] = useState('');
  const [scenarioResult, setScenarioResult] = useState<any>(null);
  const [scenarioRecommendations, setScenarioRecommendations] = useState<any[]>([]);
  const [userInsights, setUserInsights] = useState<any>(null);

  // 商品搜索
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/shopping/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          platforms,
          page: 1,
          page_size: 20
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.products || []);
      }
    } catch (error) {
      console.error('搜索失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 图片识别
  const handleImageRecognition = async () => {
    if (!imageUrl.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/shopping/image-recognition', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image_url: imageUrl }),
      });

      if (response.ok) {
        const data = await response.json();
        setImageResults(data);
      }
    } catch (error) {
      console.error('图片识别失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 图片搜索
  const handleImageSearch = async () => {
    if (!imageUrl.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/shopping/image-search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_url: imageUrl,
          platforms
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.similar_products || []);
      }
    } catch (error) {
      console.error('图片搜索失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 价格对比
  const handlePriceComparison = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/shopping/price-comparison', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          platforms
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setPriceComparison(data);
      }
    } catch (error) {
      console.error('价格对比失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取最佳优惠
  const getBestDeal = async (productId: string) => {
    try {
      const response = await fetch(`/api/shopping/best-deal/${productId}`, {
        method: 'GET',
      });

      if (response.ok) {
        const data = await response.json();
        console.log('最佳优惠:', data);
      }
    } catch (error) {
      console.error('获取优惠失败:', error);
    }
  };

  // 获取相似商品
  const getSimilarProducts = async (productId: string, platform: PlatformType) => {
    try {
      const response = await fetch(`/api/shopping/similar-products/${productId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ platform }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('相似商品:', data);
      }
    } catch (error) {
      console.error('获取相似商品失败:', error);
    }
  };

  // 场景解析
  const handleScenarioParse = async () => {
    if (!scenarioInput.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/shopping/scenario-parse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ scenario: scenarioInput }),
      });

      if (response.ok) {
        const data = await response.json();
        setScenarioResult(data);
        setScenarioRecommendations(data.recommendations || []);
      }
    } catch (error) {
      console.error('场景解析失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取用户洞察
  const handleGetInsights = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/shopping/user-insights/${userId}`, {
        method: 'GET',
      });

      if (response.ok) {
        const data = await response.json();
        setUserInsights(data);
      }
    } catch (error) {
      console.error('获取用户洞察失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 切换商品选择
  const toggleProductSelection = (product: ProductResponse) => {
    const isSelected = selectedProducts.some(p => p.id === product.id);
    if (isSelected) {
      setSelectedProducts(selectedProducts.filter(p => p.id !== product.id));
    } else {
      setSelectedProducts([...selectedProducts, product]);
    }
  };

  // 切换平台
  const togglePlatform = (platform: PlatformType) => {
    if (platforms.includes(platform)) {
      setPlatforms(platforms.filter(p => p !== platform));
    } else {
      setPlatforms([...platforms, platform]);
    }
  };

  // 获取平台名称
  const getPlatformName = (platform: PlatformType) => {
    const names = {
      [PlatformType.JD]: '京东',
      [PlatformType.TAOBAO]: '淘宝',
      [PlatformType.PDD]: '拼多多',
      [PlatformType.XIAOHONGSHU]: '小红书',
      [PlatformType.DOUYIN]: '抖音',
      [PlatformType.OTHER]: '其他'
    };
    return names[platform] || platform;
  };

  // 获取平台颜色
  const getPlatformColor = (platform: PlatformType) => {
    const colors = {
      [PlatformType.JD]: 'bg-red-100 text-red-800',
      [PlatformType.TAOBAO]: 'bg-orange-100 text-orange-800',
      [PlatformType.PDD]: 'bg-red-100 text-red-800',
      [PlatformType.XIAOHONGSHU]: 'bg-pink-100 text-pink-800',
      [PlatformType.DOUYIN]: 'bg-blue-100 text-blue-800',
      [PlatformType.OTHER]: 'bg-gray-100 text-gray-800'
    };
    return colors[platform] || colors[PlatformType.OTHER];
  };

  // 格式化价格
  const formatPrice = (price: number) => {
    return `¥${price.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  // 使用现代化设计
  if (useModernDesign) {
    return (
      <div style={{ height: '100%', width: '100%' }}>
        <ModernShoppingAssistant userId={userId} />

        {/* 切换设计按钮 */}
        <div style={{
          position: 'fixed',
          top: '80px',
          right: '20px',
          zIndex: 1000
        }}>
          <Button
            type="primary"
            size="small"
            onClick={() => setUseModernDesign(false)}
            style={{
              borderRadius: '20px',
              background: 'linear-gradient(135deg, #fa541c 0%, #ff7875 100%)',
              border: 'none',
              boxShadow: '0 2px 8px rgba(250, 84, 28, 0.3)'
            }}
          >
            切换到经典设计
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* 切换设计按钮 */}
      <div style={{
        position: 'absolute',
        top: '80px',
        right: '20px',
        zIndex: 1000
      }}>
        <Button
          type="primary"
          size="small"
          onClick={() => setUseModernDesign(true)}
          style={{
            borderRadius: '20px',
            background: 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)',
            border: 'none',
            boxShadow: '0 2px 8px rgba(24, 144, 255, 0.3)'
          }}
        >
          切换到现代设计
        </Button>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">🛍️ 智能购物助手 (经典设计)</h2>
        <div className="flex space-x-1">
          {Object.values(PlatformType).map(platform => (
            <button
              key={platform}
              onClick={() => togglePlatform(platform)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                platforms.includes(platform)
                  ? `${getPlatformColor(platform)}`
                  : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
              }`}
            >
              {getPlatformName(platform)}
            </button>
          ))}
        </div>
      </div>

      {/* 标签页 */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8 flex-wrap">
          {[
            { id: 'search', label: '商品搜索', icon: '🔍' },
            { id: 'image', label: '图片识别', icon: '🖼️' },
            { id: 'compare', label: '价格对比', icon: '📊' },
            { id: 'deals', label: '优惠计算', icon: '💰' },
            { id: 'scenario', label: '场景推荐', icon: '🎭' },
            { id: 'insights', label: '用户洞察', icon: '📈' },
            { id: 'prediction', label: '价格预测', icon: '📈' },
            { id: 'risk', label: '风险分析', icon: '🛡️' },
            { id: 'decision', label: '决策工具', icon: '🎯' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-1">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* 搜索标签页 */}
      {activeTab === 'search' && (
        <div className="space-y-4">
          <div className="flex space-x-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索商品..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? '搜索中...' : '搜索'}
            </button>
          </div>

          {searchResults.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {searchResults.map(product => (
                <div key={`${product.platform}-${product.product_id}`} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPlatformColor(product.platform)}`}>
                      {getPlatformName(product.platform)}
                    </span>
                    <button
                      onClick={() => toggleProductSelection(product)}
                      className={`p-1 rounded ${selectedProducts.find(p => p.id === product.id) ? 'text-blue-600 bg-blue-100' : 'text-gray-400 hover:text-gray-600'}`}
                    >
                      {selectedProducts.find(p => p.id === product.id) ? '✓' : '+'}
                    </button>
                  </div>

                  <h3 className="font-medium text-gray-800 mb-2 line-clamp-2">{product.title}</h3>

                  <div className="space-y-1 mb-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg font-bold text-red-600">{formatPrice(product.price || 0)}</span>
                      {product.original_price && product.price && product.original_price > product.price && (
                        <span className="text-sm text-gray-500 line-through">{formatPrice(product.original_price)}</span>
                      )}
                    </div>
                    {product.rating && (
                      <div className="flex items-center space-x-1 text-sm text-gray-600">
                        <span>⭐ {product.rating}</span>
                        {product.review_count && (
                          <span>({product.review_count}条评价)</span>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex space-x-2">
                    <button
                      onClick={() => getBestDeal(product.id.toString())}
                      className="flex-1 px-3 py-1 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200 transition-colors"
                    >
                      查优惠
                    </button>
                    <button
                      onClick={() => getSimilarProducts(product.id.toString(), product.platform)}
                      className="flex-1 px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200 transition-colors"
                    >
                      相似商品
                    </button>
                  </div>

                  {product.image_url && (
                    <img
                      src={product.image_url}
                      alt={product.title}
                      className="w-full h-32 object-cover rounded mt-2"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 图片识别标签页 */}
      {activeTab === 'image' && (
        <div className="space-y-4">
          <div className="space-y-2">
            <input
              type="text"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="输入图片URL..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex space-x-2">
              <button
                onClick={handleImageRecognition}
                disabled={loading || !imageUrl.trim()}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
              >
                {loading ? '识别中...' : '🔍 识别商品'}
              </button>
              <button
                onClick={handleImageSearch}
                disabled={loading || !imageUrl.trim()}
                className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {loading ? '搜索中...' : '🖼️ 以图搜图'}
              </button>
            </div>
          </div>

          {imageResults && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium text-gray-800 mb-2">识别结果</h3>
              <p className="text-sm text-gray-600 mb-2">置信度: {(imageResults.confidence * 100).toFixed(1)}%</p>
              <p className="text-sm text-gray-700 mb-3">{imageResults.description}</p>

              {imageResults.product_info && (
                <div className="border rounded p-3 bg-white">
                  <h4 className="font-medium text-gray-800 mb-2">识别到的商品</h4>
                  <div className="space-y-1 text-sm">
                    <p><span className="font-medium">名称:</span> {imageResults.product_info.title}</p>
                    <p><span className="font-medium">平台:</span> {getPlatformName(imageResults.product_info.platform)}</p>
                    {imageResults.product_info.price && (
                      <p><span className="font-medium">价格:</span> {formatPrice(imageResults.product_info.price)}</p>
                    )}
                  </div>
                </div>
              )}

              {imageResults.similar_products && imageResults.similar_products.length > 0 && (
                <div className="mt-3">
                  <h4 className="font-medium text-gray-800 mb-2">相似商品推荐</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {imageResults.similar_products.slice(0, 4).map((product: ProductResponse, index: number) => (
                      <div key={index} className="border rounded p-2 bg-white text-sm">
                        <p className="font-medium text-gray-800 line-clamp-1">{product.title}</p>
                        <p className="text-red-600 font-medium">{formatPrice(product.price || 0)}</p>
                        <span className={`text-xs px-1 rounded ${getPlatformColor(product.platform)}`}>
                          {getPlatformName(product.platform)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 价格预测标签页 */}
      {activeTab === 'prediction' && (
        <PricePrediction userId={userId} />
      )}

      {/* 风险分析标签页 */}
      {activeTab === 'risk' && (
        <RiskAnalysis userId={userId} />
      )}

      {/* 决策工具标签页 */}
      {activeTab === 'decision' && (
        <DecisionTool userId={userId} />
      )}
    </div>
  );
};