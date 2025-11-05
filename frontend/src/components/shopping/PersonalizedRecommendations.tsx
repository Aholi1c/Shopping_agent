import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Button, Badge, Tag, Rate, Avatar, Tooltip, Divider, Space, message, Spin } from 'antd';
import { ShoppingApiService, RecommendationResponse, RecommendationItem, PlatformType } from '../../services/shoppingApi';
import {
  ThunderboltOutlined,
  HeartOutlined,
  StarOutlined,
  FireOutlined,
  CrownOutlined,
  GiftOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  EyeOutlined,
  ShoppingCartOutlined,
  RightOutlined,
  UserOutlined,
  BulbOutlined,
  TrophyOutlined,
  RocketOutlined,
  DownOutlined
} from '@ant-design/icons';
import ProductCard from './ProductCard';

interface PersonalizedRecommendationsProps {
  userId?: number;
  onViewProduct?: (product: RecommendationItem) => void;
  onAddToCart?: (product: RecommendationItem) => void;
  showTitle?: boolean;
  maxItems?: number;
  className?: string;
}

const PersonalizedRecommendations: React.FC<PersonalizedRecommendationsProps> = ({
  userId = 1,
  onViewProduct,
  onAddToCart,
  showTitle = true,
  maxItems = 8,
  className = ''
}) => {
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'personalized' | 'trending' | 'similar' | 'new_arrivals'>('personalized');

  // 加载推荐数据
  const loadRecommendations = async () => {
    setLoading(true);
    try {
      let response: RecommendationResponse;

      switch (activeTab) {
        case 'personalized':
          // 个性化推荐
          response = await ShoppingApiService.getRecommendations(userId, undefined, maxItems);
          break;
        case 'trending':
          // 热门推荐（可以通过特定category参数获取）
          response = await ShoppingApiService.getRecommendations(userId, 'trending', maxItems);
          break;
        case 'similar':
          // 相似商品推荐
          response = await ShoppingApiService.getRecommendations(userId, 'similar', maxItems);
          break;
        case 'new_arrivals':
          // 新品推荐
          response = await ShoppingApiService.getRecommendations(userId, 'new', maxItems);
          break;
        default:
          response = await ShoppingApiService.getRecommendations(userId, undefined, maxItems);
      }

      setRecommendations(response.recommendations.slice(0, maxItems));
    } catch (error) {
      console.error('加载推荐数据失败:', error);
      message.error('加载推荐数据失败');

      // 使用模拟数据作为后备
      const fallbackData: RecommendationItem[] = [
        {
          id: 1,
          title: 'Apple MacBook Air M2 13英寸 8GB 256GB',
          price: 7999,
          original_price: 8999,
          platform: PlatformType.JD,
          rating: 4.8,
          review_count: 2341,
          image_url: 'https://via.placeholder.com/300x200',
          category: '笔记本',
          reason: '基于您的浏览历史，您对高性能笔记本电脑感兴趣',
          confidence: 0.92,
          match_score: 95,
          tags: ['热销', '办公必备', '高性能'],
          discount_rate: 11,
          is_hot: true
        },
        {
          id: 2,
          title: 'Sony WH-1000XM5 无线降噪耳机',
          price: 2499,
          platform: PlatformType.TAOBAO,
          rating: 4.7,
          review_count: 1856,
          image_url: 'https://via.placeholder.com/300x200',
          category: '音频设备',
          reason: '与您收藏的商品风格相似',
          confidence: 0.88,
          match_score: 88,
          tags: ['降噪', '高音质', '长续航'],
          limited_time: true
        }
      ];
      setRecommendations(fallbackData.slice(0, maxItems));
    } finally {
      setLoading(false);
    }
  };

  // 根据标签页加载推荐数据
  useEffect(() => {
    loadRecommendations();
  }, [activeTab, userId, maxItems]);

  const getReasonIcon = (reason: string) => {
    if (reason.includes('浏览历史')) return <EyeOutlined />;
    if (reason.includes('收藏')) return <HeartOutlined />;
    if (reason.includes('购买')) return <ShoppingCartOutlined />;
    if (reason.includes('品牌')) return <CrownOutlined />;
    if (reason.includes('新品')) return <RocketOutlined />;
    return <BulbOutlined />;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return '#52c41a';
    if (confidence >= 0.8) return '#1890ff';
    if (confidence >= 0.7) return '#faad14';
    return '#ff4d4f';
  };

  const formatPrice = (price: number) => {
    return `¥${price.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  // 处理加入购物车
  const handleAddToCart = async (item: RecommendationItem) => {
    try {
      await ShoppingApiService.addToCart(userId, item.id);
      message.success('已添加到购物车');
      onAddToCart?.(item);
    } catch (error) {
      console.error('添加到购物车失败:', error);
      message.error('添加到购物车失败');
    }
  };

  // 处理查看商品详情
  const handleViewDetails = (item: RecommendationItem) => {
    onViewProduct?.(item);
  };

  const renderRecommendationCard = (item: RecommendationItem) => (
    <Col xs={24} sm={12} md={8} lg={6} key={item.id}>
      <Card
        hoverable
        style={{
          height: '100%',
          borderRadius: '12px',
          overflow: 'hidden',
          border: '1px solid #f0f0f0',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          position: 'relative'
        }}
        bodyStyle={{ padding: '0' }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-4px)';
          e.currentTarget.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.12)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.06)';
        }}
        cover={
          <div style={{ position: 'relative', height: '200px', overflow: 'hidden' }}>
            {/* 推荐标签 */}
            <div style={{ position: 'absolute', top: '8px', left: '8px', zIndex: 2 }}>
              <Badge
                count={`${Math.round(item.match_score)}%匹配`}
                style={{
                  backgroundColor: getConfidenceColor(item.confidence),
                  fontSize: '10px',
                  height: '18px',
                  lineHeight: '18px',
                  borderRadius: '9px'
                }}
              />
            </div>

            {/* 状态标签 */}
            <div style={{ position: 'absolute', top: '8px', right: '8px', zIndex: 2 }}>
              {item.is_hot && (
                <Tag color="#ff4d4f" style={{ borderRadius: '8px', fontSize: '10px', marginBottom: '4px' }}>
                  <FireOutlined style={{ fontSize: '8px', marginRight: '2px' }} />
                  热销
                </Tag>
              )}
              {item.is_new && (
                <Tag color="#52c41a" style={{ borderRadius: '8px', fontSize: '10px', marginBottom: '4px' }}>
                  <RocketOutlined style={{ fontSize: '8px', marginRight: '2px' }} />
                  新品
                </Tag>
              )}
              {item.limited_time && (
                <Tag color="#faad14" style={{ borderRadius: '8px', fontSize: '10px' }}>
                  <ClockCircleOutlined style={{ fontSize: '8px', marginRight: '2px' }} />
                  限时
                </Tag>
              )}
            </div>

            {/* 折扣标签 */}
            {item.discount_rate && item.discount_rate > 0 && (
              <div style={{
                position: 'absolute',
                bottom: '8px',
                right: '8px',
                zIndex: 2
              }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  background: 'linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%)',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontWeight: 'bold',
                  fontSize: '10px',
                  boxShadow: '0 2px 8px rgba(255, 77, 79, 0.3)'
                }}>
                  -{item.discount_rate}%
                </div>
              </div>
            )}

            {/* 商品图片 */}
            {item.image_url ? (
              <img
                src={item.image_url}
                alt={item.title}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  transition: 'transform 0.3s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'scale(1.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                }}
              />
            ) : (
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  background: 'linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#8c8c8c'
                }}
              >
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '32px', marginBottom: '4px' }}>📦</div>
                  <div style={{ fontSize: '12px' }}>暂无图片</div>
                </div>
              </div>
            )}
          </div>
        }
      >
        <div style={{ padding: '12px' }}>
          {/* 商品标题 */}
          <h4 style={{
            fontSize: '14px',
            fontWeight: 600,
            color: '#262626',
            lineHeight: '1.4',
            margin: '0 0 8px 0',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            minHeight: '38px'
          }}>
            {item.title}
          </h4>

          {/* 评分 */}
          {item.rating && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Rate
                disabled
                defaultValue={item.rating}
                style={{ fontSize: '12px', color: '#faad14' }}
              />
              <span style={{ fontSize: '12px', color: '#8c8c8c' }}>
                {item.rating.toFixed(1)}
                {item.review_count && ` (${item.review_count > 999 ? `${(item.review_count / 1000).toFixed(1)}k` : item.review_count})`}
              </span>
            </div>
          )}

          {/* 价格 */}
          <div style={{ marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
              <span style={{
                fontSize: '18px',
                fontWeight: 'bold',
                color: '#ff4d4f',
                fontFamily: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif'
              }}>
                {formatPrice(item.price)}
              </span>
              {item.original_price && item.original_price > item.price && (
                <span style={{
                  fontSize: '14px',
                  color: '#8c8c8c',
                  textDecoration: 'line-through'
                }}>
                  {formatPrice(item.original_price)}
                </span>
              )}
            </div>
          </div>

          {/* 推荐理由 */}
          <div style={{
            background: '#f6ffed',
            border: '1px solid #b7eb8f',
            borderRadius: '6px',
            padding: '8px',
            marginBottom: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
              <div style={{
                color: '#52c41a',
                fontSize: '12px',
                marginTop: '1px'
              }}>
                {getReasonIcon(item.reason)}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{
                  fontSize: '11px',
                  color: '#389e0d',
                  fontWeight: 500,
                  marginBottom: '2px'
                }}>
                  AI推荐理由
                </div>
                <div style={{
                  fontSize: '12px',
                  color: '#595959',
                  lineHeight: '1.3'
                }}>
                  {item.reason}
                </div>
              </div>
            </div>
          </div>

          {/* 标签 */}
          {item.tags.length > 0 && (
            <div style={{ marginBottom: '12px' }}>
              {item.tags.slice(0, 3).map((tag, index) => (
                <Tag
                  key={index}
                  style={{
                    borderRadius: '10px',
                    fontSize: '10px',
                    padding: '2px 8px',
                    marginBottom: '4px',
                    background: '#f0f9ff',
                    color: '#1890ff',
                    border: '1px solid #bae7ff'
                  }}
                >
                  {tag}
                </Tag>
              ))}
            </div>
          )}

          {/* 操作按钮 */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button
              type="primary"
              size="small"
              icon={<ShoppingCartOutlined />}
              style={{
                flex: 1,
                height: '32px',
                borderRadius: '6px',
                fontSize: '12px',
                background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
                border: 'none'
              }}
              onClick={() => handleAddToCart(item)}
            >
              加入购物车
            </Button>
            <Button
              size="small"
              icon={<RightOutlined />}
              style={{
                height: '32px',
                borderRadius: '6px',
                fontSize: '12px'
              }}
              onClick={() => handleViewDetails(item)}
            >
              查看
            </Button>
          </div>
        </div>
      </Card>
    </Col>
  );

  const tabs = [
    {
      key: 'personalized',
      label: '个性化推荐',
      icon: <BulbOutlined />,
      color: '#1890ff'
    },
    {
      key: 'trending',
      label: '热门推荐',
      icon: <WarningOutlined />,
      color: '#ff4d4f'
    },
    {
      key: 'similar',
      label: '相似商品',
      icon: <HeartOutlined />,
      color: '#faad14'
    },
    {
      key: 'new_arrivals',
      label: '新品上架',
      icon: <RocketOutlined />,
      color: '#52c41a'
    }
  ];

  return (
    <div className={`personalized-recommendations ${className}`}>
      {showTitle && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '24px',
          padding: '20px 24px',
          background: 'linear-gradient(135deg, #f6ffed 0%, #f0f9ff 100%)',
          borderRadius: '12px',
          border: '1px solid #d9f7be'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              background: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: '20px'
            }}>
              <ThunderboltOutlined />
            </div>
            <div>
              <h3 style={{
                margin: 0,
                fontSize: '18px',
                fontWeight: 600,
                color: '#262626',
                marginBottom: '4px'
              }}>
                AI智能推荐
              </h3>
              <p style={{
                margin: 0,
                fontSize: '13px',
                color: '#595959'
              }}>
                基于您的偏好和浏览历史，为您精选最合适的商品
              </p>
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{
              fontSize: '12px',
              color: '#8c8c8c',
              marginBottom: '4px'
            }}>
              推荐准确率
            </div>
            <div style={{
              fontSize: '20px',
              fontWeight: 'bold',
              color: '#52c41a'
            }}>
              94.5%
            </div>
          </div>
        </div>
      )}

      {/* 标签页 */}
      <div style={{
        display: 'flex',
        gap: '16px',
        marginBottom: '24px',
        borderBottom: '1px solid #f0f0f0',
        paddingBottom: '12px'
      }}>
        {tabs.map(tab => (
          <Button
            key={tab.key}
            type={activeTab === tab.key ? 'primary' : 'text'}
            size="large"
            icon={tab.icon}
            style={{
              borderRadius: '8px',
              height: '40px',
              paddingLeft: '16px',
              paddingRight: '16px',
              fontSize: '14px',
              fontWeight: 500,
              backgroundColor: activeTab === tab.key ? tab.color : 'transparent',
              borderColor: activeTab === tab.key ? tab.color : 'transparent',
              color: activeTab === tab.key ? 'white' : '#595959'
            }}
            onClick={() => setActiveTab(tab.key as any)}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {/* 推荐商品网格 */}
      {loading ? (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '400px'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '16px', color: '#8c8c8c', marginBottom: '8px' }}>
              AI正在为您分析推荐...
            </div>
            <div style={{
              width: '200px',
              height: '4px',
              background: '#f0f0f0',
              borderRadius: '2px',
              overflow: 'hidden',
              margin: '0 auto'
            }}>
              <div style={{
                width: '60%',
                height: '100%',
                background: 'linear-gradient(90deg, #1890ff, #36cfc9)',
                borderRadius: '2px',
                animation: 'loading 1.5s ease-in-out infinite'
              }} />
            </div>
          </div>
        </div>
      ) : (
        <>
          {recommendations.length > 0 ? (
            <Row gutter={[16, 16]}>
              {recommendations.map(renderRecommendationCard)}
            </Row>
          ) : (
            <div style={{
              textAlign: 'center',
              padding: '60px 20px',
              background: '#fafafa',
              borderRadius: '12px'
            }}>
              <div style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }}>
                🤖
              </div>
              <div style={{ fontSize: '16px', color: '#8c8c8c', marginBottom: '8px' }}>
                暂无推荐商品
              </div>
              <div style={{ fontSize: '13px', color: '#bfbfbf' }}>
                请先浏览一些商品，AI将为您推荐合适的产品
              </div>
            </div>
          )}

          {/* 查看更多 */}
          {recommendations.length > 0 && (
            <div style={{ textAlign: 'center', marginTop: '32px' }}>
              <Button
                type="primary"
                size="large"
                icon={<RightOutlined />}
                style={{
                  borderRadius: '24px',
                  height: '48px',
                  padding: '0 32px',
                  fontSize: '16px',
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
                  border: 'none',
                  boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)'
                }}
              >
                查看更多推荐
              </Button>
            </div>
          )}
        </>
      )}

      </div>
  );
};

export default PersonalizedRecommendations;