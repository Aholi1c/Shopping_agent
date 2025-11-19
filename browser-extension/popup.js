/**
 * Popup Script
 * Handles popup interface logic
 */

(async () => {
  // Initialize
  init();
  
  async function init() {
    // Check current tab
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs[0]) {
      await loadProductInfo(tabs[0].id);
    }
    
    // Setup event listeners
    setupEventListeners();
    
    // Check connection status
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
    
    document.getElementById('product-name').textContent = productInfo.name || 'Unknown Product';
    document.getElementById('product-price').textContent = productInfo.price || '0.00';
  }
  
  function showNoProduct() {
    const productCard = document.getElementById('current-product');
    const noProduct = document.getElementById('no-product');
    
    productCard.style.display = 'none';
    noProduct.style.display = 'block';
  }
  
  function setupEventListeners() {
    // Open sidepanel
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
    
    // Analyze product
    document.getElementById('analyze-btn').addEventListener('click', async () => {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, { action: 'analyzeCurrentPage' });
        chrome.sidePanel.open({ tabId: tabs[0].id });
        window.close();
      }
    });
    
    // Price comparison
    document.getElementById('compare-btn').addEventListener('click', async () => {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs[0]) {
        chrome.sidePanel.open({ tabId: tabs[0].id });
        // Open price comparison page in sidepanel
        chrome.runtime.sendMessage({
          action: 'openSidePanel',
          view: 'price-comparison'
        });
        window.close();
      }
    });
    
    // Price tracker
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
    
    // Compare prices
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
    
    // Recommendations
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
        statusEl.querySelector('span:last-child').textContent = 'Connected';
      } else {
        statusDot.style.backgroundColor = '#ff4d4f';
        statusEl.querySelector('span:last-child').textContent = 'Connection Failed';
      }
    } catch (error) {
      const statusEl = document.getElementById('connection-status');
      const statusDot = statusEl.querySelector('.status-dot');
      statusDot.style.backgroundColor = '#ff4d4f';
      statusEl.querySelector('span:last-child').textContent = 'Connection Failed';
    }
  }
})();

