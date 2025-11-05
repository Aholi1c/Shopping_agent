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
  Select,
  DatePicker,
  Table
} from 'antd';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar
} from 'recharts';
import {
  BarChartOutlined,
  RiseOutlined,
  UserOutlined,
  ShoppingOutlined,
  MessageOutlined,
  DatabaseOutlined,
  ThunderboltOutlined,
  EyeOutlined,
  DownloadOutlined,
  FilterOutlined,
  CalendarOutlined,
  GlobalOutlined,
  TrophyOutlined,
  FireOutlined,
  StarOutlined,
  AlertOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface AnalyticsProps {
  userId?: number;
}

export const Analytics: React.FC<AnalyticsProps> = ({ userId = 1 }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [timeRange, setTimeRange] = useState('7d');

  // 模拟数据
  const overviewStats = {
    totalUsers: 15420,
    activeUsers: 3890,
    totalConversations: 45780,
    shoppingRequests: 12340,
    avgResponseTime: 1.2,
    satisfaction: 94.5
  };

  const userGrowthData = [
    { date: '2024-01', users: 12000, newUsers: 1200 },
    { date: '2024-02', users: 13200, newUsers: 1200 },
    { date: '2024-03', users: 14500, newUsers: 1300 },
    { date: '2024-04', users: 15100, newUsers: 600 },
    { date: '2024-05', users: 15420, newUsers: 320 }
  ];

  const categoryData = [
    { name: '电子产品', value: 35, color: '#1890ff' },
    { name: '服装鞋帽', value: 25, color: '#52c41a' },
    { name: '家居用品', value: 20, color: '#fa8c16' },
    { name: '美妆护肤', value: 12, color: '#eb2f96' },
    { name: '运动户外', value: 8, color: '#722ed1' }
  ];

  const satisfactionTrends = [
    { date: '周一', satisfaction: 92, responses: 450 },
    { date: '周二', satisfaction: 94, responses: 520 },
    { date: '周三', satisfaction: 93, responses: 480 },
    { date: '周四', satisfaction: 95, responses: 510 },
    { date: '周五', satisfaction: 96, responses: 550 },
    { date: '周六', satisfaction: 94, responses: 380 },
    { date: '周日', satisfaction: 93, responses: 320 }
  ];

  const topProducts = [
    {
      id: 1,
      name: 'iPhone 15 Pro',
      category: '电子产品',
      views: 15420,
      purchases: 2340,
      conversion: 15.2,
      trend: 'up'
    },
    {
      id: 2,
      name: 'Nike Air Max',
      category: '服装鞋帽',
      views: 12340,
      purchases: 1890,
      conversion: 15.3,
      trend: 'up'
    },
    {
      id: 3,
      name: '戴森吸尘器',
      category: '家居用品',
      views: 9870,
      purchases: 1245,
      conversion: 12.6,
      trend: 'stable'
    },
    {
      id: 4,
      name: '兰蔻面霜',
      category: '美妆护肤',
      views: 8760,
      purchases: 980,
      conversion: 11.2,
      trend: 'down'
    },
    {
      id: 5,
      name: '瑜伽垫',
      category: '运动户外',
      views: 7650,
      purchases: 890,
      conversion: 11.6,
      trend: 'up'
    }
  ];

  const userBehavior = [
    {
      behavior: '商品搜索',
      count: 45780,
      percentage: 42,
      trend: '+12%'
    },
    {
      behavior: '价格对比',
      count: 23450,
      percentage: 22,
      trend: '+8%'
    },
    {
      behavior: '图片识别',
      count: 18900,
      percentage: 17,
      trend: '+25%'
    },
    {
      behavior: '查看评价',
      count: 12340,
      percentage: 11,
      trend: '+5%'
    },
    {
      behavior: '购买咨询',
      count: 7890,
      percentage: 8,
      trend: '+15%'
    }
  ];

  const getTrendIcon = (trend: string) => {
    const icons = {
      up: <RiseOutlined style={{ color: '#52c41a' }} />,
      down: <RiseOutlined style={{ color: '#ff4d4f', transform: 'rotate(180deg)' }} />,
      stable: <div style={{ width: 12, height: 2, backgroundColor: '#d9d9d9' }} />
    };
    return icons[trend as keyof typeof icons] || icons.stable;
  };

  return (
    <div style={{ padding: '24px', maxWidth: 1600, margin: '0 auto' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
          <BarChartOutlined style={{ fontSize: 48, color: '#1890ff', marginRight: '16px' }} />
          <div>
            <Title level={1} style={{ margin: 0 }}>数据分析中心</Title>
            <Text type="secondary" style={{ fontSize: 16 }}>用户行为与市场趋势深度分析</Text>
          </div>
        </div>
      </div>

      {/* 时间范围选择 */}
      <Card style={{ marginBottom: '24px' }}>
        <Space>
          <Text strong>时间范围:</Text>
          <Select value={timeRange} onChange={setTimeRange} style={{ width: 120 }}>
            <Option value="1d">今天</Option>
            <Option value="7d">最近7天</Option>
            <Option value="30d">最近30天</Option>
            <Option value="90d">最近90天</Option>
          </Select>
          <RangePicker />
          <Button icon={<FilterOutlined />}>自定义筛选</Button>
          <Button icon={<DownloadOutlined />}>导出报告</Button>
        </Space>
      </Card>

      {/* 核心指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '32px' }}>
        <Col xs={24} sm={12} md={4}>
          <Card>
            <Statistic
              title="总用户数"
              value={overviewStats.totalUsers}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>较上月</Text>
              <Text type="success" style={{ fontSize: 12, marginLeft: 4 }}>+12.5%</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={4}>
          <Card>
            <Statistic
              title="活跃用户"
              value={overviewStats.activeUsers}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>活跃率</Text>
              <Text type="success" style={{ fontSize: 12, marginLeft: 4 }}>25.2%</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={4}>
          <Card>
            <Statistic
              title="对话总数"
              value={overviewStats.totalConversations}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>较昨日</Text>
              <Text type="success" style={{ fontSize: 12, marginLeft: 4 }}>+8.3%</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={4}>
          <Card>
            <Statistic
              title="购物请求"
              value={overviewStats.shoppingRequests}
              prefix={<ShoppingOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>转化率</Text>
              <Text type="success" style={{ fontSize: 12, marginLeft: 4 }}>26.9%</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={4}>
          <Card>
            <Statistic
              title="响应时间"
              value={overviewStats.avgResponseTime}
              suffix="秒"
              precision={1}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#13c2c2' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>较上周</Text>
              <Text type="success" style={{ fontSize: 12, marginLeft: 4 }}>-0.3s</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={4}>
          <Card>
            <Statistic
              title="满意度"
              value={overviewStats.satisfaction}
              suffix="%"
              precision={1}
              prefix={<StarOutlined />}
              valueStyle={{ color: '#eb2f96' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>评价数</Text>
              <Text type="success" style={{ fontSize: 12, marginLeft: 4 }}>3,240</Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 主要内容区 */}
      <Card style={{ marginBottom: '24px' }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="📊 数据概览" key="overview">
            <Row gutter={[16, 16]}>
              {/* 用户增长趋势 */}
              <Col xs={24} lg={12}>
                <Card title="👥 用户增长趋势" size="small">
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={userGrowthData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="users" stroke="#1890ff" name="总用户数" />
                      <Line type="monotone" dataKey="newUsers" stroke="#52c41a" name="新增用户" />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              </Col>

              {/* 热门品类分布 */}
              <Col xs={24} lg={12}>
                <Card title="🏷️ 热门品类分布" size="small">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={categoryData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(props: any) => `${props.name} ${(props.percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {categoryData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
            </Row>

            {/* 用户行为分析 */}
            <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
              <Col xs={24} lg={16}>
                <Card title="🔍 用户行为分析" size="small">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={userBehavior}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="behavior" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#1890ff" />
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
              </Col>

              <Col xs={24} lg={8}>
                <Card title="⭐ 满意度趋势" size="small">
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={satisfactionTrends}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis domain={[90, 100]} />
                      <Tooltip />
                      <Line type="monotone" dataKey="satisfaction" stroke="#52c41a" />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="🛍️ 商品分析" key="products">
            <Card title="🔥 热门商品排行" size="small">
              <Table
                dataSource={topProducts}
                pagination={false}
                columns={[
                  {
                    title: '商品名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (text, record) => (
                      <Space>
                        <Text strong>{text}</Text>
                        <Tag color="blue">{record.category}</Tag>
                      </Space>
                    )
                  },
                  {
                    title: '浏览量',
                    dataIndex: 'views',
                    key: 'views',
                    render: (text) => text.toLocaleString()
                  },
                  {
                    title: '购买量',
                    dataIndex: 'purchases',
                    key: 'purchases',
                    render: (text) => text.toLocaleString()
                  },
                  {
                    title: '转化率',
                    dataIndex: 'conversion',
                    key: 'conversion',
                    render: (text) => `${text}%`
                  },
                  {
                    title: '趋势',
                    dataIndex: 'trend',
                    key: 'trend',
                    render: (text) => getTrendIcon(text)
                  }
                ]}
              />
            </Card>
          </TabPane>

          <TabPane tab="👥 用户分析" key="users">
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="🎯 用户画像" size="small">
                  <Space direction="vertical" style={{ width: '100%' }} size="large">
                    <div>
                      <Text strong>年龄分布</Text>
                      <div style={{ marginTop: 8 }}>
                        <Progress percent={35} strokeColor="#1890ff" format={() => '18-25岁 35%'} />
                        <Progress percent={30} strokeColor="#52c41a" format={() => '26-35岁 30%'} />
                        <Progress percent={20} strokeColor="#fa8c16" format={() => '36-45岁 20%'} />
                        <Progress percent={15} strokeColor="#eb2f96" format={() => '45岁以上 15%'} />
                      </div>
                    </div>

                    <div>
                      <Text strong>地域分布</Text>
                      <div style={{ marginTop: 8 }}>
                        <Space wrap>
                          <Tag color="blue">北京 18%</Tag>
                          <Tag color="green">上海 15%</Tag>
                          <Tag color="orange">广州 12%</Tag>
                          <Tag color="purple">深圳 10%</Tag>
                          <Tag color="cyan">杭州 8%</Tag>
                          <Tag>其他 37%</Tag>
                        </Space>
                      </div>
                    </div>
                  </Space>
                </Card>
              </Col>

              <Col xs={24} lg={12}>
                <Card title="💰 消费能力" size="small">
                  <Space direction="vertical" style={{ width: '100%' }} size="large">
                    <div>
                      <Text strong>客单价分布</Text>
                      <div style={{ marginTop: 8 }}>
                        <Progress percent={25} strokeColor="#52c41a" format={() => '0-100元 25%'} />
                        <Progress percent={35} strokeColor="#1890ff" format={() => '100-500元 35%'} />
                        <Progress percent={25} strokeColor="#fa8c16" format={() => '500-1000元 25%'} />
                        <Progress percent={15} strokeColor="#eb2f96" format={() => '1000元以上 15%'} />
                      </div>
                    </div>

                    <div>
                      <Text strong>购买频次</Text>
                      <div style={{ marginTop: 8 }}>
                        <Progress percent={20} strokeColor="#722ed1" format={() => '每周多次 20%'} />
                        <Progress percent={40} strokeColor="#13c2c2" format={() => '每月2-3次 40%'} />
                        <Progress percent={25} strokeColor="#1890ff" format={() => '每月1次 25%'} />
                        <Progress percent={15} strokeColor="#fa8c16" format={() => '偶尔购买 15%'} />
                      </div>
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="📈 趋势预测" key="trends">
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <RiseOutlined style={{ fontSize: 64, color: '#d9d9d9', marginBottom: '16px' }} />
              <Title level={3} type="secondary">趋势预测功能</Title>
              <Text type="secondary" style={{ display: 'block', marginBottom: '24px' }}>
                基于机器学习的市场趋势、用户行为、销售预测等功能正在开发中
              </Text>
              <Space>
                <Button type="primary">销售预测</Button>
                <Button>用户流失预警</Button>
                <Button>市场趋势分析</Button>
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
              icon={<DownloadOutlined />}
              size="large"
              style={{ width: '100%', height: '60px' }}
            >
              生成报告
            </Button>
          </Col>
          <Col xs={24} sm={6}>
            <Button
              type="default"
              icon={<FilterOutlined />}
              size="large"
              style={{ width: '100%', height: '60px' }}
            >
              自定义分析
            </Button>
          </Col>
          <Col xs={24} sm={6}>
            <Button
              type="dashed"
              icon={<CalendarOutlined />}
              size="large"
              style={{ width: '100%', height: '60px' }}
            >
              定时报告
            </Button>
          </Col>
          <Col xs={24} sm={6}>
            <Button
              type="default"
              icon={<GlobalOutlined />}
              size="large"
              style={{ width: '100%', height: '60px' }}
            >
              实时监控
            </Button>
          </Col>
        </Row>
      </Card>
    </div>
  );
};