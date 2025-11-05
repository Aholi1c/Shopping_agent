import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  Space,
  Avatar,
  Typography,
  Badge,
  Divider,
  Tooltip,
  Drawer,
  List,
  Tag,
  Progress,
  Spin,
  message
} from 'antd';
import {
  SendOutlined,
  PaperClipOutlined,
  AudioOutlined,
  StopOutlined,
  SettingOutlined,
  UserOutlined,
  RobotOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  TeamOutlined
} from '@ant-design/icons';
import { Message, Conversation, ChatRequest, FeatureToggle } from '../types';
import { chatAPI } from '../services/api';
import { FeaturePanel } from './FeaturePanel';

const { TextArea } = Input;
const { Text, Paragraph } = Typography;

interface ChatInterfaceProps {
  conversationId?: number;
  onConversationChange?: (conversation: Conversation) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  conversationId,
  onConversationChange,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [recording, setRecording] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [features, setFeatures] = useState<FeatureToggle>({
    useMemory: false,
    useRAG: false,
    useAgentCollaboration: false,
    selectedKnowledgeBases: [],
    selectedAgents: [],
    collaborationType: 'sequential'
  });
  const [showFeaturePanel, setShowFeaturePanel] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (conversationId) {
      loadConversationMessages(conversationId);
    }
  }, [conversationId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadConversationMessages = async (convId: number) => {
    try {
      const conversationMessages = await chatAPI.getConversationMessages(convId);
      setMessages(conversationMessages);
    } catch (error) {
      console.error('Failed to load conversation messages:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() && !selectedFile) return;

    await handleRegularSendMessage();
  };

  const handleRegularSendMessage = async () => {
    const request: ChatRequest = {
      message: inputMessage,
      conversation_id: conversationId,
      message_type: selectedFile ? 'image' : 'text',
      model: process.env.REACT_APP_LLM_PROVIDER === 'bigmodel' ? 'glm-4-0520' : 'gpt-3.5-turbo',
    };

    const userMessage: Message = {
      id: Date.now(),
      conversation_id: conversationId || 0,
      role: 'user',
      content: inputMessage,
      message_type: selectedFile ? 'image' : 'text',
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    setInputMessage('');
    setSelectedFile(null);
    setIsLoading(true);
    setIsTyping(true);

    // Simulate typing delay for better UX
    setTimeout(() => {
      setIsTyping(false);
    }, 1000);

    try {
      let response;
      if (selectedFile) {
        const formData = new FormData();
        formData.append('message', request.message);
        if (request.conversation_id) {
          formData.append('conversation_id', request.conversation_id.toString());
        }
        if (request.model) {
          formData.append('model', request.model);
        }
        formData.append('file', selectedFile);

        response = await chatAPI.sendMessageWithFile(formData);
      } else {
        response = await chatAPI.sendMessage(request);
      }

      const assistantMessage: Message = {
        id: response.message_id,
        conversation_id: response.conversation_id,
        role: 'assistant',
        content: response.response,
        message_type: 'text',
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMessage]);

      if (onConversationChange) {
        const conversation = await chatAPI.getConversation(response.conversation_id);
        onConversationChange(conversation);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      message.error('发送消息失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeatureChange = (newFeatures: FeatureToggle) => {
    setFeatures(newFeatures);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        chunks.push(event.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' });
        setSelectedFile(audioFile);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
      message.error('无法访问麦克风，请检查权限设置');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (timeString: string) => {
    return new Date(timeString).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getActiveFeatures = () => {
    const activeFeatures = [];
    if (features.useMemory) activeFeatures.push({ name: '记忆系统', icon: <DatabaseOutlined />, color: 'green' });
    if (features.useRAG) activeFeatures.push({ name: '知识库', icon: <ThunderboltOutlined />, color: 'blue' });
    if (features.useAgentCollaboration) activeFeatures.push({ name: '多智能体', icon: <TeamOutlined />, color: 'purple' });
    return activeFeatures;
  };

  const activeFeatures = getActiveFeatures();

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: '#f8fafc'
    }}>
      {/* 顶部工具栏 */}
      <div style={{
        padding: '16px 20px',
        background: 'white',
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <RobotOutlined style={{ color: 'white', fontSize: 18 }} />
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#1f2937' }}>智能购物助手</div>
            <div style={{ fontSize: 12, color: '#6b7280' }}>基于 GLM-4.5 的 AI 对话</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {activeFeatures.map((feature, index) => (
            <Tooltip key={index} title={feature.name}>
              <Tag color={feature.color} style={{ cursor: 'pointer' }}>
                {feature.icon} {feature.name}
              </Tag>
            </Tooltip>
          ))}

          <Button
            type="text"
            icon={<SettingOutlined />}
            onClick={() => setShowFeaturePanel(true)}
            style={{ color: '#6b7280' }}
          >
            高级设置
          </Button>
        </div>
      </div>

      {/* 消息区域 */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}>
        {messages.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '60px 20px',
            color: '#6b7280'
          }}>
            <div style={{ fontSize: 48, marginBottom: '16px' }}>🛍️</div>
            <div style={{ fontSize: 18, fontWeight: 600, marginBottom: '8px', color: '#1f2937' }}>
              欢迎使用智能购物助手
            </div>
            <div style={{ fontSize: 14, color: '#6b7280' }}>
              我可以帮助您查找商品、比较价格、提供购物建议
            </div>
            <div style={{ marginTop: '16px', fontSize: 12, color: '#9ca3af' }}>
              💡 您可以尝试询问："帮我找一款性价比高的手机"
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              style={{
                display: 'flex',
                justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: '16px'
              }}
            >
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                maxWidth: message.role === 'user' ? '70%' : '60%'
              }}>
                {message.role === 'assistant' && (
                  <Avatar
                    icon={<RobotOutlined />}
                    style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
                  />
                )}

                <div>
                  <Card
                    style={{
                      boxShadow: message.role === 'user' ? '0 2px 8px rgba(0,0,0,0.1)' : '0 2px 8px rgba(0,0,0,0.05)',
                      border: message.role === 'user' ? 'none' : '1px solid #e5e7eb'
                    }}
                    bodyStyle={{
                      padding: '16px 20px',
                      background: message.role === 'user' ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'white',
                      borderRadius: message.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px'
                    }}
                  >
                    {message.message_type === 'image' && message.media_url && (
                      <div style={{ marginBottom: '12px' }}>
                        <img
                          src={message.media_url}
                          alt="Uploaded content"
                          style={{
                            maxWidth: '100%',
                            borderRadius: '8px',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                          }}
                        />
                      </div>
                    )}

                    <div style={{
                      fontSize: 14,
                      lineHeight: '1.6',
                      color: message.role === 'user' ? 'white' : '#1f2937',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {message.content}
                    </div>

                    <div style={{
                      marginTop: '8px',
                      fontSize: 11,
                      color: message.role === 'user' ? 'rgba(255,255,255,0.8)' : '#9ca3af',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}>
                      <ClockCircleOutlined style={{ fontSize: 10 }} />
                      {formatTime(message.created_at)}
                      {message.role === 'user' && (
                        <CheckCircleOutlined style={{ fontSize: 10, marginLeft: '4px' }} />
                      )}
                    </div>
                  </Card>
                </div>

                {message.role === 'user' && (
                  <Avatar
                    icon={<UserOutlined />}
                    style={{ background: '#e5e7eb' }}
                  />
                )}
              </div>
            </div>
          ))
        )}

        {/* 输入状态指示器 */}
        {(isLoading || isTyping) && (
          <div style={{
            display: 'flex',
            justifyContent: 'flex-start',
            marginBottom: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <Avatar
                icon={<RobotOutlined />}
                style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
              />
              <Card
                style={{
                  border: '1px solid #e5e7eb',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
                }}
                bodyStyle={{
                  padding: '12px 20px',
                  background: 'white',
                  borderRadius: '18px 18px 18px 4px'
                }}
              >
                {isTyping ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Spin size="small" />
                    <Text style={{ fontSize: 12, color: '#6b7280', marginLeft: '8px' }}>
                      正在思考中...
                    </Text>
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <Spin size="small" />
                    <Text style={{ fontSize: 12, color: '#6b7280', marginLeft: '8px' }}>
                      正在处理请求...
                    </Text>
                  </div>
                )}
              </Card>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div style={{
        padding: '20px',
        background: 'white',
        borderTop: '1px solid #e5e7eb'
      }}>
        {/* 文件预览 */}
        {selectedFile && (
          <div style={{
            marginBottom: '16px',
            padding: '12px',
            background: '#f3f4f6',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <PaperClipOutlined style={{ color: '#6b7280' }} />
              <Text style={{ fontSize: 12, color: '#374151' }}>
                {selectedFile.name}
              </Text>
              <Text style={{ fontSize: 11, color: '#6b7280' }}>
                ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </Text>
            </div>
            <Button
              type="text"
              size="small"
              onClick={() => setSelectedFile(null)}
              style={{ color: '#ef4444' }}
            >
              移除
            </Button>
          </div>
        )}

        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <TextArea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="请输入您的问题..."
              autoSize={{ minRows: 1, maxRows: 4 }}
              style={{
                borderRadius: '12px',
                border: '1px solid #e5e7eb',
                fontSize: 14,
                resize: 'none'
              }}
              disabled={isLoading || recording}
            />
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept="image/*,audio/*"
              style={{ display: 'none' }}
            />

            <Tooltip title="上传文件">
              <Button
                icon={<PaperClipOutlined />}
                onClick={() => fileInputRef.current?.click()}
                style={{
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb',
                  height: '44px',
                  width: '44px'
                }}
                disabled={isLoading || recording}
              />
            </Tooltip>

            <Tooltip title={recording ? '停止录音' : '语音输入'}>
              <Button
                icon={recording ? <StopOutlined /> : <AudioOutlined />}
                onClick={recording ? stopRecording : startRecording}
                style={{
                  borderRadius: '8px',
                  height: '44px',
                  width: '44px',
                  ...(recording ? {
                    background: '#ef4444',
                    borderColor: '#ef4444',
                    color: 'white'
                  } : {
                    border: '1px solid #e5e7eb'
                  })
                }}
                disabled={isLoading}
              />
            </Tooltip>

            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSendMessage}
              disabled={isLoading || (!inputMessage.trim() && !selectedFile)}
              style={{
                borderRadius: '8px',
                height: '44px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: 'none'
              }}
            >
              发送
            </Button>
          </div>
        </div>

        <div style={{
          marginTop: '8px',
          textAlign: 'center',
          fontSize: 11,
          color: '#9ca3af'
        }}>
          按 Enter 发送，Shift + Enter 换行
        </div>
      </div>

      {/* 高级功能抽屉 */}
      <Drawer
        title="高级功能设置"
        placement="right"
        onClose={() => setShowFeaturePanel(false)}
        open={showFeaturePanel}
        width={400}
        bodyStyle={{ padding: '20px' }}
      >
        <FeaturePanel
          onFeatureChange={handleFeatureChange}
          sessionId={sessionId}
        />
      </Drawer>
    </div>
  );
};