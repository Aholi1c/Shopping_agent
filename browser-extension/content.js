/**
 * Content Script
 * 注入到购物网站页面，提取商品信息并提供交互功能
 */

(function() {
  'use strict';
  
  let productInfo = null;
  let analysisResult = null;
  let assistantWidget = null;
  
  // 初始化
  init();
  
  function init() {
    // 等待页面加载完成
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', onPageReady);
    } else {
      onPageReady();
    }
    
    // 监听来自background的消息
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === 'extractProductInfo') {
        extractProductInfo();
        sendResponse({ success: true });
      } else if (request.action === 'showAnalysis') {
        showAnalysis(request.data);
        sendResponse({ success: true });
      } else if (request.action === 'analyzeCurrentPage') {
        analyzeCurrentPage();
        sendResponse({ success: true });
      }
      return true;
    });
    
    // 创建浮动助手按钮
    createFloatingButton();
  }
  
  function onPageReady() {
    // 延迟提取，确保页面完全加载
    setTimeout(() => {
      extractProductInfo();
    }, 1000);
  }
  
  // 提取商品信息
  async function extractProductInfo() {
    const url = window.location.href;
    let info = {};
    
    console.log('开始提取商品信息，URL:', url);
    
    // 根据不同的购物网站提取商品信息
    if (url.includes('jd.com')) {
      info = extractJDProductInfo();
    } else if (url.includes('taobao.com') || url.includes('tmall.com')) {
      info = extractTaobaoProductInfo();
    } else if (url.includes('pdd.com')) {
      info = extractPDDProductInfo();
    } else if (url.includes('amazon.com') || url.includes('amazon.')) {
      info = extractAmazonProductInfo();
    } else {
      info = extractGenericProductInfo();
    }
    
    console.log('提取到的商品信息:', info);
    
    if (info.name || info.price) {
      productInfo = {
        ...info,
        url: url,
        platform: detectPlatform(url),
        timestamp: Date.now()
      };
      
      // 立即保存到storage（不等待background响应）
      try {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tabs[0] && chrome.storage && chrome.storage.local) {
          await chrome.storage.local.set({
            [`product_${tabs[0].id}`]: productInfo,
            [`product_current`]: productInfo
          });
          console.log('商品信息已直接保存到storage');
        }
      } catch (e) {
        console.warn('直接保存商品信息失败:', e);
      }
      
      // 发送商品信息到background
      chrome.runtime.sendMessage({
        action: 'extractProductInfo',
        data: productInfo
      }, (response) => {
        if (chrome.runtime.lastError) {
          console.warn('发送商品信息到background失败:', chrome.runtime.lastError);
        } else {
          console.log('商品信息已发送到background');
        }
      });
    } else {
      console.warn('未能提取到商品信息（名称或价格为空）');
    }
  }
  
  // 提取京东商品信息
  function extractJDProductInfo() {
    const info = {};
    
    // 商品名称 - 尝试多个选择器
    const nameSelectors = [
      '.sku-name', 
      '#itemName',
      '[data-sku-name]',
      '.product-intro .name',
      'h1',
      '.goods-name',
      '.p-name',
      '[data-product-name]'
    ];
    for (const selector of nameSelectors) {
      const nameEl = document.querySelector(selector);
      if (nameEl && nameEl.textContent.trim()) {
        info.name = nameEl.textContent.trim();
        break;
      }
    }
    
    // 商品价格 - 尝试多个选择器
    const priceSelectors = [
      '.price .J-price',
      '#jd-price',
      '.p-price .price',
      '.price-current',
      '[data-price]',
      '.price-main',
      '.J-price',
      '.p-price'
    ];
    for (const selector of priceSelectors) {
      const priceEl = document.querySelector(selector);
      if (priceEl) {
        const priceText = priceEl.textContent.trim();
        // 检测货币（京东默认人民币，但也要支持其他货币）
        const currencyPattern = /(HK\$|HKD|US\$|USD|\$|¥|CNY|RMB|€|EUR|£|GBP)/i;
        const currencyMatch = priceText.match(currencyPattern);
        if (currencyMatch) {
          const symbol = currencyMatch[1].toUpperCase();
          if (symbol.includes('HK$') || symbol.includes('HKD')) {
            info.currency = 'HKD';
          } else if (symbol.includes('$') || symbol.includes('USD')) {
            info.currency = 'USD';
          } else if (symbol.includes('¥') || symbol.includes('CNY') || symbol.includes('RMB')) {
            info.currency = 'CNY';
          }
        } else {
          info.currency = 'CNY'; // 京东默认人民币
        }
        const cleanedPrice = priceText.replace(/[^\d.]/g, '');
        if (cleanedPrice) {
          info.price = parseFloat(cleanedPrice);
          break;
        }
      }
    }
    
    // 商品图片
    const imgSelectors = [
      '#spec-img img',
      '.main-img img',
      '.preview img',
      '.product-intro img',
      '#spec-n1 img',
      '.jqzoom img'
    ];
    for (const selector of imgSelectors) {
      const imgEl = document.querySelector(selector);
      if (imgEl && imgEl.src && !imgEl.src.includes('placeholder')) {
        info.image = imgEl.src;
        break;
      }
    }
    
    // 商品ID
    const match = window.location.href.match(/(\d+)\.html/);
    if (match) info.productId = match[1];
    
    // 商品描述 - 尝试多个选择器
    const descSelectors = [
      '.parameter2',
      '.detail-content',
      '.product-intro .intro',
      '#detail .tab-detail',
      '.p-parameter',
      '.detail',
      '.product-detail',
      '[data-description]'
    ];
    for (const selector of descSelectors) {
      const descEl = document.querySelector(selector);
      if (descEl) {
        // 获取描述文本，清理空白和换行
        let descText = descEl.textContent || descEl.innerText;
        descText = descText.trim().replace(/\s+/g, ' ');
        if (descText && descText.length > 10) {  // 确保有实际内容
          info.description = descText.substring(0, 2000);  // 限制长度
          break;
        }
      }
    }
    
    // 如果没有找到描述，尝试从meta标签获取
    if (!info.description) {
      const metaDesc = document.querySelector('meta[name="description"]');
      if (metaDesc && metaDesc.content) {
        info.description = metaDesc.content.trim().substring(0, 500);
      }
    }
    
    // 商品参数/规格信息
    const paramSelectors = [
      '.p-parameter-list',
      '.parameter2 ul',
      '.detail-param',
      '[data-params]'
    ];
    const params = {};
    for (const selector of paramSelectors) {
      const paramEl = document.querySelector(selector);
      if (paramEl) {
        const paramItems = paramEl.querySelectorAll('li, tr, .param-item');
        paramItems.forEach(item => {
          const text = item.textContent.trim();
          if (text.includes('：') || text.includes(':')) {
            const separator = text.includes('：') ? '：' : ':';
            const [key, ...valueParts] = text.split(separator);
            if (key && valueParts.length > 0) {
              params[key.trim()] = valueParts.join(separator).trim();
            }
          }
        });
        if (Object.keys(params).length > 0) {
          info.parameters = params;
          break;
        }
      }
    }
    
    return info;
  }
  
  // 提取淘宝商品信息
  function extractTaobaoProductInfo() {
    const info = {};
    
    // 商品名称 - 尝试多个选择器
    const nameSelectors = [
      '.tb-main-title',
      'h1',
      '[data-title]',
      '.tb-detail-hd h1',
      '.goods-name',
      '.title'
    ];
    for (const selector of nameSelectors) {
      const nameEl = document.querySelector(selector);
      if (nameEl && nameEl.textContent.trim()) {
        info.name = nameEl.textContent.trim();
        break;
      }
    }
    
    // 商品价格 - 尝试多个选择器
    const priceSelectors = [
      '.tm-price-panel .tm-price',
      '.price .price-current',
      '[data-price]',
      '.tm-price',
      '.price-now',
      '.tb-rmb-num'
    ];
    for (const selector of priceSelectors) {
      const priceEl = document.querySelector(selector);
      if (priceEl) {
        const priceText = priceEl.textContent.trim();
        // 检测货币（淘宝默认人民币）
        const currencyPattern = /(HK\$|HKD|US\$|USD|\$|¥|CNY|RMB|€|EUR|£|GBP)/i;
        const currencyMatch = priceText.match(currencyPattern);
        if (currencyMatch) {
          const symbol = currencyMatch[1].toUpperCase();
          if (symbol.includes('HK$') || symbol.includes('HKD')) {
            info.currency = 'HKD';
          } else if (symbol.includes('$') || symbol.includes('USD')) {
            info.currency = 'USD';
          } else {
            info.currency = 'CNY';
          }
        } else {
          info.currency = 'CNY'; // 淘宝默认人民币
        }
        const cleanedPrice = priceText.replace(/[^\d.]/g, '');
        if (cleanedPrice) {
          info.price = parseFloat(cleanedPrice);
          break;
        }
      }
    }
    
    // 商品图片
    const imgSelectors = [
      '#J_ImgBooth img',
      '.tb-main-pic img',
      '.tb-booth img',
      '.preview img'
    ];
    for (const selector of imgSelectors) {
      const imgEl = document.querySelector(selector);
      if (imgEl && imgEl.src) {
        info.image = imgEl.src;
        break;
      }
    }
    
    // 商品ID
    const match = window.location.href.match(/id=(\d+)/);
    if (match) info.productId = match[1];
    
    // 商品描述 - 淘宝/天猫的描述通常在详情区域
    const descSelectors = [
      '#J_DetailMeta',
      '.tb-detail-hd',
      '.tb-content',
      '#description',
      '.detail-content',
      '.item-desc',
      '[data-description]'
    ];
    for (const selector of descSelectors) {
      const descEl = document.querySelector(selector);
      if (descEl) {
        let descText = descEl.textContent || descEl.innerText;
        descText = descText.trim().replace(/\s+/g, ' ');
        if (descText && descText.length > 10) {
          info.description = descText.substring(0, 2000);
          break;
        }
      }
    }
    
    // 如果没有找到描述，尝试从meta标签获取
    if (!info.description) {
      const metaDesc = document.querySelector('meta[name="description"]');
      if (metaDesc && metaDesc.content) {
        info.description = metaDesc.content.trim().substring(0, 500);
      }
    }
    
    // 商品参数/规格信息
    const paramSelectors = [
      '#J_AttrUL',
      '.tb-prop-list',
      '.attributes-list',
      '[data-attr]'
    ];
    const params = {};
    for (const selector of paramSelectors) {
      const paramEl = document.querySelector(selector);
      if (paramEl) {
        const paramItems = paramEl.querySelectorAll('li, .attr-item');
        paramItems.forEach(item => {
          const text = item.textContent.trim();
          if (text.includes('：') || text.includes(':')) {
            const separator = text.includes('：') ? '：' : ':';
            const [key, ...valueParts] = text.split(separator);
            if (key && valueParts.length > 0) {
              params[key.trim()] = valueParts.join(separator).trim();
            }
          }
        });
        if (Object.keys(params).length > 0) {
          info.parameters = params;
          break;
        }
      }
    }
    
    return info;
  }
  
  // 提取拼多多商品信息
  function extractPDDProductInfo() {
    const info = {};
    
    // 商品名称 - 尝试多个选择器
    const nameSelectors = [
      '.goods-title',
      '[data-title]',
      '.title',
      'h1',
      '.goods-name'
    ];
    for (const selector of nameSelectors) {
      const nameEl = document.querySelector(selector);
      if (nameEl && nameEl.textContent.trim()) {
        info.name = nameEl.textContent.trim();
        break;
      }
    }
    
    // 商品价格 - 尝试多个选择器
    const priceSelectors = [
      '.price .price-main',
      '[data-price]',
      '.price-current',
      '.current-price',
      '.price'
    ];
    for (const selector of priceSelectors) {
      const priceEl = document.querySelector(selector);
      if (priceEl) {
        const priceText = priceEl.textContent.trim();
        // 检测货币（拼多多默认人民币）
        const currencyPattern = /(HK\$|HKD|US\$|USD|\$|¥|CNY|RMB|€|EUR|£|GBP)/i;
        const currencyMatch = priceText.match(currencyPattern);
        if (currencyMatch) {
          const symbol = currencyMatch[1].toUpperCase();
          if (symbol.includes('HK$') || symbol.includes('HKD')) {
            info.currency = 'HKD';
          } else if (symbol.includes('$') || symbol.includes('USD')) {
            info.currency = 'USD';
          } else {
            info.currency = 'CNY';
          }
        } else {
          info.currency = 'CNY'; // 拼多多默认人民币
        }
        const cleanedPrice = priceText.replace(/[^\d.]/g, '');
        if (cleanedPrice) {
          info.price = parseFloat(cleanedPrice);
          break;
        }
      }
    }
    
    // 商品描述
    const descSelectors = [
      '.goods-detail',
      '.detail-content',
      '.description',
      '[data-description]',
      '.goods-desc'
    ];
    for (const selector of descSelectors) {
      const descEl = document.querySelector(selector);
      if (descEl) {
        let descText = descEl.textContent || descEl.innerText;
        descText = descText.trim().replace(/\s+/g, ' ');
        if (descText && descText.length > 10) {
          info.description = descText.substring(0, 2000);
          break;
        }
      }
    }
    
    // 商品参数
    const paramSelectors = [
      '.parameter-list',
      '.attributes',
      '[data-params]'
    ];
    const params = {};
    for (const selector of paramSelectors) {
      const paramEl = document.querySelector(selector);
      if (paramEl) {
        const paramItems = paramEl.querySelectorAll('li, .param-item');
        paramItems.forEach(item => {
          const text = item.textContent.trim();
          if (text.includes('：') || text.includes(':')) {
            const separator = text.includes('：') ? '：' : ':';
            const [key, ...valueParts] = text.split(separator);
            if (key && valueParts.length > 0) {
              params[key.trim()] = valueParts.join(separator).trim();
            }
          }
        });
        if (Object.keys(params).length > 0) {
          info.parameters = params;
          break;
        }
      }
    }
    
    return info;
  }
  
  // 提取Amazon商品信息
  function extractAmazonProductInfo() {
    const info = {};
    
    // 商品名称 - Amazon的商品标题选择器
    const nameSelectors = [
      '#productTitle',
      'h1.a-size-large.product-title-word-break',
      'h1.a-size-base-plus',
      '#title > span.a-size-large',
      'h1 span',
      'span#productTitle',
      '.product-title'
    ];
    for (const selector of nameSelectors) {
      const nameEl = document.querySelector(selector);
      if (nameEl && nameEl.textContent.trim()) {
        info.name = nameEl.textContent.trim();
        break;
      }
    }
    
    // 商品价格 - Amazon有多种价格显示方式
    const priceSelectors = [
      '.a-price .a-offscreen',  // 隐藏的价格元素（完整价格）
      '.a-price-whole',         // 整数部分
      'span.a-price[data-a-color="price"]',  // 价格容器
      '#priceblock_ourprice',   // 我们的价格
      '#priceblock_dealprice',  // 优惠价格
      '#priceblock_saleprice',  // 销售价格
      '.a-price .a-price-symbol + .a-price-whole',  // 符号+整数部分
      '[data-a-color="price"] .a-offscreen',  // 隐藏价格
      '.a-price-range .a-offscreen',  // 价格范围
      '#twister-plus-price-data-price',  // 动态价格数据
      'span[data-a-color="price"]'  // 通用价格span
    ];
    
    // 货币符号映射
    const currencySymbols = {
      'HK$': 'HKD',
      'HKD': 'HKD',
      'HK$': 'HKD',
      '$': 'USD',
      'USD': 'USD',
      'US$': 'USD',
      '¥': 'CNY',
      'CNY': 'CNY',
      'RMB': 'CNY',
      '€': 'EUR',
      'EUR': 'EUR',
      '£': 'GBP',
      'GBP': 'GBP',
      'JP¥': 'JPY',
      'JPY': 'JPY',
      'A$': 'AUD',
      'AUD': 'AUD'
    };
    
    // 检测货币符号的正则表达式
    const currencyPattern = /(HK\$|HKD|US\$|USD|\$|¥|CNY|RMB|€|EUR|£|GBP|JP¥|JPY|A\$|AUD)/i;
    
    let detectedCurrency = 'CNY'; // 默认人民币
    
    for (const selector of priceSelectors) {
      const priceEl = document.querySelector(selector);
      if (priceEl) {
        // 优先获取data-a-color="price"的元素文本
        let priceText = '';
        if (priceEl.classList.contains('a-offscreen')) {
          priceText = priceEl.textContent.trim();
        } else {
          // 尝试从文本中提取价格
          priceText = priceEl.textContent.trim();
        }
        
        // 检测货币符号
        const currencyMatch = priceText.match(currencyPattern);
        if (currencyMatch) {
          const currencySymbol = currencyMatch[1].toUpperCase();
          // 查找货币代码
          for (const [symbol, code] of Object.entries(currencySymbols)) {
            if (currencySymbol.includes(symbol) || symbol.includes(currencySymbol)) {
              detectedCurrency = code;
              break;
            }
          }
          // 特殊情况：单独的$可能是USD或HKD，需要根据域名判断
          if (currencySymbol === '$' || currencySymbol === 'USD') {
            const hostname = window.location.hostname.toLowerCase();
            if (hostname.includes('amazon.com.hk') || hostname.includes('amazon.hk')) {
              detectedCurrency = 'HKD';
            } else {
              detectedCurrency = 'USD';
            }
          }
        }
        
        // 提取价格数字（支持多种格式：$19.99, 19.99, $19,99等）
        const priceMatch = priceText.match(/[\d,]+\.?\d*/);
        if (priceMatch) {
          const cleanedPrice = priceMatch[0].replace(/,/g, '');
          const price = parseFloat(cleanedPrice);
          if (price && price > 0) {
            info.price = price;
            info.currency = detectedCurrency;
            break;
          }
        }
      }
    }
    
    // 如果还没找到价格，尝试从页面中搜索价格模式
    if (!info.price) {
      const pricePatterns = [
        /\$\s*([\d,]+\.?\d*)/g,
        /USD\s*([\d,]+\.?\d*)/gi,
        /([\d,]+\.?\d*)\s*USD/gi
      ];
      
      for (const pattern of pricePatterns) {
        const matches = document.body.innerText.match(pattern);
        if (matches && matches.length > 0) {
          // 取第一个匹配的价格
          const priceMatch = matches[0].match(/[\d,]+\.?\d*/);
          if (priceMatch) {
            const cleanedPrice = priceMatch[0].replace(/,/g, '');
            const price = parseFloat(cleanedPrice);
            if (price && price > 0 && price < 100000) { // 合理价格范围
              info.price = price;
              break;
            }
          }
        }
      }
    }
    
    // 商品图片
    const imgSelectors = [
      '#landingImage',
      '#imgBlkFront',
      '#main-image',
      '#prodImage',
      '#imageBlock_feature_div img',
      '#main-image-container img',
      '.a-dynamic-image-main'
    ];
    for (const selector of imgSelectors) {
      const imgEl = document.querySelector(selector);
      if (imgEl && imgEl.src && !imgEl.src.includes('placeholder')) {
        info.image = imgEl.src;
        break;
      }
    }
    
    // 商品ID (ASIN) - 从URL或页面中提取
    const currentUrl = window.location.href;
    const asinMatch = currentUrl.match(/\/dp\/([A-Z0-9]{10})/);
    if (asinMatch) {
      info.productId = asinMatch[1];
      info.asin = asinMatch[1];
    } else {
      // 尝试从页面数据中提取ASIN
      const asinData = document.querySelector('[data-asin]');
      if (asinData) {
        info.productId = asinData.getAttribute('data-asin');
        info.asin = asinData.getAttribute('data-asin');
      }
    }
    
    // 评分信息
    const ratingEl = document.querySelector('#acrPopover span.a-icon-alt');
    if (ratingEl) {
      const ratingText = ratingEl.textContent.trim();
      const ratingMatch = ratingText.match(/([\d.]+)\s+out of/);
      if (ratingMatch) {
        info.rating = parseFloat(ratingMatch[1]);
      }
    }
    
    // 评论数量
    const reviewCountEl = document.querySelector('#acrCustomerReviewText');
    if (reviewCountEl) {
      const reviewText = reviewCountEl.textContent.trim();
      const reviewMatch = reviewText.match(/([\d,]+)/);
      if (reviewMatch) {
        info.reviewCount = parseInt(reviewMatch[1].replace(/,/g, ''));
      }
    }
    
    // 商品描述 - Amazon的商品描述通常在feature-bullets和productDescription区域
    const descSelectors = [
      '#productDescription',
      '#feature-bullets',
      '#productDescription_feature_div',
      '.product-description',
      '#aplus_feature_div',
      '[data-feature-name="productDescription"]'
    ];
    for (const selector of descSelectors) {
      const descEl = document.querySelector(selector);
      if (descEl) {
        let descText = descEl.textContent || descEl.innerText;
        descText = descText.trim().replace(/\s+/g, ' ');
        if (descText && descText.length > 20) {  // Amazon描述通常较长
          info.description = descText.substring(0, 2000);
          break;
        }
      }
    }
    
    // 如果没有找到详细描述，尝试从feature-bullets中提取要点
    if (!info.description || info.description.length < 50) {
      const featureBullets = document.querySelectorAll('#feature-bullets li, .a-unordered-list li');
      if (featureBullets.length > 0) {
        const features = Array.from(featureBullets)
          .map(li => li.textContent.trim())
          .filter(text => text.length > 10 && !text.includes('Make sure'))
          .slice(0, 10)  // 最多取10个要点
          .join(' ');
        if (features) {
          info.description = (info.description || '') + ' ' + features;
          info.description = info.description.trim().substring(0, 2000);
        }
      }
    }
    
    // 商品参数/规格信息（Technical Details）
    const techDetailsEl = document.querySelector('#productDetails_techSpec_section_1, .prodDetTable');
    const params = {};
    if (techDetailsEl) {
      const rows = techDetailsEl.querySelectorAll('tr, .prodDetSectionEntry');
      rows.forEach(row => {
        const label = row.querySelector('th, .prodDetSectionEntry, .prodDetLabel');
        const value = row.querySelector('td, .prodDetAttrValue');
        if (label && value) {
          const key = label.textContent.trim();
          const val = value.textContent.trim();
          if (key && val) {
            params[key] = val;
          }
        }
      });
      if (Object.keys(params).length > 0) {
        info.parameters = params;
      }
    }
    
    console.log('Amazon商品信息提取完成:', info);
    return info;
  }
  
  // 通用商品信息提取
  function extractGenericProductInfo() {
    const info = {};
    
    // 尝试提取商品名称
    const nameSelectors = ['h1', '[data-product-name]', '.product-name', '.product-title'];
    for (const selector of nameSelectors) {
      const el = document.querySelector(selector);
      if (el && el.textContent.trim()) {
        info.name = el.textContent.trim();
        break;
      }
    }
    
    // 尝试提取价格
    const priceSelectors = ['[data-price]', '.price', '.product-price'];
    for (const selector of priceSelectors) {
      const el = document.querySelector(selector);
      if (el) {
        const priceText = el.textContent.trim().replace(/[^\d.]/g, '');
        if (priceText) {
          info.price = parseFloat(priceText);
          break;
        }
      }
    }
    
    // 尝试提取商品描述
    const descSelectors = [
      '.product-description',
      '.description',
      '[data-description]',
      '.detail-content',
      '.product-detail',
      'meta[name="description"]'
    ];
    for (const selector of descSelectors) {
      const el = document.querySelector(selector);
      if (el) {
        let descText = '';
        if (el.tagName === 'META') {
          descText = el.content || '';
        } else {
          descText = el.textContent || el.innerText || '';
        }
        descText = descText.trim().replace(/\s+/g, ' ');
        if (descText && descText.length > 10) {
          info.description = descText.substring(0, 2000);
          break;
        }
      }
    }
    
    // 尝试提取商品参数
    const paramSelectors = [
      '.product-attributes',
      '.specifications',
      '.params',
      '[data-params]'
    ];
    const params = {};
    for (const selector of paramSelectors) {
      const paramEl = document.querySelector(selector);
      if (paramEl) {
        const paramItems = paramEl.querySelectorAll('li, tr, .param-item, .spec-item');
        paramItems.forEach(item => {
          const text = item.textContent.trim();
          if (text.includes('：') || text.includes(':')) {
            const separator = text.includes('：') ? '：' : ':';
            const [key, ...valueParts] = text.split(separator);
            if (key && valueParts.length > 0) {
              params[key.trim()] = valueParts.join(separator).trim();
            }
          }
        });
        if (Object.keys(params).length > 0) {
          info.parameters = params;
          break;
        }
      }
    }
    
    return info;
  }
  
  // 检测平台
  function detectPlatform(url) {
    if (url.includes('jd.com')) return 'jd';
    if (url.includes('taobao.com') || url.includes('tmall.com')) return 'taobao';
    if (url.includes('pdd.com')) return 'pdd';
    if (url.includes('amazon.com') || url.includes('amazon.')) return 'amazon';
    if (url.includes('xiaohongshu.com')) return 'xiaohongshu';
    if (url.includes('douyin.com')) return 'douyin';
    return 'unknown';
  }
  
  // 创建浮动助手按钮
  function createFloatingButton() {
    // 移除已存在的按钮
    const existing = document.getElementById('shopping-assistant-float-btn');
    if (existing) existing.remove();
    
    const button = document.createElement('div');
    button.id = 'shopping-assistant-float-btn';
    button.innerHTML = `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z" fill="currentColor"/>
      </svg>
    `;
    button.title = '智能购物助手';
    button.addEventListener('click', () => {
      chrome.runtime.sendMessage({ action: 'openSidePanel' });
    });
    
    // 添加样式
    button.style.cssText = `
      position: fixed;
      right: 20px;
      bottom: 80px;
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 999999;
      transition: transform 0.2s;
      color: white;
    `;
    
    button.addEventListener('mouseenter', () => {
      button.style.transform = 'scale(1.1)';
    });
    
    button.addEventListener('mouseleave', () => {
      button.style.transform = 'scale(1)';
    });
    
    document.body.appendChild(button);
  }
  
  // 显示分析结果
  function showAnalysis(data) {
    analysisResult = data;
    
    // 可以在这里在页面上显示分析结果提示
    // 例如：显示一个通知卡片
    if (assistantWidget) {
      assistantWidget.updateAnalysis(data);
    }
  }
  
  // 分析当前页面
  async function analyzeCurrentPage() {
    console.log('开始分析当前页面，URL:', window.location.href);
    
    // 重置商品信息，确保使用最新提取的数据
    productInfo = null;
    
    // 先提取商品信息（等待完成）
    await extractProductInfo();
    
    // 如果第一次提取失败，等待页面加载后重试
    if (!productInfo || (!productInfo.name && !productInfo.price)) {
      console.warn('首次提取失败，等待页面加载后重试...');
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 再次提取
      await extractProductInfo();
    }
    
    // 再次检查
    if (!productInfo || (!productInfo.name && !productInfo.price)) {
      console.error('仍然无法提取商品信息');
      showNotification('未能提取商品信息，请确保在商品详情页', 'error');
      
      // 最后一次尝试：等待更长时间（可能是动态加载的页面）
      await new Promise(resolve => setTimeout(resolve, 2000));
      await extractProductInfo();
      
      if (!productInfo || (!productInfo.name && !productInfo.price)) {
        showNotification('无法识别当前页面的商品信息，请手动在侧边栏输入', 'error');
        return;
      }
    }
    
    console.log('商品信息提取成功，开始分析:', productInfo);
    performAnalysis();
  }
  
  // 执行分析
  async function performAnalysis() {
    // 再次确认商品信息是最新的
    if (!productInfo || (!productInfo.name && !productInfo.price)) {
      console.warn('商品信息为空或不完整，重新提取...');
      await extractProductInfo();
    }
    
    if (!productInfo || (!productInfo.name && !productInfo.price)) {
      console.error('商品信息为空，无法进行分析');
      showNotification('商品信息提取失败，请刷新页面后重试', 'error');
      return;
    }
    
    console.log('执行分析，商品信息:', productInfo);
    console.log('商品URL:', window.location.href);
    
    // 保存商品信息到storage，以便侧边栏使用
    try {
      // 先获取当前标签页ID
      let tabId = null;
      try {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tabs[0]) {
          tabId = tabs[0].id;
        }
      } catch (e) {
        console.warn('获取标签页ID失败:', e);
      }
      
      // 保存到storage
      if (chrome.storage && chrome.storage.local && tabId) {
        await chrome.storage.local.set({
          [`product_${tabId}`]: productInfo
        });
        console.log('商品信息已保存到storage:', `product_${tabId}`);
        
        // 同时也保存为current，作为备用
        await chrome.storage.local.set({
          [`product_current`]: productInfo
        });
      }
      
      // 通知background已保存商品信息
      try {
        chrome.runtime.sendMessage({
          action: 'productInfoExtracted',
          productData: productInfo,
          tabId: tabId
        }, (response) => {
          if (chrome.runtime.lastError) {
            console.warn('通知background失败:', chrome.runtime.lastError);
          }
        });
      } catch (e) {
        console.warn('发送通知失败:', e);
      }
    } catch (e) {
      console.error('保存商品信息失败:', e);
    }
    
    // 发送分析请求
    chrome.runtime.sendMessage({
      action: 'apiRequest',
      endpoint: '/api/shopping/product-analysis',
      options: {
        method: 'POST',
        body: productInfo
      }
    }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('API请求错误:', chrome.runtime.lastError);
        showNotification('分析失败: ' + chrome.runtime.lastError.message, 'error');
        return;
      }
      
      if (response && response.success) {
        console.log('分析成功:', response.data);
        showAnalysis(response.data);
        
        // 保存分析结果到storage
        if (chrome.storage && chrome.storage.local) {
          chrome.runtime.sendMessage({ action: 'getCurrentTab' }).then(tab => {
            chrome.storage.local.set({
              [`analysis_${tab?.id || 'current'}`]: response.data
            });
          }).catch(e => console.warn('保存分析结果失败:', e));
        }
        
        // 通知侧边栏更新
        chrome.runtime.sendMessage({
          action: 'analysisComplete',
          productData: productInfo,
          analysisData: response.data
        }).catch(e => console.warn('通知侧边栏失败:', e));
        
        showNotification('分析完成！请查看侧边栏', 'success');
      } else {
        console.error('分析失败:', response);
        showNotification('分析失败: ' + (response?.error || '未知错误'), 'error');
      }
    });
  }
  
  // 显示通知
  function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#007bff'};
      color: white;
      padding: 15px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      z-index: 999999;
      font-size: 14px;
      max-width: 300px;
      animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    // 添加动画样式
    if (!document.getElementById('notification-styles')) {
      const style = document.createElement('style');
      style.id = 'notification-styles';
      style.textContent = `
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `;
      document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
      notification.style.animation = 'slideIn 0.3s ease-out reverse';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }
  
  // 在商品价格旁边显示价格对比按钮
  function addPriceComparisonButton() {
    // 这里可以添加价格对比功能
    // 在商品价格旁边添加一个小按钮
  }
  
})();

