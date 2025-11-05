import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Timeline,
  Tag,
  Button,
  Space,
  Typography,
  List,
  Avatar,
  Badge,
  Progress,
  Statistic,
  Tabs,
  Input
} from 'antd';
import {
  DatabaseOutlined,
  ClockCircleOutlined,
  MessageOutlined,
  UserOutlined,
  HeartOutlined,
  ShoppingOutlined,
  ThunderboltOutlined,
  BarChartOutlined,
  EyeOutlined,
  FilterOutlined,
  ExportOutlined,
  DeleteOutlined,
  EditOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

interface MemorySystemProps {
  userId?: number;
}

export const MemorySystem: React.FC<MemorySystemProps> = ({ userId = 1 }) => {
  const [activeTab, setActiveTab] = useState('overview');
  
  const memoryStats = {
    totalMemories: 15420,
    conversations: 8740,
    preferences: 3280,
    shoppingHistory: 2340,
    behaviors: 1060,
    accuracy: 92.3
  };

  const recentMemories = [
    {
      id: 1,
      type: 'conversation',
      title: '用户询问手机推荐',
      content: '用户表现出对摄影功能的重视，预算3000-4000元',
      time: '2分钟前',
      importance: 'high'
    },
    {
      id: 2,
      type: 'preference',
      title: '品牌偏好',
      content: '偏好苹果和华为产品，对性价比敏感',
      time: '15分钟前',
      importance: 'medium'
    },
    {
      id: 3,
      type: 'shopping',
      title: '购买行为',
      content: '浏览了笔记本电脑，比较了多个型号',
      time: '1小时前',
      importance: 'medium'
    },
    {
      id: 4,
      type: 'behavior',
      title: '使用模式',
      content: '活跃时间段：晚上8-11点，周末使用频率高',
      time: '3小时前',
      importance: 'low'
    }
  ];

  const memoryCategories = [
    {
      name: '对话记忆',
      count: 8740,
      icon: <MessageOutlined />,
      color: '#1890ff',
      description: '用户对话历史和上下文信息'
    },
    {
      name: '偏好设置',
      count: 3280,
      icon: <HeartOutlined />,
      color: '#eb2f96',
      description: '个人偏好和习惯模式'
    },
    {
      name: '购物历史',
      count: 2340,
      icon: <ShoppingOutlined />,
      color: '#52c41a',
      description: '购买行为和商品偏好'
    },
    {
      name: '行为模式',
      count: 1060,
      icon: <ThunderboltOutlined />,
      color: '#fa8c16',
      description: '使用习惯和行为特征'
    }
  ];

  const getImportanceColor = (importance: string) => {
    const colors = {
      high: 'red',
      medium: 'orange',
      low: 'green'
    };
    return colors[importance as keyof typeof colors] || 'default';
  };

  const getTypeIcon = (type: string) => {
    const icons = {
      conversation: <MessageOutlined />,
      preference: <HeartOutlined />,
      shopping: <ShoppingOutlined />,
      behavior: <ThunderboltOutlined />
    };
    return icons[type as keyof typeof icons] || <DatabaseOutlined />;
  };

  return (
    <div style={{ padding: '24px', maxWidth: 1400, margin: '0 auto' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
          <DatabaseOutlined style={{ fontSize: 48, color: '#722ed1', marginRight: '16px' }} />
          <div>
            <Title level={1} style={{ margin: 0 }}>记忆系统</Title>
            <Text type="secondary" style={{ fontSize: 16 }}>个性化记忆与上下文管理</Text>
          </div>
        </div>
      </div>

      {/* 统计概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '32px' }}>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="总记忆数"
              value={memoryStats.totalMemories}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="对话记忆"
              value={memoryStats.conversations}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="偏好设置"
              value={memoryStats.preferences}
              prefix={<HeartOutlined />}
              valueStyle={{ color: '#eb2f96' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="购物历史"
              value={memoryStats.shoppingHistory}
              prefix={<ShoppingOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="行为模式"
              value={memoryStats.behaviors}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="记忆准确率"
              value={memoryStats.accuracy}
              prefix={<BarChartOutlined />}
              suffix="%"
              precision={1}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容区 */}
      <Card style={{ marginBottom: '24px' }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="📊 记忆概览" key="overview">
            <Row gutter={[16, 16]}>
              {/* 记忆分类 */}
              <Col xs={24} lg={12}>
                <Card title="📂 记忆分类" size="small">
                  <Row gutter={[8, 8]}>
                    {memoryCategories.map((category, index) => (
                      <Col xs={12} key={index}>
                        <div style={{
                          padding: '16px',
                          border: '1px solid #f0f0f0',
                          borderRadius: '8px',
                          textAlign: 'center',
                          transition: 'all 0.3s',
                          cursor: 'pointer'
                        }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.borderColor = category.color;
                            e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.borderColor = '#f0f0f0';
                            e.currentTarget.style.boxShadow = 'none';
                          }}
                        >
                          <div style={{ fontSize: '32px', color: category.color, marginBottom: '8px' }}>
                            {category.icon}
                          </div>
                          <Text strong>{category.name}</Text>
                          <div style={{ fontSize: '18px', fontWeight: 'bold', color: category.color, margin: '4px 0' }}>
                            {category.count.toLocaleString()}
                          </div>
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            {category.description}
                          </Text>
                        </div>
                      </Col>
                    ))}
                  </Row>
                </Card>
              </Col>

              {/* 最近记忆 */}
              <Col xs={24} lg={12}>
                <Card title="🕐 最近记忆" size="small" extra={<Button type="link" size="small">查看全部</Button>}>
                  <List
                    dataSource={recentMemories}
                    renderItem={(item) => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={
                            <Avatar style={{ backgroundColor: getImportanceColor(item.importance) }}>
                              {getTypeIcon(item.type)}
                            </Avatar>
                          }
                          title={
                            <Space>
                              <Text strong>{item.title}</Text>
                              <Tag color={getImportanceColor(item.importance)}>
                                {item.importance === 'high' ? '重要' :
                                 item.importance === 'medium' ? '中等' : '一般'}
                              </Tag>
                            </Space>
                          }
                          description={
                            <div>
                              <Paragraph style={{ margin: '4px 0', fontSize: '12px' }}>
                                {item.content}
                              </Paragraph>
                              <Text type="secondary" style={{ fontSize: '11px' }}>
                                <ClockCircleOutlined /> {item.time}
                              </Text>
                            </div>
                          }
                        />
                      </List.Item>
                    )}
                  />
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="🧠 智能分析" key="analysis">
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={8}>
                <Card title="🎯 用户画像" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text strong>年龄层:</Text>
                      <div style={{ marginTop: 4 }}>
                        <Progress percent={75} size="small" strokeColor="#1890ff" />
                        <Text type="secondary" style={{ fontSize: 12 }}>25-35岁</Text>
                      </div>
                    </div>
                    <div>
                      <Text strong>消费能力:</Text>
                      <div style={{ marginTop: 4 }}>
                        <Progress percent={60} size="small" strokeColor="#52c41a" />
                        <Text type="secondary" style={{ fontSize: 12 }}>中等水平</Text>
                      </div>
                    </div>
                    <div>
                      <Text strong>技术敏感度:</Text>
                      <div style={{ marginTop: 4 }}>
                        <Progress percent={85} size="small" strokeColor="#fa8c16" />
                        <Text type="secondary" style={{ fontSize: 12 }}>高度关注</Text>
                      </div>
                    </div>
                  </Space>
                </Card>
              </Col>

              <Col xs={24} lg={8}>
                <Card title="💡 兴趣偏好" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {['电子产品', '智能家居', '运动健身', '数码配件'].map((interest, index) => (
                      <div key={index} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text>{interest}</Text>
                        <Space>
                          <Progress
                            percent={Math.floor(Math.random() * 40 + 60)}
                            size="small"
                            style={{ width: 60 }}
                          />
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            {Math.floor(Math.random() * 30 + 70)}%
                          </Text>
                        </Space>
                      </div>
                    ))}
                  </Space>
                </Card>
              </Col>

              <Col xs={24} lg={8}>
                <Card title="📈 行为趋势" size="small">
                  <Timeline>
                    <Timeline.Item color="blue">最近活跃度上升</Timeline.Item>
                    <Timeline.Item color="green">购物频率稳定</Timeline.Item>
                    <Timeline.Item color="orange">对话深度增加</Timeline.Item>
                    <Timeline.Item color="purple">偏好逐渐明确</Timeline.Item>
                  </Timeline>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="⚙️ 记忆管理" key="management">
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <DatabaseOutlined style={{ fontSize: 64, color: '#d9d9d9', marginBottom: '16px' }} />
              <Title level={3} type="secondary">记忆管理功能</Title>
              <Text type="secondary" style={{ display: 'block', marginBottom: '24px' }}>
                记忆的导入、导出、清理和分析功能正在开发中
              </Text>
              <Space>
                <Button icon={<ExportOutlined />}>导出记忆</Button>
                <Button icon={<FilterOutlined />}>筛选记忆</Button>
                <Button danger icon={<DeleteOutlined />}>清理记忆</Button>
              </Space>
            </div>
          </TabPane>
        </Tabs>
      </Card>

      {/* 快速操作 */}
      <Card title="⚡ 快速操作">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={6}>
            <Button
              type="primary"
              icon={<EyeOutlined />}
              size="large"
              style={{ width: '100%', height: '60px' }}
            >
              查看记忆详情
            </Button>
          </Col>
          <Col xs={24} sm={6}>
            <Button
              type="default"
              icon={<BarChartOutlined />}
              size="large"
              style={{ width: '100%', height: '60px' }}
            >
              分析用户画像
            </Button>
          </Col>
          <Col xs={24} sm={6}>
            <Button
              type="dashed"
              icon={<EditOutlined />}
              size="large"
              style={{ width: '100%', height: '60px' }}
            >
              编辑偏好设置
            </Button>
          </Col>
          <Col xs={24} sm={6}>
            <Button
              type="default"
              icon={<DatabaseOutlined />}
              size="large"
              style={{ width: '100%', height: '60px' }}
            >
              记忆备份
            </Button>
          </Col>
        </Row>
      </Card>
    </div>
  );
};