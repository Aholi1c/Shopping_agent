import React, { useState, useEffect } from 'react';

interface RiskAnalysis {
  product_id: number;
  overall_risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_score: number;
  risk_factors: Array<{
    category: string;
    description: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    confidence: number;
    evidence: string[];
    mitigation_suggestions: string[];
  }>;
  complaint_analysis: {
    total_complaints: number;
    recent_complaints: number;
    complaint_trend: 'increasing' | 'stable' | 'decreasing';
    common_issues: Array<{
      issue: string;
      frequency: number;
      severity: 'low' | 'medium' | 'high';
    }>;
  };
  review_consistency: {
    consistency_score: number;
    suspicious_patterns: Array<{
      pattern: string;
      severity: 'low' | 'medium' | 'high';
      description: string;
    }>;
  };
  description_contradictions: Array<{
    contradiction_type: string;
    description: string;
    confidence: number;
    severity: 'low' | 'medium' | 'high';
  }>;
  recommendation: {
    action: 'safe' | 'cautious' | 'avoid' | 'investigate';
    reasoning: string;
    confidence: number;
    priority_issues: string[];
  };
}

interface RiskKeyword {
  id: number;
  keyword: string;
  risk_category: string;
  severity_score: number;
  context_patterns: string[];
  frequency_weight: number;
}

interface RiskStatistics {
  total_analyses: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  critical_risk_count: number;
  risk_distribution: Record<string, number>;
  top_risk_categories: Array<{
    category: string;
    count: number;
    percentage: number;
  }>;
  trend_analysis: {
    period: string;
    risk_level_changes: Array<{
      date: string;
      average_risk_score: number;
      high_risk_percentage: number;
    }>;
  };
}

interface RiskAnalysisProps {
  userId?: number;
}

export const RiskAnalysis: React.FC<RiskAnalysisProps> = ({ userId = 1 }) => {
  const [activeTab, setActiveTab] = useState<'analysis' | 'keywords' | 'statistics'>('analysis');
  const [productId, setProductId] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [riskAnalysis, setRiskAnalysis] = useState<RiskAnalysis | null>(null);
  const [riskKeywords, setRiskKeywords] = useState<RiskKeyword[]>([]);
  const [riskStatistics, setRiskStatistics] = useState<RiskStatistics | null>(null);
  const [newKeyword, setNewKeyword] = useState('');
  const [newCategory, setNewCategory] = useState('');
  const [newSeverity, setNewSeverity] = useState<number>(0.5);

  // 获取风险分析
  const fetchRiskAnalysis = async () => {
    if (!productId) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/advanced/risk-analysis/${productId}`);
      if (response.ok) {
        const data = await response.json();
        setRiskAnalysis(data);
      } else {
        console.error('Failed to fetch risk analysis');
      }
    } catch (error) {
      console.error('Error fetching risk analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  // 批量风险分析
  const performBatchAnalysis = async () => {
    const productIds = [1, 2, 3, 4, 5]; // 示例商品ID
    setLoading(true);
    try {
      const response = await fetch('/api/advanced/risk-analysis/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_ids: productIds
        }),
      });

      if (response.ok) {
        const data = await response.json();
        alert(`批量分析完成，共分析了 ${data.analyzed_count} 个商品`);
      } else {
        alert('批量分析失败');
      }
    } catch (error) {
      console.error('Error in batch analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取风险关键词
  const fetchRiskKeywords = async (category?: string) => {
    try {
      const url = category
        ? `/api/advanced/risk-keywords?risk_category=${category}&limit=100`
        : '/api/advanced/risk-keywords?limit=100';
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setRiskKeywords(data.risk_keywords || []);
      }
    } catch (error) {
      console.error('Error fetching risk keywords:', error);
    }
  };

  // 添加风险关键词
  const addRiskKeyword = async () => {
    if (!newKeyword.trim() || !newCategory.trim()) return;

    try {
      const response = await fetch('/api/advanced/risk-keywords', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          keyword: newKeyword.trim(),
          risk_category: newCategory.trim(),
          severity_score: newSeverity,
          context_patterns: []
        }),
      });

      if (response.ok) {
        alert('风险关键词添加成功');
        setNewKeyword('');
        setNewCategory('');
        setNewSeverity(0.5);
        fetchRiskKeywords();
      } else {
        alert('添加风险关键词失败');
      }
    } catch (error) {
      console.error('Error adding risk keyword:', error);
    }
  };

  // 获取风险统计
  const fetchRiskStatistics = async () => {
    try {
      const response = await fetch('/api/advanced/risk-statistics?days=30');
      if (response.ok) {
        const data = await response.json();
        setRiskStatistics(data);
      }
    } catch (error) {
      console.error('Error fetching risk statistics:', error);
    }
  };

  useEffect(() => {
    fetchRiskKeywords();
    fetchRiskStatistics();
  }, []);

  const getRiskLevelColor = (level: string) => {
    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800',
    };
    return colors[level as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getRiskLevelIcon = (level: string) => {
    const icons = {
      low: '✅',
      medium: '⚠️',
      high: '🔥',
      critical: '🚨',
    };
    return icons[level as keyof typeof icons] || '❓';
  };

  const getSeverityColor = (severity: number) => {
    if (severity >= 0.8) return 'text-red-600';
    if (severity >= 0.6) return 'text-orange-600';
    if (severity >= 0.4) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">🛡️ 商品风险识别</h2>
        <div className="flex items-center space-x-2">
          <input
            type="number"
            value={productId}
            onChange={(e) => setProductId(parseInt(e.target.value) || 1)}
            placeholder="商品ID"
            className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={fetchRiskAnalysis}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '分析中...' : '风险分析'}
          </button>
        </div>
      </div>

      {/* 标签页 */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'analysis', label: '风险分析', icon: '🔍' },
            { id: 'keywords', label: '关键词库', icon: '📝' },
            { id: 'statistics', label: '风险统计', icon: '📊' },
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

      {/* 风险分析标签页 */}
      {activeTab === 'analysis' && riskAnalysis && (
        <div className="space-y-6">
          {/* 总体风险概览 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-medium text-blue-800 mb-2">风险等级</h3>
              <div className="flex items-center space-x-2">
                <span className="text-2xl">{getRiskLevelIcon(riskAnalysis.overall_risk_level)}</span>
                <span className={`px-2 py-1 rounded-full text-sm font-medium ${getRiskLevelColor(riskAnalysis.overall_risk_level)}`}>
                  {riskAnalysis.overall_risk_level.toUpperCase()}
                </span>
              </div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg">
              <h3 className="font-medium text-red-800 mb-2">风险评分</h3>
              <p className={`text-2xl font-bold ${getSeverityColor(riskAnalysis.risk_score)}`}>
                {(riskAnalysis.risk_score * 100).toFixed(1)}
              </p>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <h3 className="font-medium text-yellow-800 mb-2">投诉数量</h3>
              <p className="text-2xl font-bold text-yellow-600">{riskAnalysis.complaint_analysis.total_complaints}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-medium text-green-800 mb-2">推荐操作</h3>
              <span className={`px-2 py-1 rounded-full text-sm font-medium ${getRiskLevelColor(riskAnalysis.recommendation.action)}`}>
                {riskAnalysis.recommendation.action.toUpperCase()}
              </span>
            </div>
          </div>

          {/* 风险因素详情 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-medium text-gray-800 mb-4">🎯 风险因素详情</h3>
            <div className="space-y-4">
              {riskAnalysis.risk_factors.map((factor, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(factor.severity)}`}>
                        {factor.severity.toUpperCase()}
                      </span>
                      <h4 className="font-medium text-gray-800">{factor.category}</h4>
                    </div>
                    <span className="text-sm text-gray-500">
                      置信度: {(factor.confidence * 100).toFixed(1)}%
                    </span>
                  </div>

                  <p className="text-gray-700 mb-3">{factor.description}</p>

                  {factor.evidence.length > 0 && (
                    <div className="mb-3">
                      <h5 className="text-sm font-medium text-gray-600 mb-1">证据:</h5>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {factor.evidence.map((evidence, i) => (
                          <li key={i} className="flex items-start">
                            <span className="mr-2">•</span>
                            <span>{evidence}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {factor.mitigation_suggestions.length > 0 && (
                    <div>
                      <h5 className="text-sm font-medium text-gray-600 mb-1">建议措施:</h5>
                      <ul className="text-sm text-blue-600 space-y-1">
                        {factor.mitigation_suggestions.map((suggestion, i) => (
                          <li key={i} className="flex items-start">
                            <span className="mr-2">💡</span>
                            <span>{suggestion}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 投诉分析 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-medium text-gray-800 mb-4">📊 投诉分析</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="bg-red-50 p-3 rounded">
                <p className="text-sm text-red-800">总投诉数</p>
                <p className="text-xl font-bold text-red-600">{riskAnalysis.complaint_analysis.total_complaints}</p>
              </div>
              <div className="bg-orange-50 p-3 rounded">
                <p className="text-sm text-orange-800">近期投诉</p>
                <p className="text-xl font-bold text-orange-600">{riskAnalysis.complaint_analysis.recent_complaints}</p>
              </div>
              <div className="bg-yellow-50 p-3 rounded">
                <p className="text-sm text-yellow-800">投诉趋势</p>
                <p className="text-lg font-bold text-yellow-600 capitalize">
                  {riskAnalysis.complaint_analysis.complaint_trend}
                </p>
              </div>
            </div>

            {riskAnalysis.complaint_analysis.common_issues.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-700 mb-3">常见问题</h4>
                <div className="space-y-2">
                  {riskAnalysis.complaint_analysis.common_issues.map((issue, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">{issue.issue}</span>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-500">频次: {issue.frequency}</span>
                        <span className={`text-xs px-2 py-1 rounded ${getRiskLevelColor(issue.severity)}`}>
                          {issue.severity}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 推荐建议 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-medium text-gray-800 mb-4">💡 综合建议</h3>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getRiskLevelColor(riskAnalysis.recommendation.action)}`}>
                  {riskAnalysis.recommendation.action === 'safe' && '✅'}
                  {riskAnalysis.recommendation.action === 'cautious' && '⚠️'}
                  {riskAnalysis.recommendation.action === 'avoid' && '🚫'}
                  {riskAnalysis.recommendation.action === 'investigate' && '🔍'}
                </div>
                <div className="flex-1">
                  <p className="text-gray-700 mb-2">{riskAnalysis.recommendation.reasoning}</p>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>建议置信度: {(riskAnalysis.recommendation.confidence * 100).toFixed(1)}%</span>
                  </div>

                  {riskAnalysis.recommendation.priority_issues.length > 0 && (
                    <div className="mt-3">
                      <h5 className="text-sm font-medium text-gray-700 mb-1">优先关注问题:</h5>
                      <ul className="text-sm text-red-600 space-y-1">
                        {riskAnalysis.recommendation.priority_issues.map((issue, i) => (
                          <li key={i} className="flex items-start">
                            <span className="mr-2">•</span>
                            <span>{issue}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* 批量分析按钮 */}
          <div className="text-center">
            <button
              onClick={performBatchAnalysis}
              disabled={loading}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
            >
              {loading ? '批量分析中...' : '🔄 批量风险分析'}
            </button>
          </div>
        </div>
      )}

      {/* 关键词库标签页 */}
      {activeTab === 'keywords' && (
        <div className="space-y-6">
          {/* 添加关键词 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-medium text-gray-800 mb-4">➕ 添加风险关键词</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">关键词</label>
                <input
                  type="text"
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  placeholder="输入关键词..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">风险类别</label>
                <input
                  type="text"
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  placeholder="如: 质量, 物流, 售后..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">严重程度</label>
                <input
                  type="range"
                  value={newSeverity}
                  onChange={(e) => setNewSeverity(parseFloat(e.target.value))}
                  min="0"
                  max="1"
                  step="0.1"
                  className="w-full"
                />
                <div className="text-center text-sm text-gray-600">{(newSeverity * 100).toFixed(0)}%</div>
              </div>
              <div className="flex items-end">
                <button
                  onClick={addRiskKeyword}
                  disabled={!newKeyword.trim() || !newCategory.trim()}
                  className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                >
                  添加关键词
                </button>
              </div>
            </div>
          </div>

          {/* 关键词列表 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-medium text-gray-800 mb-4">📝 风险关键词库</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {riskKeywords.map((keyword) => (
                <div key={keyword.id} className="border rounded-lg p-3 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-2">
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      {keyword.risk_category}
                    </span>
                    <span className={`text-sm font-medium ${getSeverityColor(keyword.severity_score)}`}>
                      {(keyword.severity_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <h4 className="font-medium text-gray-800 mb-1">{keyword.keyword}</h4>
                  {keyword.context_patterns.length > 0 && (
                    <div className="text-xs text-gray-500">
                      上下文模式: {keyword.context_patterns.length} 个
                    </div>
                  )}
                </div>
              ))}
            </div>

            {riskKeywords.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <p>暂无风险关键词</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 风险统计标签页 */}
      {activeTab === 'statistics' && riskStatistics && (
        <div className="space-y-6">
          {/* 统计概览 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-medium text-blue-800 mb-2">总分析数</h3>
              <p className="text-2xl font-bold text-blue-600">{riskStatistics.total_analyses}</p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg">
              <h3 className="font-medium text-red-800 mb-2">高风险商品</h3>
              <p className="text-2xl font-bold text-red-600">{riskStatistics.high_risk_count}</p>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <h3 className="font-medium text-yellow-800 mb-2">中风险商品</h3>
              <p className="text-2xl font-bold text-yellow-600">{riskStatistics.medium_risk_count}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-medium text-green-800 mb-2">低风险商品</h3>
              <p className="text-2xl font-bold text-green-600">{riskStatistics.low_risk_count}</p>
            </div>
          </div>

          {/* 风险分布 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-medium text-gray-800 mb-4">📊 风险分布</h3>
            <div className="space-y-3">
              {Object.entries(riskStatistics.risk_distribution).map(([level, count]) => (
                <div key={level} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className={`w-4 h-4 rounded ${getRiskLevelColor(level).split(' ')[0]}`}></span>
                    <span className="text-sm font-medium text-gray-700 capitalize">{level}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getRiskLevelColor(level).split(' ')[0]}`}
                        style={{ width: `${(count / riskStatistics.total_analyses) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600">{count} ({((count / riskStatistics.total_analyses) * 100).toFixed(1)}%)</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 主要风险类别 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-medium text-gray-800 mb-4">🔥 主要风险类别</h3>
            <div className="space-y-3">
              {riskStatistics.top_risk_categories.map((category, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span className="font-medium text-gray-800">{category.category}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">{category.count} 个商品</span>
                    <span className="text-sm font-medium text-red-600">{category.percentage.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 趋势分析 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-medium text-gray-800 mb-4">📈 风险趋势分析</h3>
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
              <p className="text-gray-500">风险趋势图表 (需要集成图表库)</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};