import React, { useState, useEffect } from 'react';
import {
  KnowledgeBase, Agent, FeatureToggle
} from '../types';
import {
  ragAPI, agentAPI
} from '../services/api';

type CollaborationType = 'sequential' | 'parallel' | 'hierarchical';

interface FeaturePanelProps {
  onFeatureChange: (features: FeatureToggle) => void;
  sessionId: string;
}

export const FeaturePanel: React.FC<FeaturePanelProps> = ({
  onFeatureChange,
  sessionId
}) => {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [features, setFeatures] = useState<FeatureToggle>({
    useMemory: true,
    useRAG: false,
    useAgentCollaboration: false,
    selectedKnowledgeBases: [],
    selectedAgents: [],
    collaborationType: 'sequential'
  });
  
  useEffect(() => {
    loadKnowledgeBases();
    loadAgents();
  }, []);

  useEffect(() => {
    onFeatureChange(features);
  }, [features, onFeatureChange]);

  const loadKnowledgeBases = async () => {
    try {
      const data = await ragAPI.getKnowledgeBases();
      setKnowledgeBases(data);
    } catch (error) {
      console.error('Failed to load knowledge bases:', error);
    }
  };

  const loadAgents = async () => {
    try {
      const data = await agentAPI.getActiveAgents();
      setAgents(data);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const handleFeatureToggle = (feature: keyof FeatureToggle, value: any) => {
    setFeatures(prev => ({
      ...prev,
      [feature]: value
    }));
  };

  const handleKnowledgeBaseToggle = (kbId: number) => {
    setFeatures(prev => {
      const selected = prev.selectedKnowledgeBases.includes(kbId);
      return {
        ...prev,
        selectedKnowledgeBases: selected
          ? prev.selectedKnowledgeBases.filter(id => id !== kbId)
          : [...prev.selectedKnowledgeBases, kbId],
        useRAG: !prev.selectedKnowledgeBases.includes(kbId) || selected
          ? prev.useRAG
          : true
      };
    });
  };

  const handleAgentToggle = (agentId: number) => {
    setFeatures(prev => {
      const selected = prev.selectedAgents.includes(agentId);
      return {
        ...prev,
        selectedAgents: selected
          ? prev.selectedAgents.filter(id => id !== agentId)
          : [...prev.selectedAgents, agentId],
        useAgentCollaboration: !prev.selectedAgents.includes(agentId) || selected
          ? prev.useAgentCollaboration
          : true
      };
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 space-y-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        🚀 高级功能控制
      </h3>

      {/* 记忆系统 */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">🧠 记忆系统</span>
            <span className="text-xs text-gray-500">
              (长期记忆、短期记忆、上下文管理)
            </span>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={features.useMemory}
              onChange={(e) => handleFeatureToggle('useMemory', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>
      </div>

      {/* RAG系统 */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">📚 RAG增强</span>
            <span className="text-xs text-gray-500">
              (检索增强生成，基于知识库)
            </span>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={features.useRAG}
              onChange={(e) => handleFeatureToggle('useRAG', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {features.useRAG && knowledgeBases.length > 0 && (
          <div className="ml-4 space-y-1">
            <p className="text-xs text-gray-600">选择知识库:</p>
            <div className="grid grid-cols-1 gap-1 max-h-32 overflow-y-auto">
              {knowledgeBases.map((kb) => (
                <label key={kb.id} className="flex items-center space-x-2 text-xs">
                  <input
                    type="checkbox"
                    checked={features.selectedKnowledgeBases.includes(kb.id)}
                    onChange={() => handleKnowledgeBaseToggle(kb.id)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-gray-700">{kb.name}</span>
                  <span className="text-gray-500">({kb.document_count} 文档)</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 多Agent协作 */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">🤖 多Agent协作</span>
            <span className="text-xs text-gray-500">
              (多个AI助手协同工作)
            </span>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={features.useAgentCollaboration}
              onChange={(e) => handleFeatureToggle('useAgentCollaboration', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {features.useAgentCollaboration && (
          <div className="ml-4 space-y-2">
            {/* Agent选择 */}
            {agents.length > 0 && (
              <div>
                <p className="text-xs text-gray-600 mb-1">选择参与协作的Agent:</p>
                <div className="grid grid-cols-1 gap-1 max-h-32 overflow-y-auto">
                  {agents.map((agent) => (
                    <label key={agent.id} className="flex items-center space-x-2 text-xs">
                      <input
                        type="checkbox"
                        checked={features.selectedAgents.includes(agent.id)}
                        onChange={() => handleAgentToggle(agent.id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <div className="flex-1">
                        <span className="text-gray-700 font-medium">{agent.name}</span>
                        <div className="flex flex-wrap gap-1">
                          {agent.capabilities.map((cap, index) => (
                            <span
                              key={index}
                              className="text-xs bg-blue-100 text-blue-800 px-1 rounded"
                            >
                              {cap}
                            </span>
                          ))}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* 协作类型选择 */}
            <div>
              <p className="text-xs text-gray-600 mb-1">协作方式:</p>
              <select
                value={features.collaborationType}
                onChange={(e) => handleFeatureToggle('collaborationType', e.target.value as CollaborationType)}
                className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="sequential">顺序执行</option>
                <option value="parallel">并行执行</option>
                <option value="hierarchical">层级协作</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* 功能预览 */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-700 mb-2">当前配置:</h4>
        <div className="text-xs text-gray-600 space-y-1">
          <p>🧠 记忆系统: {features.useMemory ? '✅ 启用' : '❌ 禁用'}</p>
          <p>📚 RAG增强: {features.useRAG ? '✅ 启用' : '❌ 禁用'}</p>
          {features.useRAG && features.selectedKnowledgeBases.length > 0 && (
            <p className="ml-2">已选择 {features.selectedKnowledgeBases.length} 个知识库</p>
          )}
          <p>🤖 多Agent协作: {features.useAgentCollaboration ? '✅ 启用' : '❌ 禁用'}</p>
          {features.useAgentCollaboration && features.selectedAgents.length > 0 && (
            <>
              <p className="ml-2">已选择 {features.selectedAgents.length} 个Agent</p>
              <p className="ml-2">协作方式: {
                features.collaborationType === 'sequential' ? '顺序执行' :
                features.collaborationType === 'parallel' ? '并行执行' : '层级协作'
              }</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
};