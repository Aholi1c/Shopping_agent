import React, { useState, useRef, useEffect } from 'react';
import {
  Layout,
  Card,
  Input,
  Button,
  Avatar,
  Typography,
  Space,
  Dropdown,
  Upload,
  message as antdMessage,
  Badge,
  Tooltip,
  Divider,
  List,
  Tag,
  Progress
} from 'antd';
import {
  SendOutlined,
  PaperClipOutlined,
  PictureOutlined,
  AudioOutlined,
  SmileOutlined,
  ThunderboltOutlined,
  UserOutlined,
  RobotOutlined,
  ShoppingCartOutlined,
  HeartOutlined,
  StarOutlined,
  CopyOutlined,
  LikeOutlined,
  DislikeOutlined
} from '@ant-design/icons';

const { Content } = Layout;
const { TextArea } = Input;
const { Text, Paragraph } = Typography;

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: Array<{
    type: 'image' | 'file';
    url: string;
    name: string;
  }>;
  reactions?: {
    like?: number;
    dislike?: number;
  };
}

interface ProductCard {
  id: string;
  name: string;
  price: number;
  originalPrice?: number;
  image: string;
  rating: number;
  reviews: number;
  platform: string;
  discount?: number;
}

interface EnhancedChatInterfaceProps {
  conversationId?: number;
  onConversationChange?: (conversation: any) => void;
}

const EnhancedChatInterface: React.FC<EnhancedChatInterfaceProps> = ({
  conversationId,
  onConversationChange
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: '您好！我是您的智能购物助手 🛍️ 我可以帮您：\n\n🔍 搜索和比较商品价格\n📊 分析价格趋势\n🎯 个性化商品推荐\n🤖 智能购物决策\n\n请告诉我您想要什么商品或有什么购物需求？',
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [recording, setRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 模拟商品数据
  const mockProducts: ProductCard[] = [
    {
      id: '1',
      name: 'iPhone 15 Pro Max 256GB',
      price: 9999,
      originalPrice: 11999,
      image: 'https://via.placeholder.com/200x200?text=iPhone15',
      rating: 4.8,
      reviews: 2580,
      platform: '京东',
      discount: 16
    },
    {
      id: '2',
      name: '戴森V15无绳吸尘器',
      price: 4990,
      originalPrice: 5990,
      image: 'https://via.placeholder.com/200x200?text=Dyson',
      rating: 4.9,
      reviews: 1890,
      platform: '天猫',
      discount: 17
    }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // 模拟AI回复
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '我为您找到了几款热门商品，让我为您详细介绍：\n\n**iPhone 15 Pro Max** - 最新款苹果旗舰，性能强劲，拍照出色\n**戴森V15吸尘器** - 无线便携，吸力持久，家庭清洁好帮手\n\n您对哪款商品感兴趣？我可以为您提供更详细的价格分析和购买建议。',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleVoiceInput = () => {
    setRecording(!recording);
    antdMessage.info(recording ? '停止录音' : '开始录音');
  };

  const handleImageUpload = (file: any) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const imageMessage: Message = {
        id: Date.now().toString(),
        type: 'user',
        content: '我上传了一张图片，请帮我分析',
        timestamp: new Date(),
        attachments: [{
          type: 'image',
          url: e.target?.result as string,
          name: file.name
        }]
      };
      setMessages(prev => [...prev, imageMessage]);

      setTimeout(() => {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: '我看到了您上传的图片！这是一款很不错的商品。根据图片分析，我可以为您：\n\n🔍 识别商品类型和品牌\n💰 查找相似商品和价格对比\n⭐ 评价商品质量和性价比\n\n您希望我帮您进行哪种分析？',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, assistantMessage]);
      }, 1500);
    };
    reader.readAsDataURL(file);
    return false;
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const renderMessage = (message: Message) => {
    const isUser = message.type === 'user';

    return (
      <div
        key={message.id}
        style={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          marginBottom: 16,
          padding: '0 16px'
        }}
      >
        <div style={{
          display: 'flex',
          flexDirection: isUser ? 'row-reverse' : 'row',
          alignItems: 'flex-start',
          maxWidth: '70%',
          gap: 8
        }}>
          <Avatar
            size={40}
            icon={isUser ? <UserOutlined /> : <RobotOutlined />}
            style={{
              background: isUser ? '#1890ff' : '#52c41a',
              flexShrink: 0
            }}
          />

          <div style={{ flex: 1 }}>
            <Card
              size="small"
              style={{
                borderRadius: 16,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                background: isUser ? '#e6f7ff' : 'white'
              }}
              bodyStyle={{ padding: '12px 16px' }}
            >
              <div style={{ marginBottom: 8 }}>
                <Text strong style={{ fontSize: 12, color: '#666' }}>
                  {isUser ? '您' : 'AI购物助手'} · {formatTime(message.timestamp)}
                </Text>
              </div>

              {message.attachments && (
                <div style={{ marginBottom: 8 }}>
                  {message.attachments.map((attachment, index) => (
                    <div key={index}>
                      {attachment.type === 'image' && (
                        <img
                          src={attachment.url}
                          alt={attachment.name}
                          style={{
                            maxWidth: '100%',
                            borderRadius: 8,
                            marginBottom: 8
                          }}
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}

              <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                {message.content.split('\n').map((line, index) => (
                  <div key={index}>
                    {line}
                    {index < message.content.split('\n').length - 1 && <br />}
                  </div>
                ))}
              </div>
            </Card>

            {/* 快捷操作按钮 */}
            {!isUser && (
              <Space size="small" style={{ marginTop: 4, marginLeft: 48 }}>
                <Tooltip title="复制">
                  <Button
                    type="text"
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => {
                      navigator.clipboard.writeText(message.content);
                      antdMessage.success('已复制');
                    }}
                  />
                </Tooltip>
                <Tooltip title="有帮助">
                  <Button
                    type="text"
                    size="small"
                    icon={<LikeOutlined />}
                  />
                </Tooltip>
                <Tooltip title="无帮助">
                  <Button
                    type="text"
                    size="small"
                    icon={<DislikeOutlined />}
                  />
                </Tooltip>
              </Space>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <Layout style={{ background: 'transparent', height: '100%' }}>
      <Content style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'white',
        borderRadius: 12,
        overflow: 'hidden'
      }}>
        {/* 聊天头部 */}
        <div style={{
          padding: '16px 24px',
          borderBottom: '1px solid #f0f0f0',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white'
        }}>
          <Space size="large" align="center">
            <Avatar size={48} icon={<RobotOutlined />} style={{ background: 'rgba(255,255,255,0.2)' }} />
            <div>
              <Text strong style={{ fontSize: 18, color: 'white', display: 'block' }}>
                🤖 GLM-4.5 智能购物助手
              </Text>
              <Text style={{ fontSize: 12, color: 'rgba(255,255,255,0.8)' }}>
                多模态对话 · 实时响应 · 智能推荐
              </Text>
            </div>
            <Badge status="success" text="在线" />
          </Space>
        </div>

        {/* 聊天消息区域 */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px 0',
          background: '#fafafa'
        }}>
          {messages.map(renderMessage)}

          {isTyping && (
            <div style={{ padding: '0 16px', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Avatar size={40} icon={<RobotOutlined />} style={{ background: '#52c41a' }} />
                <Card size="small" style={{ borderRadius: 16 }}>
                  <Space>
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <Text type="secondary">AI正在思考中...</Text>
                  </Space>
                </Card>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 商品推荐展示区 */}
        {messages.length > 2 && (
          <div style={{
            padding: '16px 24px',
            borderTop: '1px solid #f0f0f0',
            background: '#f8f9fa'
          }}>
            <Text strong style={{ display: 'block', marginBottom: 12 }}>
              🛍️ 为您推荐
            </Text>
            <div style={{ display: 'flex', gap: 16, overflowX: 'auto' }}>
              {mockProducts.map(product => (
                <Card
                  key={product.id}
                  hoverable
                  style={{ minWidth: 200, flexShrink: 0 }}
                  cover={
                    <div style={{
                      height: 150,
                      background: '#f0f0f0',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <PictureOutlined style={{ fontSize: 48, color: '#999' }} />
                    </div>
                  }
                >
                  <Card.Meta
                    title={
                      <Text style={{ fontSize: 14 }} ellipsis={{ tooltip: product.name }}>
                        {product.name}
                      </Text>
                    }
                    description={
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <Text strong style={{ color: '#f5222d', fontSize: 16 }}>
                            ¥{product.price}
                          </Text>
                          {product.originalPrice && (
                            <Text delete type="secondary" style={{ fontSize: 12 }}>
                              ¥{product.originalPrice}
                            </Text>
                          )}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 4 }}>
                          <Tag color="red">
                            省¥{(product.originalPrice! - product.price)}
                          </Tag>
                          <Text type="secondary" style={{ fontSize: 10 }}>
                            {product.platform}
                          </Text>
                        </div>
                      </div>
                    }
                  />
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* 输入区域 */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid #f0f0f0',
          background: 'white'
        }}>
          <Space.Compact style={{ width: '100%' }}>
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入您的问题，支持文字、语音、图片..."
              autoSize={{ minRows: 1, maxRows: 4 }}
              style={{ borderRadius: 24 }}
            />

            <Space size="small">
              <Upload
                accept="image/*"
                showUploadList={false}
                beforeUpload={handleImageUpload}
              >
                <Button
                  type="text"
                  icon={<PictureOutlined />}
                  size="large"
                  style={{ borderRadius: 20 }}
                />
              </Upload>

              <Button
                type={recording ? "primary" : "default"}
                danger={recording}
                icon={<AudioOutlined />}
                size="large"
                onClick={handleVoiceInput}
                style={{ borderRadius: 20 }}
              />

              <Button
                type="primary"
                icon={<SendOutlined />}
                size="large"
                onClick={handleSend}
                disabled={!inputValue.trim()}
                style={{ borderRadius: 20 }}
              >
                发送
              </Button>
            </Space>
          </Space.Compact>

          <div style={{ marginTop: 8 }}>
            <Space size="small">
              <Text type="secondary" style={{ fontSize: 12 }}>
                💡 支持图片识别、语音输入、智能推荐
              </Text>
            </Space>
          </div>
        </div>
      </Content>
    </Layout>
  );
};

export default EnhancedChatInterface;