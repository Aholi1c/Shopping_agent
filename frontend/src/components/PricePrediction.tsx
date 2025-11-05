import React, { useState, useEffect } from 'react';

interface PricePrediction {
  product_id: number;
  prediction_days: number;
  current_price: number;
  predictions: Array<{
    date: string;
    predicted_price: number;
    confidence: number;
    price_change: number;
    price_change_percent: number;
  }>;
  models_used: string[];
  ensemble_prediction: {
    predicted_price: number;
    confidence: number;
    trend_direction: 'up' | 'down' | 'stable';
    volatility_level: 'low' | 'medium' | 'high';
  };
  purchase_advice: {
    action: 'buy_now' | 'wait' | 'avoid' | 'set_alert';
    reasoning: string;
    confidence: number;
    expected_savings?: number;
    recommended_wait_days?: number;
  };
  risk_factors: Array<{
    factor: string;
    severity: 'low' | 'medium' | 'high';
    description: string;
  }>;
}

interface PromotionCalendar {
  id: number;
  platform: string;
  promotion_name: string;
  start_date: string;
  end_date: string;
  discount_type: string;
  expected_discount: number;
  promotion_type: string;
  is_active: boolean;
}

interface PricePredictionProps {
  userId?: number;
}

export const PricePrediction: React.FC<PricePredictionProps> = ({ userId = 1 }) => {
  const [activeTab, setActiveTab] = useState<'prediction' | 'promotion' | 'alerts'>('prediction');
  const [productId, setProductId] = useState<number>(1);
  const [predictionDays, setPredictionDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const [pricePrediction, setPricePrediction] = useState<PricePrediction | null>(null);
  const [promotionCalendar, setPromotionCalendar] = useState<PromotionCalendar[]>([]);
  const [platformFilter, setPlatformFilter] = useState<string>('');
  const [alertThreshold, setAlertThreshold] = useState<number>(0);
  const [alertType, setAlertType] = useState<'below' | 'above'>('below');

  // 获取价格预测
  const fetchPricePrediction = async () => {
    if (!productId) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/advanced/price-prediction/${productId}?prediction_days=${predictionDays}`);
      if (response.ok) {
        const data = await response.json();
        setPricePrediction(data);
      } else {
        console.error('Failed to fetch price prediction');
      }
    } catch (error) {
      console.error('Error fetching price prediction:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取促销日历
  const fetchPromotionCalendar = async () => {
    try {
      const url = platformFilter
        ? `/api/advanced/promotion-calendar?platform=${platformFilter}`
        : '/api/advanced/promotion-calendar';
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setPromotionCalendar(data.promotions || []);
      }
    } catch (error) {
      console.error('Error fetching promotion calendar:', error);
    }
  };

  // 创建价格提醒
  const createPriceAlert = async () => {
    if (!productId || alertThreshold <= 0) return;

    try {
      const response = await fetch('/api/advanced/price-alerts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          product_id: productId,
          alert_type: alertType,
          threshold_value: alertThreshold,
          notification_method: 'app',
        }),
      });

      if (response.ok) {
        alert('价格提醒创建成功！');
      } else {
        alert('创建价格提醒失败');
      }
    } catch (error) {
      console.error('Error creating price alert:', error);
    }
  };

  // 优化购买时机
  const optimizePurchaseTiming = async () => {
    if (!productId) return;

    setLoading(true);
    try {
      const response = await fetch('/api/advanced/price-prediction/optimize-timing', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_id: productId,
          user_id: userId,
          quantity: 1,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        alert(`购买时机优化建议：${data.recommendation}`);
      } else {
        alert('获取购买时机建议失败');
      }
    } catch (error) {
      console.error('Error optimizing purchase timing:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPromotionCalendar();
  }, [platformFilter]);

  const formatPrice = (price: number) => `¥${price.toFixed(2)}`;
  const formatDate = (dateString: string) => new Date(dateString).toLocaleDateString('zh-CN');

  const getActionColor = (action: string) => {
    const colors = {
      buy_now: 'bg-green-100 text-green-800',
      wait: 'bg-yellow-100 text-yellow-800',
      avoid: 'bg-red-100 text-red-800',
      set_alert: 'bg-blue-100 text-blue-800',
    };
    return colors[action as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getActionText = (action: string) => {
    const texts = {
      buy_now: '立即购买',
      wait: '建议等待',
      avoid: '避免购买',
      set_alert: '设置提醒',
    };
    return texts[action as keyof typeof texts] || action;
  };

  const getTrendIcon = (trend: string) => {
    const icons = {
      up: '📈',
      down: '📉',
      stable: '➡️',
    };
    return icons[trend as keyof typeof icons] || '➡️';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">📈 价格预测与促销优化</h2>
        <div className="flex items-center space-x-2">
          <input
            type="number"
            value={productId}
            onChange={(e) => setProductId(parseInt(e.target.value) || 1)}
            placeholder="商品ID"
            className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={fetchPricePrediction}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '预测中...' : '获取预测'}
          </button>
        </div>
      </div>

      {/* 标签页 */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'prediction', label: '价格预测', icon: '📊' },
            { id: 'promotion', label: '促销日历', icon: '🎉' },
            { id: 'alerts', label: '价格提醒', icon: '🔔' },
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

      {/* 价格预测标签页 */}
      {activeTab === 'prediction' && pricePrediction && (
        <div className="space-y-6">
          {/* 当前价格和预测概览 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-medium text-blue-800 mb-2">当前价格</h3>
              <p className="text-2xl font-bold text-blue-600">{formatPrice(pricePrediction.current_price)}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-medium text-green-800 mb-2">预测趋势</h3>
              <p className="text-xl">
                {getTrendIcon(pricePrediction.ensemble_prediction.trend_direction)}
                <span className="ml-2 font-medium text-green-600 capitalize">
                  {pricePrediction.ensemble_prediction.trend_direction}
                </span>
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <h3 className="font-medium text-purple-800 mb-2">置信度</h3>
              <p className="text-2xl font-bold text-purple-600">
                {(pricePrediction.ensemble_prediction.confidence * 100).toFixed(1)}%
              </p>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <h3 className="font-medium text-yellow-800 mb-2">购买建议</h3>
              <span className={`px-2 py-1 rounded-full text-sm font-medium ${getActionColor(pricePrediction.purchase_advice.action)}`}>
                {getActionText(pricePrediction.purchase_advice.action)}
              </span>
            </div>
          </div>

          {/* 购买建议 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-medium text-gray-800 mb-4">💡 购买建议</h3>
            <div className="space-y-3">
              <div className="flex items-start space-x-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getActionColor(pricePrediction.purchase_advice.action)}`}>
                  {pricePrediction.purchase_advice.action === 'buy_now' && '🛒'}
                  {pricePrediction.purchase_advice.action === 'wait' && '⏰'}
                  {pricePrediction.purchase_advice.action === 'avoid' && '⚠️'}
                  {pricePrediction.purchase_advice.action === 'set_alert' && '🔔'}
                </div>
                <div className="flex-1">
                  <p className="text-gray-700 mb-2">{pricePrediction.purchase_advice.reasoning}</p>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>建议置信度: {(pricePrediction.purchase_advice.confidence * 100).toFixed(1)}%</span>
                    {pricePrediction.purchase_advice.expected_savings && (
                      <span>预期节省: {formatPrice(pricePrediction.purchase_advice.expected_savings)}</span>
                    )}
                    {pricePrediction.purchase_advice.recommended_wait_days && (
                      <span>建议等待: {pricePrediction.purchase_advice.recommended_wait_days}天</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-4 flex space-x-2">
              <button
                onClick={optimizePurchaseTiming}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                优化购买时机
              </button>
            </div>
          </div>

          {/* 价格预测图表 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-medium text-gray-800 mb-4">📈 价格走势预测</h3>
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
              <p className="text-gray-500">价格走势图表 (需要集成图表库如 Chart.js 或 Recharts)</p>
            </div>
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {pricePrediction.predictions.slice(0, 6).map((pred, index) => (
                <div key={index} className="border rounded p-3 bg-gray-50">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-600">{formatDate(pred.date)}</span>
                    <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700">
                      {(pred.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{formatPrice(pred.predicted_price)}</span>
                    <span className={`text-sm ${pred.price_change > 0 ? 'text-red-600' : pred.price_change < 0 ? 'text-green-600' : 'text-gray-600'}`}>
                      {pred.price_change > 0 ? '+' : ''}{(pred.price_change_percent * 100).toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 风险因素 */}
          {pricePrediction.risk_factors && pricePrediction.risk_factors.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="font-medium text-gray-800 mb-4">⚠️ 风险因素</h3>
              <div className="space-y-3">
                {pricePrediction.risk_factors.map((risk, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                      risk.severity === 'high' ? 'bg-red-100 text-red-800' :
                      risk.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {risk.severity === 'high' ? 'H' : risk.severity === 'medium' ? 'M' : 'L'}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-800">{risk.factor}</h4>
                      <p className="text-sm text-gray-600 mt-1">{risk.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 促销日历标签页 */}
      {activeTab === 'promotion' && (
        <div className="space-y-4">
          <div className="flex items-center space-x-4">
            <input
              type="text"
              value={platformFilter}
              onChange={(e) => setPlatformFilter(e.target.value)}
              placeholder="筛选平台..."
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={fetchPromotionCalendar}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              刷新
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {promotionCalendar.map((promo) => (
              <div key={promo.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                    {promo.platform}
                  </span>
                  {promo.is_active && (
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      活跃
                    </span>
                  )}
                </div>

                <h4 className="font-medium text-gray-800 mb-2">{promo.promotion_name}</h4>

                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>开始时间:</span>
                    <span>{formatDate(promo.start_date)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>结束时间:</span>
                    <span>{formatDate(promo.end_date)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>优惠类型:</span>
                    <span>{promo.discount_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>预期折扣:</span>
                    <span className="font-medium text-red-600">{(promo.expected_discount * 100).toFixed(1)}%</span>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-gray-200">
                  <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                    {promo.promotion_type}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {promotionCalendar.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <p>暂无促销活动</p>
            </div>
          )}
        </div>
      )}

      {/* 价格提醒标签页 */}
      {activeTab === 'alerts' && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-medium text-gray-800 mb-4">创建价格提醒</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">商品ID</label>
                <input
                  type="number"
                  value={productId}
                  onChange={(e) => setProductId(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">提醒类型</label>
                <select
                  value={alertType}
                  onChange={(e) => setAlertType(e.target.value as 'below' | 'above')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="below">价格低于</option>
                  <option value="above">价格高于</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">阈值价格 (¥)</label>
                <input
                  type="number"
                  value={alertThreshold}
                  onChange={(e) => setAlertThreshold(parseFloat(e.target.value) || 0)}
                  step="0.01"
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={createPriceAlert}
                  disabled={!productId || alertThreshold <= 0}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  创建提醒
                </button>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="font-medium text-gray-800 mb-4">📋 提醒说明</h3>
            <div className="space-y-2 text-sm text-gray-600">
              <p>• 当商品价格达到设定阈值时，系统将通过应用内通知提醒您</p>
              <p>• 可以创建多个不同条件的价格提醒</p>
              <p>• 提醒会在价格变化时自动触发检查</p>
              <p>• 建议结合价格预测功能设置更精准的提醒阈值</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};