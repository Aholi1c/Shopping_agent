import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  List,
  Tag,
  Button,
  Space,
  Typography,
  Progress,
  Timeline,
  Avatar,
  Badge,
  Divider,
  Grid
} from 'antd';
import {
  MessageOutlined,
  ShoppingOutlined,
  DatabaseOutlined,
  TeamOutlined,
  EyeOutlined,
  BarChartOutlined,
  SecurityScanOutlined,
  AimOutlined,
  ExperimentOutlined,
  ApiOutlined,
  CloudServerOutlined,
  MonitorOutlined,
  MobileOutlined,
  DollarOutlined,
  TrophyOutlined,
  FireOutlined,
  StarOutlined,
  ThunderboltOutlined,
  BulbOutlined,
  HeartOutlined,
  ShopOutlined,
  PercentageOutlined,
  GlobalOutlined,
  RiseOutlined,
  UserOutlined,
  ClockCircleOutlined,
  SearchOutlined
} from '@ant-design/icons';

const { useBreakpoint } = Grid;
const { Text, Title } = Typography;

interface DashboardProps {
  onViewChange: (view: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onViewChange }) => {
  const screens = useBreakpoint();
  const [stats, setStats] = useState({
    totalConversations: 1247,
    activeUsers: 89,
    knowledgeBaseSize: 15420,
    agentTasks: 156,
    responseTime: 1.2,
    accuracy: 94.5
  });

  const [recentActivities] = useState([
    {
      id: 1,
      type: 'conversation',
      title: '用户询问手机推荐',
      time: '2分钟前',
      user: '张三',
      status: 'completed'
    },
    {
      id: 2,
      type: 'shopping',
      title: '价格对比分析',
      time: '5分钟前',
      user: '李四',
      status: 'processing'
    },
    {
      id: 3,
      type: 'rag',
      title: '知识库更新',
      time: '10分钟前',
      user: '系统',
      status: 'completed'
    },
    {
      id: 4,
      type: 'agent',
      title: '多智能体协作任务',
      time: '15分钟前',
      user: '王五',
      status: 'completed'
    }
  ]);

  const [systemStatus] = useState({
    cpu: 45,
    memory: 67,
    disk: 82,
    network: 23,
    uptime: '99.9%'
  });

  const featureModules = [
    {
      id: 'chat',
      title: '智能对话',
      icon: <MessageOutlined className="text-2xl text-blue-500" />,
      description: '基于GLM-4.5的智能对话系统',
      color: 'blue',
      stats: '1247次对话',
      action: () => onViewChange('chat')
    },
    {
      id: 'shopping',
      title: '购物助手',
      icon: <ShoppingOutlined className="text-2xl text-green-500" />,
      description: '智能商品搜索、价格对比、推荐系统',
      color: 'green',
      stats: '89个活跃用户',
      action: () => onViewChange('shopping')
    },
    {
      id: 'memory',
      title: '记忆系统',
      icon: <DatabaseOutlined className="text-2xl text-purple-500" />,
      description: '个性化记忆与上下文管理',
      color: 'purple',
      stats: '15420条记录',
      action: () => onViewChange('memory')
    },
    {
      id: 'agents',
      title: '多智能体',
      icon: <TeamOutlined className="text-2xl text-orange-500" />,
      description: '专业领域智能体协作',
      color: 'orange',
      stats: '156个任务',
      action: () => onViewChange('agents')
    }
  ];

  const advancedFeatures = [
    {
      title: 'RAG知识库',
      icon: <BulbOutlined />,
      description: '向量检索增强生成',
      status: 'active',
      progress: 85
    },
    {
      title: '多模态处理',
      icon: <EyeOutlined />,
      description: '图像、语音、文本综合理解',
      status: 'active',
      progress: 92
    },
    {
      title: '实时数据分析',
      icon: <BarChartOutlined />,
      description: '用户行为与市场趋势分析',
      status: 'active',
      progress: 78
    },
    {
      title: '安全防护',
      icon: <SecurityScanOutlined />,
      description: '数据安全与隐私保护',
      status: 'active',
      progress: 96
    }
  ];

  const shoppingFeatures = [
    {
      title: '商品搜索',
      icon: <SearchOutlined />,
      description: '多平台商品智能搜索'
    },
    {
      title: '价格对比',
      icon: <PercentageOutlined />,
      description: '实时价格对比与历史追踪'
    },
    {
      title: '图片识别',
      icon: <EyeOutlined />,
      description: '以图搜图与商品识别'
    },
    {
      title: '场景推荐',
      icon: <BulbOutlined />,
      description: '基于场景的个性化推荐'
    },
    {
      title: '价格预测',
      icon: <RiseOutlined />,
      description: 'AI驱动的价格趋势预测'
    },
    {
      title: '风险评估',
      icon: <SecurityScanOutlined />,
      description: '购物决策风险分析'
    }
  ];

  const getStatusColor = (status: string) => {
    const colors = {
      completed: 'success',
      processing: 'processing',
      error: 'error',
      warning: 'warning'
    };
    return colors[status as keyof typeof colors] || 'default';
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>🚀 智能购物助手控制台</Title>
        <Text type="secondary">基于GLM-4.5的全方位AI购物助手平台</Text>
      </div>

      {/* 核心统计指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="总对话数"
              value={stats.totalConversations}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="活跃用户"
              value={stats.activeUsers}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="知识库大小"
              value={stats.knowledgeBaseSize}
              prefix={<DatabaseOutlined />}
              suffix="条"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="智能体任务"
              value={stats.agentTasks}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="响应时间"
              value={stats.responseTime}
              prefix={<ClockCircleOutlined />}
              suffix="秒"
              precision={1}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="准确率"
              value={stats.accuracy}
              prefix={<TrophyOutlined />}
              suffix="%"
              precision={1}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 功能模块入口 */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={3}>🎯 核心功能模块</Title>
        <Row gutter={[16, 16]}>
          {featureModules.map((module) => (
            <Col xs={24} sm={12} md={6} key={module.id}>
              <Card
                hoverable
                style={{ height: '100%' }}
                actions={[
                  <Button type="primary" onClick={module.action}>
                    进入模块
                  </Button>
                ]}
              >
                <div style={{ textAlign: 'center', padding: '20px 0' }}>
                  <div style={{ marginBottom: '16px' }}>
                    {module.icon}
                  </div>
                  <Title level={4}>{module.title}</Title>
                  <Text type="secondary" style={{ display: 'block', marginBottom: '8px' }}>
                    {module.description}
                  </Text>
                  <Text strong>{module.stats}</Text>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      <Row gutter={[16, 16]}>
        {/* 高级功能状态 */}
        <Col xs={24} lg={12}>
          <Card title="🔧 高级功能状态" style={{ height: '100%' }}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {advancedFeatures.map((feature, index) => (
                <div key={index}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <Space>
                      {feature.icon}
                      <div>
                        <Text strong>{feature.title}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {feature.description}
                        </Text>
                      </div>
                    </Space>
                    <Tag color={feature.status === 'active' ? 'green' : 'orange'}>
                      {feature.status === 'active' ? '运行中' : '待配置'}
                    </Tag>
                  </div>
                  <Progress percent={feature.progress} size="small" />
                </div>
              ))}
            </Space>
          </Card>
        </Col>

        {/* 购物助手特色功能 */}
        <Col xs={24} lg={12}>
          <Card title="🛍️ 购物助手特色功能" style={{ height: '100%' }}>
            <Row gutter={[8, 8]}>
              {shoppingFeatures.map((feature, index) => (
                <Col xs={12} sm={6} key={index}>
                  <div style={{ textAlign: 'center', padding: '12px', border: '1px solid #f0f0f0', borderRadius: '8px' }}>
                    <div style={{ fontSize: '24px', marginBottom: '8px', color: '#1890ff' }}>
                      {feature.icon}
                    </div>
                    <Text style={{ fontSize: '12px', display: 'block' }}>
                      {feature.title}
                    </Text>
                  </div>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 系统状态与活动 */}
      <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
        {/* 系统状态 */}
        <Col xs={24} lg={8}>
          <Card title="📊 系统状态">
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <Text>CPU使用率</Text>
                  <Text>{systemStatus.cpu}%</Text>
                </div>
                <Progress percent={systemStatus.cpu} size="small" />
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <Text>内存使用</Text>
                  <Text>{systemStatus.memory}%</Text>
                </div>
                <Progress percent={systemStatus.memory} size="small" />
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <Text>磁盘使用</Text>
                  <Text>{systemStatus.disk}%</Text>
                </div>
                <Progress percent={systemStatus.disk} size="small" />
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <Text>网络流量</Text>
                  <Text>{systemStatus.network}%</Text>
                </div>
                <Progress percent={systemStatus.network} size="small" />
              </div>
              <Divider />
              <div style={{ textAlign: 'center' }}>
                <Text strong>系统可用性</Text>
                <div style={{ fontSize: '24px', color: '#52c41a', fontWeight: 'bold' }}>
                  {systemStatus.uptime}
                </div>
              </div>
            </Space>
          </Card>
        </Col>

        {/* 最近活动 */}
        <Col xs={24} lg={16}>
          <Card title="🕐 最近活动">
            <List
              dataSource={recentActivities}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Badge status={getStatusColor(item.status) as any}>
                        <Avatar icon={<UserOutlined />} />
                      </Badge>
                    }
                    title={
                      <Space>
                        <Text strong>{item.title}</Text>
                        <Tag color={getStatusColor(item.status) as any}>
                          {item.status === 'completed' ? '已完成' :
                           item.status === 'processing' ? '处理中' : '错误'}
                        </Tag>
                      </Space>
                    }
                    description={
                      <Space>
                        <Text type="secondary">{item.user}</Text>
                        <Text type="secondary">•</Text>
                        <Text type="secondary">{item.time}</Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* 快速操作 */}
      <Card title="⚡ 快速操作" style={{ marginTop: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8} md={6}>
            <Button
              type="primary"
              icon={<MessageOutlined />}
              size="large"
              style={{ width: '100%', height: '60px' }}
              onClick={() => onViewChange('chat')}
            >
              开始对话
            </Button>
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Button
              type="default"
              icon={<ShoppingOutlined />}
              size="large"
              style={{ width: '100%', height: '60px' }}
              onClick={() => onViewChange('shopping')}
            >
              购物助手
            </Button>
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Button
              type="dashed"
              icon={<BulbOutlined />}
              size="large"
              style={{ width: '100%', height: '60px' }}
            >
              RAG搜索
            </Button>
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Button
              type="default"
              icon={<TeamOutlined />}
              size="large"
              style={{ width: '100%', height: '60px' }}
              onClick={() => onViewChange('agents')}
            >
              多智能体
            </Button>
          </Col>
        </Row>
      </Card>
    </div>
  );
};