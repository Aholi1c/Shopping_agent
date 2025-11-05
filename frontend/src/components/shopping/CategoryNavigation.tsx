import React, { useState, useEffect } from 'react';
import { Menu, Badge, Tooltip, Button, Divider, message, Spin } from 'antd';
import { ShoppingApiService, Category as ApiCategory } from '../../services/shoppingApi';
import {
  MobileOutlined,
  LaptopOutlined,
  CameraOutlined,
  HomeOutlined,
  HeartOutlined,
  BookOutlined,
  SkinOutlined,
  CrownOutlined,
  AppstoreOutlined,
  SoundOutlined,
  ToolOutlined,
  CarOutlined,
  BankOutlined,
  CoffeeOutlined,
  MedicineBoxOutlined,
  TagsOutlined,
  FireOutlined,
  ThunderboltOutlined,
  StarOutlined,
  MoreOutlined
} from '@ant-design/icons';

interface Category {
  id: string;
  name: string;
  icon: React.ReactNode;
  count?: number;
  hot?: boolean;
  subcategories?: Category[];
  color?: string;
}

interface CategoryNavigationProps {
  onCategoryChange?: (category: string) => void;
  selectedCategory?: string;
  className?: string;
}

const CategoryNavigation: React.FC<CategoryNavigationProps> = ({
  onCategoryChange,
  selectedCategory: propSelectedCategory,
  className = ''
}) => {
  const [internalSelectedCategory, setInternalSelectedCategory] = useState<string>(propSelectedCategory || 'all');
  const [expandedCategories, setExpandedCategories] = useState<string[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    totalProducts: 0,
    mainCategories: 0,
    subCategories: 0
  });

  // 默认分类配置
  const getDefaultCategories = (): Category[] => [
    {
      id: 'all',
      name: '全部分类',
      icon: <AppstoreOutlined />,
      color: '#1890ff'
    },
    {
      id: 'electronics',
      name: '数码电器',
      icon: <MobileOutlined />,
      color: '#722ed1',
      subcategories: [
        { id: 'phone', name: '手机', icon: <MobileOutlined />, hot: true },
        { id: 'laptop', name: '笔记本', icon: <LaptopOutlined /> },
        { id: 'camera', name: '相机', icon: <CameraOutlined /> },
        { id: 'audio', name: '音频设备', icon: <SoundOutlined /> },
        { id: 'tablet', name: '平板电脑', icon: <LaptopOutlined /> },
        { id: 'wearables', name: '智能穿戴', icon: <MobileOutlined /> }
      ]
    },
    {
      id: 'home',
      name: '家居生活',
      icon: <HomeOutlined />,
      color: '#52c41a',
      subcategories: [
        { id: 'furniture', name: '家具', icon: <HomeOutlined /> },
        { id: 'decoration', name: '装饰', icon: <CrownOutlined /> },
        { id: 'kitchen', name: '厨具', icon: <CoffeeOutlined /> },
        { id: 'cleaning', name: '清洁', icon: <ToolOutlined /> },
        { id: 'bedding', name: '家纺', icon: <HomeOutlined /> },
        { id: 'storage', name: '收纳', icon: <ToolOutlined /> }
      ]
    },
    {
      id: 'fashion',
      name: '服饰鞋包',
      icon: <HeartOutlined />,
      hot: true,
      color: '#eb2f96',
      subcategories: [
        { id: 'clothing', name: '服装', icon: <HeartOutlined />, hot: true },
        { id: 'shoes', name: '鞋履', icon: <MobileOutlined /> },
        { id: 'bags', name: '箱包', icon: <CrownOutlined /> },
        { id: 'accessories', name: '配饰', icon: <StarOutlined /> },
        { id: 'jewelry', name: '珠宝', icon: <CrownOutlined /> },
        { id: 'watches', name: '手表', icon: <StarOutlined /> }
      ]
    },
    {
      id: 'beauty',
      name: '美妆护肤',
      icon: <SkinOutlined />,
      color: '#fa541c',
      subcategories: [
        { id: 'skincare', name: '护肤', icon: <SkinOutlined /> },
        { id: 'makeup', name: '彩妆', icon: <CrownOutlined /> },
        { id: 'fragrance', name: '香水', icon: <FireOutlined /> },
        { id: 'tools', name: '美容工具', icon: <ToolOutlined /> },
        { id: 'personal_care', name: '个护', icon: <HeartOutlined /> }
      ]
    },
    {
      id: 'sports',
      name: '运动户外',
      icon: <ThunderboltOutlined />,
      color: '#13c2c2',
      subcategories: [
        { id: 'fitness', name: '健身器材', icon: <ToolOutlined /> },
        { id: 'outdoor', name: '户外装备', icon: <MobileOutlined /> },
        { id: 'sports_clothing', name: '运动服装', icon: <HeartOutlined /> },
        { id: 'sports_shoes', name: '运动鞋', icon: <MobileOutlined /> },
        { id: 'equipment', name: '运动配件', icon: <ToolOutlined /> }
      ]
    },
    {
      id: 'books',
      name: '图书文娱',
      icon: <BookOutlined />,
      color: '#2f54eb',
      subcategories: [
        { id: 'literature', name: '文学', icon: <BookOutlined /> },
        { id: 'education', name: '教育', icon: <BookOutlined /> },
        { id: 'entertainment', name: '娱乐', icon: <StarOutlined /> },
        { id: 'stationery', name: '文具', icon: <ToolOutlined /> },
        { id: 'digital', name: '数码阅读', icon: <LaptopOutlined /> }
      ]
    },
    {
      id: 'food',
      name: '食品生鲜',
      icon: <CoffeeOutlined />,
      color: '#52c41a',
      subcategories: [
        { id: 'fresh', name: '生鲜', icon: <HeartOutlined /> },
        { id: 'snacks', name: '零食', icon: <CoffeeOutlined />, hot: true },
        { id: 'drinks', name: '饮料', icon: <CoffeeOutlined /> },
        { id: 'seasoning', name: '调味', icon: <ToolOutlined /> },
        { id: 'health_food', name: '保健食品', icon: <MedicineBoxOutlined /> }
      ]
    },
    {
      id: 'automotive',
      name: '汽车用品',
      icon: <CarOutlined />,
      color: '#fa541c',
      subcategories: [
        { id: 'accessories', name: '汽车配件', icon: <ToolOutlined /> },
        { id: 'care', name: '汽车养护', icon: <ToolOutlined /> },
        { id: 'electronics', name: '车载电子', icon: <MobileOutlined /> },
        { id: 'interior', name: '内饰用品', icon: <HomeOutlined /> }
      ]
    },
    {
      id: 'more',
      name: '更多分类',
      icon: <MoreOutlined />,
      color: '#8c8c8c'
    }
  ];

  // 初始化和加载分类数据
  useEffect(() => {
    loadCategories();
    loadCategoryStats();
  }, []);

  useEffect(() => {
    if (propSelectedCategory !== undefined && propSelectedCategory !== internalSelectedCategory) {
      setInternalSelectedCategory(propSelectedCategory);
    }
  }, [propSelectedCategory]);

  // 加载分类数据
  const loadCategories = async () => {
    setLoading(true);
    try {
      // 使用默认分类配置，后续可以从API加载
      const defaultCategories = getDefaultCategories();
      setCategories(defaultCategories);
    } catch (error) {
      console.error('加载分类失败:', error);
      // 使用默认分类作为后备
      setCategories(getDefaultCategories());
    } finally {
      setLoading(false);
    }
  };

  // 加载分类统计数据
  const loadCategoryStats = async () => {
    try {
      const response = await ShoppingApiService.getCategoryStats();
      if (response) {
        setStats({
          totalProducts: response.total_products || 125000,
          mainCategories: response.main_categories || 9,
          subCategories: response.sub_categories || 35
        });
      }
    } catch (error) {
      console.error('加载分类统计失败:', error);
      // 使用默认统计数据
      setStats({
        totalProducts: 125000,
        mainCategories: 9,
        subCategories: 35
      });
    }
  };

  const handleCategoryClick = (categoryId: string) => {
    setInternalSelectedCategory(categoryId);
    onCategoryChange?.(categoryId === 'all' ? '' : categoryId);
  };

  const handleSubcategoryClick = (categoryId: string, subcategoryId: string) => {
    const subcategoryKey = `${categoryId}-${subcategoryId}`;
    setInternalSelectedCategory(subcategoryKey);
    onCategoryChange?.(subcategoryKey);
  };

  // 刷新分类数据
  const handleRefresh = async () => {
    await loadCategories();
    await loadCategoryStats();
    message.success('分类数据已更新');
  };

  const toggleCategoryExpansion = (categoryId: string) => {
    setExpandedCategories(prev =>
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  const renderMenuItem = (category: Category, isSubcategory = false) => {
    const isSelected = internalSelectedCategory === category.id || internalSelectedCategory.includes(`-${category.id}`);
    const isExpanded = expandedCategories.includes(category.id);

    return (
      <Menu.Item
        key={category.id}
        icon={
          <div style={{
            color: isSelected ? category.color : undefined,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '16px',
            height: '16px'
          }}>
            {category.icon}
          </div>
        }
        onClick={() => {
          handleCategoryClick(category.id);
          if (category.subcategories) {
            toggleCategoryExpansion(category.id);
          }
        }}
        style={{
          margin: '2px 8px',
          borderRadius: '8px',
          borderLeft: isSelected ? `3px solid ${category.color}` : '3px solid transparent',
          backgroundColor: isSelected ? `${category.color}08` : undefined,
          color: isSelected ? category.color : undefined,
          fontWeight: isSelected ? 600 : 500,
          height: '40px',
          lineHeight: '40px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>{category.name}</span>
            {category.hot && (
              <Badge
                count={<FireOutlined style={{ color: '#ff4d4f', fontSize: '10px' }} />}
                style={{ backgroundColor: 'transparent' }}
              />
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {category.count && (
              <span style={{ fontSize: '11px', color: '#8c8c8c', opacity: 0.7 }}>
                {category.count > 9999 ? `${(category.count / 10000).toFixed(1)}w+` : category.count}
              </span>
            )}
            {category.subcategories && (
              <Button
                type="text"
                size="small"
                icon={isExpanded ? <CrownOutlined rotate={90} /> : <CrownOutlined />}
                style={{
                  padding: '0',
                  height: '16px',
                  width: '16px',
                  fontSize: '10px',
                  color: isSelected ? category.color : '#8c8c8c'
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  toggleCategoryExpansion(category.id);
                }}
              />
            )}
          </div>
        </div>
      </Menu.Item>
    );
  };

  return (
    <div className={`category-navigation ${className}`} style={{
      background: '#fff',
      borderRadius: '12px',
      padding: '16px',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
      border: '1px solid #f0f0f0'
    }}>
      {/* 标题区域 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '16px',
        paddingBottom: '12px',
        borderBottom: '1px solid #f0f0f0'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TagsOutlined style={{ fontSize: '18px', color: '#1890ff' }} />
          <span style={{ fontSize: '16px', fontWeight: 600, color: '#262626' }}>
            商品分类
          </span>
        </div>
        <Tooltip title="刷新分类数据">
          <Button
            type="text"
            icon={<ThunderboltOutlined />}
            size="small"
            style={{ color: '#8c8c8c' }}
            onClick={handleRefresh}
            loading={loading}
          />
        </Tooltip>
      </div>

      {/* 分类菜单 */}
      {loading ? (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '200px'
        }}>
          <Spin size="large" />
        </div>
      ) : (
        <Menu
          mode="inline"
          selectedKeys={[internalSelectedCategory]}
          style={{
            border: 'none',
            backgroundColor: 'transparent'
          }}
        >
        {categories.map(category => (
          <div key={category.id}>
            {renderMenuItem(category)}

            {/* 子分类 */}
            {category.subcategories && expandedCategories.includes(category.id) && (
              <div style={{
                marginLeft: '24px',
                marginTop: '4px',
                padding: '8px 12px',
                background: '#fafafa',
                borderRadius: '8px',
                border: '1px solid #f0f0f0'
              }}>
                {category.subcategories.map(subcategory => (
                  <div
                    key={subcategory.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '6px 8px',
                      margin: '2px 0',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      backgroundColor: internalSelectedCategory === `${category.id}-${subcategory.id}` ? `${category.color}08` : 'transparent',
                      borderLeft: internalSelectedCategory === `${category.id}-${subcategory.id}` ? `2px solid ${category.color}` : '2px solid transparent',
                      transition: 'all 0.2s ease'
                    }}
                    onClick={() => handleSubcategoryClick(category.id, subcategory.id)}
                    onMouseEnter={(e) => {
                      if (internalSelectedCategory !== `${category.id}-${subcategory.id}`) {
                        e.currentTarget.style.backgroundColor = '#f5f5f5';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (internalSelectedCategory !== `${category.id}-${subcategory.id}`) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{
                        color: internalSelectedCategory === `${category.id}-${subcategory.id}` ? category.color : '#8c8c8c',
                        fontSize: '12px'
                      }}>
                        {subcategory.icon}
                      </div>
                      <span style={{
                        fontSize: '13px',
                        color: internalSelectedCategory === `${category.id}-${subcategory.id}` ? category.color : '#595959',
                        fontWeight: internalSelectedCategory === `${category.id}-${subcategory.id}` ? 500 : 400
                      }}>
                        {subcategory.name}
                      </span>
                      {subcategory.hot && (
                        <Badge
                          count={<FireOutlined style={{ color: '#ff4d4f', fontSize: '8px' }} />}
                          style={{ backgroundColor: 'transparent' }}
                        />
                      )}
                    </div>
                    <span style={{
                      fontSize: '11px',
                      color: '#bfbfbf',
                      opacity: 0.8
                    }}>
                      {subcategory.count && (subcategory.count > 999 ? `${(subcategory.count / 1000).toFixed(1)}k+` : subcategory.count)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        </Menu>
      )}

      {/* 底部统计信息 */}
      <Divider style={{ margin: '16px 0 12px 0' }} />
      <div style={{
        display: 'flex',
        justifyContent: 'space-around',
        textAlign: 'center',
        padding: '8px 0',
        background: '#fafafa',
        borderRadius: '8px'
      }}>
        <div>
          <div style={{ fontSize: '16px', fontWeight: 600, color: '#52c41a' }}>
            {stats.totalProducts > 10000 ? `${(stats.totalProducts / 10000).toFixed(1)}w+` : stats.totalProducts}
          </div>
          <div style={{ fontSize: '11px', color: '#8c8c8c' }}>商品总数</div>
        </div>
        <div>
          <div style={{ fontSize: '16px', fontWeight: 600, color: '#1890ff' }}>{stats.mainCategories}</div>
          <div style={{ fontSize: '11px', color: '#8c8c8c' }}>主要分类</div>
        </div>
        <div>
          <div style={{ fontSize: '16px', fontWeight: 600, color: '#fa541c' }}>{stats.subCategories}</div>
          <div style={{ fontSize: '11px', color: '#8c8c8c' }}>子分类</div>
        </div>
      </div>
    </div>
  );
};

export default CategoryNavigation;