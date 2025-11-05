import React, { useState } from 'react';
import { Card, Tag, Button, Rate, Avatar, Tooltip, Badge } from 'antd';
import {
  HeartOutlined,
  ShareAltOutlined,
  EyeOutlined,
  ShoppingCartOutlined,
  SwapOutlined,
  StarOutlined,
  ThunderboltOutlined,
  FireOutlined,
  CrownOutlined,
  TagOutlined
} from '@ant-design/icons';
import { Product, PlatformType } from '../../services/shoppingApi';

interface ProductCardProps {
  product: Product;
  onViewDetails?: (product: Product) => void;
  onAddToCart?: (product: Product) => void;
  onCompare?: (product: Product) => void;
  onToggleFavorite?: (product: Product) => void;
  className?: string;
}

const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onViewDetails,
  onAddToCart,
  onCompare,
  onToggleFavorite,
  className = ''
}) => {
  const [isFavorited, setIsFavorited] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [imageError, setImageError] = useState(false);

  const getPlatformConfig = (platform: PlatformType) => {
    const configs = {
      [PlatformType.JD]: {
        name: '京东',
        color: '#e4393c',
        bgColor: '#fff1f0',
        borderColor: '#ffccc7'
      },
      [PlatformType.TAOBAO]: {
        name: '淘宝',
        color: '#ff6a00',
        bgColor: '#fff7e6',
        borderColor: '#ffd591'
      },
      [PlatformType.PDD]: {
        name: '拼多多',
        color: '#e02e24',
        bgColor: '#fff1f0',
        borderColor: '#ffccc7'
      },
      [PlatformType.XIAOHONGSHU]: {
        name: '小红书',
        color: '#fe2c55',
        bgColor: '#fff0f5',
        borderColor: '#ffadd2'
      },
      [PlatformType.DOUYIN]: {
        name: '抖音',
        color: '#69c9ff',
        bgColor: '#e6f7ff',
        borderColor: '#91d5ff'
      },
      [PlatformType.OTHER]: {
        name: '其他',
        color: '#8c8c8c',
        bgColor: '#f5f5f5',
        borderColor: '#d9d9d9'
      }
    };
    return configs[platform] || configs[PlatformType.OTHER];
  };

  const formatPrice = (price: number) => {
    return `¥${price.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const calculateDiscount = () => {
    if (product.original_price && product.price && product.original_price > product.price) {
      return Math.round(((product.original_price - product.price) / product.original_price) * 100);
    }
    return 0;
  };

  const discount = calculateDiscount();
  const platformConfig = getPlatformConfig(product.platform);

  const handleFavoriteToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsFavorited(!isFavorited);
    onToggleFavorite?.(product);
  };

  const handleAddToCart = (e: React.MouseEvent) => {
    e.stopPropagation();
    onAddToCart?.(product);
  };

  const handleCompare = (e: React.MouseEvent) => {
    e.stopPropagation();
    onCompare?.(product);
  };

  return (
    <Card
      className={`modern-product-card ${className}`}
      style={{
        width: '100%',
        borderRadius: '16px',
        boxShadow: isHovered ? '0 8px 24px rgba(0, 0, 0, 0.12)' : '0 2px 8px rgba(0, 0, 0, 0.06)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        border: '1px solid #f0f0f0',
        overflow: 'hidden',
        cursor: 'pointer',
        transform: isHovered ? 'translateY(-4px)' : 'translateY(0)',
      }}
      bodyStyle={{ padding: '0' }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onViewDetails?.(product)}
    >
      {/* 商品图片区域 */}
      <div style={{ position: 'relative', width: '100%', height: '240px', overflow: 'hidden' }}>
        {/* 平台标签 */}
        <div
          style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            zIndex: 2,
          }}
        >
          <Tag
            color={platformConfig.color}
            style={{
              borderRadius: '12px',
              padding: '4px 12px',
              fontWeight: 600,
              fontSize: '12px',
              border: 'none',
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
            }}
          >
            {platformConfig.name}
          </Tag>
        </div>

        {/* 热销/推荐标签 */}
        <div style={{ position: 'absolute', top: '12px', right: '12px', zIndex: 2 }}>
          {product.is_hot && (
            <Tag
              icon={<FireOutlined />}
              color="#ff4d4f"
              style={{
                borderRadius: '12px',
                padding: '4px 8px',
                fontWeight: 600,
                fontSize: '11px',
                border: 'none',
                marginBottom: '4px'
              }}
            >
              热销
            </Tag>
          )}
          {product.is_recommended && (
            <Tag
              icon={<CrownOutlined />}
              color="#faad14"
              style={{
                borderRadius: '12px',
                padding: '4px 8px',
                fontWeight: 600,
                fontSize: '11px',
                border: 'none'
              }}
            >
              推荐
            </Tag>
          )}
        </div>

        {/* 折扣标签 */}
        {discount > 0 && (
          <div
            style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              zIndex: 2,
            }}
          >
            <div
              style={{
                width: '40px',
                height: '40px',
                background: 'linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 'bold',
                fontSize: '12px',
                boxShadow: '0 2px 8px rgba(255, 77, 79, 0.3)'
              }}
            >
              -{discount}%
            </div>
          </div>
        )}

        {/* 商品图片 */}
        {product.image_url && !imageError ? (
          <img
            src={product.image_url}
            alt={product.title}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              transition: 'transform 0.3s ease',
              transform: isHovered ? 'scale(1.05)' : 'scale(1)'
            }}
            onError={() => setImageError(true)}
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
              <div style={{ fontSize: '48px', marginBottom: '8px' }}>📦</div>
              <div style={{ fontSize: '14px' }}>暂无图片</div>
            </div>
          </div>
        )}

        {/* 悬停操作按钮 */}
        {isHovered && (
          <div
            style={{
              position: 'absolute',
              bottom: '12px',
              left: '50%',
              transform: 'translateX(-50%)',
              display: 'flex',
              gap: '8px',
              zIndex: 2
            }}
          >
            <Tooltip title="收藏">
              <Button
                type="primary"
                shape="circle"
                size="small"
                icon={<HeartOutlined />}
                style={{
                  backgroundColor: isFavorited ? '#ff4d4f' : 'rgba(255, 255, 255, 0.9)',
                  borderColor: isFavorited ? '#ff4d4f' : '#d9d9d9',
                  color: isFavorited ? 'white' : '#8c8c8c',
                  backdropFilter: 'blur(8px)',
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)'
                }}
                onClick={handleFavoriteToggle}
              />
            </Tooltip>
            <Tooltip title="对比">
              <Button
                shape="circle"
                size="small"
                icon={<SwapOutlined />}
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.9)',
                  borderColor: '#d9d9d9',
                  color: '#8c8c8c',
                  backdropFilter: 'blur(8px)',
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)'
                }}
                onClick={handleCompare}
              />
            </Tooltip>
            <Tooltip title="快速查看">
              <Button
                shape="circle"
                size="small"
                icon={<EyeOutlined />}
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.9)',
                  borderColor: '#d9d9d9',
                  color: '#8c8c8c',
                  backdropFilter: 'blur(8px)',
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)'
                }}
              />
            </Tooltip>
          </div>
        )}
      </div>

      {/* 商品信息区域 */}
      <div style={{ padding: '16px' }}>
        {/* 商品标题 */}
        <div style={{ marginBottom: '12px' }}>
          <h3
            style={{
              fontSize: '14px',
              fontWeight: 600,
              color: '#262626',
              lineHeight: '1.4',
              margin: 0,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              minHeight: '39.2px'
            }}
          >
            {product.title}
          </h3>
        </div>

        {/* 评分和销量 */}
        <div style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          {product.rating && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Rate
                disabled
                defaultValue={product.rating}
                style={{ fontSize: '12px', color: '#faad14' }}
              />
              <span style={{ fontSize: '12px', color: '#8c8c8c' }}>
                {product.rating.toFixed(1)}
              </span>
            </div>
          )}
          {product.review_count && (
            <span style={{ fontSize: '12px', color: '#8c8c8c' }}>
              {product.review_count > 1000 ? `${(product.review_count / 1000).toFixed(1)}k` : product.review_count}条评价
            </span>
          )}
          {product.sales_count && (
            <span style={{ fontSize: '12px', color: '#8c8c8c' }}>
              月销{product.sales_count > 1000 ? `${(product.sales_count / 1000).toFixed(1)}k+` : `${product.sales_count}+`}
            </span>
          )}
        </div>

        {/* 价格区域 */}
        <div style={{ marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span
              style={{
                fontSize: '20px',
                fontWeight: 'bold',
                color: '#ff4d4f',
                fontFamily: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif'
              }}
            >
              {formatPrice(product.price || 0)}
            </span>
            {product.original_price && product.original_price > (product.price || 0) && (
              <span
                style={{
                  fontSize: '14px',
                  color: '#8c8c8c',
                  textDecoration: 'line-through'
                }}
              >
                {formatPrice(product.original_price)}
              </span>
            )}
          </div>
        </div>

        {/* 优惠信息 */}
        {(product.coupon_info || product.shipping_info) && (
          <div style={{ marginBottom: '12px' }}>
            {product.coupon_info && (
              <Tag
                icon={<TagOutlined />}
                color="#ff7875"
                style={{
                  borderRadius: '4px',
                  fontSize: '11px',
                  padding: '2px 6px',
                  marginBottom: '4px'
                }}
              >
                {product.coupon_info}
              </Tag>
            )}
            {product.shipping_info && (
              <Tag
                color="#52c41a"
                style={{
                  borderRadius: '4px',
                  fontSize: '11px',
                  padding: '2px 6px'
                }}
              >
                {product.shipping_info}
              </Tag>
            )}
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
              borderRadius: '8px',
              fontWeight: 600,
              background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
              border: 'none',
              boxShadow: '0 2px 4px rgba(24, 144, 255, 0.2)'
            }}
            onClick={handleAddToCart}
          >
            加入购物车
          </Button>
          <Button
            size="small"
            icon={<ShareAltOutlined />}
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              borderColor: '#d9d9d9',
              backgroundColor: '#fafafa'
            }}
          />
        </div>
      </div>
    </Card>
  );
};

export default ProductCard;