import React, { useState, useEffect } from 'react';
import {
  Drawer,
  List,
  Button,
  Badge,
  Tooltip,
  Divider,
  Space,
  Typography,
  Card,
  Image,
  InputNumber,
  Tag,
  Empty,
  FloatButton,
  Dropdown,
  Modal,
  message,
  Spin
} from 'antd';
import {
  ShoppingCartOutlined,
  DeleteOutlined,
  PlusOutlined,
  MinusOutlined,
  EyeOutlined,
  HeartOutlined,
  ShareAltOutlined,
  CloseOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  GiftOutlined,
  TruckOutlined,
  CrownOutlined,
  PercentageOutlined
} from '@ant-design/icons';
import { ShoppingApiService, CartItem, CartResponse, PlatformType, Product } from '../../services/shoppingApi';

const { Text, Title } = Typography;

interface ShoppingCartQuickAccessProps {
  userId?: number;
  cartItemsCount?: number;
  onCheckout?: (items: CartItem[]) => void;
  onRemoveItem?: (itemId: number) => void;
  onUpdateQuantity?: (itemId: number, quantity: number) => void;
  onToggleSelection?: (itemId: number) => void;
  className?: string;
}

const ShoppingCartQuickAccess: React.FC<ShoppingCartQuickAccessProps> = ({
  userId = 1,
  cartItemsCount = 0,
  onCheckout,
  onRemoveItem,
  onUpdateQuantity,
  onToggleSelection,
  className = ''
}) => {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [cartData, setCartData] = useState<CartResponse | null>(null);
  const [loading, setLoading] = useState(false);

  // 加载购物车数据
  useEffect(() => {
    loadCartData();
  }, [userId]);

  // 当抽屉打开时重新加载购物车数据
  useEffect(() => {
    if (isDrawerOpen) {
      loadCartData();
    }
  }, [isDrawerOpen, userId]);

  // 加载购物车数据
  const loadCartData = async () => {
    setLoading(true);
    try {
      const response = await ShoppingApiService.getCart(userId);
      setCartData(response);
      setCartItems(response.items);
    } catch (error) {
      console.error('加载购物车失败:', error);
      message.error('加载购物车失败');

      // 设置空购物车作为后备
      setCartData({
        items: [],
        total_amount: 0,
        total_discount: 0,
        final_amount: 0,
        item_count: 0,
        selected_count: 0
      });
      setCartItems([]);
    } finally {
      setLoading(false);
    }
  };

  const getPlatformConfig = (platform: PlatformType) => {
    const configs = {
      [PlatformType.JD]: { name: '京东', color: '#e4393c' },
      [PlatformType.TAOBAO]: { name: '淘宝', color: '#ff6a00' },
      [PlatformType.PDD]: { name: '拼多多', color: '#e02e24' },
      [PlatformType.XIAOHONGSHU]: { name: '小红书', color: '#fe2c55' },
      [PlatformType.DOUYIN]: { name: '抖音', color: '#69c9ff' },
      [PlatformType.OTHER]: { name: '其他', color: '#8c8c8c' }
    };
    return configs[platform] || configs[PlatformType.OTHER];
  };

  const formatPrice = (price: number) => {
    return `¥${price.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  // 使用cartData中的计算值，如果不可用则计算
  const selectedItemsCount = cartData?.selected_count || cartItems.filter(item => item.selected).length;
  const subtotal = cartData?.total_amount || cartItems
    .filter(item => item.selected)
    .reduce((sum, item) => sum + (item.product.price || 0) * item.quantity, 0);
  const savings = cartData?.total_discount || cartItems
    .filter(item => item.selected)
    .reduce((sum, item) => {
      const discount = item.product.original_price && item.product.original_price > (item.product.price || 0)
        ? (item.product.original_price - (item.product.price || 0)) * item.quantity
        : 0;
      return sum + discount;
    }, 0);

  const handleQuantityChange = async (itemId: number, newQuantity: number) => {
    if (newQuantity < 1) return;

    try {
      await ShoppingApiService.updateCartQuantity(userId, itemId, newQuantity);
      setCartItems(prev =>
        prev.map(item =>
          item.id === itemId ? { ...item, quantity: newQuantity } : item
        )
      );
      onUpdateQuantity?.(itemId, newQuantity);
      message.success('数量已更新');
    } catch (error) {
      console.error('更新数量失败:', error);
      message.error('更新数量失败');
    }
  };

  const handleRemoveItem = async (itemId: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要从购物车中删除这个商品吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await ShoppingApiService.removeFromCart(userId, itemId);
          setCartItems(prev => prev.filter(item => item.id !== itemId));
          onRemoveItem?.(itemId);
          message.success('商品已删除');
          // 重新加载购物车数据以更新统计信息
          loadCartData();
        } catch (error) {
          console.error('删除商品失败:', error);
          message.error('删除商品失败');
        }
      }
    });
  };

  const handleToggleSelection = (itemId: number) => {
    setCartItems(prev =>
      prev.map(item =>
        item.id === itemId ? { ...item, selected: !item.selected } : item
      )
    );
    onToggleSelection?.(itemId);
  };

  const handleSelectAll = () => {
    const allSelected = cartItems.every(item => item.selected);
    setCartItems(prev =>
      prev.map(item => ({ ...item, selected: !allSelected }))
    );
  };

  const getStockStatusTag = (status: string) => {
    switch (status) {
      case 'in_stock':
        return <Tag color="success">有货</Tag>;
      case 'low_stock':
        return <Tag color="warning">库存紧张</Tag>;
      case 'out_of_stock':
        return <Tag color="error">缺货</Tag>;
      default:
        return <Tag color="default">未知</Tag>;
    }
  };

  const renderCartItem = (item: CartItem) => {
    const platformConfig = getPlatformConfig(item.product.platform);
    const discount = item.product.original_price && item.product.original_price > (item.product.price || 0)
      ? Math.round(((item.product.original_price - (item.product.price || 0)) / item.product.original_price) * 100)
      : 0;

    return (
      <Card
        key={item.id}
        size="small"
        style={{
          marginBottom: '12px',
          borderRadius: '12px',
          border: item.selected ? '2px solid #1890ff' : '1px solid #f0f0f0',
          backgroundColor: item.selected ? '#f6ffed' : '#fff'
        }}
        bodyStyle={{ padding: '12px' }}
      >
        <div style={{ display: 'flex', gap: '12px' }}>
          {/* 选择框 */}
          <div style={{ display: 'flex', alignItems: 'flex-start', paddingTop: '8px' }}>
            <input
              type="checkbox"
              checked={item.selected}
              onChange={() => handleToggleSelection(item.id)}
              style={{
                width: '16px',
                height: '16px',
                cursor: 'pointer'
              }}
            />
          </div>

          {/* 商品图片 */}
          <div style={{ flexShrink: 0 }}>
            {item.product.image_url ? (
              <Image
                src={item.product.image_url}
                alt={item.product.title}
                width={80}
                height={80}
                style={{
                  borderRadius: '8px',
                  objectFit: 'cover'
                }}
                preview={false}
              />
            ) : (
              <div
                style={{
                  width: '80px',
                  height: '80px',
                  borderRadius: '8px',
                  background: '#f5f5f5',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#8c8c8c'
                }}
              >
                📦
              </div>
            )}
          </div>

          {/* 商品信息 */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ flex: 1, marginRight: '12px' }}>
                {/* 商品标题和标签 */}
                <div style={{ marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <Tag
                      color={platformConfig.color}
                      style={{
                        borderRadius: '4px',
                        fontSize: '10px',
                        padding: '2px 6px',
                        fontWeight: 600
                      }}
                    >
                      {platformConfig.name}
                    </Tag>
                    {getStockStatusTag(item.product.stock_status || 'in_stock')}
                    {discount > 0 && (
                      <Tag color="#ff4d4f" style={{ borderRadius: '4px', fontSize: '10px' }}>
                        -{discount}%
                      </Tag>
                    )}
                  </div>
                  <h4 style={{
                    margin: 0,
                    fontSize: '13px',
                    fontWeight: 500,
                    color: '#262626',
                    lineHeight: '1.4',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden'
                  }}>
                    {item.product.title}
                  </h4>
                </div>

                {/* 价格信息 */}
                <div style={{ marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                    <Text strong style={{ fontSize: '16px', color: '#ff4d4f' }}>
                      {formatPrice(item.product.price || 0)}
                    </Text>
                    {item.product.original_price && item.product.original_price > (item.product.price || 0) && (
                      <Text delete style={{ fontSize: '12px', color: '#8c8c8c' }}>
                        {formatPrice(item.product.original_price)}
                      </Text>
                    )}
                  </div>
                </div>
              </div>

              {/* 操作区域 */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
                {/* 数量调整 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Button
                    type="text"
                    size="small"
                    icon={<MinusOutlined />}
                    style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '4px',
                      border: '1px solid #d9d9d9'
                    }}
                    onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                    disabled={item.quantity <= 1}
                  />
                  <InputNumber
                    value={item.quantity}
                    onChange={(value) => handleQuantityChange(item.id, value || 1)}
                    min={1}
                    max={99}
                    style={{
                      width: '50px',
                      textAlign: 'center'
                    }}
                    controls={false}
                  />
                  <Button
                    type="text"
                    size="small"
                    icon={<PlusOutlined />}
                    style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '4px',
                      border: '1px solid #d9d9d9'
                    }}
                    onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                  />
                </div>

                {/* 快捷操作 */}
                <div style={{ display: 'flex', gap: '4px' }}>
                  <Tooltip title="查看详情">
                    <Button
                      type="text"
                      size="small"
                      icon={<EyeOutlined />}
                      style={{ fontSize: '12px' }}
                    />
                  </Tooltip>
                  <Tooltip title="移除">
                    <Button
                      type="text"
                      size="small"
                      icon={<DeleteOutlined />}
                      style={{ fontSize: '12px', color: '#ff4d4f' }}
                      onClick={() => handleRemoveItem(item.id)}
                    />
                  </Tooltip>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>
    );
  };

  const renderDrawerContent = () => (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 头部 */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid #f0f0f0',
        background: '#fafafa'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Title level={4} style={{ margin: 0, fontSize: '16px' }}>
              <ShoppingCartOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
              购物车
            </Title>
            <Badge count={cartItems.length} style={{ backgroundColor: '#52c41a' }} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Button
              type="text"
              size="small"
              onClick={handleSelectAll}
            >
              {cartItems.every(item => item.selected) ? '取消全选' : '全选'}
            </Button>
            <Button
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={() => setIsDrawerOpen(false)}
            />
          </div>
        </div>
      </div>

      {/* 购物车列表 */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: '16px 20px'
      }}>
        {cartItems.length > 0 ? (
          <>
            {cartItems.map(renderCartItem)}
          </>
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="购物车是空的"
            style={{ marginTop: '100px' }}
          >
            <Button type="primary" onClick={() => setIsDrawerOpen(false)}>
              去购物
            </Button>
          </Empty>
        )}
      </div>

      {/* 底部结算栏 */}
      {cartItems.length > 0 && (
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid #f0f0f0',
          background: '#fff',
          boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.06)'
        }}>
          <div style={{ marginBottom: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <Text type="secondary">已选 {selectedItemsCount} 件商品</Text>
              <Text type="secondary">小计: {formatPrice(subtotal)}</Text>
            </div>
            {savings > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text type="success" style={{ fontSize: '12px' }}>
                  <GiftOutlined style={{ marginRight: '4px' }} />
                  已节省 {formatPrice(savings)}
                </Text>
              </div>
            )}
          </div>

          <Button
            type="primary"
            size="large"
            block
            style={{
              height: '48px',
              fontSize: '16px',
              fontWeight: 600,
              background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
              border: 'none',
              borderRadius: '8px'
            }}
            disabled={selectedItemsCount === 0}
            onClick={() => {
              const selectedItems = cartItems.filter(item => item.selected);
              onCheckout?.(selectedItems);
              setIsDrawerOpen(false);
            }}
          >
            <CrownOutlined style={{ marginRight: '8px' }} />
            去结算 ({formatPrice(subtotal)})
          </Button>

          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '8px',
            fontSize: '11px',
            color: '#8c8c8c'
          }}>
            <span>满99元免运费</span>
            <span>支持7天无理由退货</span>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className={`shopping-cart-quick-access ${className}`}>
      {/* 浮动购物车按钮 */}
      <FloatButton
        icon={<ShoppingCartOutlined />}
        badge={{ count: cartItemsCount }}
        type="primary"
        style={{
          right: 24,
          bottom: 80,
          width: '56px',
          height: '56px',
          background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
          boxShadow: '0 4px 12px rgba(24, 144, 255, 0.4)'
        }}
        onClick={() => setIsDrawerOpen(true)}
      />

      {/* 购物车抽屉 */}
      <Drawer
        title={null}
        placement="right"
        open={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        width={420}
        styles={{
          body: { padding: 0 },
          mask: { backgroundColor: 'rgba(0, 0, 0, 0.5)' }
        }}
        closable={false}
      >
        {renderDrawerContent()}
      </Drawer>
    </div>
  );
};

export default ShoppingCartQuickAccess;