/**
 * Popup Script
 * 处理弹窗界面的逻辑
 */

(async () => {
  // 初始化
  init();
  
  async function init() {
    // 检查当前标签页
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs[0]) {
      await loadProductInfo(tabs[0].id);
    }
    
    // 设置事件监听
    setupEventListeners();
    
    // 检查连接状态
    checkConnectionStatus();
  }
  
  async function loadProductInfo(tabId) {
    try {
      const result = await chrome.storage.local.get([`product_${tabId}`]);
      const productInfo = result[`product_${tabId}`];
      
      if (productInfo) {
        displayProductInfo(productInfo);
      } else {
        showNoProduct();
      }
    } catch (error) {
      console.error('Error loading product info:', error);
      showNoProduct();
    }
  }
  
  function displayProductInfo(productInfo) {
    const productCard = document.getElementById('current-product');
    const noProduct = document.getElementById('no-product');
    
    productCard.style.display = 'block';
    noProduct.style.display = 'none';
    
    document.getElementById('product-name').textContent = productInfo.name || '未知商品';
    document.getElementById('product-price').textContent = productInfo.price || '0.00';
  }
  
  function showNoProduct() {
    const productCard = document.getElementById('current-product');
    const noProduct = document.getElementById('no-product');
    
    productCard.style.display = 'none';
    noProduct.style.display = 'block';
  }
  
  function setupEventListeners() {
    // 打开侧边栏
    document.getElementById('open-sidepanel').addEventListener('click', async () => {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs[0]) {
        chrome.sidePanel.open({ tabId: tabs[0].id });
        window.close();
      }
    });
    
    document.getElementById('open-sidepanel-btn').addEventListener('click', async () => {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs[0]) {
        chrome.sidePanel.open({ tabId: tabs[0].id });
        window.close();
      }
    });
    
    // 分析商品
    document.getElementById('analyze-btn').addEventListener('click', async () => {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, { action: 'analyzeCurrentPage' });
        chrome.sidePanel.open({ tabId: tabs[0].id });
        window.close();
      }
    });
    
    // 价格对比
    document.getElementById('compare-btn').addEventListener('click', async () => {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs[0]) {
        chrome.sidePanel.open({ tabId: tabs[0].id });
        // 在侧边栏中打开价格对比页面
        chrome.runtime.sendMessage({
          action: 'openSidePanel',
          view: 'price-comparison'
        });
        window.close();
      }
    });
    
    // 价格追踪
    document.getElementById('price-tracker').addEventListener('click', async () => {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs[0]) {
        chrome.sidePanel.open({ tabId: tabs[0].id });
        chrome.runtime.sendMessage({
          action: 'openSidePanel',
          view: 'price-tracker'
        });
        window.close();
      }
    });
    
    // 比价
    document.getElementById('compare-prices').addEventListener('click', async () => {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs[0]) {
        chrome.sidePanel.open({ tabId: tabs[0].id });
        chrome.runtime.sendMessage({
          action: 'openSidePanel',
          view: 'price-comparison'
        });
        window.close();
      }
    });
    
    // 推荐
    document.getElementById('recommendations').addEventListener('click', async () => {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs[0]) {
        chrome.sidePanel.open({ tabId: tabs[0].id });
        chrome.runtime.sendMessage({
          action: 'openSidePanel',
          view: 'recommendations'
        });
        window.close();
      }
    });
  }
  
  async function checkConnectionStatus() {
    const config = await chrome.storage.sync.get(['config']);
    const apiUrl = config.config?.apiUrl || 'http://localhost:8000';
    
    try {
      const response = await fetch(`${apiUrl}/health`);
      const data = await response.json();
      
      const statusEl = document.getElementById('connection-status');
      const statusDot = statusEl.querySelector('.status-dot');
      
      if (data.status === 'healthy') {
        statusDot.style.backgroundColor = '#52c41a';
        statusEl.querySelector('span:last-child').textContent = '已连接';
      } else {
        statusDot.style.backgroundColor = '#ff4d4f';
        statusEl.querySelector('span:last-child').textContent = '连接失败';
      }
    } catch (error) {
      const statusEl = document.getElementById('connection-status');
      const statusDot = statusEl.querySelector('.status-dot');
      statusDot.style.backgroundColor = '#ff4d4f';
      statusEl.querySelector('span:last-child').textContent = '连接失败';
    }
  }
})();

