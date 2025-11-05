import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  Avatar,
  Typography,
  Spin,
  message,
  Space,
  Tag
} from 'antd';
import {
  SendOutlined,
  UserOutlined,
  RobotOutlined,
  ShoppingOutlined
} from '@ant-design/icons';
import ChatApiService, { ChatRequest, ChatResponse, ChatHistoryItem } from '../../services/chatApi';

const { TextArea } = Input;
const { Text, Title } = Typography;

interface SmartChatInterfaceProps {
  userId?: number;
  title?: string;
  className?: string;
}

const SmartChatInterface: React.FC<SmartChatInterfaceProps> = ({
  userId = 1,
  title = "智能购物助手",
  className = ''
}) => {
  const [messages, setMessages] = useState<ChatHistoryItem[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 加载历史消息
    loadChatHistory();
    // 发送欢迎消息
    sendWelcomeMessage();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadChatHistory = async () => {
    try {
      const historyResponse = await ChatApiService.getChatHistory(sessionId);
      if (historyResponse.history && historyResponse.history.length > 0) {
        setMessages(historyResponse.history);
      }
    } catch (error) {
      console.log('没有历史消息，开始新对话');
    }
  };

  const sendWelcomeMessage = () => {
    const welcomeMessage: ChatHistoryItem = {
      user_message: '',
      bot_response: '您好！我是您的智能购物助手 🤖\n\n我可以帮您：\n• 智能购物推荐\n• 商品价格比较\n• 产品信息查询\n• 购物决策建议\n\n请告诉我您想了解什么商品，我会为您提供专业的建议！',
      timestamp: new Date().toISOString(),
      user_id: userId
    };
    setMessages([welcomeMessage]);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    // 添加用户消息到界面
    const tempUserMessage: ChatHistoryItem = {
      user_message: userMessage,
      bot_response: '',
      timestamp: new Date().toISOString(),
      user_id: userId
    };
    setMessages(prev => [...prev, tempUserMessage]);

    try {
      const request: ChatRequest = {
        message: userMessage,
        user_id: userId,
        session_id: sessionId
      };

      const response: ChatResponse = await ChatApiService.sendMessage(request);

      // 更新最后一条消息的机器人回复
      setMessages(prev => {
        const updated = [...prev];
        if (updated.length > 0) {
          updated[updated.length - 1].bot_response = response.response;
        }
        return updated;
      });

    } catch (error) {
      console.error('发送消息失败:', error);
      message.error('发送消息失败，请稍后重试');

      // 添加错误回复
      setMessages(prev => {
        const updated = [...prev];
        if (updated.length > 0) {
          updated[updated.length - 1].bot_response = '抱歉，我现在无法回应。请稍后再试或检查网络连接。';
        }
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const clearHistory = async () => {
    try {
      await ChatApiService.clearChatHistory(sessionId);
      setMessages([]);
      sendWelcomeMessage();
      message.success('对话历史已清除');
    } catch (error) {
      console.error('清除历史失败:', error);
      message.error('清除历史失败');
    }
  };

  return (
    <Card
      className={`smart-chat-interface ${className}`}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <RobotOutlined style={{ color: '#1890ff', fontSize: '20px' }} />
          <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
            {title}
          </Title>
          <Tag color="green" icon={<ShoppingOutlined />}>
            购物助手
          </Tag>
        </div>
      }
      extra={
        <Button size="small" onClick={clearHistory}>
          清除历史
        </Button>
      }
      style={{
        height: '600px',
        display: 'flex',
        flexDirection: 'column'
      }}
      bodyStyle={{
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden'
      }}
    >
      {/* 消息列表 */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          marginBottom: '16px',
          padding: '8px',
          backgroundColor: '#fafafa',
          borderRadius: '8px'
        }}
      >
        {messages.map((msg, index) => (
          <div key={index} style={{ marginBottom: '16px' }}>
            {/* 用户消息 */}
            {msg.user_message && (
              <div style={{
                display: 'flex',
                justifyContent: 'flex-end',
                marginBottom: '8px'
              }}>
                <div style={{
                  maxWidth: '70%',
                  backgroundColor: '#1890ff',
                  color: 'white',
                  padding: '12px 16px',
                  borderRadius: '18px 18px 4px 18px',
                  wordBreak: 'break-word'
                }}>
                  <Text style={{ color: 'inherit' }}>{msg.user_message}</Text>
                  <div style={{
                    fontSize: '11px',
                    opacity: 0.8,
                    marginTop: '4px',
                    textAlign: 'right'
                  }}>
                    {formatTime(msg.timestamp)}
                  </div>
                </div>
                <Avatar
                  icon={<UserOutlined />}
                  style={{ marginLeft: '8px' }}
                  size="small"
                />
              </div>
            )}

            {/* 机器人回复 */}
            {msg.bot_response && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <Avatar
                  icon={<RobotOutlined />}
                  style={{ marginRight: '8px', backgroundColor: '#52c41a' }}
                  size="small"
                />
                <div style={{
                  maxWidth: '70%',
                  backgroundColor: 'white',
                  padding: '12px 16px',
                  borderRadius: '18px 18px 18px 4px',
                  wordBreak: 'break-word',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
                }}>
                  <Text style={{ whiteSpace: 'pre-line' }}>
                    {msg.bot_response}
                  </Text>
                  <div style={{
                    fontSize: '11px',
                    color: '#8c8c8c',
                    marginTop: '4px'
                  }}>
                    {formatTime(msg.timestamp)}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* 加载指示器 */}
        {isLoading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', gap: '8px' }}>
            <Avatar
              icon={<RobotOutlined />}
              style={{ backgroundColor: '#52c41a' }}
              size="small"
            />
            <div style={{
              backgroundColor: 'white',
              padding: '12px 16px',
              borderRadius: '18px 18px 18px 4px',
              boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
            }}>
              <Spin size="small" />
              <Text style={{ marginLeft: '8px', color: '#8c8c8c' }}>
                正在思考中...
              </Text>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
        <TextArea
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="请输入您的问题，比如：我想买一部手机..."
          autoSize={{ minRows: 1, maxRows: 4 }}
          style={{ flex: 1 }}
          disabled={isLoading}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSendMessage}
          loading={isLoading}
          style={{
            height: '40px',
            background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
            border: 'none'
          }}
        >
          发送
        </Button>
      </div>
    </Card>
  );
};

export default SmartChatInterface;