import React, { useState, useEffect, useCallback } from 'react';
import { Row, Col, Card, Space, Typography, BackTop, FloatButton, Affix, Button, message, Spin, Pagination } from 'antd';
import { ShoppingApiService, Product, SearchRequest, SearchResponse, PlatformType, CartItem } from '../../services/shoppingApi';
import {
  ArrowUpOutlined,
  CustomerServiceOutlined,
  FilterOutlined,
  SortAscendingOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import SmartSearchBox from './SmartSearchBox';
import CategoryNavigation from './CategoryNavigation';
import ProductCard from './ProductCard';
import ShoppingCartQuickAccess from './ShoppingCartQuickAccess';
import PersonalizedRecommendations from './PersonalizedRecommendations';
import SmartChatInterface from './SmartChatInterface';

const { Title, Text } = Typography;

// 使用API服务中的Product接口

interface ModernShoppingAssistantProps {
  userId?: number;
}

const ModernShoppingAssistant: React.FC<ModernShoppingAssistantProps> = ({ userId = 1 }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('relevance');
  const [filters, setFilters] = useState({
    platforms: [PlatformType.JD, PlatformType.TAOBAO, PlatformType.PDD],
    priceRange: [0, 10000],
    category: ''
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [cartItemsCount, setCartItemsCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);

  // 初始化加载购物车数据
  useEffect(() => {
    loadCartItems();
  }, [userId]);

  useEffect(() => {
    loadProducts();
  }, [selectedCategory, sortBy, filters, searchQuery, currentPage]);

  // 加载购物车数据
  const loadCartItems = async () => {
    try {
      const cartResponse = await ShoppingApiService.getCart(userId);
      setCartItemsCount(cartResponse.item_count);
    } catch (error) {
      console.error('加载购物车失败:', error);
    }
  };

  const loadProducts = async () => {
    setLoading(true);
    try {
      const searchRequest: SearchRequest = {
        query: searchQuery.trim(),
        platforms: filters.platforms.length > 0 ? filters.platforms : undefined,
        category: selectedCategory || filters.category || undefined,
        price_min: filters.priceRange[0] > 0 ? filters.priceRange[0] : undefined,
        price_max: filters.priceRange[1] < 10000 ? filters.priceRange[1] : undefined,
        sort_by: sortBy === 'default' ? 'relevance' : sortBy,
        page: currentPage,
        page_size: 20
      };

      const response = await ShoppingApiService.searchProducts(searchRequest);
      setProducts(response.products);
      setTotalCount(response.total_count);
      setHasNext(response.has_next);

    } catch (error) {
      console.error('加载商品失败:', error);
      message.error('加载商品失败，请稍后重试');
      setProducts([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (query: string, searchFilters: any) => {
    setSearchQuery(query);
    setFilters(prev => ({ ...prev, ...searchFilters }));
    setCurrentPage(1); // 重置到第一页
  };

  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
    setCurrentPage(1); // 重置到第一页
  };

  const handleSortChange = (sort: string) => {
    setSortBy(sort);
    setCurrentPage(1); // 重置到第一页
  };

  const handleAddToCart = async (product: Product) => {
    try {
      await ShoppingApiService.addToCart(userId, product.id);
      setCartItemsCount(prev => prev + 1);
      message.success('已添加到购物车');
    } catch (error) {
      console.error('添加到购物车失败:', error);
      message.error('添加到购物车失败');
    }
  };

  const handleToggleFavorite = (product: Product) => {
    // 这里可以添加收藏逻辑
    console.log('切换收藏状态:', product);
  };

  const handleViewDetails = (product: Product) => {
    // 这里可以添加查看详情逻辑
    console.log('查看商品详情:', product);
  };

  const handleCompare = (product: Product) => {
    // 这里可以添加对比逻辑
    console.log('添加到对比:', product);
  };

  const handleRefresh = () => {
    loadProducts();
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  return (
    <div className="shopping-layout">
      {/* 主头部区域 */}
      <div className="shopping-header" style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '32px 0',
        marginBottom: '32px'
      }}>
        <div className="shopping-container">
          <div style={{ textAlign: 'center', color: 'white' }}>
            <Title level={1} style={{
              color: 'white',
              margin: '0 0 16px 0',
              fontSize: 'clamp(24px, 4vw, 36px)',
              fontWeight: 700
            }}>
              🛍️ 智能购物助手
            </Title>
            <Text style={{
              color: 'rgba(255, 255, 255, 0.9)',
              fontSize: 'clamp(14px, 2vw, 18px)',
              marginBottom: '32px',
              display: 'block'
            }}>
              AI驱动的个性化购物体验，为您推荐最合适的商品
            </Text>

            {/* 智能搜索框 */}
            <div style={{ maxWidth: '800px', margin: '0 auto' }}>
              <SmartSearchBox
                onSearch={handleSearch}
                onVoiceSearch={() => console.log('语音搜索')}
                onImageSearch={(file) => console.log('图片搜索:', file)}
                size="large"
                showFilters={true}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="shopping-container">
        <Row gutter={[24, 24]}>
          {/* 左侧边栏 */}
          <Col xs={24} lg={6}>
            <div className="shopping-sidebar">
              {/* 分类导航 */}
              <Affix offsetTop={80}>
                <div style={{ marginBottom: '24px' }}>
                  <CategoryNavigation
                  selectedCategory={selectedCategory}
                  onCategoryChange={handleCategoryChange}
                />
                </div>
              </Affix>

              {/* 智能聊天助手 */}
              <div style={{ marginTop: '24px' }}>
                <SmartChatInterface
                  userId={userId}
                  title="智能助手"
                />
              </div>

              {/* 个性化推荐 */}
              <div style={{ marginTop: '24px' }}>
                <PersonalizedRecommendations
                  userId={userId}
                  onViewProduct={(product: any) => handleViewDetails(product as any)}
                  onAddToCart={(product: any) => handleAddToCart(product as any)}
                  maxItems={4}
                  showTitle={true}
                />
              </div>
            </div>
          </Col>

          {/* 主内容区域 */}
          <Col xs={24} lg={18}>
            <div className="shopping-main">
              {/* 工具栏 */}
              <Card style={{
                marginBottom: '24px',
                borderRadius: '12px',
                border: '1px solid #f0f0f0'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '16px'
                }}>
                  <div>
                    <Title level={4} style={{ margin: 0 }}>
                      {searchQuery ? `"${searchQuery}"的搜索结果` : (selectedCategory || '全部商品')}
                    </Title>
                    <Text type="secondary">
                      找到 {totalCount} 个商品 {totalCount > 0 && `(第 ${currentPage} 页)`}
                    </Text>
                  </div>

                  <Space size="middle">
                    {/* 视图切换 */}
                    <Space>
                      <Button
                        type={viewMode === 'grid' ? 'primary' : 'default'}
                        icon={<AppstoreOutlined />}
                        onClick={() => setViewMode('grid')}
                      />
                      <Button
                        type={viewMode === 'list' ? 'primary' : 'default'}
                        icon={<UnorderedListOutlined />}
                        onClick={() => setViewMode('list')}
                      />
                    </Space>

                    {/* 排序 */}
                    <select
                      value={sortBy}
                      onChange={(e) => handleSortChange(e.target.value)}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '6px',
                        border: '1px solid #d9d9d9'
                      }}
                    >
                      <option value="default">默认排序</option>
                      <option value="price_asc">价格从低到高</option>
                      <option value="price_desc">价格从高到低</option>
                      <option value="rating">好评优先</option>
                      <option value="sales">销量优先</option>
                    </select>

                    {/* 刷新按钮 */}
                    <Button
                      icon={<ReloadOutlined />}
                      onClick={handleRefresh}
                      loading={loading}
                    >
                      刷新
                    </Button>
                  </Space>
                </div>
              </Card>

              {/* 商品列表 */}
              {loading ? (
                <div style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: '400px'
                }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{
                      width: '200px',
                      height: '4px',
                      background: '#f0f0f0',
                      borderRadius: '2px',
                      overflow: 'hidden',
                      margin: '0 auto 16px'
                    }}>
                      <div className="loading-bar" style={{ height: '100%' }} />
                    </div>
                    <Text type="secondary">正在加载商品...</Text>
                  </div>
                </div>
              ) : (
                <>
                  {products.length > 0 ? (
                    <div className={viewMode === 'grid' ? 'shopping-grid' : ''}>
                      {viewMode === 'grid' ? (
                        <Row gutter={[16, 16]}>
                          {products.map(product => (
                            <Col xs={24} sm={12} md={8} lg={8} xl={6} key={product.id}>
                              <ProductCard
                                product={product}
                                onViewDetails={handleViewDetails}
                                onAddToCart={(product: any) => handleAddToCart(product as any)}
                                onCompare={handleCompare}
                                onToggleFavorite={handleToggleFavorite}
                                className="hover-lift"
                              />
                            </Col>
                          ))}
                        </Row>
                      ) : (
                        // 列表视图可以在这里实现
                        <div>
                          {products.map(product => (
                            <Card key={product.id} style={{ marginBottom: '16px' }}>
                              <ProductCard
                                product={product}
                                onViewDetails={handleViewDetails}
                                onAddToCart={(product: any) => handleAddToCart(product as any)}
                                onCompare={handleCompare}
                                onToggleFavorite={handleToggleFavorite}
                              />
                            </Card>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{
                      textAlign: 'center',
                      padding: '80px 20px',
                      background: '#fafafa',
                      borderRadius: '12px'
                    }}>
                      <div style={{ fontSize: '64px', marginBottom: '16px' }}>📦</div>
                      <Title level={4} style={{ color: '#8c8c8c' }}>
                        没有找到相关商品
                      </Title>
                      <Text type="secondary">
                        请尝试调整搜索条件或浏览其他分类
                      </Text>
                    </div>
                  )}

                  {/* 分页组件 */}
                  {totalCount > 20 && (
                    <div style={{
                      display: 'flex',
                      justifyContent: 'center',
                      marginTop: '32px',
                      padding: '24px',
                      background: '#fff',
                      borderRadius: '12px',
                      border: '1px solid #f0f0f0'
                    }}>
                      <Pagination
                        current={currentPage}
                        total={totalCount}
                        pageSize={20}
                        onChange={handlePageChange}
                        showSizeChanger={false}
                        showQuickJumper
                        showTotal={(total, range) =>
                          `第 ${range[0]}-${range[1]} 项，共 ${total} 项商品`
                        }
                      />
                    </div>
                  )}
                </>
              )}
            </div>
          </Col>
        </Row>
      </div>

      {/* 购物车快捷入口 */}
      <ShoppingCartQuickAccess
        userId={userId}
        cartItemsCount={cartItemsCount}
        onCheckout={(items: CartItem[]) => console.log('结算:', items)}
        onRemoveItem={(itemId: number) => console.log('移除商品:', itemId)}
        onUpdateQuantity={(itemId: number, quantity: number) => console.log('更新数量:', itemId, quantity)}
        onToggleSelection={(itemId: number) => console.log('切换选择:', itemId)}
      />

      {/* 客服悬浮按钮 */}
      <FloatButton.Group
        trigger="hover"
        type="primary"
        style={{ right: 24, bottom: 150 }}
        icon={<CustomerServiceOutlined />}
      >
        <FloatButton
          icon={<FilterOutlined />}
          tooltip="筛选"
        />
        <FloatButton
          icon={<SortAscendingOutlined />}
          tooltip="排序"
        />
      </FloatButton.Group>

      {/* 回到顶部 */}
      <BackTop>
        <Button
          type="primary"
          shape="circle"
          icon={<ArrowUpOutlined />}
          size="large"
          style={{
            background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
            border: 'none',
            boxShadow: '0 4px 12px rgba(24, 144, 255, 0.4)'
          }}
        />
      </BackTop>
    </div>
  );
};

export default ModernShoppingAssistant;