import React, { useState, useEffect } from 'react';

interface DecisionDimension {
  dimension: string;
  weight: number;
  description: string;
  category: 'performance' | 'price' | 'quality' | 'service' | 'risk';
}

interface ProductCandidate {
  id: number;
  name: string;
  price: number;
  rating: number;
  reviews: number;
  platform: string;
  image_url?: string;
  features: Record<string, any>;
}

interface DecisionRecommendation {
  product_id: number;
  product_name: string;
  score: number;
  reasoning: string;
  strengths: string[];
  weaknesses: string[];
  match_score: number;
  value_score: number;
  risk_score: number;
}

interface DecisionSession {
  session_id: string;
  user_id: number;
  product_candidates: number[];
  context: string;
  current_weights: Record<string, number>;
  recommendations: DecisionRecommendation[];
  created_at: string;
  last_updated: string;
}

interface DecisionHistory {
  session_id: string;
  context: string;
  selected_product_id: number;
  decision_weights: Record<string, number>;
  recommendation_score: number;
  user_satisfaction?: number;
  created_at: string;
}

interface DecisionDimensionsResponse {
  dimensions: Record<string, DecisionDimension>;
  descriptions: Record<string, string>;
}

interface DecisionToolProps {
  userId?: number;
}

export const DecisionTool: React.FC<DecisionToolProps> = ({ userId = 1 }) => {
  const [activeTab, setActiveTab] = useState<'session' | 'weights' | 'history'>('session');
  const [loading, setLoading] = useState(false);
  const [currentSession, setCurrentSession] = useState<DecisionSession | null>(null);
  const [decisionHistory, setDecisionHistory] = useState<DecisionHistory[]>([]);
  const [decisionDimensions, setDecisionDimensions] = useState<DecisionDimensionsResponse | null>(null);
  const [availableProducts, setAvailableProducts] = useState<ProductCandidate[]>([]);

  // Session creation
  const [selectedProducts, setSelectedProducts] = useState<number[]>([]);
  const [sessionContext, setSessionContext] = useState('general');

  // Weight adjustment
  const [customWeights, setCustomWeights] = useState<Record<string, number>>({});
  const [weightExplanations, setWeightExplanations] = useState<Record<string, string>>({});

  // 获取决策维度信息
  const fetchDecisionDimensions = async () => {
    try {
      const response = await fetch('/api/advanced/decision/dimensions');
      if (response.ok) {
        const data = await response.json();
        setDecisionDimensions(data);
        setCustomWeights(data.dimensions);
      }
    } catch (error) {
      console.error('Error fetching decision dimensions:', error);
    }
  };

  // 创建决策会话
  const createDecisionSession = async () => {
    if (selectedProducts.length < 2) {
      alert('请至少选择2个商品进行比较');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/advanced/decision/create-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          product_candidates: selectedProducts,
          context: sessionContext,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentSession(data);
        setCustomWeights(data.current_weights);
      } else {
        alert('创建决策会话失败');
      }
    } catch (error) {
      console.error('Error creating decision session:', error);
    } finally {
      setLoading(false);
    }
  };

  // 更新权重和重新推荐
  const updateWeightsAndRecommend = async () => {
    if (!currentSession) return;

    setLoading(true);
    try {
      const response = await fetch('/api/advanced/decision/update-weights', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          session_id: currentSession.session_id,
          new_weights: customWeights,
          product_candidates: selectedProducts,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentSession(prev => prev ? { ...prev, recommendations: data.recommendations, current_weights: data.current_weights } : null);
      } else {
        alert('更新权重失败');
      }
    } catch (error) {
      console.error('Error updating weights:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取决策历史
  const fetchDecisionHistory = async () => {
    try {
      const response = await fetch(`/api/advanced/decision/history/${userId}?limit=10`);
      if (response.ok) {
        const data = await response.json();
        setDecisionHistory(data.history || []);
      }
    } catch (error) {
      console.error('Error fetching decision history:', error);
    }
  };

  // 获取用户权重
  const fetchUserWeights = async () => {
    try {
      const response = await fetch(`/api/advanced/user-weights/${userId}?context=${sessionContext}`);
      if (response.ok) {
        const data = await response.json();
        setCustomWeights(data.weights);
      }
    } catch (error) {
      console.error('Error fetching user weights:', error);
    }
  };

  // 模拟商品数据
  const mockProducts: ProductCandidate[] = [
    {
      id: 1,
      name: "iPhone 15 Pro",
      price: 7999,
      rating: 4.8,
      reviews: 1250,
      platform: "京东",
      features: {
        performance: 0.95,
        quality: 0.92,
        camera: 0.94,
        battery: 0.85,
        display: 0.90
      }
    },
    {
      id: 2,
      name: "华为 Mate 60 Pro",
      price: 6999,
      rating: 4.7,
      reviews: 980,
      platform: "淘宝",
      features: {
        performance: 0.88,
        quality: 0.90,
        camera: 0.92,
        battery: 0.95,
        display: 0.85
      }
    },
    {
      id: 3,
      name: "小米 14 Pro",
      price: 4999,
      rating: 4.5,
      reviews: 756,
      platform: "拼多多",
      features: {
        performance: 0.82,
        quality: 0.80,
        camera: 0.85,
        battery: 0.88,
        display: 0.87
      }
    }
  ];

  useEffect(() => {
    fetchDecisionDimensions();
    fetchDecisionHistory();
    setAvailableProducts(mockProducts);
  }, []);

  const formatPrice = (price: number) => `¥${price.toFixed(2)}`;

  const handleWeightChange = (dimension: string, value: number) => {
    setCustomWeights(prev => ({
      ...prev,
      [dimension]: value
    }));
  };

  const handleProductToggle = (productId: number) => {
    setSelectedProducts(prev =>
      prev.includes(productId)
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    );
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRecommendationText = (score: number) => {
    if (score >= 0.8) return '强烈推荐';
    if (score >= 0.6) return '推荐';
    if (score >= 0.4) return '考虑';
    return '不推荐';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">🎯 交互式决策工具</h2>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">会话ID:</span>
          <span className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
            {currentSession?.session_id || '未开始'}
          </span>
        </div>
      </div>

      {/* 标签页 */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'session', label: '决策会话', icon: '🎯' },
            { id: 'weights', label: '权重调整', icon: '⚖️' },
            { id: 'history', label: '决策历史', icon: '📜' },
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

      {/* 决策会话标签页 */}
      {activeTab === 'session' && (
        <div className="space-y-6">
          {!currentSession ? (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="font-medium text-gray-800 mb-4">创建新决策会话</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">选择商品进行比较</label>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {availableProducts.map(product => (
                      <div key={product.id} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between mb-3">
                          <input
                            type="checkbox"
                            checked={selectedProducts.includes(product.id)}
                            onChange={() => handleProductToggle(product.id)}
                            className="mt-1"
                          />
                          <span className="text-sm text-gray-500">{product.platform}</span>
                        </div>

                        <h4 className="font-medium text-gray-800 mb-2">{product.name}</h4>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">价格:</span>
                            <span className="font-medium text-red-600">{formatPrice(product.price)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">评分:</span>
                            <span className="font-medium">{product.rating} ⭐</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">评价:</span>
                            <span className="font-medium">{product.reviews} 条</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">决策场景</label>
                  <select
                    value={sessionContext}
                    onChange={(e) => setSessionContext(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="general">通用购物</option>
                    <option value="business">商务用途</option>
                    <option value="personal">个人使用</option>
                    <option value="gift">礼品选择</option>
                    <option value="budget">预算敏感</option>
                    <option value="premium">高端选择</option>
                  </select>
                </div>

                <button
                  onClick={createDecisionSession}
                  disabled={selectedProducts.length < 2 || loading}
                  className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {loading ? '创建中...' : '开始决策分析'}
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* 推荐结果 */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="font-medium text-gray-800 mb-4">🎯 推荐结果</h3>
                <div className="space-y-4">
                  {currentSession.recommendations
                    .sort((a, b) => b.score - a.score)
                    .map((recommendation, index) => (
                    <div key={recommendation.product_id} className={`border rounded-lg p-4 ${
                      index === 0 ? 'border-green-200 bg-green-50' : 'border-gray-200'
                    }`}>
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          {index === 0 && <span className="text-2xl">🏆</span>}
                          <div>
                            <h4 className="font-medium text-gray-800">{recommendation.product_name}</h4>
                            <div className="flex items-center space-x-2 mt-1">
                              <span className={`text-lg font-bold ${getScoreColor(recommendation.score)}`}>
                                {(recommendation.score * 100).toFixed(1)}
                              </span>
                              <span className="text-sm text-gray-600">分</span>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                recommendation.score >= 0.8 ? 'bg-green-100 text-green-800' :
                                recommendation.score >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                                'bg-red-100 text-red-800'
                              }`}>
                                {getRecommendationText(recommendation.score)}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right text-sm">
                          <div className="text-green-600">匹配度: {(recommendation.match_score * 100).toFixed(0)}%</div>
                          <div className="text-blue-600">价值: {(recommendation.value_score * 100).toFixed(0)}%</div>
                          <div className="text-orange-600">风险: {(recommendation.risk_score * 100).toFixed(0)}%</div>
                        </div>
                      </div>

                      <div className="mb-3">
                        <p className="text-gray-700 text-sm">{recommendation.reasoning}</p>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {recommendation.strengths.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium text-green-700 mb-2">优势:</h5>
                            <ul className="text-sm text-green-600 space-y-1">
                              {recommendation.strengths.map((strength, i) => (
                                <li key={i} className="flex items-start">
                                  <span className="mr-2">•</span>
                                  <span>{strength}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {recommendation.weaknesses.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium text-orange-700 mb-2">劣势:</h5>
                            <ul className="text-sm text-orange-600 space-y-1">
                              {recommendation.weaknesses.map((weakness, i) => (
                                <li key={i} className="flex items-start">
                                  <span className="mr-2">•</span>
                                  <span>{weakness}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 决策说明 */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 className="font-medium text-blue-800 mb-3">💡 决策说明</h3>
                <div className="text-sm text-blue-700 space-y-2">
                  <p>• 推荐结果基于您设置的权重进行多维度评分</p>
                  <p>• 评分综合考虑了性能、价格、质量、服务和风险等因素</p>
                  <p>• 您可以在"权重调整"标签页中修改各因素的优先级</p>
                  <p>• 系统会实时重新计算并更新推荐结果</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 权重调整标签页 */}
      {activeTab === 'weights' && decisionDimensions && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-medium text-gray-800 mb-4">⚖️ 决策权重调整</h3>
            <p className="text-sm text-gray-600 mb-4">
              拖动滑块调整各因素的权重，系统将实时重新计算推荐结果
            </p>

            <div className="space-y-6">
              {Object.entries(decisionDimensions.dimensions).map(([key, dimension]) => (
                <div key={key} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-gray-800">{dimension.dimension}</h4>
                      <p className="text-sm text-gray-600">{dimension.description}</p>
                    </div>
                    <div className="text-right">
                      <span className={`text-lg font-bold ${getScoreColor(dimension.weight)}`}>
                        {(dimension.weight * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <input
                      type="range"
                      value={customWeights[key] || dimension.weight}
                      onChange={(e) => handleWeightChange(key, parseFloat(e.target.value) / 100)}
                      min="0"
                      max="100"
                      step="5"
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>不重要</span>
                      <span>一般</span>
                      <span>重要</span>
                      <span>非常重要</span>
                    </div>
                  </div>

                  {dimension.category && (
                    <div className="mt-2">
                      <span className="text-xs px-2 py-1 rounded-full bg-purple-100 text-purple-700">
                        {dimension.category}
                      </span>
                    </div>
                  )}
                </div>
              ))}

              <div className="flex space-x-4">
                <button
                  onClick={updateWeightsAndRecommend}
                  disabled={loading || !currentSession}
                  className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {loading ? '更新中...' : '🔄 重新计算推荐'}
                </button>
                <button
                  onClick={fetchUserWeights}
                  className="flex-1 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  🔄 重置为默认权重
                </button>
              </div>
            </div>
          </div>

          {/* 权重说明 */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="font-medium text-yellow-800 mb-3">💡 权重调整说明</h3>
            <div className="text-sm text-yellow-700 space-y-1">
              <p>• 权重总和会自动归一化，无需手动调整</p>
              <p>• 提高某个因素的权重会使该因素在推荐中更重要</p>
              <p>• 不同场景建议使用不同的权重配置</p>
              <p>• 系统会保存您的权重偏好，下次使用时自动应用</p>
            </div>
          </div>
        </div>
      )}

      {/* 决策历史标签页 */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-gray-800">📜 决策历史</h3>
              <button
                onClick={fetchDecisionHistory}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                刷新
              </button>
            </div>

            {decisionHistory.length > 0 ? (
              <div className="space-y-4">
                {decisionHistory.map((history) => (
                  <div key={history.session_id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-medium text-gray-800 capitalize">{history.context}</h4>
                        <p className="text-sm text-gray-600">
                          {new Date(history.created_at).toLocaleDateString('zh-CN')}
                        </p>
                      </div>
                      <div className="text-right">
                        <span className={`px-2 py-1 rounded-full text-sm font-medium ${
                          history.recommendation_score >= 0.8 ? 'bg-green-100 text-green-800' :
                          history.recommendation_score >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          评分: {(history.recommendation_score * 100).toFixed(1)}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                      {Object.entries(history.decision_weights).slice(0, 4).map(([key, weight]) => (
                        <div key={key} className="bg-gray-50 rounded p-2">
                          <div className="text-gray-600 text-xs capitalize">{key}</div>
                          <div className="font-medium">{(weight * 100).toFixed(0)}%</div>
                        </div>
                      ))}
                    </div>

                    {history.user_satisfaction && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600">用户满意度:</span>
                          <div className="flex items-center">
                            {Array.from({ length: 5 }, (_, i) => (
                              <span key={i} className={`text-lg ${i < Math.floor(history.user_satisfaction!) ? 'text-yellow-400' : 'text-gray-300'}`}>
                                ⭐
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>暂无决策历史</p>
                <p className="text-sm">开始使用决策工具后，历史记录将显示在这里</p>
              </div>
            )}
          </div>

          {/* 历史分析 */}
          {decisionHistory.length > 0 && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
              <h3 className="font-medium text-purple-800 mb-3">📊 决策偏好分析</h3>
              <div className="text-sm text-purple-700">
                <p>• 平均推荐评分: {(decisionHistory.reduce((sum, h) => sum + h.recommendation_score, 0) / decisionHistory.length * 100).toFixed(1)}分</p>
                <p>• 最常用场景: {
                  (() => {
                    const contextCounts = decisionHistory.reduce((acc, h) => {
                      acc[h.context] = (acc[h.context] || 0) + 1;
                      return acc;
                    }, {} as Record<string, number>);
                    const sortedContexts = Object.entries(contextCounts).sort(([,a], [,b]) => b - a);
                    return sortedContexts[0]?.[0] || '未知';
                  })()
                }</p>
                <p>• 总决策次数: {decisionHistory.length}次</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};