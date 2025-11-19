/**
 * Sidepanel Script
 * Main application script for the sidepanel
 * This is a simplified version. For a full React application, build tools are required.
 */

(function() {
  'use strict';
  
  let currentProduct = null;
  let currentView = 'chat'; // chat, analysis, comparison, tracker
  
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
  
  // Format price with currency symbol
  function formatPrice(price, currency = 'CNY') {
    const symbol = currencySymbols[currency] || '¥';
    const formattedPrice = typeof price === 'number' ? price.toFixed(2) : parseFloat(price || 0).toFixed(2);
    return `${symbol}${formattedPrice}`;
  }
  
  // Initialize
  init();
  
  async function init() {
    console.log('Sidepanel initializing...');
    
    // Listen for messages from background
    if (chrome.runtime && chrome.runtime.onMessage) {
      chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        console.log('Sidepanel received message:', request.action, request);
        
        if (request.action === 'startAnalysis') {
          console.log('Received analysis request:', request);
          if (request.productData) {
            currentProduct = request.productData;
            console.log('Setting current product:', currentProduct);
            
            // Automatically switch to analysis view
            currentView = 'analysis';
            
            // Save product info to storage
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
              if (tabs[0] && chrome.storage && chrome.storage.local) {
                chrome.storage.local.set({
                  [`product_${tabs[0].id}`]: request.productData
                });
              }
            });
            
            // Re-render
            render();
            setupEventListeners();
            
            // Wait for DOM update then trigger analysis
            setTimeout(() => {
              console.log('Attempting to trigger analyze button...');
              const analyzeBtn = document.getElementById('analyze-btn');
              if (analyzeBtn) {
                console.log('Found analyze button, clicking...');
                analyzeBtn.click();
              } else {
                console.warn('Analyze button not found, waiting longer...');
                setTimeout(() => {
                  const btn = document.getElementById('analyze-btn');
                  if (btn) {
                    btn.click();
                  } else {
                    console.error('Still cannot find analyze button');
                  }
                }, 500);
              }
            }, 200);
          }
          sendResponse({ success: true });
        } else if (request.action === 'updateProduct') {
          // Update product information
          if (request.productData) {
            currentProduct = request.productData;
            render();
            setupEventListeners();
          }
          sendResponse({ success: true });
        }
        return true;
      });
    }
    
    // Get current tab
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs[0]) {
      console.log('Current tab:', tabs[0].id);
      // Load product information from current page
      await loadProductInfo(tabs[0].id);
      
      // Render interface
      render();
      
      // Setup event listeners
      setupEventListeners();
    }
  }
  
  async function loadProductInfo(tabId) {
    try {
      // First check if there's an analysis request
      const analysisRequest = await chrome.storage.local.get([`analysis_request_${tabId}`]);
      if (analysisRequest[`analysis_request_${tabId}`]) {
        const request = analysisRequest[`analysis_request_${tabId}`];
        console.log('Found analysis request:', request);
        if (request.productData) {
          currentProduct = request.productData;
          currentView = 'analysis';
          
          // Clear request marker
          chrome.storage.local.remove([`analysis_request_${tabId}`]);
          
          // Immediately trigger analysis
          setTimeout(() => {
            const analyzeBtn = document.getElementById('analyze-btn');
            if (analyzeBtn) {
              console.log('Auto-triggering analysis...');
              analyzeBtn.click();
            }
          }, 300);
          
          return;
        }
      }
      
      // Load product information
      const result = await chrome.storage.local.get([`product_${tabId}`, `product_current`]);
      const productInfo = result[`product_${tabId}`] || result[`product_current`];
      
      if (productInfo) {
        console.log('Loaded product information:', productInfo);
        currentProduct = productInfo;
      } else {
        console.log('Product information not found, attempting to extract from page...');
        // Try to extract from current page
        try {
          const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
          if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, {
              action: 'extractProductInfo'
            }, (response) => {
              if (response && response.success) {
                console.log('Product information extracted from page:', response);
              }
            });
          }
        } catch (e) {
          console.warn('Unable to extract product information from page:', e);
        }
      }
    } catch (error) {
      console.error('Error loading product info:', error);
    }
  }
  
  function render() {
    const root = document.getElementById('root');
    
    root.innerHTML = `
      <div class="sidepanel-container">
        <div class="sidepanel-header">
          <h2>🛍️ Smart Shopping Assistant</h2>
          <div class="header-actions">
            <button id="refresh-btn" class="icon-btn" title="Refresh">🔄</button>
            <button id="settings-btn" class="icon-btn" title="Settings">⚙️</button>
          </div>
        </div>
        
        <div class="sidepanel-tabs">
          <button class="tab-btn ${currentView === 'chat' ? 'active' : ''}" data-view="chat">💬 Chat</button>
          <button class="tab-btn ${currentView === 'analysis' ? 'active' : ''}" data-view="analysis">📊 Analysis</button>
          <button class="tab-btn ${currentView === 'comparison' ? 'active' : ''}" data-view="comparison">🔍 Compare</button>
          <button class="tab-btn ${currentView === 'tracker' ? 'active' : ''}" data-view="tracker">📈 Tracker</button>
        </div>
        
        <div class="sidepanel-content">
          ${renderCurrentView()}
        </div>
      </div>
    `;
    
    // Bind events
    setupEventListeners();
  }
  
  function renderCurrentView() {
    switch (currentView) {
      case 'chat':
        return renderChatView();
      case 'analysis':
        return renderAnalysisView();
      case 'comparison':
        return renderComparisonView();
      case 'tracker':
        return renderTrackerView();
      default:
        return renderChatView();
    }
  }
  
  function renderChatView() {
    return `
      <div class="view-container chat-view">
        ${currentProduct ? `
          <div class="current-product-card">
            <h3>Current Product</h3>
            <div class="product-info">
              <div class="product-name">${currentProduct.name || 'Unknown Product'}</div>
              <div class="product-price">${formatPrice(currentProduct.price || 0, currentProduct.currency || 'CNY')}</div>
            </div>
          </div>
        ` : ''}
        
        <div class="chat-messages" id="chat-messages">
          <div class="message assistant">
            <div class="message-content">
              Hello! I'm your smart shopping assistant. How can I help you?
            </div>
          </div>
        </div>
        
        <div class="chat-input-container">
          <textarea id="chat-input" placeholder="Enter your question..." rows="3"></textarea>
          <button id="send-btn" class="send-btn">Send</button>
        </div>
      </div>
    `;
  }
  
  function renderAnalysisView() {
    if (!currentProduct) {
      return `
        <div class="empty-state">
          <p>Please visit a product page first</p>
        </div>
      `;
    }
    
    return `
      <div class="view-container analysis-view">
        <div class="analysis-card">
          <h3>Product Information</h3>
          <div class="info-item">
            <label>Product Name:</label>
            <span>${currentProduct.name || 'Unknown'}</span>
          </div>
          <div class="info-item">
            <label>Current Price:</label>
            <span class="price">${formatPrice(currentProduct.price || 0, currentProduct.currency || 'CNY')}</span>
          </div>
          <div class="info-item">
            <label>Platform:</label>
            <span>${currentProduct.platform || 'Unknown'}</span>
          </div>
        </div>
        
        <div class="analysis-actions">
          <button id="analyze-btn" class="action-button primary">Analyze Product</button>
          <button id="risk-btn" class="action-button secondary">Risk Analysis</button>
          <button id="predict-btn" class="action-button secondary">Price Prediction</button>
        </div>
        
        <div id="analysis-result" class="analysis-result"></div>
      </div>
    `;
  }
  
  function renderComparisonView() {
    return `
      <div class="view-container comparison-view">
        <div class="comparison-form">
          <input type="text" id="product-search" placeholder="Enter product name to search..." />
          <button id="search-btn" class="search-btn">Search</button>
        </div>
        
        <div id="comparison-results" class="comparison-results"></div>
      </div>
    `;
  }
  
  function renderTrackerView() {
    return `
      <div class="view-container tracker-view">
        <div class="tracker-form">
          <input type="number" id="target-price" placeholder="Target Price" />
          <button id="track-btn" class="track-btn">Start Tracking</button>
        </div>
        
        <div id="tracker-list" class="tracker-list"></div>
      </div>
    `;
  }
  
  function setupEventListeners() {
    // Tab switching
    const tabButtons = document.querySelectorAll('.tab-btn');
    if (tabButtons.length > 0) {
      tabButtons.forEach(btn => {
        // Remove old listeners (if they exist)
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        newBtn.addEventListener('click', () => {
          console.log('Switching to view:', newBtn.dataset.view);
          document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
          newBtn.classList.add('active');
          currentView = newBtn.dataset.view;
          
          // Re-render content
          const content = document.querySelector('.sidepanel-content');
          if (content) {
            content.innerHTML = renderCurrentView();
            setupViewEventListeners();
          }
        });
      });
    }
    
    // Refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', async () => {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tabs[0]) {
          chrome.tabs.reload(tabs[0].id);
          await loadProductInfo(tabs[0].id);
          render();
        }
      });
    }
    
    // Setup view-specific event listeners
    setupViewEventListeners();
  }
  
  function setupViewEventListeners() {
    if (currentView === 'chat') {
      const sendBtn = document.getElementById('send-btn');
      const chatInput = document.getElementById('chat-input');
      
      if (sendBtn && chatInput) {
        const sendMessage = async () => {
          const message = chatInput.value.trim();
          if (!message) return;
          
          // Display user message
          addChatMessage('user', message);
          chatInput.value = '';
          
          // Send to API
          try {
            const response = await window.apiClient.sendChatMessage(message, null, {
              message_type: 'text',
              model: 'glm-4-0520',
              use_memory: true,  // Enable memory function, let agent remember user preferences
              use_rag: false
            });
            addChatMessage('assistant', response.response || 'Sorry, I cannot answer your question.');
          } catch (error) {
            console.error('Failed to send message:', error);
            let errorMessage = 'Sorry, connection failed. Please check your network connection.';
            if (error.message) {
              if (error.message.includes('Failed to connect') || error.message.includes('Failed to connect to server')) {
                errorMessage = 'Failed to connect to backend service. Please ensure the backend service is running at http://localhost:8000';
              } else if (error.message.includes('LLM')) {
                errorMessage = 'AI service error: ' + error.message.substring(0, 100);
              } else {
                errorMessage = 'Error: ' + error.message.substring(0, 100);
              }
            }
            addChatMessage('assistant', errorMessage);
          }
        };
        
        sendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
          }
        });
      }
    } else if (currentView === 'analysis') {
      const analyzeBtn = document.getElementById('analyze-btn');
      const riskBtn = document.getElementById('risk-btn');
      const predictBtn = document.getElementById('predict-btn');
      
      if (analyzeBtn && currentProduct) {
        analyzeBtn.addEventListener('click', async () => {
          console.log('Analyze button clicked, current product:', currentProduct);
          
          // Validate product information
          if (!currentProduct.name && !currentProduct.title) {
            const resultDiv = document.getElementById('analysis-result');
            resultDiv.innerHTML = `
              <div class="error">
                <p>❌ Unable to analyze: Product information incomplete</p>
                <p style="font-size: 0.8em; color: #666; margin-top: 10px;">
                  Please ensure you are on a product detail page, or manually enter product information
                </p>
              </div>
            `;
            return;
          }
          
          analyzeBtn.disabled = true;
          analyzeBtn.textContent = 'Analyzing...';
          const resultDiv = document.getElementById('analysis-result');
          resultDiv.innerHTML = '<div class="loading">Analyzing product, please wait...</div>';
          
          try {
            // Ensure product data format is correct
            const productDataToSend = {
              name: currentProduct.name || currentProduct.title || '',
              price: currentProduct.price || 0,
              platform: currentProduct.platform || 'unknown',
              productId: currentProduct.productId || currentProduct.id || '',
              image: currentProduct.image || currentProduct.image_url || '',
              url: currentProduct.url || window.location?.href || '',
              description: currentProduct.description || '',
              parameters: currentProduct.parameters || {}
            };
            
            console.log('Sending analysis request, product data:', productDataToSend);
            
            const result = await window.apiClient.analyzeProduct(productDataToSend);
            console.log('Received analysis result:', result);
            
            const analysis = result.data || result;
            
            if (!analysis || (analysis.error && !analysis.comprehensive_analysis)) {
              throw new Error(analysis?.error || 'Analysis failed: No valid result returned');
            }
            
            resultDiv.innerHTML = `
              <div class="result-content">
                <h4>📊 Comprehensive Analysis</h4>
                <div class="analysis-text">${formatAnalysisText(analysis.comprehensive_analysis || analysis.analysis || 'Analysis completed but no detailed report generated')}</div>
                
                ${analysis.recommendation ? `
                  <div class="recommendation">
                    <h5>💡 Purchase Recommendation</h5>
                    <p><strong>Action:</strong>${getActionText(analysis.recommendation.action)}</p>
                    <p><strong>Confidence:</strong>${(analysis.recommendation.confidence * 100).toFixed(0)}%</p>
                    ${analysis.recommendation.reason ? `<p><strong>Reason:</strong>${analysis.recommendation.reason}</p>` : ''}
                  </div>
                ` : ''}
                
                ${analysis.price_analysis && !analysis.price_analysis.error ? `
                  <div class="price-analysis">
                    <h5>💰 Price Analysis</h5>
                    <p>Current Price: ${formatPrice(analysis.price_analysis.current_price || currentProduct.price || 0, currentProduct.currency || 'CNY')}</p>
                    <p>Platform: ${analysis.price_analysis.platform || currentProduct.platform || 'Unknown'}</p>
                    ${analysis.price_analysis.lowest_found_price ? `
                      <p>Lowest Price: ${formatPrice(analysis.price_analysis.lowest_found_price, 'CNY')}</p>
                      ${analysis.price_analysis.savings_potential > 0 ? `
                        <p class="savings">Potential Savings: ${formatPrice(analysis.price_analysis.savings_potential, 'CNY')}</p>
                      ` : ''}
                    ` : ''}
                  </div>
                ` : ''}
                
                ${analysis.risk_analysis && !analysis.risk_analysis.error ? `
                  <div class="risk-analysis">
                    <h5>⚠️ Risk Assessment</h5>
                    <p>Risk Level: <span class="risk-level risk-${analysis.risk_analysis.overall_risk_level || 'unknown'}">${getRiskLevelText(analysis.risk_analysis.overall_risk_level || 'unknown')}</span></p>
                    <p>Risks Found: ${analysis.risk_analysis.risk_count || 0}</p>
                  </div>
                ` : ''}
              </div>
            `;
          } catch (error) {
            console.error('Analysis error:', error);
            let errorMsg = 'Unknown error';
            if (error && typeof error === 'object') {
              if (error.message) {
                errorMsg = error.message;
              } else if (error.detail) {
                errorMsg = error.detail;
              } else if (error.error) {
                errorMsg = typeof error.error === 'string' ? error.error : JSON.stringify(error.error);
              } else {
                errorMsg = JSON.stringify(error).substring(0, 200);
              }
            } else if (typeof error === 'string') {
              errorMsg = error;
            }
            
            resultDiv.innerHTML = `
              <div class="error">
                <p>❌ Analysis failed: ${errorMsg}</p>
                <p style="font-size: 0.8em; color: #666; margin-top: 10px;">
                  Please ensure the backend service is running at http://localhost:8000<br>
                  If the problem persists, please check the browser console and backend logs
                </p>
              </div>
            `;
          } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Product';
          }
        });
      } else if (analyzeBtn && !currentProduct) {
        // If button exists but no product information, show prompt
        analyzeBtn.addEventListener('click', () => {
          const resultDiv = document.getElementById('analysis-result');
          resultDiv.innerHTML = `
            <div class="error">
              <p>❌ Unable to analyze: Product information not detected</p>
              <p style="font-size: 0.8em; color: #666; margin-top: 10px;">
                Please ensure you are on a product detail page, or refresh the page and try again
              </p>
            </div>
          `;
        });
      }
      
      if (riskBtn && currentProduct) {
        riskBtn.addEventListener('click', async () => {
          riskBtn.disabled = true;
          riskBtn.textContent = 'Analyzing...';
          const resultDiv = document.getElementById('analysis-result');
          resultDiv.innerHTML = '<div class="loading">Performing risk assessment...</div>';
          
          try {
            const result = await window.apiClient.analyzeProduct(currentProduct);
            const riskAnalysis = result.data?.risk_analysis || result.risk_analysis;
            
            if (riskAnalysis && !riskAnalysis.error) {
              resultDiv.innerHTML = `
                <div class="result-content">
                  <h4>⚠️ Risk Assessment Report</h4>
                  <div class="risk-level-badge risk-${riskAnalysis.overall_risk_level || 'unknown'}">
                    ${getRiskLevelText(riskAnalysis.overall_risk_level || 'unknown')}
                  </div>
                  
                  ${riskAnalysis.detailed_risks && riskAnalysis.detailed_risks.length > 0 ? `
                    <div class="risks-list">
                      <h5>Risks Found:</h5>
                      ${riskAnalysis.detailed_risks.map(risk => `
                        <div class="risk-item">
                          <strong>${risk.risk_type || 'Unknown Type'}</strong>
                          <p>${risk.evidence || 'No detailed information'}</p>
                          <span class="severity">Severity: ${((risk.severity || 0) * 100).toFixed(0)}%</span>
                        </div>
                      `).join('')}
                    </div>
                  ` : '<p>No significant risks found</p>'}
                  
                  ${riskAnalysis.mitigation_suggestions && riskAnalysis.mitigation_suggestions.length > 0 ? `
                    <div class="suggestions">
                      <h5>💡 Suggestions:</h5>
                      <ul>
                        ${riskAnalysis.mitigation_suggestions.map(s => `<li>${s}</li>`).join('')}
                      </ul>
                    </div>
                  ` : ''}
                </div>
              `;
            } else {
              resultDiv.innerHTML = '<div class="error">Risk assessment failed or no risks found</div>';
            }
          } catch (error) {
            console.error('Risk analysis error:', error);
            resultDiv.innerHTML = `<div class="error">❌ Risk assessment failed: ${error.message || 'Unknown error'}</div>`;
          } finally {
            riskBtn.disabled = false;
            riskBtn.textContent = 'Risk Analysis';
          }
        });
      }
      
      if (predictBtn && currentProduct) {
        predictBtn.addEventListener('click', async () => {
          predictBtn.disabled = true;
          predictBtn.textContent = 'Predicting...';
          const resultDiv = document.getElementById('analysis-result');
          resultDiv.innerHTML = '<div class="loading">Performing price prediction...</div>';
          
          try {
            if (currentProduct.productId) {
              const result = await window.apiClient.predictPrice(currentProduct.productId);
              resultDiv.innerHTML = `
                <div class="result-content">
                  <h4>📈 Price Prediction</h4>
                  <pre>${JSON.stringify(result, null, 2)}</pre>
                </div>
              `;
            } else {
              resultDiv.innerHTML = '<div class="error">Unable to predict price: Product ID missing</div>';
            }
          } catch (error) {
            console.error('Price prediction error:', error);
            resultDiv.innerHTML = `<div class="error">❌ Price prediction failed: ${error.message || 'Unknown error'}</div>`;
          } finally {
            predictBtn.disabled = false;
            predictBtn.textContent = 'Price Prediction';
          }
        });
      }
    } else if (currentView === 'comparison') {
      const searchBtn = document.getElementById('search-btn');
      const productSearch = document.getElementById('product-search');
      
      if (searchBtn && productSearch) {
        const performComparison = async () => {
          const query = productSearch.value.trim();
          if (!query) {
            alert('Please enter a product name');
            return;
          }
          
          searchBtn.disabled = true;
          searchBtn.textContent = 'Searching...';
          const resultsDiv = document.getElementById('comparison-results');
          resultsDiv.innerHTML = '<div class="loading">Searching and comparing prices...</div>';
          
          try {
            const result = await window.apiClient.comparePrices(query);
            console.log('Price comparison result:', result);
            
            // Handle different return formats
            let comparison = result.comparison || result.data?.comparison || {};
            const totalProducts = result.total_products || 0;
            const message = result.message || '';
            const dataSource = result.data_source || 'unknown';
            
            if (Object.keys(comparison).length > 0) {
              // Check if it's all_products format
              if (comparison.all_products) {
                const allProducts = comparison.all_products;
                const platformPrices = allProducts.platform_prices || {};
                const products = allProducts.products || [];
                
                resultsDiv.innerHTML = `
                  <div class="comparison-results-content">
                    <h4>💰 Price Comparison Results</h4>
                    <p style="font-size: 0.9em; color: #666;">Data Source: ${dataSource === 'database' ? 'Database' : 'API'} | Found ${totalProducts} products</p>
                    ${Object.entries(platformPrices).map(([platform, platformProducts]) => {
                      if (Array.isArray(platformProducts)) {
                        return `
                          <div class="comparison-group">
                            <h5>${platform.toUpperCase()} Platform</h5>
                            <div class="products-list">
                              ${platformProducts.map(p => `
                                <div class="product-item">
                                  <strong>${p.title || p.name || 'Unknown Product'}</strong>
                                  <span class="price">${formatPrice(p.price || 0, p.currency || 'CNY')}</span>
                                  ${p.product_id ? `<span class="product-id">ID: ${p.product_id}</span>` : ''}
                                  ${p.product_url ? `<a href="${p.product_url}" target="_blank" class="product-link">View Product</a>` : ''}
                                </div>
                              `).join('')}
                            </div>
                          </div>
                        `;
                      } else {
                        return `
                          <div class="comparison-group">
                            <h5>${platform.toUpperCase()} Platform</h5>
                            <div class="price-comparison">
                              <p>Price: ${formatPrice(platformProducts.price || 0, platformProducts.currency || 'CNY')}</p>
                              <p>${platformProducts.title || ''}</p>
                              ${platformProducts.product_url ? `<a href="${platformProducts.product_url}" target="_blank">View Product</a>` : ''}
                            </div>
                          </div>
                        `;
                      }
                    }).join('')}
                  </div>
                `;
              } else {
                // Standard format - has product groups
                resultsDiv.innerHTML = `
                  <div class="comparison-results-content">
                    <h4>💰 Price Comparison Results</h4>
                    <p style="font-size: 0.9em; color: #666;">Found ${totalProducts} products | Data Source: ${dataSource === 'database' ? 'Database' : 'API'}</p>
                    ${Object.entries(comparison).map(([productKey, data]) => {
                      // Handle different data formats
                      const products = data.products || [];
                      const platformPrices = data.platform_prices || {};
                      
                      // If platform_prices exists, use it first
                      if (platformPrices && Object.keys(platformPrices).length > 0) {
                        return `
                          <div class="comparison-group">
                            <h5>${productKey}</h5>
                            <div class="price-comparison">
                              ${data.min_price ? `<p><strong>Lowest Price:</strong> ${formatPrice(data.min_price, 'CNY')}</p>` : ''}
                              ${data.max_price ? `<p><strong>Highest Price:</strong> ${formatPrice(data.max_price, 'CNY')}</p>` : ''}
                              ${data.price_diff ? `<p><strong>Price Difference:</strong> ${formatPrice(data.price_diff, 'CNY')}</p>` : ''}
                              ${data.price_diff_percent ? `<p><strong>Savings:</strong> ${data.price_diff_percent.toFixed(1)}%</p>` : ''}
                              ${data.best_platform ? `<p><strong>Best Platform:</strong> ${data.best_platform}</p>` : ''}
                            </div>
                            <div class="platform-prices">
                              ${Object.entries(platformPrices).map(([platform, info]) => `
                                <div class="platform-price-item ${platform === data.best_platform ? 'best-price' : ''}">
                                  <span class="platform-badge platform-${platform}">${platform.toUpperCase()}</span>
                                  <span class="price">${formatPrice(info.price || 0, info.currency || 'CNY')}</span>
                                  <div class="product-info">
                                    <div class="product-title">${info.title || ''}</div>
                                    ${info.product_url ? `<a href="${info.product_url}" target="_blank" class="product-link">View Product</a>` : ''}
                                  </div>
                                </div>
                              `).join('')}
                            </div>
                          </div>
                        `;
                      } else if (products.length > 0) {
                        // Fallback to products list
                        return `
                          <div class="comparison-group">
                            <h5>${productKey}</h5>
                            <div class="price-comparison">
                              ${data.min_price ? `<p><strong>Lowest Price:</strong> ${formatPrice(data.min_price, 'CNY')}</p>` : ''}
                              ${data.max_price ? `<p><strong>Highest Price:</strong> ${formatPrice(data.max_price, 'CNY')}</p>` : ''}
                              ${data.price_difference ? `<p><strong>Price Difference:</strong> ${formatPrice(data.price_difference, 'CNY')}</p>` : ''}
                              ${data.savings_percentage ? `<p><strong>Savings:</strong> ${data.savings_percentage.toFixed(1)}%</p>` : ''}
                              ${data.best_platform ? `<p><strong>Best Platform:</strong> ${data.best_platform}</p>` : ''}
                            </div>
                            <div class="products-list">
                              ${products.map(p => `
                                <div class="product-item">
                                  <strong>${p.title || p.name || productKey}</strong>
                                  <span class="platform-badge platform-${p.platform}">${p.platform || 'Unknown'}</span>
                                  <span class="price">${formatPrice(p.price || 0, p.currency || 'CNY')}</span>
                                  ${p.product_url ? `<a href="${p.product_url}" target="_blank" class="product-link">View</a>` : ''}
                                </div>
                              `).join('')}
                            </div>
                          </div>
                        `;
                      } else {
                        // Only basic information
                        return `
                          <div class="comparison-group">
                            <h5>${productKey}</h5>
                            <p>Product Count: ${data.product_count || 0}</p>
                            <p>Platforms: ${(data.platforms || []).join(', ')}</p>
                          </div>
                        `;
                      }
                    }).join('')}
                  </div>
                `;
              }
            } else {
              // No results found
              let errorMsg = message || 'No price comparison results found';
              if (totalProducts > 0) {
                errorMsg = `Found ${totalProducts} products, but unable to perform price comparison. ${message || 'Please try using more specific keywords.'}`;
              } else {
                errorMsg = `${message || 'No price comparison results found. Please ensure product data has been uploaded to the database, or try using more specific keywords.'}`;
              }
              resultsDiv.innerHTML = `<div class="error">${errorMsg}</div>`;
            }
          } catch (error) {
            console.error('Comparison error:', error);
            // Better error handling
            let errorMessage = 'Unknown error';
            if (error && typeof error === 'object') {
              if (error.message) {
                errorMessage = error.message;
              } else if (error.detail) {
                errorMessage = error.detail;
              } else if (error.error) {
                errorMessage = typeof error.error === 'string' ? error.error : JSON.stringify(error.error);
              } else {
                errorMessage = JSON.stringify(error).substring(0, 200);
              }
            } else if (typeof error === 'string') {
              errorMessage = error;
            }
            resultsDiv.innerHTML = `<div class="error">❌ Price comparison failed: ${errorMessage}</div>`;
          } finally {
            searchBtn.disabled = false;
            searchBtn.textContent = 'Search';
          }
        };
        
        searchBtn.addEventListener('click', performComparison);
        productSearch.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') {
            performComparison();
          }
        });
      }
    } else if (currentView === 'tracker') {
      const trackBtn = document.getElementById('track-btn');
      const targetPriceInput = document.getElementById('target-price');
      
      if (trackBtn && targetPriceInput && currentProduct) {
        trackBtn.addEventListener('click', async () => {
          const targetPrice = parseFloat(targetPriceInput.value);
          if (!targetPrice || targetPrice <= 0) {
            alert('Please enter a valid target price');
            return;
          }
          
          if (!currentProduct.productId) {
            alert('Unable to track: Product ID missing');
            return;
          }
          
          trackBtn.disabled = true;
          trackBtn.textContent = 'Setting...';
          
          try {
            const result = await window.apiClient.trackPrice(currentProduct.productId, targetPrice);
            alert('Price tracking has been set!');
            
            // Refresh tracker list
            const trackerList = document.getElementById('tracker-list');
            trackerList.innerHTML = `
              <div class="tracker-item">
                <strong>${currentProduct.name || 'Unknown Product'}</strong>
                <p>Target Price: ${formatPrice(targetPrice, currentProduct.currency || 'CNY')}</p>
                <p>Current Price: ${formatPrice(currentProduct.price || 0, currentProduct.currency || 'CNY')}</p>
              </div>
            `;
          } catch (error) {
            console.error('Track price error:', error);
            alert('Failed to set price tracking: ' + (error.message || 'Unknown error'));
          } finally {
            trackBtn.disabled = false;
            trackBtn.textContent = 'Start Tracking';
          }
        });
      }
    }
  }
  
  function addChatMessage(role, content) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = `
      <div class="message-content">${content}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
  
  // Helper functions
  function formatAnalysisText(text) {
    if (!text) return 'No analysis content available';
    // Simple text formatting
    return text.split('\n').map(line => {
      if (line.trim().startsWith('#') || line.trim().match(/^\d+\./)) {
        return `<strong>${line}</strong>`;
      }
      return line;
    }).join('<br>');
  }
  
  function getActionText(action) {
    const actionMap = {
      'buy_now': '✅ Buy Now',
      'wait': '⏳ Wait for Price Drop',
      'consider': '🤔 Consider Buying',
      'avoid': '❌ Not Recommended',
      'neutral': '➡️ Neutral',
      'cautious': '⚠️ Consider Carefully'
    };
    return actionMap[action] || action;
  }
  
  function getRiskLevelText(level) {
    const levelMap = {
      'low': 'Low Risk',
      'medium': 'Medium Risk',
      'high': 'High Risk',
      'critical': 'Critical Risk',
      'unknown': 'Unknown'
    };
    return levelMap[level] || level;
  }
  
})();

