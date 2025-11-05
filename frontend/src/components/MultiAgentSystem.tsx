import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
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
  Timeline,
  Switch,
  Select,
  Input,
  Form,
  Modal,
  Divider
} from 'antd';
import {
  TeamOutlined,
  RobotOutlined,
  MessageOutlined,
  ShoppingOutlined,
  BarChartOutlined,
  SecurityScanOutlined,
  DatabaseOutlined,
  ThunderboltOutlined,
  UserOutlined,
  SettingOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;

interface MultiAgentSystemProps {
  userId?: number;
}

export const MultiAgentSystem: React.FC<MultiAgentSystemProps> = ({ userId = 1 }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [modalVisible, setModalVisible] = useState(false);

  const agents = [
    {
      id: 1,
      name: '对话助手',
      type: 'chat',
      icon: <MessageOutlined />,
      color: '#1890ff',
      status: 'active',
      performance: 95.2,
      tasks: 1247,
      description: '负责自然语言对话和用户交互',
      capabilities: ['多轮对话', '上下文理解', '个性化回复'],
      lastActive: '刚刚'
    },
    {
      id: 2,
      name: '购物专家',
      type: 'shopping',
      icon: <ShoppingOutlined />,
      color: '#52c41a',
      status: 'active',
      performance: 88.7,
      tasks: 356,
      description: '专门处理商品推荐和购物相关任务',
      capabilities: ['商品搜索', '价格对比', '购买建议'],
      lastActive: '2分钟前'
    },
    {
      id: 3,
      name: '数据分析师',
      type: 'analytics',
      icon: <BarChartOutlined />,
      color: '#722ed1',
      status: 'idle',
      performance: 92.1,
      tasks: 189,
      description: '分析用户行为和市场数据',
      capabilities: ['趋势分析', '用户画像', '预测建模'],
      lastActive: '15分钟前'
    },
    {
      id: 4,
      name: '安全卫士',
      type: 'security',
      icon: <SecurityScanOutlined />,
      color: '#fa8c16',
      status: 'active',
      performance: 97.8,
      tasks: 89,
      description: '确保系统安全和数据保护',
      capabilities: ['风险检测', '隐私保护', '安全审计'],
      lastActive: '1分钟前'
    },
    {
      id: 5,
      name: '知识管理师',
      type: 'knowledge',
      icon: <DatabaseOutlined />,
      color: '#eb2f96',
      status: 'active',
      performance: 90.4,
      tasks: 234,
      description: '管理和优化知识库系统',
      capabilities: ['知识更新', '检索优化', '质量保证'],
      lastActive: '5分钟前'
    },
    {
      id: 6,
      name: '性能优化师',
      type: 'performance',
      icon: <ThunderboltOutlined />,
      color: '#13c2c2',
      status: 'idle',
      performance: 93.6,
      tasks: 67,
      description: '监控系统性能和优化响应',
      capabilities: ['性能监控', '资源优化', '响应优化'],
      lastActive: '30分钟前'
    }
  ];

  const collaborationTasks = [
    {
      id: 1,
      title: '用户购物需求分析',
      description: '综合分析用户偏好、预算和市场信息',
      participants: ['对话助手', '购物专家', '数据分析师'],
      status: 'active',
      progress: 75,
      startTime: '10:30',
      estimatedEnd: '10:45'
    },
    {
      id: 2,
      title: '系统安全审计',
      description: '全面的安全检查和漏洞评估',
      participants: ['安全卫士', '性能优化师'],
      status: 'completed',
      progress: 100,
      startTime: '09:00',
      estimatedEnd: '09:30'
    },
    {
      id: 3,
      title: '知识库更新任务',
      description: '更新商品信息和用户偏好数据',
      participants: ['知识管理师', '数据分析师'],
      status: 'pending',
      progress: 0,
      startTime: '11:00',
      estimatedEnd: '11:30'
    }
  ];

  const getStatusBadge = (status: string) => {
    const badges = {
      active: { status: 'processing', text: '运行中' },
      idle: { status: 'default', text: '待机' },
      offline: { status: 'error', text: '离线' },
      maintenance: { status: 'warning', text: '维护中' }
    };
    const badge = badges[status as keyof typeof badges] || badges.idle;
    return <Badge status={badge.status as any} text={badge.text} />;
  };

  const getStatusIcon = (status: string) => {
    const icons = {
      active: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      idle: <ClockCircleOutlined style={{ color: '#d9d9d9' }} />,
      offline: <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />,
      maintenance: <SettingOutlined style={{ color: '#faad14' }} />
    };
    return icons[status as keyof typeof icons] || icons.idle;
  };

  return (
    <div style={{ padding: '24px', maxWidth: 1600, margin: '0 auto' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
          <TeamOutlined style={{ fontSize: 48, color: '#fa8c16', marginRight: '16px' }} />
          <div>
            <Title level={1} style={{ margin: 0 }}>多智能体系统</Title>
            <Text type="secondary" style={{ fontSize: 16 }}>专业领域智能体协作平台</Text>
          </div>
        </div>
      </div>

      {/* 系统概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '32px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃智能体"
              value={agents.filter(a => a.status === 'active').length}
              suffix={`/ ${agents.length}`}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="协作任务"
              value={collaborationTasks.filter(t => t.status === 'active').length}
              suffix={`/ ${collaborationTasks.length}`}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均性能"
              value={Math.round(agents.reduce((sum, agent) => sum + agent.performance, 0) / agents.length)}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日任务"
              value={agents.reduce((sum, agent) => sum + agent.tasks, 0)}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容区 */}
      <Card style={{ marginBottom: '24px' }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="🤖 智能体管理" key="agents">
            <Row gutter={[16, 16]}>
              {agents.map((agent) => (
                <Col xs={24} sm={12} lg={8} xl={6} key={agent.id}>
                  <Card
                    hoverable
                    style={{ height: '100%' }}
                    actions={[
                      <Button
                        type="text"
                        icon={<SettingOutlined />}
                        onClick={() => setSelectedAgent(agent)}
                      >
                        配置
                      </Button>,
                      <Button
                        type="text"
                        icon={<PlayCircleOutlined />}
                        disabled={agent.status === 'active'}
                      >
                        启动
                      </Button>
                    ]}
                  >
                    <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                      <Avatar
                        size={64}
                        style={{ backgroundColor: agent.color, marginBottom: '8px' }}
                      >
                        {agent.icon}
                      </Avatar>
                      <Title level={4} style={{ margin: 0 }}>{agent.name}</Title>
                      {getStatusBadge(agent.status)}
                    </div>

                    <Divider style={{ margin: '12px 0' }} />

                    <Space direction="vertical" style={{ width: '100%' }} size="small">
                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>性能评分</Text>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <Progress
                            percent={agent.performance}
                            size="small"
                            strokeColor={agent.performance >= 90 ? '#52c41a' : '#fa8c16'}
                            showInfo={false}
                            style={{ flex: 1 }}
                          />
                          <Text strong style={{ fontSize: 12 }}>{agent.performance}%</Text>
                        </div>
                      </div>

                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>今日任务</Text>
                        <Text strong style={{ display: 'block' }}>{agent.tasks} 个</Text>
                      </div>

                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>最后活跃</Text>
                        <Text style={{ display: 'block', fontSize: 12 }}>{agent.lastActive}</Text>
                      </div>
                    </Space>

                    <Divider style={{ margin: '12px 0' }} />

                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>核心能力</Text>
                      <div style={{ marginTop: 4 }}>
                        {agent.capabilities.slice(0, 2).map((capability, index) => (
                          <Tag key={index} style={{ marginBottom: 4 }}>
                            {capability}
                          </Tag>
                        ))}
                        {agent.capabilities.length > 2 && (
                          <Tag>+{agent.capabilities.length - 2}</Tag>
                        )}
                      </div>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>

            <div style={{ textAlign: 'center', marginTop: '24px' }}>
              <Button type="dashed" icon={<PlusOutlined />} size="large">
                添加新智能体
              </Button>
            </div>
          </TabPane>

          <TabPane tab="🤝 协作任务" key="collaboration">
            <List
              dataSource={collaborationTasks}
              renderItem={(task) => (
                <List.Item>
                  <Card style={{ width: '100%' }}>
                    <Row gutter={[16, 16]} align="middle">
                      <Col xs={24} md={12}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Space>
                            {getStatusIcon(task.status)}
                            <Title level={4} style={{ margin: 0 }}>{task.title}</Title>
                            {getStatusBadge(task.status)}
                          </Space>
                          <Paragraph type="secondary" style={{ margin: 0 }}>
                            {task.description}
                          </Paragraph>
                        </Space>
                      </Col>
                      <Col xs={24} md={6}>
                        <div>
                          <Text type="secondary" style={{ fontSize: 12 }}>参与智能体</Text>
                          <div style={{ marginTop: 4 }}>
                            {task.participants.map((participant, index) => (
                              <Tag key={index} color="blue">{participant}</Tag>
                            ))}
                          </div>
                        </div>
                      </Col>
                      <Col xs={24} md={6}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <div>
                            <Text type="secondary" style={{ fontSize: 12 }}>进度</Text>
                            <Progress percent={task.progress} size="small" />
                          </div>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {task.startTime} - {task.estimatedEnd}
                          </Text>
                        </Space>
                      </Col>
                    </Row>
                  </Card>
                </List.Item>
              )}
            />
          </TabPane>

          <TabPane tab="📊 性能监控" key="performance">
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="🏆 性能排行榜" size="small">
                  <List
                    dataSource={[...agents].sort((a, b) => b.performance - a.performance)}
                    renderItem={(agent, index) => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={
                            <Avatar style={{ backgroundColor: agent.color }}>
                              {index + 1}
                            </Avatar>
                          }
                          title={
                            <Space>
                              <Text strong>{agent.name}</Text>
                              <Tag color={agent.performance >= 90 ? 'green' : 'orange'}>
                                {agent.performance}%
                              </Tag>
                            </Space>
                          }
                          description={
                            <Progress
                              percent={agent.performance}
                              size="small"
                              strokeColor={agent.performance >= 90 ? '#52c41a' : '#fa8c16'}
                            />
                          }
                        />
                      </List.Item>
                    )}
                  />
                </Card>
              </Col>

              <Col xs={24} lg={12}>
                <Card title="⚡ 系统负载" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text strong>CPU使用率</Text>
                      <Progress percent={67} size="small" />
                    </div>
                    <div>
                      <Text strong>内存使用</Text>
                      <Progress percent={45} size="small" />
                    </div>
                    <div>
                      <Text strong>网络I/O</Text>
                      <Progress percent={23} size="small" />
                    </div>
                    <div>
                      <Text strong>任务队列</Text>
                      <Progress percent={34} size="small" />
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="⚙️ 系统配置" key="settings">
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <SettingOutlined style={{ fontSize: 64, color: '#d9d9d9', marginBottom: '16px' }} />
              <Title level={3} type="secondary">系统配置</Title>
                  <Text type="secondary" style={{ display: 'block', marginBottom: '24px' }}>
                    智能体参数配置、协作规则设置、权限管理等功能正在开发中
                  </Text>
                  <Space>
                    <Button type="primary">全局配置</Button>
                    <Button>协作规则</Button>
                    <Button>权限管理</Button>
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
                  icon={<PlayCircleOutlined />}
                  size="large"
                  style={{ width: '100%', height: '60px' }}
                >
                  启动所有智能体
                </Button>
              </Col>
              <Col xs={24} sm={6}>
                <Button
                  type="default"
                  icon={<ThunderboltOutlined />}
                  size="large"
                  style={{ width: '100%', height: '60px' }}
                >
                  创建协作任务
                </Button>
              </Col>
              <Col xs={24} sm={6}>
                <Button
                  type="dashed"
                  icon={<BarChartOutlined />}
                  size="large"
                  style={{ width: '100%', height: '60px' }}
                >
                  性能分析
                </Button>
              </Col>
              <Col xs={24} sm={6}>
                <Button
                  type="default"
                  icon={<TeamOutlined />}
                  size="large"
                  style={{ width: '100%', height: '60px' }}
                >
                  查看日志
                </Button>
              </Col>
            </Row>
          </Card>

          {/* 智能体配置模态框 */}
          <Modal
            title={selectedAgent ? `配置 ${selectedAgent.name}` : ''}
            open={modalVisible}
            onCancel={() => setModalVisible(false)}
            footer={[
              <Button key="cancel" onClick={() => setModalVisible(false)}>
                取消
              </Button>,
              <Button key="submit" type="primary">
                保存配置
              </Button>
            ]}
            width={600}
          >
            {selectedAgent && (
              <Form layout="vertical">
                <Form.Item label="智能体名称">
                  <Input defaultValue={selectedAgent.name} />
                </Form.Item>
                <Form.Item label="性能目标">
                  <Select defaultValue={selectedAgent.performance >= 90 ? 'high' : 'medium'}>
                    <Option value="high">高性能 (90%+)</Option>
                    <Option value="medium">标准性能 (80-90%)</Option>
                    <Option value="low">基础性能 (70-80%)</Option>
                  </Select>
                </Form.Item>
                <Form.Item label="启用功能">
                  <div>
                    {selectedAgent.capabilities.map((capability: string, index: number) => (
                      <div key={index} style={{ marginBottom: 8 }}>
                        <Switch defaultChecked size="small" /> {capability}
                      </div>
                    ))}
                  </div>
                </Form.Item>
                <Form.Item label="备注说明">
                  <TextArea rows={3} placeholder="添加配置说明..." />
                </Form.Item>
              </Form>
            )}
          </Modal>
        </div>
      );
    };