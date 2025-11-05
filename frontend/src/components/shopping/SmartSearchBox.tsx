import React, { useState, useEffect, useRef, useCallback } from 'react';
import { AutoComplete, Input, Button, Badge, Tooltip, Popover, Space, Divider, message } from 'antd';
import { ShoppingApiService, PlatformType, SearchRequest } from '../../services/shoppingApi';
import {
  SearchOutlined,
  CameraOutlined,
  PhoneOutlined,
  CloseOutlined,
  HistoryOutlined,
  FireOutlined,
  ClockCircleOutlined,
  TagsOutlined,
  ThunderboltOutlined,
  StarOutlined,
  ShoppingCartOutlined,
  FilterOutlined,
  ArrowRightOutlined
} from '@ant-design/icons';

interface SearchSuggestion {
  value: string;
  category?: string;
  type: 'history' | 'hot' | 'recommend' | 'ai';
  count?: number;
  description?: string;
  icon?: React.ReactNode;
}

interface SmartSearchBoxProps {
  onSearch: (value: string, filters?: any) => void;
  onVoiceSearch?: () => void;
  onImageSearch?: (image: File) => void;
  placeholder?: string;
  size?: 'small' | 'middle' | 'large';
  showFilters?: boolean;
  className?: string;
}

const SmartSearchBox: React.FC<SmartSearchBoxProps> = ({
  onSearch,
  onVoiceSearch,
  onImageSearch,
  placeholder = '搜索商品、品牌或描述您的需求...',
  size = 'large',
  showFilters = true,
  className = ''
}) => {
  const [searchValue, setSearchValue] = useState('');
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [filteredSuggestions, setFilteredSuggestions] = useState<SearchSuggestion[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [showFiltersPopover, setShowFiltersPopover] = useState(false);
  const [selectedFilters, setSelectedFilters] = useState({
    platforms: [PlatformType.JD, PlatformType.TAOBAO, PlatformType.PDD],
    priceRange: [0, 10000],
    category: '',
    sortBy: 'relevance'
  });
  const [isVoiceSupported, setIsVoiceSupported] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const inputRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 加载热门搜索和建议
  useEffect(() => {
    loadInitialSuggestions();

    // 检查语音搜索支持
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      setIsVoiceSupported(true);
    }
  }, []);

  // 加载初始建议（热门搜索、历史记录等）
  const loadInitialSuggestions = async () => {
    try {
      // 加载热门搜索
      const hotSearches = await ShoppingApiService.getHotSearches(8);

      // 获取搜索历史（从localStorage）
      const searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');

      // 组合建议数据
      const allSuggestions: SearchSuggestion[] = [
        // 热门搜索
        ...hotSearches.slice(0, 4).map((term, index) => ({
          value: term,
          type: 'hot' as const,
          icon: <FireOutlined style={{ color: '#ff4d4f' }} />,
          count: Math.floor(Math.random() * 5000) + 500
        })),

        // 搜索历史
        ...searchHistory.slice(0, 3).map((term: string) => ({
          value: term,
          type: 'history' as const,
          icon: <HistoryOutlined style={{ color: '#8c8c8c' }} />
        }))
      ];

      setSuggestions(allSuggestions);
      setFilteredSuggestions(allSuggestions);
    } catch (error) {
      console.error('加载搜索建议失败:', error);
      // 使用默认建议
      setDefaultSuggestions();
    }
  };

  // 设置默认建议（作为后备）
  const setDefaultSuggestions = () => {
    const defaultSuggestions: SearchSuggestion[] = [
      { value: 'iPhone 15 Pro', category: '手机', type: 'hot', icon: <FireOutlined style={{ color: '#ff4d4f' }} /> },
      { value: 'MacBook Air M2', category: '笔记本', type: 'hot', icon: <FireOutlined style={{ color: '#ff4d4f' }} /> },
      { value: '戴森吸尘器', category: '家电', type: 'hot', icon: <FireOutlined style={{ color: '#ff4d4f' }} /> },
      { value: 'SK-II神仙水', category: '美妆', type: 'hot', icon: <FireOutlined style={{ color: '#ff4d4f' }} /> },
    ];
    setSuggestions(defaultSuggestions);
    setFilteredSuggestions(defaultSuggestions);
  };

  // 实时搜索建议
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (searchValue.trim()) {
        loadSearchSuggestions(searchValue);
      } else {
        setFilteredSuggestions(suggestions);
      }
    }, 300); // 300ms延迟

    return () => clearTimeout(delayDebounceFn);
  }, [searchValue, suggestions]);

  // 加载搜索建议
  const loadSearchSuggestions = async (query: string) => {
    try {
      setLoadingSuggestions(true);
      const apiSuggestions = await ShoppingApiService.getSearchSuggestions(query);

      // 过滤现有建议
      const filtered = suggestions.filter(suggestion =>
        suggestion.value.toLowerCase().includes(query.toLowerCase()) ||
        suggestion.category?.toLowerCase().includes(query.toLowerCase())
      );

      // 添加API建议
      const apiSuggestionItems: SearchSuggestion[] = apiSuggestions.map((suggestion, index) => ({
        value: suggestion,
        type: 'recommend' as const,
        icon: <ThunderboltOutlined style={{ color: '#1890ff' }} />,
        description: '搜索建议'
      }));

      setFilteredSuggestions([...filtered, ...apiSuggestionItems].slice(0, 8));
    } catch (error) {
      console.error('加载搜索建议失败:', error);
      // 使用本地过滤
      const filtered = suggestions.filter(suggestion =>
        suggestion.value.toLowerCase().includes(query.toLowerCase()) ||
        suggestion.category?.toLowerCase().includes(query.toLowerCase())
      );
      setFilteredSuggestions(filtered);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const handleSearch = useCallback(async (value: string) => {
    if (value.trim()) {
      try {
        // 保存到搜索历史
        const searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        const updatedHistory = [
          value.trim(),
          ...searchHistory.filter((item: string) => item !== value.trim())
        ].slice(0, 20);
        localStorage.setItem('searchHistory', JSON.stringify(updatedHistory));

        // 准备搜索请求
        const searchRequest: SearchRequest = {
          query: value.trim(),
          platforms: selectedFilters.platforms.length > 0 ? selectedFilters.platforms : [PlatformType.JD, PlatformType.TAOBAO, PlatformType.PDD],
          category: selectedFilters.category || undefined,
          price_min: selectedFilters.priceRange[0] > 0 ? selectedFilters.priceRange[0] : undefined,
          price_max: selectedFilters.priceRange[1] < 10000 ? selectedFilters.priceRange[1] : undefined,
          sort_by: selectedFilters.sortBy === 'default' ? 'relevance' : selectedFilters.sortBy,
          page: 1,
          page_size: 20
        };

        // 调用搜索API
        const searchResult = await ShoppingApiService.searchProducts(searchRequest);

        // 通知父组件搜索结果
        onSearch(value.trim(), {
          ...searchRequest,
          results: searchResult
        });

        // 显示成功消息
        message.success(`找到 ${searchResult.total_count} 个相关商品`);

      } catch (error) {
        console.error('搜索失败:', error);
        message.error('搜索失败，请稍后重试');

        // 仍然调用父组件，让其处理错误情况
        onSearch(value.trim(), selectedFilters);
      }
    }
  }, [selectedFilters, onSearch]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch(searchValue);
    }
  };

  const startVoiceSearch = () => {
    if (!isVoiceSupported) {
      onVoiceSearch?.();
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.lang = 'zh-CN';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsRecording(true);
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setSearchValue(transcript);
      setIsRecording(false);
      handleSearch(transcript);
    };

    recognition.onerror = () => {
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognition.start();
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      try {
        message.loading('正在处理图片...', 0);

        // 转换文件为base64或上传到服务器
        const imageUrl = await fileToImageUrl(file);

        // 调用图片搜索API
        const searchResult = await ShoppingApiService.searchByImage(imageUrl, selectedFilters.platforms);

        message.destroy();
        message.success(`通过图片找到 ${searchResult.total_count} 个相似商品`);

        // 通知父组件
        onImageSearch?.(file);
        onSearch('图片搜索', {
          query: '图片搜索',
          results: searchResult,
          imageUrl
        });

      } catch (error) {
        message.destroy();
        console.error('图片搜索失败:', error);
        message.error('图片搜索失败，请稍后重试');
      }
    }
  };

  // 将文件转换为图片URL（这里简化处理，实际应该上传到服务器）
  const fileToImageUrl = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        resolve(e.target?.result as string);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const renderSuggestionOption = (suggestion: SearchSuggestion) => {
    const getIconColor = (type: string) => {
      switch (type) {
        case 'hot': return '#ff4d4f';
        case 'ai': return '#1890ff';
        case 'history': return '#8c8c8c';
        default: return '#52c41a';
      }
    };

    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        padding: '8px 12px',
        borderRadius: '8px',
        transition: 'background-color 0.2s ease'
      }}>
        <div style={{ marginRight: '12px', color: getIconColor(suggestion.type) }}>
          {suggestion.icon}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{
            fontSize: '14px',
            fontWeight: 500,
            color: '#262626',
            marginBottom: '2px'
          }}>
            {suggestion.value}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {suggestion.category && (
              <span style={{
                fontSize: '12px',
                color: '#8c8c8c',
                background: '#f5f5f5',
                padding: '2px 6px',
                borderRadius: '4px'
              }}>
                {suggestion.category}
              </span>
            )}
            {suggestion.description && (
              <span style={{ fontSize: '12px', color: '#bfbfbf' }}>
                {suggestion.description}
              </span>
            )}
            {suggestion.count && (
              <span style={{ fontSize: '12px', color: '#bfbfbf' }}>
                {suggestion.count > 999 ? `${(suggestion.count / 1000).toFixed(1)}k+` : suggestion.count}搜索
              </span>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderFiltersContent = () => (
    <div style={{ width: '320px', padding: '16px' }}>
      <div style={{ marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 600 }}>价格区间</h4>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Input
            placeholder="最低价"
            style={{ flex: 1 }}
            value={selectedFilters.priceRange[0] || ''}
            onChange={(e) => setSelectedFilters(prev => ({
              ...prev,
              priceRange: [Number(e.target.value) || 0, prev.priceRange[1]]
            }))}
          />
          <span>-</span>
          <Input
            placeholder="最高价"
            style={{ flex: 1 }}
            value={selectedFilters.priceRange[1] || ''}
            onChange={(e) => setSelectedFilters(prev => ({
              ...prev,
              priceRange: [prev.priceRange[0], Number(e.target.value) || 10000]
            }))}
          />
        </div>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 600 }}>商品分类</h4>
        <Input
          placeholder="选择分类"
          value={selectedFilters.category}
          onChange={(e) => setSelectedFilters(prev => ({ ...prev, category: e.target.value }))}
        />
      </div>

      <div style={{ marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 600 }}>排序方式</h4>
        <select
          style={{
            width: '100%',
            padding: '8px',
            border: '1px solid #d9d9d9',
            borderRadius: '6px'
          }}
          value={selectedFilters.sortBy}
          onChange={(e) => setSelectedFilters(prev => ({ ...prev, sortBy: e.target.value }))}
        >
          <option value="default">默认排序</option>
          <option value="price_asc">价格从低到高</option>
          <option value="price_desc">价格从高到低</option>
          <option value="sales">销量优先</option>
          <option value="rating">好评优先</option>
        </select>
      </div>

      <Divider style={{ margin: '12px 0' }} />

      <div style={{ display: 'flex', gap: '8px' }}>
        <Button
          type="primary"
          size="small"
          style={{ flex: 1 }}
          onClick={() => {
            setShowFiltersPopover(false);
            handleSearch(searchValue);
          }}
        >
          应用筛选
        </Button>
        <Button
          size="small"
          onClick={() => setSelectedFilters({
            platforms: [],
            priceRange: [0, 10000],
            category: '',
            sortBy: 'default'
          })}
        >
          重置
        </Button>
      </div>
    </div>
  );

  return (
    <div className={`smart-search-box ${className}`} style={{ position: 'relative' }}>
      {/* 主要搜索框 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '4px',
        background: '#fff',
        borderRadius: '24px',
        border: '2px solid #e8f4fd',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
        transition: 'all 0.3s ease'
      }}>
        {/* 搜索输入框 */}
        <AutoComplete
          ref={inputRef}
          style={{ flex: 1 }}
          value={searchValue}
          onChange={setSearchValue}
          options={filteredSuggestions.slice(0, 8).map(suggestion => ({
            value: suggestion.value,
            label: renderSuggestionOption(suggestion)
          }))}
          onSelect={(value) => {
            setSearchValue(value);
            handleSearch(value);
          }}
          filterOption={false}
        >
          <Input
            placeholder={placeholder}
            size={size}
            bordered={false}
            style={{
              fontSize: size === 'large' ? '16px' : '14px',
              padding: size === 'large' ? '12px 16px' : '8px 12px'
            }}
            suffix={null}
            onPressEnter={handleKeyPress}
          />
        </AutoComplete>

        {/* 左侧功能按钮 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', paddingLeft: '8px' }}>
          {showFilters && (
            <Tooltip title="高级筛选">
              <Popover
                content={renderFiltersContent()}
                trigger="click"
                open={showFiltersPopover}
                onOpenChange={setShowFiltersPopover}
                placement="bottomLeft"
                title="搜索筛选"
              >
                <Button
                  type="text"
                  icon={<FilterOutlined />}
                  size={size}
                  style={{
                    borderRadius: '50%',
                    width: size === 'large' ? '36px' : '28px',
                    height: size === 'large' ? '36px' : '28px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: selectedFilters.category || selectedFilters.priceRange[0] > 0 ? '#1890ff' : '#8c8c8c'
                  }}
                />
              </Popover>
            </Tooltip>
          )}

          <Tooltip title="图片搜索">
            <Button
              type="text"
              icon={<CameraOutlined />}
              size={size}
              style={{
                borderRadius: '50%',
                width: size === 'large' ? '36px' : '28px',
                height: size === 'large' ? '36px' : '28px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              onClick={() => fileInputRef.current?.click()}
            />
          </Tooltip>

          {isVoiceSupported && (
            <Tooltip title={isRecording ? "正在录音..." : "语音搜索"}>
              <Button
                type="text"
                icon={<PhoneOutlined />}
                size={size}
                style={{
                  borderRadius: '50%',
                  width: size === 'large' ? '36px' : '28px',
                  height: size === 'large' ? '36px' : '28px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: isRecording ? '#ff4d4f' : '#8c8c8c',
                  animation: isRecording ? 'pulse 1.5s infinite' : 'none'
                }}
                onClick={startVoiceSearch}
              />
            </Tooltip>
          )}
        </div>

        {/* 搜索按钮 */}
        <Button
          type="primary"
          icon={<SearchOutlined />}
          size={size}
          style={{
            borderRadius: '20px',
            height: size === 'large' ? '48px' : '36px',
            padding: '0 24px',
            background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
            border: 'none',
            boxShadow: '0 2px 8px rgba(24, 144, 255, 0.3)',
            fontWeight: 600
          }}
          onClick={() => handleSearch(searchValue)}
        >
          搜索
        </Button>
      </div>

      {/* 快捷搜索标签 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginTop: '12px',
        flexWrap: 'wrap'
      }}>
        <span style={{ fontSize: '12px', color: '#8c8c8c', marginRight: '4px' }}>热门:</span>
        {suggestions
          .filter(s => s.type === 'hot')
          .slice(0, 5)
          .map((suggestion, index) => (
            <Button
              key={index}
              type="text"
              size="small"
              style={{
                borderRadius: '12px',
                height: '24px',
                padding: '0 12px',
                fontSize: '12px',
                color: '#595959',
                background: '#f5f5f5',
                border: '1px solid #f0f0f0'
              }}
              onClick={() => {
                setSearchValue(suggestion.value);
                handleSearch(suggestion.value);
              }}
            >
              {suggestion.value}
            </Button>
          ))}
      </div>

      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleImageUpload}
      />

      </div>
  );
};

export default SmartSearchBox;