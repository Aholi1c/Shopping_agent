/**
 * Sidepanel Script
 * Main sidepanel application script
 * This is a simplified version, if you need a complete React application, build tools are required
 */

(function() {
  'use strict';

  let currentProduct = null;
  let currentView = 'chat'; // chat, analysis, comparison, tracker
  let guideMode = false; // Smart shopping guide mode switch

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

            // Trigger analysis after DOM update
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
          console.warn('Cannot extract product information from page:', e);
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
              <div class="product-price">¥${currentProduct.price || '0.00'}</div>
            </div>
          </div>
        ` : ''}

        <div class="guide-toggle">
          <label style="font-size:12px;color:#666;">
            <input type="checkbox" id="guide-mode-toggle" ${guideMode ? 'checked' : ''} />
            Enable Smart Shopping Guide Mode
          </label>
        </div>

        <div class="chat-messages" id="chat-messages">
          <div class="message assistant">
            <div class="message-content">
              Hello! I'm your Smart Shopping Assistant. How can I help you today?
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
            <span class="price">¥${currentProduct.price || '0.00'}</span>
          </div>
          <div class="info-item">
            <label>Platform:</label>
            <span>${currentProduct.platform || 'Unknown'}</span>
          </div>
        </div>

        <div class="analysis-actions">
          <button id="analyze-btn" class="action-button primary" data-action="analyze">Analyze Product</button>
          <button id="risk-btn" class="action-button primary" data-action="risk">Risk Analysis</button>
          <button id="predict-btn" class="action-button primary" data-action="predict">Price Prediction</button>
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
        // Remove old listeners (if any)
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
          setupEventListeners();
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
      const guideToggle = document.getElementById('guide-mode-toggle');
      let stopBtn = document.getElementById('stop-stream-btn');
      let currentStreamController = null;

      if (guideToggle) {
        guideToggle.addEventListener('change', (e) => {
          guideMode = e.target.checked;
          if (guideMode) {
            addChatMessage('assistant', 'Smart Shopping Guide Mode enabled: Please describe your budget, product type, brand preferences, and main use cases in natural language.');
          } else {
            addChatMessage('assistant', 'Smart Shopping Guide Mode disabled, returning to normal chat.');
          }
        });
      }

      // If there's no stop button, create one dynamically (initially hidden)
      if (!stopBtn && sendBtn) {
        stopBtn = document.createElement('button');
        stopBtn.id = 'stop-stream-btn';
        stopBtn.textContent = 'Stop';
        stopBtn.className = 'send-btn';
        stopBtn.style.marginLeft = '8px';
        stopBtn.style.backgroundColor = '#ff4d4f';
        stopBtn.style.display = 'none';
        sendBtn.parentNode.appendChild(stopBtn);
      }

      const startStreamingUI = () => {
        if (sendBtn) {
          sendBtn.disabled = true;
          sendBtn.classList.add('streaming');
        }
        if (stopBtn) stopBtn.style.display = 'inline-block';
      };

      const endStreamingUI = () => {
        if (sendBtn) {
          sendBtn.disabled = false;
          sendBtn.classList.remove('streaming');
        }
        if (stopBtn) stopBtn.style.display = 'none';
        currentStreamController = null;
      };

      if (stopBtn) {
        stopBtn.addEventListener('click', () => {
          if (currentStreamController) {
            currentStreamController.abort();
          }
          endStreamingUI();
        });
      }

      if (sendBtn && chatInput) {
        const cleanRecommendationText = (text) => {
          if (!text) return text;
          const dropLinePatterns = [
            /^\s*用户需求/,
            /^\s*基于用户需求/,
            /^\s*根据用户描述/,
            /^\s*根据用户需求/,
            /^\s*Based on the user's (description|request)/i,
            /^\s*Based on user/i,
            /^\s*Based on (the )?user's/i,
            /^\s*Information complete,\s*ready to recommend\.?/i,
            /^\s*complete,\s*ready to recommend\.?/i,
            /^\s*Information incomplete/i,
            /^\s*Incomplete\./i,
            /^\s*Please rewrite in the following format/i,
          ];

          const lines = text.split(/\r?\n/).filter((line) => {
            const trimmed = line.trim();
            if (!trimmed) return false;
            return !dropLinePatterns.some((pattern) => pattern.test(trimmed));
          });

          let cleaned = lines.join('\n').trim();
          cleaned = cleaned.replace(/(^|\n)(Information )?complete,\s*ready to recommend\.?/gi, '');
          cleaned = cleaned.replace(/(^|\n)(Information )?incomplete.*$/gi, '');
          cleaned = cleaned.replace(/(^|\n)Please rewrite in the following format:?[\s\S]*$/gi, '');
          cleaned = cleaned.replace(/(^|\n)根据用户(?:描述|需求)[^\n]*/g, '');
          cleaned = cleaned.replace(/(^|\n)基于用户需求[^\n]*/g, '');
          cleaned = cleaned.replace(/(^|\n)用户需求[^\n]*/g, '');

          return cleaned.trim();
        };

        const shouldSuppressGuideSummary = (text) => {
          if (!text) return false;
          const normalized = text.trim();
          return /complete,\s*ready to recommend/i.test(normalized)
            || /information complete/i.test(normalized)
            || /ready to recommend/i.test(normalized)
            || /可以开始推荐/.test(normalized);
        };

        const sendMessage = async () => {
          const message = chatInput.value.trim();
          if (!message || currentStreamController) return;

          // Display user message
          addChatMessage('user', message);
          chatInput.value = '';

           // Construct the actual message to send to the model based on guide mode
           let payloadMessage = message;
           if (guideMode) {
             const guidePrefix = `[Shopping Guide Instruction]
You are now acting as a "Smart Shopping Consultant" to help users organize their purchase requirements. Please strictly follow these rules:

1) When you find the user's description is too brief, vague, missing information, or contradictory, reply with the following fixed content without adding any other text:
"Information incomplete. Please rewrite in the following format:
- Product type desired:
- Budget range:
- Brand preference:
- Main use case:
- Other special requirements:"

2) When you determine the information is complete enough:
- First summarize the user's purchase requirements in a short paragraph in Chinese;
- The last line must include this exact sentence (verbatim, do not modify):
"Information complete, ready to recommend"

3) In this mode, do not provide specific product recommendations yet, and do not call any external tools. Only ask questions, clarify requirements, and request users to rewrite descriptions in the format.

Below is the user's original description for this round:`;

             payloadMessage = `${guidePrefix}\n${message}`;
           }

          const messagesContainer = document.getElementById('chat-messages');
          if (!messagesContainer) return;

          // Create an empty assistant message as placeholder for streaming updates
          const assistantDiv = document.createElement('div');
          assistantDiv.className = 'message assistant';
          const contentDiv = document.createElement('div');
          contentDiv.className = 'message-content streaming-active';
          contentDiv.textContent = '';
          assistantDiv.appendChild(contentDiv);
          messagesContainer.appendChild(assistantDiv);
          messagesContainer.scrollTop = messagesContainer.scrollHeight;

          startStreamingUI();

          try {
            let rawBuffer = '';
            let hideGuideSummary = false;
            await window.apiClient.streamChatMessage(
              payloadMessage,
              null,
              {
                message_type: 'text',
                model: 'glm-4-0520',
                use_memory: true,
                use_rag: false,
              },
              {
                onController: (controller) => {
                  currentStreamController = controller;
                },
                onMeta: (meta) => {
                  // Extensible: manage subsequent conversations based on meta.conversation_id
                },
                onDelta: (delta) => {
                  rawBuffer += delta;
                  contentDiv.innerHTML = renderMarkdown(rawBuffer);
                  messagesContainer.scrollTop = messagesContainer.scrollHeight;
                  if (guideMode && shouldSuppressGuideSummary(rawBuffer)) {
                    hideGuideSummary = true;
                  }
                },
                onError: (error) => {
                  console.error('Streaming chat error:', error);
                  let errorMessage = 'Sorry, connection failed. Please check your network connection.';
                  if (error && error.message) {
                    if (error.message.includes('Cannot connect to server') || error.message.includes('无法连接到服务器')) {
                      errorMessage = 'Cannot connect to backend service. Please ensure backend is running at: http://localhost:8000';
                    } else {
                      errorMessage = 'Error: ' + error.message.substring(0, 100);
                    }
                  }
                  contentDiv.innerHTML = errorMessage;
                  contentDiv.classList.remove('streaming-active');
                  messagesContainer.scrollTop = messagesContainer.scrollHeight;
                  endStreamingUI();
                },
                onDone: () => {
                  if (guideMode && hideGuideSummary && assistantDiv.parentNode) {
                    assistantDiv.parentNode.removeChild(assistantDiv);
                  } else {
                    contentDiv.classList.remove('streaming-active');
                  }
                  endStreamingUI();
                },
              }
            );

            // In guide mode, if model indicates information is complete, automatically trigger e-commerce RAG recommendation
            if (guideMode && (rawBuffer.includes('ready to recommend') || rawBuffer.includes('可以开始推荐'))) {
              try {
                const budgetMatch = message.match(/(\d+(\.\d+)?)/);
                const budget = budgetMatch ? parseFloat(budgetMatch[1]) : undefined;

                const preferred_brands = [];
                if (message.includes('小米') || /Xiaomi/i.test(message)) {
                  preferred_brands.push('Xiaomi');
                }
                if (message.toLowerCase().includes('oppo')) {
                  preferred_brands.push('OPPO');
                }

                const usage_scenarios = [];
                if (message.includes('游戏') || /game/i.test(message)) {
                  usage_scenarios.push('Gaming');
                }
                if (message.includes('拍照') || /photo/i.test(message)) {
                  usage_scenarios.push('Photography');
                }

                const recRequest = {
                  query: message,
                  limit: 5,
                };
                if (budget) {
                  recRequest.budget = budget;
                }
                if (preferred_brands.length || usage_scenarios.length) {
                  recRequest.preferences = {};
                  if (preferred_brands.length) {
                    recRequest.preferences.preferred_brands = preferred_brands;
                  }
                  if (usage_scenarios.length) {
                    recRequest.preferences.usage_scenarios = usage_scenarios;
                  }
                }

                const recResponse = await window.apiClient.getEcommerceRecommendations(recRequest);
                const data = recResponse.data || recResponse;
                const recTextRaw = data.recommendation_text || 'Recommendation generated, but no detailed content returned.';
                const recText = cleanRecommendationText(recTextRaw);

                addChatMessage('assistant', `Smart Shopping Guide Recommendation:\n\n${recText}`);
              } catch (e) {
                console.error('Failed to get e-commerce recommendations:', e);
                addChatMessage('assistant', 'Error occurred while generating smart shopping guide recommendations. Please try again later.');
              }
            }
          } catch (error) {
            console.error('Failed to send message', error);
            // contentDiv was created before try, ensure it exists before use
            const lastAssistant = messagesContainer.querySelector('.message.assistant:last-child .message-content');
            if (lastAssistant) lastAssistant.classList.remove('streaming-active');
            endStreamingUI();
          }
        };

        // Bind send and keyboard shortcuts
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
                <p>Analysis failed: Product information incomplete</p>
                <p style="font-size: 0.8em; color: #666; margin-top: 10px;">
                  Please ensure you're on a product detail page, or manually enter product information
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
                <h4>Comprehensive Analysis</h4>
                <div class="analysis-text">${formatAnalysisText(analysis.comprehensive_analysis || analysis.analysis || 'Analysis complete, but no detailed report generated')}</div>

                ${analysis.recommendation ? `
                  <div class="recommendation">
                    <h5>Purchase Recommendation</h5>
                    <p><strong>Action:</strong>${getActionText(analysis.recommendation.action)}</p>
                    <p><strong>Confidence:</strong>${(analysis.recommendation.confidence * 100).toFixed(0)}%</p>
                    ${analysis.recommendation.reason ? `<p><strong>Reason:</strong>${analysis.recommendation.reason}</p>` : ''}
                  </div>
                ` : ''}

                ${analysis.price_analysis && !analysis.price_analysis.error ? `
                  <div class="price-analysis">
                    <h5>Price Analysis</h5>
                    <p>Current Price: ¥${analysis.price_analysis.current_price || currentProduct.price || '0.00'}</p>
                    <p>Platform: ${analysis.price_analysis.platform || currentProduct.platform || 'Unknown'}</p>
                    ${analysis.price_analysis.lowest_found_price ? `
                      <p>Lowest Price: ¥${analysis.price_analysis.lowest_found_price}</p>
                      ${analysis.price_analysis.savings_potential > 0 ? `
                        <p class="savings">Potential Savings: ¥${analysis.price_analysis.savings_potential.toFixed(2)}</p>
                      ` : ''}
                    ` : ''}
                  </div>
                ` : ''}

                ${analysis.risk_analysis && !analysis.risk_analysis.error ? `
                  <div class="risk-analysis">
                    <h5>Risk Assessment</h5>
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
                <p>Analysis failed: ${errorMsg}</p>
                <p style="font-size: 0.8em; color: #666; margin-top: 10px;">
                  Please ensure backend service is running at http://localhost:8000<br>
                  If the problem persists, please check browser console and backend logs
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
              <p>Cannot analyze: No product information detected</p>
              <p style="font-size: 0.8em; color: #666; margin-top: 10px;">
                Please ensure you're on a product detail page, or refresh and try again
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
                  <h4>Risk Assessment Report</h4>
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
                      <h5>Suggestions:</h5>
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
            resultDiv.innerHTML = `<div class="error">Risk assessment failed: ${error.message || 'Unknown error'}</div>`;
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
                  <h4>Price Prediction</h4>
                  <pre>${JSON.stringify(result, null, 2)}</pre>
                </div>
              `;
            } else {
              resultDiv.innerHTML = '<div class="error">Cannot perform price prediction: Product ID missing</div>';
            }
          } catch (error) {
            console.error('Price prediction error:', error);
            resultDiv.innerHTML = `<div class="error">Price prediction failed: ${error.message || 'Unknown error'}</div>`;
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
            alert('Please enter product name');
            return;
          }

          searchBtn.disabled = true;
          searchBtn.textContent = 'Searching...';
          const resultsDiv = document.getElementById('comparison-results');
          resultsDiv.innerHTML = '<div class="loading">Searching and comparing prices...</div>';

          try {
            const result = await window.apiClient.comparePrices(query);
            console.log('Comparison result:', result);

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
                    <h4>Price Comparison Results</h4>
                    <p style="font-size: 0.9em; color: #666;">Data source: ${dataSource === 'database' ? 'Database' : 'API'} | Found ${totalProducts} products</p>
                    ${Object.entries(platformPrices).map(([platform, platformProducts]) => {
                      if (Array.isArray(platformProducts)) {
                        return `
                          <div class="comparison-group">
                            <h5>${platform.toUpperCase()} Platform</h5>
                            <div class="products-list">
                              ${platformProducts.map(p => `
                                <div class="product-item">
                                  <strong>${p.title || p.name || 'Unknown Product'}</strong>
                                  <span class="price">¥${p.price || 'N/A'}</span>
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
                              <p>Price: ¥${platformProducts.price || 'N/A'}</p>
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
                // Standard format - with product groups
                resultsDiv.innerHTML = `
                  <div class="comparison-results-content">
                    <h4>Price Comparison Results</h4>
                    <p style="font-size: 0.9em; color: #666;">Found ${totalProducts} products | Data source: ${dataSource === 'database' ? 'Database' : 'API'}</p>
                    ${Object.entries(comparison).map(([productKey, data]) => {
                      // Handle different data formats
                      const products = data.products || [];
                      const platformPrices = data.platform_prices || {};

                      // If there's platform_prices, use it first
                      if (platformPrices && Object.keys(platformPrices).length > 0) {
                        return `
                          <div class="comparison-group">
                            <h5>${productKey}</h5>
                            <div class="price-comparison">
                              ${data.min_price ? `<p><strong>Lowest Price:</strong> ¥${data.min_price}</p>` : ''}
                              ${data.max_price ? `<p><strong>Highest Price:</strong> ¥${data.max_price}</p>` : ''}
                              ${data.price_diff ? `<p><strong>Price Difference:</strong> ¥${data.price_diff.toFixed(2)}</p>` : ''}
                              ${data.price_diff_percent ? `<p><strong>Savings:</strong> ${data.price_diff_percent.toFixed(1)}%</p>` : ''}
                              ${data.best_platform ? `<p><strong>Best Platform:</strong> ${data.best_platform}</p>` : ''}
                            </div>
                            <div class="platform-prices">
                              ${Object.entries(platformPrices).map(([platform, info]) => `
                                <div class="platform-price-item ${platform === data.best_platform ? 'best-price' : ''}">
                                  <span class="platform-badge platform-${platform}">${platform.toUpperCase()}</span>
                                  <span class="price">¥${info.price || 'N/A'}</span>
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
                        // Fall back to products list
                        return `
                          <div class="comparison-group">
                            <h5>${productKey}</h5>
                            <div class="price-comparison">
                              ${data.min_price ? `<p><strong>Lowest Price:</strong> ¥${data.min_price}</p>` : ''}
                              ${data.max_price ? `<p><strong>Highest Price:</strong> ¥${data.max_price}</p>` : ''}
                              ${data.price_difference ? `<p><strong>Price Difference:</strong> ¥${data.price_difference}</p>` : ''}
                              ${data.savings_percentage ? `<p><strong>Savings:</strong> ${data.savings_percentage.toFixed(1)}%</p>` : ''}
                              ${data.best_platform ? `<p><strong>Best Platform:</strong> ${data.best_platform}</p>` : ''}
                            </div>
                            <div class="products-list">
                              ${products.map(p => `
                                <div class="product-item">
                                  <strong>${p.title || p.name || productKey}</strong>
                                  <span class="platform-badge platform-${p.platform}">${p.platform || 'Unknown'}</span>
                                  <span class="price">¥${p.price || 'N/A'}</span>
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
                errorMsg = `Found ${totalProducts} products, but unable to compare prices. ${message || 'Please try using more specific keywords.'}`;
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
            resultsDiv.innerHTML = `<div class="error">Price comparison failed: ${errorMessage}</div>`;
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
            alert('Cannot track: Product ID missing');
            return;
          }

          trackBtn.disabled = true;
          trackBtn.textContent = 'Setting up...';

          try {
            const result = await window.apiClient.trackPrice(currentProduct.productId, targetPrice);
            alert('Price tracking has been set!');

            // Refresh tracking list
            const trackerList = document.getElementById('tracker-list');
            trackerList.innerHTML = `
              <div class="tracker-item">
                <strong>${currentProduct.name || 'Unknown Product'}</strong>
                <p>Target Price: ¥${targetPrice}</p>
                <p>Current Price: ¥${currentProduct.price || 'N/A'}</p>
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
    const html = renderMarkdown(content);
    messageDiv.innerHTML = `
      <div class="message-content">${html}</div>
    `;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // Basic Markdown rendering (security: escape first, then replace common markers)
  function renderMarkdown(raw) {
    if (!raw) return '';
    // Pre-normalize: convert ": . ", inline " . " and start-of-line ". " to standard list format
    let normalized = raw
      // After Chinese colon followed by ". " to start bullet points: e.g. "Features: . A . B" -> line break and start item
      .replace(/(：)\s*\.\s+/g, '$1\n- ')
      // Inline " . " continuing bullet points: replace separator with line break bullet points
      .replace(/\s\.\s+(?=\S)/g, '\n- ')
      // Start-of-line ". " treated as bullet point
      .replace(/(^|\n)\s*\.\s+/g, '$1- ');

    // Escape HTML
    let escaped = normalized
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');

    // Code snippets `code`
    escaped = escaped.replace(/`([^`]+?)`/g, '<code>$1</code>');
    // Bold **text**
    escaped = escaped.replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>');
    // Italic *text* (avoid conflict with bold, use negative lookahead for bold)
    escaped = escaped.replace(/(^|[^*])\*([^*]+?)\*(?!\*)/g, '$1<em>$2</em>');
    // Headings #, ##, ### at start of line
    escaped = escaped.replace(/^###\s+(.+)$/gm, '<strong style="font-size:14px;">$1</strong>')
                     .replace(/^##\s+(.+)$/gm, '<strong style="font-size:15px;">$1</strong>')
                     .replace(/^#\s+(.+)$/gm, '<strong style="font-size:16px;">$1</strong>');
    // Ordered lists 1. or 1、
    escaped = escaped.replace(/^(\d+)[\.\u3001]\s+(.+)$/gm, '<div class="md-li"><span class="md-li-num">$1</span> $2</div>');
    // Unordered lists - or *
    escaped = escaped.replace(/^[-*]\s+(.+)$/gm, '<div class="md-li">• $1</div>');
    // Common bullet points • · ・ at start of line
    escaped = escaped.replace(/^[\u2022\u00b7\u30fb•·・]\s+(.+)$/gm, '<div class="md-li">• $1</div>');

    // Line breaks -> <br>
    escaped = escaped.replace(/\r?\n/g, '<br>');

    return escaped;
  }

  // Add smarter line break/bullet formatting for analysis results
  function formatAnalysisText(text) {
    if (!text) return '';
    let s = String(text);

    // 1) Handle "。." or "；." separation into new bullet points
    s = s.replace(/(。|；|！|？|\?|\!)\s*\.\s+/g, '$1\n- ');
    // 2) Handle "。• "/"；• " etc.
    s = s.replace(/(。|；|！|？|\?|\!)\s*[•·・]\s+/g, '$1\n- ');
    // 3) If entire paragraph has no line breaks but contains multiple "。 ", treat space after period as line break (Chinese period only)
    if (!/\n/.test(s) && /。\s*\S/.test(s)) {
      s = s.replace(/。\s*/g, '。\n');
    }
    // 4) Break line before common ending CTA, e.g. "Can I help you...?"
    s = s.replace(/\s*(Can I help you[^。！？]*[？?]|我帮您[^。！？]*[？?])/g, '\n$1');

    // Reuse Markdown rendering, supports lists and line breaks
    return renderMarkdown(s);
  }

  // Map backend enum/English actions to readable text, avoiding runtime errors from undefined functions
  function getActionText(action) {
    const map = {
      buy: 'Recommended to Buy',
      purchase: 'Recommended to Buy',
      wait: 'Recommended to Wait',
      hold: 'Recommended to Wait',
      avoid: 'Not Recommended',
      skip: 'Not Recommended'
    };
    if (!action) return '—';
    const key = String(action).toLowerCase();
    return map[key] || action;
  }

  function getRiskLevelText(level) {
    const map = {
      low: 'Low Risk',
      medium: 'Medium Risk',
      mid: 'Medium Risk',
      high: 'High Risk',
      unknown: 'Unknown Risk'
    };
    if (!level) return 'Unknown Risk';
    const key = String(level).toLowerCase();
    return map[key] || level;
  }

  // Modify chat streaming section: keep streaming logic in setupViewEventListeners unchanged, add global hook here
  // Rewrite streaming append when sending messages: find existing streaming-active logic, use markdown in onDelta.
  // Since original logic is already defined above, not repeating here; just ensure onDelta uses contentDiv.innerHTML = renderMarkdown(rawBuffer);
})();
