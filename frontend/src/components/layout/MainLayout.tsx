import React, { useState } from 'react';
import {
  Layout,
  Menu,
  Avatar,
  Dropdown,
  Badge,
  Input,
  Button,
  Space,
  Typography,
  theme,
  Card,
  Row,
  Col,
  Statistic,
  List,
  Tag,
  Divider
} from 'antd';
import {
  ShoppingOutlined,
  MessageOutlined,
  UserOutlined,
  ShoppingCartOutlined,
  SearchOutlined,
  BellOutlined,
  SettingOutlined,
  PictureOutlined,
  AudioOutlined,
  SendOutlined,
  BulbOutlined,
  EyeOutlined,
  BarChartOutlined,
  SecurityScanOutlined,
  AimOutlined,
  ExperimentOutlined,
  DatabaseOutlined,
  TeamOutlined,
  ApiOutlined,
  CloudServerOutlined,
  MonitorOutlined,
  MobileOutlined,
  DollarOutlined,
  TrophyOutlined,
  FireOutlined,
  StarOutlined,
  ThunderboltOutlined,
  HeartOutlined,
  ShopOutlined,
  PercentageOutlined,
  GlobalOutlined
} from '@ant-design/icons';

const { Header, Sider, Content, Footer } = Layout;
const { Search } = Input;
const { Text } = Typography;

interface MainLayoutProps {
  children: React.ReactNode;
  activeView: 'chat' | 'shopping' | 'dashboard' | 'memory' | 'agents' | 'analytics' | 'settings';
  onViewChange: (view: 'chat' | 'shopping' | 'dashboard' | 'memory' | 'agents' | 'analytics' | 'settings') => void;
  cartItemsCount?: number;
}

const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  activeView,
  onViewChange,
  cartItemsCount = 0
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const userMenuItems = [
    {
      key: 'profile',
      label: '个人中心',
      icon: <UserOutlined />,
    },
    {
      key: 'settings',
      label: '设置',
      icon: <SettingOutlined />,
    },
    {
      key: 'logout',
      label: '退出登录',
      icon: <UserOutlined />,
    },
  ];

  const mainMenuItems = [
    {
      key: 'dashboard',
      icon: <MonitorOutlined />,
      label: '仪表板',
    },
    {
      key: 'chat',
      icon: <MessageOutlined />,
      label: '智能对话',
    },
    {
      key: 'shopping',
      icon: <ShoppingOutlined />,
      label: '购物助手',
    },
    {
      key: 'memory',
      icon: <DatabaseOutlined />,
      label: '记忆系统',
    },
    {
      key: 'agents',
      icon: <TeamOutlined />,
      label: '多智能体',
    },
    {
      key: 'analytics',
      icon: <BarChartOutlined />,
      label: '数据分析',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  const quickActions = [
    { icon: <PictureOutlined />, label: '图片分析' },
    { icon: <AudioOutlined />, label: '语音输入' },
    { icon: <ShoppingCartOutlined />, label: '购物车' },
    { icon: <BulbOutlined />, label: 'RAG搜索' },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 顶部导航栏 */}
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        background: colorBgContainer,
        padding: '0 24px',
        borderBottom: '1px solid #f0f0f0',
        position: 'fixed',
        top: 0,
        width: '100%',
        zIndex: 1000,
        height: 64
      }}>
        {/* Logo和标题 */}
        <div style={{ display: 'flex', alignItems: 'center', marginRight: 24 }}>
          <div style={{
            width: 40,
            height: 40,
            background: 'linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%)',
            borderRadius: 8,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginRight: 12
          }}>
            <ShoppingOutlined style={{ color: 'white', fontSize: 20 }} />
          </div>
          <div>
            <Text strong style={{ fontSize: 18, color: '#1a1a1a' }}>
              智能购物助手
            </Text>
            <div style={{ fontSize: 12, color: '#666' }}>
              Powered by GLM-4.5
            </div>
          </div>
        </div>

        {/* 搜索栏 */}
        <div style={{ flex: 1, maxWidth: 500, margin: '0 24px' }}>
          <Search
            placeholder="搜索商品、品牌或描述..."
            allowClear
            enterButton={<SearchOutlined />}
            size="large"
            style={{
              borderRadius: 20,
            }}
          />
        </div>

        {/* 右侧功能区 */}
        <Space size="large">
          {/* 快捷操作 */}
          {quickActions.map((action, index) => (
            <Button
              key={index}
              type="text"
              icon={action.icon}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                height: 'auto',
                padding: '8px 4px'
              }}
            >
              <div style={{ fontSize: 10 }}>{action.label}</div>
            </Button>
          ))}

          {/* 购物车 */}
          <Badge count={cartItemsCount} size="small">
            <Button
              type="primary"
              icon={<ShoppingCartOutlined />}
              size="large"
              style={{ borderRadius: 20 }}
            >
              购物车
            </Button>
          </Badge>

          {/* 通知 */}
          <Badge dot>
            <Button
              type="text"
              icon={<BellOutlined />}
              size="large"
            />
          </Badge>

          {/* 用户菜单 */}
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Avatar
              style={{ cursor: 'pointer', backgroundColor: '#87d068' }}
              size="large"
              icon={<UserOutlined />}
            />
          </Dropdown>
        </Space>
      </Header>

      <Layout style={{ marginTop: 64 }}>
        {/* 左侧功能菜单 */}
        <Sider
          width={280}
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          style={{
            background: colorBgContainer,
            borderRight: '1px solid #f0f0f0',
            position: 'fixed',
            left: 0,
            top: 64,
            bottom: 60,
            overflow: 'auto'
          }}
        >
          <div style={{ padding: '16px' }}>
            <Menu
              mode="inline"
              selectedKeys={[activeView]}
              items={mainMenuItems}
              onClick={({ key }) => onViewChange(key as any)}
              style={{ border: 'none' }}
            />

            {!collapsed && (
              <>
                <Divider style={{ margin: '16px 0' }} />

                {/* 功能状态面板 */}
                <div style={{ padding: '12px', background: '#f0f9ff', borderRadius: 8, marginBottom: 16 }}>
                  <Text strong style={{ fontSize: 14, color: '#1890ff' }}>✨ 系统状态</Text>
                  <div style={{ marginTop: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>API状态</Text>
                      <Badge status="success" text="正常" />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>知识库</Text>
                      <Badge status="success" text="已连接" />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>智能体</Text>
                      <Badge status="processing" text="运行中" />
                    </div>
                  </div>
                </div>

                {/* 快速统计 */}
                <div style={{ padding: '12px', background: '#f6ffed', borderRadius: 8 }}>
                  <Text strong style={{ fontSize: 14, color: '#52c41a' }}>📊 今日统计</Text>
                  <div style={{ marginTop: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>对话次数</Text>
                      <Text strong style={{ fontSize: 12 }}>247</Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>搜索请求</Text>
                      <Text strong style={{ fontSize: 12 }}>89</Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>活跃用户</Text>
                      <Text strong style={{ fontSize: 12 }}>23</Text>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </Sider>

        {/* 主内容区 */}
        <Layout style={{ marginLeft: collapsed ? 80 : 280, transition: 'margin-left 0.2s' }}>
          <Content
            style={{
              padding: '24px',
              minHeight: 'calc(100vh - 124px)',
              background: '#f0f2f5'
            }}
          >
            {children}
          </Content>
        </Layout>
      </Layout>

      {/* 底部状态栏 */}
      <Footer style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        background: colorBgContainer,
        borderTop: '1px solid #f0f0f0',
        padding: '6px 24px',
        zIndex: 999,
        height: 48,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <Space size="large">
          <Space>
            <Badge status="success" />
            <Text type="secondary" style={{ fontSize: 11 }}>
              系统运行正常
            </Text>
          </Space>
          <Text type="secondary" style={{ fontSize: 11 }}>
            GLM-4.5 | 响应时间: 1.2s | 准确率: 94.5%
          </Text>
          <Text type="secondary" style={{ fontSize: 11 }}>
            今日: 对话 247 次 | 用户 23 人 | 搜索 89 次
          </Text>
        </Space>

        <Space size="small">
          <Text type="secondary" style={{ fontSize: 10 }}>
            v2.1.0
          </Text>
          <Text type="secondary" style={{ fontSize: 10 }}>
            © 2024 AI Shopping Assistant
          </Text>
        </Space>
      </Footer>
    </Layout>
  );
};

export default MainLayout;