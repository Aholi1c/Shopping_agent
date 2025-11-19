/**
 * Content Script
 * Injected into shopping website pages to extract product information and provide interactive features
 */

(function() {
  'use strict';
  
  let productInfo = null;
  let analysisResult = null;
  let assistantWidget = null;
  
  // Currency symbol mapping
  const currencySymbols = {
    'CNY': '¥',
    'HKD': 'HK$',
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'JPY': 'JP¥',
    'AUD': 'A$',
    'SGD': 'S$',
    'CAD': 'C$'
  };
  
  // Currency detection pattern - improved to handle more cases
  const currencyPattern = /(HK\$|HKD|US\$|USD|\$|¥|CNY|RMB|€|EUR|£|GBP|JP¥|JPY|A\$|AUD|S\$|SGD|C\$|CAD)/i;
  
  // Helper function to detect currency from text and URL
  function detectCurrency(priceText, url = '') {
    if (!priceText) return 'CNY'; // Default to CNY
    
    const currencyMatch = priceText.match(currencyPattern);
    if (currencyMatch) {
      const symbol = currencyMatch[1].toUpperCase();
      
      // Handle HK$ or HKD
      if (symbol.includes('HK$') || symbol === 'HKD') {
        return 'HKD';
      }
      
      // Handle US$ or USD
      if (symbol.includes('US$') || symbol === 'USD') {
        return 'USD';
      }
      
      // Handle $ - need to check URL context
      if (symbol === '$' || symbol === 'USD') {
        const hostname = (url || window.location.href).toLowerCase();
        // Check for Hong Kong domains
        if (hostname.includes('amazon.com.hk') || 
            hostname.includes('amazon.hk') ||
            hostname.includes('.hk/') ||
            hostname.includes('hongkong') ||
            hostname.includes('hktmall') ||
            hostname.includes('hk.') ||
            hostname.includes('.com.hk')) {
          return 'HKD';
        }
        // Check for other USD domains
        if (hostname.includes('amazon.com') && !hostname.includes('amazon.cn') && !hostname.includes('amazon.co.uk')) {
          return 'USD';
        }
        // Default to USD for $ symbol
        return 'USD';
      }
      
      // Handle ¥ - could be CNY or JPY
      if (symbol === '¥' || symbol === 'CNY' || symbol === 'RMB') {
        const hostname = (url || window.location.href).toLowerCase();
        if (hostname.includes('.jp') || hostname.includes('japan')) {
          return 'JPY';
        }
        return 'CNY';
      }
      
      // Handle JP¥ or JPY
      if (symbol.includes('JP¥') || symbol === 'JPY') {
        return 'JPY';
      }
      
      // Handle other currencies
      if (symbol.includes('€') || symbol === 'EUR') return 'EUR';
      if (symbol.includes('£') || symbol === 'GBP') return 'GBP';
      if (symbol.includes('A$') || symbol === 'AUD') return 'AUD';
      if (symbol.includes('S$') || symbol === 'SGD') return 'SGD';
      if (symbol.includes('C$') || symbol === 'CAD') return 'CAD';
    }
    
    // Default based on domain if no symbol found
    const hostname = (url || window.location.href).toLowerCase();
    if (hostname.includes('.hk') || hostname.includes('hongkong')) {
      return 'HKD';
    }
    if (hostname.includes('.jp') || hostname.includes('japan')) {
      return 'JPY';
    }
    if (hostname.includes('amazon.com') && !hostname.includes('amazon.cn') && !hostname.includes('amazon.co.uk')) {
      return 'USD';
    }
    
    // Default to CNY for Chinese platforms
    return 'CNY';
  }
  
  // Initialize
  init();
  
  function init() {
    // Wait for page to load
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', onPageReady);
    } else {
      onPageReady();
    }
    
    // Listen for messages from background
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
    
    // Create floating assistant button
    createFloatingButton();
  }
  
  function onPageReady() {
    // Delay extraction to ensure page is fully loaded
    setTimeout(() => {
      extractProductInfo();
    }, 1000);
  }
  
  // Extract product information
  async function extractProductInfo() {
    const url = window.location.href;
    let info = {};
    
    console.log('Starting to extract product information, URL:', url);
    
    // Extract product information based on different shopping websites
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
    
    console.log('Extracted product information:', info);
    
    if (info.name || info.price) {
      productInfo = {
        ...info,
        url: url,
        platform: detectPlatform(url),
        timestamp: Date.now()
      };
      
      // Immediately save to storage (don't wait for background response)
      try {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tabs[0] && chrome.storage && chrome.storage.local) {
          await chrome.storage.local.set({
            [`product_${tabs[0].id}`]: productInfo,
            [`product_current`]: productInfo
          });
          console.log('Product information saved directly to storage');
        }
      } catch (e) {
        console.warn('Failed to save product information directly:', e);
      }
      
      // Send product information to background
      chrome.runtime.sendMessage({
        action: 'extractProductInfo',
        data: productInfo
      }, (response) => {
        if (chrome.runtime.lastError) {
          console.warn('Failed to send product information to background:', chrome.runtime.lastError);
        } else {
          console.log('Product information sent to background');
        }
      });
    } else {
      console.warn('Unable to extract product information (name or price is empty)');
    }
  }
  
  // Extract JD product information
  function extractJDProductInfo() {
    const info = {};
    
    // Product name - try multiple selectors
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
    
    // Product price - try multiple selectors
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
        // Detect currency using improved detection function
        info.currency = detectCurrency(priceText, window.location.href);
        const cleanedPrice = priceText.replace(/[^\d.]/g, '');
        if (cleanedPrice) {
          info.price = parseFloat(cleanedPrice);
          break;
        }
      }
    }
    
    // Ensure currency is set even if price extraction failed
    if (!info.currency) {
      info.currency = detectCurrency('', window.location.href);
    }
    
    // Product image
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
    
    // Product ID
    const match = window.location.href.match(/(\d+)\.html/);
    if (match) info.productId = match[1];
    
    // Product description - try multiple selectors
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
        // Get description text, clean whitespace and newlines
        let descText = descEl.textContent || descEl.innerText;
        descText = descText.trim().replace(/\s+/g, ' ');
        if (descText && descText.length > 10) {  // Ensure there's actual content
          info.description = descText.substring(0, 2000);  // Limit length
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
        // Detect currency using improved detection function
        info.currency = detectCurrency(priceText, window.location.href);
        const cleanedPrice = priceText.replace(/[^\d.]/g, '');
        if (cleanedPrice) {
          info.price = parseFloat(cleanedPrice);
          break;
        }
      }
    }
    
    // Ensure currency is set even if price extraction failed
    if (!info.currency) {
      info.currency = detectCurrency('', window.location.href);
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
        // Detect currency using improved detection function
        info.currency = detectCurrency(priceText, window.location.href);
        const cleanedPrice = priceText.replace(/[^\d.]/g, '');
        if (cleanedPrice) {
          info.price = parseFloat(cleanedPrice);
          break;
        }
      }
    }
    
    // Ensure currency is set even if price extraction failed
    if (!info.currency) {
      info.currency = detectCurrency('', window.location.href);
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
    
    // Use improved currency detection
    let detectedCurrency = detectCurrency('', window.location.href);
    
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
        
        // Detect currency using improved detection function
        detectedCurrency = detectCurrency(priceText, window.location.href);
        
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
    
    // If price not found yet, try searching for price patterns in page
    if (!info.price) {
      const pricePatterns = [
        /\$\s*([\d,]+\.?\d*)/g,
        /USD\s*([\d,]+\.?\d*)/gi,
        /([\d,]+\.?\d*)\s*USD/gi,
        /HK\$\s*([\d,]+\.?\d*)/gi,
        /HKD\s*([\d,]+\.?\d*)/gi,
        /([\d,]+\.?\d*)\s*HKD/gi,
        /¥\s*([\d,]+\.?\d*)/g,
        /CNY\s*([\d,]+\.?\d*)/gi,
        /([\d,]+\.?\d*)\s*CNY/gi
      ];
      
      for (const pattern of pricePatterns) {
        const matches = document.body.innerText.match(pattern);
        if (matches && matches.length > 0) {
          // Take first matching price
          const priceMatch = matches[0].match(/[\d,]+\.?\d*/);
          if (priceMatch) {
            const cleanedPrice = priceMatch[0].replace(/,/g, '');
            const price = parseFloat(cleanedPrice);
            if (price && price > 0 && price < 100000) { // Reasonable price range
              info.price = price;
              // Detect currency from the matched pattern
              const matchText = matches[0];
              if (matchText.includes('HK$') || matchText.includes('HKD')) {
                info.currency = 'HKD';
              } else if (matchText.includes('$') || matchText.includes('USD')) {
                info.currency = 'USD';
              } else if (matchText.includes('¥') || matchText.includes('CNY')) {
                info.currency = 'CNY';
              } else {
                info.currency = detectedCurrency;
              }
              break;
            }
          }
        }
      }
    }
    
    // Ensure currency is set
    if (!info.currency) {
      info.currency = detectedCurrency;
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
    
    console.log('Amazon product information extraction completed:', info);
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
    button.title = 'Smart Shopping Assistant';
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
  
  // Show analysis result
  function showAnalysis(data) {
    analysisResult = data;
    
    // Can display analysis result prompt on the page here
    // For example: show a notification card
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
    
    // Check again
    if (!productInfo || (!productInfo.name && !productInfo.price)) {
      console.error('Still unable to extract product information');
      showNotification('Unable to extract product information, please ensure you are on a product detail page', 'error');
      
      // Last attempt: wait longer (may be dynamically loaded page)
      await new Promise(resolve => setTimeout(resolve, 2000));
      await extractProductInfo();
      
      if (!productInfo || (!productInfo.name && !productInfo.price)) {
        showNotification('Unable to identify product information on current page, please manually enter in sidepanel', 'error');
        return;
      }
    }
    
    console.log('Product information extracted successfully, starting analysis:', productInfo);
    performAnalysis();
  }
  
  // Perform analysis
  async function performAnalysis() {
    // Confirm product information is up-to-date again
    if (!productInfo || (!productInfo.name && !productInfo.price)) {
      console.warn('Product information is empty or incomplete, re-extracting...');
      await extractProductInfo();
    }
    
    if (!productInfo || (!productInfo.name && !productInfo.price)) {
      console.error('Product information is empty, unable to perform analysis');
      showNotification('Product information extraction failed, please refresh the page and try again', 'error');
      return;
    }
    
    console.log('Performing analysis, product information:', productInfo);
    console.log('Product URL:', window.location.href);
    
    // Save product information to storage for sidepanel use
    try {
      // First get current tab ID
      let tabId = null;
      try {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tabs[0]) {
          tabId = tabs[0].id;
        }
      } catch (e) {
        console.warn('Failed to get tab ID:', e);
      }
      
      // Save to storage
      if (chrome.storage && chrome.storage.local && tabId) {
        await chrome.storage.local.set({
          [`product_${tabId}`]: productInfo
        });
        console.log('Product information saved to storage:', `product_${tabId}`);
        
        // Also save as current as backup
        await chrome.storage.local.set({
          [`product_current`]: productInfo
        });
      }
      
      // Notify background that product information has been saved
      try {
        chrome.runtime.sendMessage({
          action: 'productInfoExtracted',
          productData: productInfo,
          tabId: tabId
        }, (response) => {
          if (chrome.runtime.lastError) {
            console.warn('Failed to notify background:', chrome.runtime.lastError);
          }
        });
      } catch (e) {
        console.warn('Failed to send notification:', e);
      }
    } catch (e) {
      console.error('Failed to save product information:', e);
    }
    
    // Send analysis request
    chrome.runtime.sendMessage({
      action: 'apiRequest',
      endpoint: '/api/shopping/product-analysis',
      options: {
        method: 'POST',
        body: productInfo
      }
    }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('API request error:', chrome.runtime.lastError);
        showNotification('Analysis failed: ' + chrome.runtime.lastError.message, 'error');
        return;
      }
      
      if (response && response.success) {
        console.log('Analysis successful:', response.data);
        showAnalysis(response.data);
        
        // Save analysis result to storage
        if (chrome.storage && chrome.storage.local) {
          chrome.runtime.sendMessage({ action: 'getCurrentTab' }).then(tab => {
            chrome.storage.local.set({
              [`analysis_${tab?.id || 'current'}`]: response.data
            });
          }).catch(e => console.warn('Failed to save analysis result:', e));
        }
        
        // Notify sidepanel to update
        chrome.runtime.sendMessage({
          action: 'analysisComplete',
          productData: productInfo,
          analysisData: response.data
        }).catch(e => console.warn('Failed to notify sidepanel:', e));
        
        showNotification('Analysis completed! Please check the sidepanel', 'success');
      } else {
        console.error('Analysis failed:', response);
        showNotification('Analysis failed: ' + (response?.error || 'Unknown error'), 'error');
      }
    });
  }
  
  // Show notification
  function showNotification(message, type = 'info') {
    // Create notification element
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
    
    // Add animation styles
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
    
    // Auto remove after 3 seconds
    setTimeout(() => {
      notification.style.animation = 'slideIn 0.3s ease-out reverse';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }
  
  // Display price comparison button next to product price
  function addPriceComparisonButton() {
    // Can add price comparison functionality here
    // Add a small button next to product price
  }
  
})();

