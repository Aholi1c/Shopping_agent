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
  Form,
  Input,
  Switch,
  Select,
  Slider,
  Divider,
  Alert,
  Upload,
  message,
  Radio,
  Checkbox,
  DatePicker,
  TimePicker
} from 'antd';
import {
  SettingOutlined,
  UserOutlined,
  SecurityScanOutlined,
  DatabaseOutlined,
  ApiOutlined,
  BellOutlined,
  TeamOutlined,
  GlobalOutlined,
  CloudUploadOutlined,
  SaveOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;
const { RangePicker } = DatePicker;

interface SettingsProps {
  userId?: number;
}

export const Settings: React.FC<SettingsProps> = ({ userId = 1 }) => {
  const [activeTab, setActiveTab] = useState('general');
  const [form] = Form.useForm();

  const systemConfig = {
    general: {
      siteName: '智能购物助手',
      description: '基于GLM-4.5的AI购物助手平台',
      language: 'zh-CN',
      timezone: 'Asia/Shanghai',
      maintenance: false
    },
    api: {
      baseUrl: 'http://localhost:8000',
      timeout: 30000,
      retries: 3,
      rateLimit: 100
    },
    security: {
      enableHttps: true,
      enableCORS: true,
      tokenExpiry: 7200,
      sessionTimeout: 3600
    },
    notifications: {
      email: true,
      browser: true,
      mobile: false,
      frequency: 'daily'
    }
  };

  const modelSettings = [
    {
      name: 'GLM-4.5',
      provider: 'BigModel',
      status: 'active',
      performance: 95.2,
      config: {
        temperature: 0.7,
        maxTokens: 4096,
        topP: 0.9
      }
    },
    {
      name: 'GPT-3.5',
      provider: 'OpenAI',
      status: 'backup',
      performance: 89.1,
      config: {
        temperature: 0.6,
        maxTokens: 2048,
        topP: 0.8
      }
    }
  ];

  const users = [
    {
      id: 1,
      name: '张三',
      email: 'zhangsan@example.com',
      role: 'admin',
      status: 'active',
      lastLogin: '2024-01-15 10:30'
    },
    {
      id: 2,
      name: '李四',
      email: 'lisi@example.com',
      role: 'user',
      status: 'active',
      lastLogin: '2024-01-15 09:15'
    },
    {
      id: 3,
      name: '王五',
      email: 'wangwu@example.com',
      role: 'user',
      status: 'inactive',
      lastLogin: '2024-01-10 16:45'
    }
  ];

  const getStatusBadge = (status: string) => {
    const badges = {
      active: { status: 'success', text: '正常' },
      inactive: { status: 'default', text: '未激活' },
      backup: { status: 'processing', text: '备用' },
      maintenance: { status: 'warning', text: '维护中' }
    };
    const badge = badges[status as keyof typeof badges] || badges.active;
    return <Badge status={badge.status as any} text={badge.text} />;
  };

  const handleSave = () => {
    message.success('设置保存成功！');
  };

  const handleReset = () => {
    form.resetFields();
    message.info('设置已重置');
  };

  return (
    <div style={{ padding: '24px', maxWidth: 1200, margin: '0 auto' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
          <SettingOutlined style={{ fontSize: 48, color: '#52c41a', marginRight: '16px' }} />
          <div>
            <Title level={1} style={{ margin: 0 }}>系统设置</Title>
            <Text type="secondary" style={{ fontSize: 16 }}>配置管理、系统参数、安全设置</Text>
          </div>
        </div>
      </div>

      {/* 主要内容区 */}
      <Card style={{ marginBottom: '24px' }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="⚙️ 通用设置" key="general">
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="📝 基本信息" size="small">
                  <Form
                    form={form}
                    layout="vertical"
                    initialValues={systemConfig.general}
                  >
                    <Form.Item label="站点名称" name="siteName">
                      <Input />
                    </Form.Item>
                    <Form.Item label="站点描述" name="description">
                      <TextArea rows={3} />
                    </Form.Item>
                    <Form.Item label="语言" name="language">
                      <Select>
                        <Option value="zh-CN">简体中文</Option>
                        <Option value="en-US">English</Option>
                      </Select>
                    </Form.Item>
                    <Form.Item label="时区" name="timezone">
                      <Select>
                        <Option value="Asia/Shanghai">北京时间</Option>
                        <Option value="UTC">UTC</Option>
                      </Select>
                    </Form.Item>
                  </Form>
                </Card>
              </Col>

              <Col xs={24} lg={12}>
                <Card title="🚀 系统状态" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Alert
                      message="系统运行正常"
                      description="所有服务运行正常，性能良好"
                      type="success"
                      showIcon
                    />
                    <Divider />
                    <div>
                      <Text strong>CPU使用率</Text>
                      <Progress percent={67} size="small" />
                    </div>
                    <div>
                      <Text strong>内存使用</Text>
                      <Progress percent={45} size="small" />
                    </div>
                    <div>
                      <Text strong>磁盘使用</Text>
                      <Progress percent={82} size="small" />
                    </div>
                    <div>
                      <Text strong>数据库连接</Text>
                      <Badge status="success" text="正常" />
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="🔌 API配置" key="api">
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="🌐 API设置" size="small">
                  <Form
                    layout="vertical"
                    initialValues={systemConfig.api}
                  >
                    <Form.Item label="API基础URL" name="baseUrl">
                      <Input />
                    </Form.Item>
                    <Form.Item label="请求超时(毫秒)" name="timeout">
                      <Input type="number" />
                    </Form.Item>
                    <Form.Item label="重试次数" name="retries">
                      <Input type="number" />
                    </Form.Item>
                    <Form.Item label="速率限制(次/分钟)" name="rateLimit">
                      <Input type="number" />
                    </Form.Item>
                  </Form>
                </Card>
              </Col>

              <Col xs={24} lg={12}>
                <Card title="🤖 模型配置" size="small">
                  <List
                    dataSource={modelSettings}
                    renderItem={(model) => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={<Avatar>{model.name.charAt(0)}</Avatar>}
                          title={
                            <Space>
                              <Text strong>{model.name}</Text>
                              <Tag color="blue">{model.provider}</Tag>
                              {getStatusBadge(model.status)}
                            </Space>
                          }
                          description={
                            <Space direction="vertical" style={{ width: '100%' }} size="small">
                              <div>
                                <Text type="secondary">性能评分: </Text>
                                <Text strong>{model.performance}%</Text>
                              </div>
                              <div style={{ display: 'flex', gap: 16 }}>
                                <div>
                                  <Text type="secondary" style={{ fontSize: 12 }}>Temperature</Text>
                                  <Text style={{ fontSize: 12 }}>{model.config.temperature}</Text>
                                </div>
                                <div>
                                  <Text type="secondary" style={{ fontSize: 12 }}>Max Tokens</Text>
                                  <Text style={{ fontSize: 12 }}>{model.config.maxTokens}</Text>
                                </div>
                                <div>
                                  <Text type="secondary" style={{ fontSize: 12 }}>Top P</Text>
                                  <Text style={{ fontSize: 12 }}>{model.config.topP}</Text>
                                </div>
                              </div>
                            </Space>
                          }
                        />
                        <Button type="link">编辑</Button>
                      </List.Item>
                    )}
                  />
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="🔒 安全设置" key="security">
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="🛡️ 安全配置" size="small">
                  <Form
                    layout="vertical"
                    initialValues={systemConfig.security}
                  >
                    <Form.Item label="启用HTTPS" name="enableHttps" valuePropName="checked">
                      <Switch />
                    </Form.Item>
                    <Form.Item label="启用CORS" name="enableCORS" valuePropName="checked">
                      <Switch />
                    </Form.Item>
                    <Form.Item label="Token过期时间(秒)" name="tokenExpiry">
                      <Input type="number" />
                    </Form.Item>
                    <Form.Item label="会话超时时间(秒)" name="sessionTimeout">
                      <Input type="number" />
                    </Form.Item>
                  </Form>
                </Card>
              </Col>

              <Col xs={24} lg={12}>
                <Card title="👥 用户管理" size="small">
                  <List
                    dataSource={users}
                    renderItem={(user) => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={<Avatar icon={<UserOutlined />} />}
                          title={
                            <Space>
                              <Text strong>{user.name}</Text>
                              <Tag color={user.role === 'admin' ? 'red' : 'blue'}>
                                {user.role === 'admin' ? '管理员' : '用户'}
                              </Tag>
                              {getStatusBadge(user.status)}
                            </Space>
                          }
                          description={
                            <div>
                              <Text type="secondary">{user.email}</Text>
                              <br />
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                最后登录: {user.lastLogin}
                              </Text>
                            </div>
                          }
                        />
                        <Space>
                          <Button type="link" size="small">编辑</Button>
                          <Button type="link" size="small" danger>
                            删除
                          </Button>
                        </Space>
                      </List.Item>
                    )}
                  />
                  <div style={{ textAlign: 'center', marginTop: '16px' }}>
                    <Button type="dashed" icon={<UserOutlined />}>
                      添加用户
                    </Button>
                  </div>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="📢 通知设置" key="notifications">
            <Card title="🔔 通知配置" size="small">
              <Form
                layout="vertical"
                initialValues={systemConfig.notifications}
              >
                <Row gutter={[16, 16]}>
                  <Col xs={24} lg={12}>
                    <Title level={5}>通知方式</Title>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Form.Item label="邮件通知" name="email" valuePropName="checked">
                        <Switch />
                      </Form.Item>
                      <Form.Item label="浏览器通知" name="browser" valuePropName="checked">
                        <Switch />
                      </Form.Item>
                      <Form.Item label="移动端通知" name="mobile" valuePropName="checked">
                        <Switch />
                      </Form.Item>
                    </Space>
                  </Col>

                  <Col xs={24} lg={12}>
                    <Title level={5}>通知频率</Title>
                    <Form.Item name="frequency">
                      <Radio.Group>
                        <Radio value="realtime">实时</Radio>
                        <Radio value="hourly">每小时</Radio>
                        <Radio value="daily">每日</Radio>
                        <Radio value="weekly">每周</Radio>
                      </Radio.Group>
                    </Form.Item>
                  </Col>
                </Row>

                <Divider />

                <Title level={5}>通知类型</Title>
                <Row gutter={[16, 16]}>
                  <Col xs={24} lg={8}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Checkbox defaultChecked>系统更新</Checkbox>
                      <Checkbox defaultChecked>安全警报</Checkbox>
                      <Checkbox>性能警告</Checkbox>
                    </Space>
                  </Col>
                  <Col xs={24} lg={8}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Checkbox defaultChecked>用户活动</Checkbox>
                      <Checkbox>备份提醒</Checkbox>
                      <Checkbox>维护通知</Checkbox>
                    </Space>
                  </Col>
                  <Col xs={24} lg={8}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Checkbox>营销信息</Checkbox>
                      <Checkbox>报告生成</Checkbox>
                      <Checkbox defaultChecked>错误通知</Checkbox>
                    </Space>
                  </Col>
                </Row>
              </Form>
            </Card>
          </TabPane>

          <TabPane tab="💾 数据管理" key="data">
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="📊 数据统计" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text strong>数据库大小</Text>
                      <Text style={{ display: 'block', fontSize: '24px', color: '#1890ff' }}>2.4 GB</Text>
                    </div>
                    <div>
                      <Text strong>用户数据</Text>
                      <Text style={{ display: 'block', fontSize: '16px', color: '#52c41a' }}>15,420 条记录</Text>
                    </div>
                    <div>
                      <Text strong>对话记录</Text>
                      <Text style={{ display: 'block', fontSize: '16px', color: '#fa8c16' }}>45,780 条记录</Text>
                    </div>
                    <div>
                      <Text strong>缓存大小</Text>
                      <Text style={{ display: 'block', fontSize: '16px', color: '#722ed1' }}>156 MB</Text>
                    </div>
                  </Space>
                </Card>
              </Col>

              <Col xs={24} lg={12}>
                <Card title="🗂️ 数据操作" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Button
                      type="primary"
                      icon={<CloudUploadOutlined />}
                      style={{ width: '100%' }}
                    >
                      备份数据库
                    </Button>
                    <Button
                      icon={<DatabaseOutlined />}
                      style={{ width: '100%' }}
                    >
                      清理缓存
                    </Button>
                    <Button
                      icon={<ReloadOutlined />}
                      style={{ width: '100%' }}
                    >
                      重建索引
                    </Button>
                    <Upload>
                      <Button
                        icon={<CloudUploadOutlined />}
                        style={{ width: '100%' }}
                      >
                        导入数据
                      </Button>
                    </Upload>
                  </Space>
                </Card>
              </Col>
            </Row>

            <Card title="📋 操作日志" size="small" style={{ marginTop: '16px' }}>
              <List
                dataSource={[
                  { action: '用户登录', user: '张三', time: '2024-01-15 10:30:15', result: '成功' },
                  { action: '数据备份', user: '系统', time: '2024-01-15 02:00:00', result: '成功' },
                  { action: '配置修改', user: '李四', time: '2024-01-14 16:45:30', result: '成功' },
                  { action: '密码重置', user: '王五', time: '2024-01-14 09:20:45', result: '失败' }
                ]}
                renderItem={(log) => (
                  <List.Item>
                    <List.Item.Meta
                      title={
                        <Space>
                          <Text strong>{log.action}</Text>
                          <Tag color={log.result === '成功' ? 'green' : 'red'}>
                            {log.result}
                          </Tag>
                        </Space>
                      }
                      description={
                        <Space>
                          <Text type="secondary">操作人: {log.user}</Text>
                          <Text type="secondary">时间: {log.time}</Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          </TabPane>
        </Tabs>

        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <Space>
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>
              保存设置
            </Button>
            <Button icon={<ReloadOutlined />} onClick={handleReset}>
              重置
            </Button>
          </Space>
        </div>
      </Card>
    </div>
  );
};