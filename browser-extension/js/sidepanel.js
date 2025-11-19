/**
 * Sidepanel Script
 * 侧边栏主应用脚本
 * 这是一个简化版本，如果需要完整的React应用，需要使用构建工具
 */

(function() {
  'use strict';
  
  let currentProduct = null;
  let currentView = 'chat'; // chat, analysis, comparison, tracker
  let guideMode = false; // 智能导购整理模式开关
  
  // 初始化
  init();
  
  async function init() {
    console.log('侧边栏初始化...');
    
    // 监听来自background的消息
    if (chrome.runtime && chrome.runtime.onMessage) {
      chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        console.log('侧边栏收到消息:', request.action, request);
        
        if (request.action === 'startAnalysis') {
          console.log('收到分析请求:', request);
          if (request.productData) {
            currentProduct = request.productData;
            console.log('设置当前商品:', currentProduct);
            
            // 自动切换到分析视图
            currentView = 'analysis';
            
            // 保存商品信息到storage
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
              if (tabs[0] && chrome.storage && chrome.storage.local) {
                chrome.storage.local.set({
                  [`product_${tabs[0].id}`]: request.productData
                });
              }
            });
            
            // 重新渲染
            render();
            setupEventListeners();
            
            // 等待DOM更新后触发分析
            setTimeout(() => {
              console.log('尝试触发分析按钮...');
              const analyzeBtn = document.getElementById('analyze-btn');
              if (analyzeBtn) {
                console.log('找到分析按钮，点击...');
                analyzeBtn.click();
              } else {
                console.warn('未找到分析按钮，等待更长时间...');
                setTimeout(() => {
                  const btn = document.getElementById('analyze-btn');
                  if (btn) {
                    btn.click();
                  } else {
                    console.error('仍然未找到分析按钮');
                  }
                }, 500);
              }
            }, 200);
          }
          sendResponse({ success: true });
        } else if (request.action === 'updateProduct') {
          // 更新商品信息
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
    
    // 获取当前标签页
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs[0]) {
      console.log('当前标签页:', tabs[0].id);
      // 加载当前页面的商品信息
      await loadProductInfo(tabs[0].id);
      
      // 渲染界面
      render();
      
      // 设置事件监听
      setupEventListeners();
    }
  }
  
  async function loadProductInfo(tabId) {
    try {
      // 先检查是否有分析请求
      const analysisRequest = await chrome.storage.local.get([`analysis_request_${tabId}`]);
      if (analysisRequest[`analysis_request_${tabId}`]) {
        const request = analysisRequest[`analysis_request_${tabId}`];
        console.log('发现分析请求:', request);
        if (request.productData) {
          currentProduct = request.productData;
          currentView = 'analysis';
          
          // 清除请求标记
          chrome.storage.local.remove([`analysis_request_${tabId}`]);
          
          // 立即触发分析
          setTimeout(() => {
            const analyzeBtn = document.getElementById('analyze-btn');
            if (analyzeBtn) {
              console.log('自动触发分析...');
              analyzeBtn.click();
            }
          }, 300);
          
          return;
        }
      }
      
      // 加载商品信息
      const result = await chrome.storage.local.get([`product_${tabId}`, `product_current`]);
      const productInfo = result[`product_${tabId}`] || result[`product_current`];
      
      if (productInfo) {
        console.log('加载商品信息:', productInfo);
        currentProduct = productInfo;
      } else {
        console.log('未找到商品信息，尝试从页面提取...');
        // 尝试从当前页面提取
        try {
          const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
          if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, {
              action: 'extractProductInfo'
            }, (response) => {
              if (response && response.success) {
                console.log('从页面提取的商品信息:', response);
              }
            });
          }
        } catch (e) {
          console.warn('无法从页面提取商品信息:', e);
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
          <h2>智能购物助手</h2>
          <div class="header-actions">
            <button id="refresh-btn" class="icon-btn" title="刷新" aria-label="刷新">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <polyline points="23 4 23 10 17 10"></polyline>
                <path d="M20.49 15a9 9 0 1 1 2.12-9"></path>
              </svg>
            </button>
            <button id="settings-btn" class="icon-btn" title="设置" aria-label="设置">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <line x1="4" y1="6" x2="20" y2="6"></line>
                <circle cx="10" cy="6" r="2"></circle>
                <line x1="4" y1="12" x2="20" y2="12"></line>
                <circle cx="14" cy="12" r="2"></circle>
                <line x1="4" y1="18" x2="20" y2="18"></line>
                <circle cx="8" cy="18" r="2"></circle>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="sidepanel-tabs">
          <button class="tab-btn ${currentView === 'chat' ? 'active' : ''}" data-view="chat">聊天</button>
          <button class="tab-btn ${currentView === 'analysis' ? 'active' : ''}" data-view="analysis">分析</button>
          <button class="tab-btn ${currentView === 'comparison' ? 'active' : ''}" data-view="comparison">比价</button>
          <button class="tab-btn ${currentView === 'tracker' ? 'active' : ''}" data-view="tracker">追踪</button>
        </div>
        
        <div class="sidepanel-content">
          ${renderCurrentView()}
        </div>
      </div>
    `;
    
    // 绑定事件
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
            <h3>当前商品</h3>
            <div class="product-info">
              <div class="product-name">${currentProduct.name || '未知商品'}</div>
              <div class="product-price">¥${currentProduct.price || '0.00'}</div>
            </div>
          </div>
        ` : ''}
        
        <div class="guide-toggle">
          <label style="font-size:12px;color:#666;">
            <input type="checkbox" id="guide-mode-toggle" ${guideMode ? 'checked' : ''} />
            启用智能导购整理模式
          </label>
        </div>
        
        <div class="chat-messages" id="chat-messages">
          <div class="message assistant">
            <div class="message-content">
              您好！我是您的智能购物助手，有什么可以帮您的吗？
            </div>
          </div>
        </div>
        
        <div class="chat-input-container">
          <textarea id="chat-input" placeholder="输入您的问题..." rows="3"></textarea>
          <button id="send-btn" class="send-btn">发送</button>
        </div>
      </div>
    `;
  }
  
  function renderAnalysisView() {
    if (!currentProduct) {
      return `
        <div class="empty-state">
          <p>请先访问一个商品页面</p>
        </div>
      `;
    }
    
    return `
      <div class="view-container analysis-view">
        <div class="analysis-card">
          <h3>商品信息</h3>
          <div class="info-item">
            <label>商品名称：</label>
            <span>${currentProduct.name || '未知'}</span>
          </div>
          <div class="info-item">
            <label>当前价格：</label>
            <span class="price">¥${currentProduct.price || '0.00'}</span>
          </div>
          <div class="info-item">
            <label>平台：</label>
            <span>${currentProduct.platform || '未知'}</span>
          </div>
        </div>
        
        <div class="analysis-actions">
          <button id="analyze-btn" class="action-button primary" data-action="analyze">分析商品</button>
          <button id="risk-btn" class="action-button primary" data-action="risk">风险分析</button>
          <button id="predict-btn" class="action-button primary" data-action="predict">价格预测</button>
        </div>
        
        <div id="analysis-result" class="analysis-result"></div>
      </div>
    `;
  }
  
  function renderComparisonView() {
    return `
      <div class="view-container comparison-view">
        <div class="comparison-form">
          <input type="text" id="product-search" placeholder="输入商品名称搜索..." />
          <button id="search-btn" class="search-btn">搜索</button>
        </div>
        
        <div id="comparison-results" class="comparison-results"></div>
      </div>
    `;
  }
  
  function renderTrackerView() {
    return `
      <div class="view-container tracker-view">
        <div class="tracker-form">
          <input type="number" id="target-price" placeholder="目标价格" />
          <button id="track-btn" class="track-btn">开始追踪</button>
        </div>
        
        <div id="tracker-list" class="tracker-list"></div>
      </div>
    `;
  }
  
  function setupEventListeners() {
    // 标签切换
    const tabButtons = document.querySelectorAll('.tab-btn');
    if (tabButtons.length > 0) {
      tabButtons.forEach(btn => {
        // 移除旧的监听器（如果存在）
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        newBtn.addEventListener('click', () => {
          console.log('切换到视图:', newBtn.dataset.view);
          document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
          newBtn.classList.add('active');
          currentView = newBtn.dataset.view;
          
          // 重新渲染内容
          const content = document.querySelector('.sidepanel-content');
          if (content) {
            content.innerHTML = renderCurrentView();
            setupViewEventListeners();
          }
        });
      });
    }
    
    // 刷新按钮
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
    
    // 设置视图特定的事件监听器
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
            addChatMessage('assistant', '已进入智能导购整理模式：请尽量用自然语言描述您的预算、想买的商品类型、品牌偏好和主要用途。');
          } else {
            addChatMessage('assistant', '已退出智能导购整理模式，恢复普通聊天。');
          }
        });
      }

      // 如果没有停止按钮，动态创建一个（初始隐藏）
      if (!stopBtn && sendBtn) {
        stopBtn = document.createElement('button');
        stopBtn.id = 'stop-stream-btn';
        stopBtn.textContent = '停止';
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
        const sendMessage = async () => {
          const message = chatInput.value.trim();
          if (!message || currentStreamController) return;

          // 显示用户消息
          addChatMessage('user', message);
          chatInput.value = '';

           // 根据是否启用导购整理模式构造实际发送给模型的消息
           let payloadMessage = message;
           if (guideMode) {
             const guidePrefix = `【导购整理指令】
你现在以“智能导购问诊助手”的身份帮助用户整理购买需求。请严格遵守以下规则：

1）当你觉得用户描述过于简短、含糊、信息缺失或相互矛盾时，直接回复如下固定内容，不要添加任何其他文字：
"信息不完整，请按如下格式重写：
- 想买的商品类型：
- 预算范围：
- 品牌偏好：
- 主要用途：
- 其他特别要求："

2）当你判断信息已经足够完整时：
- 先用一小段话用中文总结用户的购买需求；
- 最后一行必须加上这一句（原样，不要改动）：
"信息已完整，可以开始推荐"

3）在本模式下，你暂时不要给出具体商品推荐，也不要调用任何外部工具，只负责问问题、澄清需求和要求用户按格式重写描述。

下面是用户本轮的原始描述：`;

             payloadMessage = `${guidePrefix}\n${message}`;
           }

          const messagesContainer = document.getElementById('chat-messages');
          if (!messagesContainer) return;

          // 创建一个空的 assistant 消息，占位用于流式更新
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
                  // 可扩展：根据 meta.conversation_id 做后续对话管理
                },
                onDelta: (delta) => {
                  rawBuffer += delta;
                  contentDiv.innerHTML = renderMarkdown(rawBuffer);
                  messagesContainer.scrollTop = messagesContainer.scrollHeight;
                },
                onError: (error) => {
                  console.error('流式对话错误:', error);
                  let errorMessage = '抱歉，连接失败，请检查网络连接。';
                  if (error && error.message) {
                    if (error.message.includes('无法连接到服务器')) {
                      errorMessage = '无法连接到后端服务。请确保后端服务正在运行：http://localhost:8000';
                    } else {
                      errorMessage = '错误：' + error.message.substring(0, 100);
                    }
                  }
                  contentDiv.innerHTML = errorMessage;
                  contentDiv.classList.remove('streaming-active');
                  messagesContainer.scrollTop = messagesContainer.scrollHeight;
                  endStreamingUI();
                },
                onDone: () => {
                  contentDiv.classList.remove('streaming-active');
                  endStreamingUI();
                },
              }
            );

            // 在导购整理模式下，如果模型表示信息已经完整，则自动触发电商RAG推荐
            if (guideMode && rawBuffer.includes('可以开始推荐')) {
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
                  usage_scenarios.push('游戏');
                }
                if (message.includes('拍照')) {
                  usage_scenarios.push('拍照');
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
                const recText = data.recommendation_text || '已生成推荐结果，但未返回详细文案。';

                addChatMessage('assistant', `智能导购推荐结果：\n\n${recText}`);
              } catch (e) {
                console.error('获取电商推荐失败:', e);
                addChatMessage('assistant', '尝试生成智能导购推荐时出现错误，请稍后再试。');
              }
            }
          } catch (error) {
            console.error('发送消息失败', error);
            // contentDiv 在 try 前已创建，确保存在再使用
            const lastAssistant = messagesContainer.querySelector('.message.assistant:last-child .message-content');
            if (lastAssistant) lastAssistant.classList.remove('streaming-active');
            endStreamingUI();
          }
        };

        // 绑定发送与快捷键
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
          console.log('分析按钮被点击，当前商品:', currentProduct);
          
          // 验证商品信息
          if (!currentProduct.name && !currentProduct.title) {
            const resultDiv = document.getElementById('analysis-result');
            resultDiv.innerHTML = `
              <div class="error">
                <p>分析失败：商品信息不完整</p>
                <p style="font-size: 0.8em; color: #666; margin-top: 10px;">
                  请确保在商品详情页面，或手动输入商品信息
                </p>
              </div>
            `;
            return;
          }
          
          analyzeBtn.disabled = true;
          analyzeBtn.textContent = '分析中...';
          const resultDiv = document.getElementById('analysis-result');
          resultDiv.innerHTML = '<div class="loading">正在分析商品，请稍候...</div>';
          
          try {
            // 确保商品数据格式正确
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
            
            console.log('发送分析请求，商品数据:', productDataToSend);
            
            const result = await window.apiClient.analyzeProduct(productDataToSend);
            console.log('收到分析结果:', result);
            
            const analysis = result.data || result;
            
            if (!analysis || (analysis.error && !analysis.comprehensive_analysis)) {
              throw new Error(analysis?.error || '分析失败：未返回有效结果');
            }
            
            resultDiv.innerHTML = `
              <div class="result-content">
                <h4>综合分析</h4>
                <div class="analysis-text">${formatAnalysisText(analysis.comprehensive_analysis || analysis.analysis || '分析完成，但未生成详细报告')}</div>
                
                ${analysis.recommendation ? `
                  <div class="recommendation">
                    <h5>购买建议</h5>
                    <p><strong>行动：</strong>${getActionText(analysis.recommendation.action)}</p>
                    <p><strong>置信度：</strong>${(analysis.recommendation.confidence * 100).toFixed(0)}%</p>
                    ${analysis.recommendation.reason ? `<p><strong>原因：</strong>${analysis.recommendation.reason}</p>` : ''}
                  </div>
                ` : ''}
                
                ${analysis.price_analysis && !analysis.price_analysis.error ? `
                  <div class="price-analysis">
                    <h5>价格分析</h5>
                    <p>当前价格：¥${analysis.price_analysis.current_price || currentProduct.price || '0.00'}</p>
                    <p>平台：${analysis.price_analysis.platform || currentProduct.platform || '未知'}</p>
                    ${analysis.price_analysis.lowest_found_price ? `
                      <p>最低价格：¥${analysis.price_analysis.lowest_found_price}</p>
                      ${analysis.price_analysis.savings_potential > 0 ? `
                        <p class="savings">可节省：¥${analysis.price_analysis.savings_potential.toFixed(2)}</p>
                      ` : ''}
                    ` : ''}
                  </div>
                ` : ''}
                
                ${analysis.risk_analysis && !analysis.risk_analysis.error ? `
                  <div class="risk-analysis">
                    <h5>风险评估</h5>
                    <p>风险等级：<span class="risk-level risk-${analysis.risk_analysis.overall_risk_level || 'unknown'}">${getRiskLevelText(analysis.risk_analysis.overall_risk_level || 'unknown')}</span></p>
                    <p>发现风险数：${analysis.risk_analysis.risk_count || 0}</p>
                  </div>
                ` : ''}
              </div>
            `;
          } catch (error) {
            console.error('Analysis error:', error);
            let errorMsg = '未知错误';
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
                <p>分析失败：${errorMsg}</p>
                <p style="font-size: 0.8em; color: #666; margin-top: 10px;">
                  请确保后端服务正在运行在 http://localhost:8000<br>
                  如果问题持续，请检查浏览器控制台和后端日志
                </p>
              </div>
            `;
          } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = '分析商品';
          }
        });
      } else if (analyzeBtn && !currentProduct) {
        // 如果按钮存在但没有商品信息，显示提示
        analyzeBtn.addEventListener('click', () => {
          const resultDiv = document.getElementById('analysis-result');
          resultDiv.innerHTML = `
            <div class="error">
              <p>无法分析：未检测到商品信息</p>
              <p style="font-size: 0.8em; color: #666; margin-top: 10px;">
                请确保在商品详情页面，或刷新页面后重试
              </p>
            </div>
          `;
        });
      }
      
      if (riskBtn && currentProduct) {
        riskBtn.addEventListener('click', async () => {
          riskBtn.disabled = true;
          riskBtn.textContent = '分析中...';
          const resultDiv = document.getElementById('analysis-result');
          resultDiv.innerHTML = '<div class="loading">正在进行风险评估...</div>';
          
          try {
            const result = await window.apiClient.analyzeProduct(currentProduct);
            const riskAnalysis = result.data?.risk_analysis || result.risk_analysis;
            
            if (riskAnalysis && !riskAnalysis.error) {
              resultDiv.innerHTML = `
                <div class="result-content">
                  <h4>风险评估报告</h4>
                  <div class="risk-level-badge risk-${riskAnalysis.overall_risk_level || 'unknown'}">
                    ${getRiskLevelText(riskAnalysis.overall_risk_level || 'unknown')}
                  </div>
                  
                  ${riskAnalysis.detailed_risks && riskAnalysis.detailed_risks.length > 0 ? `
                    <div class="risks-list">
                      <h5>发现的风险：</h5>
                      ${riskAnalysis.detailed_risks.map(risk => `
                        <div class="risk-item">
                          <strong>${risk.risk_type || '未知类型'}</strong>
                          <p>${risk.evidence || '无详细信息'}</p>
                          <span class="severity">严重程度：${((risk.severity || 0) * 100).toFixed(0)}%</span>
                        </div>
                      `).join('')}
                    </div>
                  ` : '<p>未发现明显风险</p>'}
                  
                  ${riskAnalysis.mitigation_suggestions && riskAnalysis.mitigation_suggestions.length > 0 ? `
                    <div class="suggestions">
                      <h5>建议：</h5>
                      <ul>
                        ${riskAnalysis.mitigation_suggestions.map(s => `<li>${s}</li>`).join('')}
                      </ul>
                    </div>
                  ` : ''}
                </div>
              `;
            } else {
              resultDiv.innerHTML = '<div class="error">风险评估失败或未发现风险</div>';
            }
          } catch (error) {
            console.error('Risk analysis error:', error);
            resultDiv.innerHTML = `<div class="error">风险评估失败：${error.message || '未知错误'}</div>`;
          } finally {
            riskBtn.disabled = false;
            riskBtn.textContent = '风险分析';
          }
        });
      }
      
      if (predictBtn && currentProduct) {
        predictBtn.addEventListener('click', async () => {
          predictBtn.disabled = true;
          predictBtn.textContent = '预测中...';
          const resultDiv = document.getElementById('analysis-result');
          resultDiv.innerHTML = '<div class="loading">正在进行价格预测...</div>';
          
          try {
            if (currentProduct.productId) {
              const result = await window.apiClient.predictPrice(currentProduct.productId);
              resultDiv.innerHTML = `
                <div class="result-content">
                  <h4>价格预测</h4>
                  <pre>${JSON.stringify(result, null, 2)}</pre>
                </div>
              `;
            } else {
              resultDiv.innerHTML = '<div class="error">无法进行价格预测：商品ID缺失</div>';
            }
          } catch (error) {
            console.error('Price prediction error:', error);
            resultDiv.innerHTML = `<div class="error">价格预测失败：${error.message || '未知错误'}</div>`;
          } finally {
            predictBtn.disabled = false;
            predictBtn.textContent = '价格预测';
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
            alert('请输入商品名称');
            return;
          }
          
          searchBtn.disabled = true;
          searchBtn.textContent = '搜索中...';
          const resultsDiv = document.getElementById('comparison-results');
          resultsDiv.innerHTML = '<div class="loading">正在搜索并比较价格...</div>';
          
          try {
            const result = await window.apiClient.comparePrices(query);
            console.log('比价结果:', result);
            
            // 处理不同的返回格式
            let comparison = result.comparison || result.data?.comparison || {};
            const totalProducts = result.total_products || 0;
            const message = result.message || '';
            const dataSource = result.data_source || 'unknown';
            
            if (Object.keys(comparison).length > 0) {
              // 检查是否是all_products格式
              if (comparison.all_products) {
                const allProducts = comparison.all_products;
                const platformPrices = allProducts.platform_prices || {};
                const products = allProducts.products || [];
                
                resultsDiv.innerHTML = `
                  <div class="comparison-results-content">
                    <h4>价格比较结果</h4>
                    <p style="font-size: 0.9em; color: #666;">数据来源: ${dataSource === 'database' ? '数据库' : 'API'} | 找到 ${totalProducts} 个商品</p>
                    ${Object.entries(platformPrices).map(([platform, platformProducts]) => {
                      if (Array.isArray(platformProducts)) {
                        return `
                          <div class="comparison-group">
                            <h5>${platform.toUpperCase()} 平台</h5>
                            <div class="products-list">
                              ${platformProducts.map(p => `
                                <div class="product-item">
                                  <strong>${p.title || p.name || '未知商品'}</strong>
                                  <span class="price">¥${p.price || 'N/A'}</span>
                                  ${p.product_id ? `<span class="product-id">ID: ${p.product_id}</span>` : ''}
                                  ${p.product_url ? `<a href="${p.product_url}" target="_blank" class="product-link">查看商品</a>` : ''}
                                </div>
                              `).join('')}
                            </div>
                          </div>
                        `;
                      } else {
                        return `
                          <div class="comparison-group">
                            <h5>${platform.toUpperCase()} 平台</h5>
                            <div class="price-comparison">
                              <p>价格：¥${platformProducts.price || 'N/A'}</p>
                              <p>${platformProducts.title || ''}</p>
                              ${platformProducts.product_url ? `<a href="${platformProducts.product_url}" target="_blank">查看商品</a>` : ''}
                            </div>
                          </div>
                        `;
                      }
                    }).join('')}
                  </div>
                `;
              } else {
                // 标准格式 - 有商品组
                resultsDiv.innerHTML = `
                  <div class="comparison-results-content">
                    <h4>价格比较结果</h4>
                    <p style="font-size: 0.9em; color: #666;">找到 ${totalProducts} 个商品 | 数据来源: ${dataSource === 'database' ? '数据库' : 'API'}</p>
                    ${Object.entries(comparison).map(([productKey, data]) => {
                      // 处理不同的数据格式
                      const products = data.products || [];
                      const platformPrices = data.platform_prices || {};
                      
                      // 如果有platform_prices，优先使用
                      if (platformPrices && Object.keys(platformPrices).length > 0) {
                        return `
                          <div class="comparison-group">
                            <h5>${productKey}</h5>
                            <div class="price-comparison">
                              ${data.min_price ? `<p><strong>最低价：</strong>¥${data.min_price}</p>` : ''}
                              ${data.max_price ? `<p><strong>最高价：</strong>¥${data.max_price}</p>` : ''}
                              ${data.price_diff ? `<p><strong>价格差：</strong>¥${data.price_diff.toFixed(2)}</p>` : ''}
                              ${data.price_diff_percent ? `<p><strong>节省：</strong>${data.price_diff_percent.toFixed(1)}%</p>` : ''}
                              ${data.best_platform ? `<p><strong>最佳平台：</strong>${data.best_platform}</p>` : ''}
                            </div>
                            <div class="platform-prices">
                              ${Object.entries(platformPrices).map(([platform, info]) => `
                                <div class="platform-price-item ${platform === data.best_platform ? 'best-price' : ''}">
                                  <span class="platform-badge platform-${platform}">${platform.toUpperCase()}</span>
                                  <span class="price">¥${info.price || 'N/A'}</span>
                                  <div class="product-info">
                                    <div class="product-title">${info.title || ''}</div>
                                    ${info.product_url ? `<a href="${info.product_url}" target="_blank" class="product-link">查看商品</a>` : ''}
                                  </div>
                                </div>
                              `).join('')}
                            </div>
                          </div>
                        `;
                      } else if (products.length > 0) {
                        // 回退到products列表
                        return `
                          <div class="comparison-group">
                            <h5>${productKey}</h5>
                            <div class="price-comparison">
                              ${data.min_price ? `<p><strong>最低价：</strong>¥${data.min_price}</p>` : ''}
                              ${data.max_price ? `<p><strong>最高价：</strong>¥${data.max_price}</p>` : ''}
                              ${data.price_difference ? `<p><strong>价格差：</strong>¥${data.price_difference}</p>` : ''}
                              ${data.savings_percentage ? `<p><strong>节省：</strong>${data.savings_percentage.toFixed(1)}%</p>` : ''}
                              ${data.best_platform ? `<p><strong>最佳平台：</strong>${data.best_platform}</p>` : ''}
                            </div>
                            <div class="products-list">
                              ${products.map(p => `
                                <div class="product-item">
                                  <strong>${p.title || p.name || productKey}</strong>
                                  <span class="platform-badge platform-${p.platform}">${p.platform || '未知'}</span>
                                  <span class="price">¥${p.price || 'N/A'}</span>
                                  ${p.product_url ? `<a href="${p.product_url}" target="_blank" class="product-link">查看</a>` : ''}
                                </div>
                              `).join('')}
                            </div>
                          </div>
                        `;
                      } else {
                        // 只有基本信息
                        return `
                          <div class="comparison-group">
                            <h5>${productKey}</h5>
                            <p>商品数量: ${data.product_count || 0}</p>
                            <p>平台: ${(data.platforms || []).join(', ')}</p>
                          </div>
                        `;
                      }
                    }).join('')}
                  </div>
                `;
              }
            } else {
              // 没有找到结果
              let errorMsg = message || '未找到价格比较结果';
              if (totalProducts > 0) {
                errorMsg = `找到 ${totalProducts} 个商品，但无法进行价格对比。${message || '请尝试使用更具体的关键词。'}`;
              } else {
                errorMsg = `${message || '未找到价格比较结果。请确保已上传商品数据到数据库，或尝试使用更具体的关键词。'}`;
              }
              resultsDiv.innerHTML = `<div class="error">${errorMsg}</div>`;
            }
          } catch (error) {
            console.error('Comparison error:', error);
            // 更好的错误处理
            let errorMessage = '未知错误';
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
            resultsDiv.innerHTML = `<div class="error">价格比较失败：${errorMessage}</div>`;
          } finally {
            searchBtn.disabled = false;
            searchBtn.textContent = '搜索';
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
            alert('请输入有效的目标价格');
            return;
          }
          
          if (!currentProduct.productId) {
            alert('无法追踪：商品ID缺失');
            return;
          }
          
          trackBtn.disabled = true;
          trackBtn.textContent = '设置中...';
          
          try {
            const result = await window.apiClient.trackPrice(currentProduct.productId, targetPrice);
            alert('价格追踪已设置！');
            
            // 刷新追踪列表
            const trackerList = document.getElementById('tracker-list');
            trackerList.innerHTML = `
              <div class="tracker-item">
                <strong>${currentProduct.name || '未知商品'}</strong>
                <p>目标价格：¥${targetPrice}</p>
                <p>当前价格：¥${currentProduct.price || 'N/A'}</p>
              </div>
            `;
          } catch (error) {
            console.error('Track price error:', error);
            alert('设置价格追踪失败：' + (error.message || '未知错误'));
          } finally {
            trackBtn.disabled = false;
            trackBtn.textContent = '开始追踪';
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

  // 基础 Markdown 渲染（安全性：先转义，再替换常见标记）
  function renderMarkdown(raw) {
    if (!raw) return '';
    // 预规范化：把“：. ”、行内“ . ”和行首“. ”转成标准列表
    let normalized = raw
      // 在中文冒号后出现的 . 开头分点：例如 “以下特点：. A . B” -> 换行并起一个项
      .replace(/(：)\s*\.\s+/g, '$1\n- ')
      // 行内以“ . ”继续分点的情况：把分隔符替换为换行的分点
      .replace(/\s\.\s+(?=\S)/g, '\n- ')
      // 行首的 “. ” 视为分点
      .replace(/(^|\n)\s*\.\s+/g, '$1- ');

    // 转义 HTML
    let escaped = normalized
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');

    // 代码片段 `code`
    escaped = escaped.replace(/`([^`]+?)`/g, '<code>$1</code>');
    // 粗体 **text**
    escaped = escaped.replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>');
    // 斜体 *text* （避免与粗体冲突，使用负向前瞻粗体）
    escaped = escaped.replace(/(^|[^*])\*([^*]+?)\*(?!\*)/g, '$1<em>$2</em>');
    // 标题 #, ##, ### 行首
    escaped = escaped.replace(/^###\s+(.+)$/gm, '<strong style="font-size:14px;">$1</strong>')
                     .replace(/^##\s+(.+)$/gm, '<strong style="font-size:15px;">$1</strong>')
                     .replace(/^#\s+(.+)$/gm, '<strong style="font-size:16px;">$1</strong>');
    // 有序列表 1. 或 1、
    escaped = escaped.replace(/^(\d+)[\.\u3001]\s+(.+)$/gm, '<div class="md-li"><span class="md-li-num">$1</span> $2</div>');
    // 无序列表 - 或 *
    escaped = escaped.replace(/^[-*]\s+(.+)$/gm, '<div class="md-li">• $1</div>');
    // 常见项目符号 • · ・ 行首
    escaped = escaped.replace(/^[\u2022\u00b7\u30fb•·・]\s+(.+)$/gm, '<div class="md-li">• $1</div>');

    // 换行 -> <br>
    escaped = escaped.replace(/\r?\n/g, '<br>');

    return escaped;
  }

  // 为分析结果添加更智能的换行/要点格式化
  function formatAnalysisText(text) {
    if (!text) return '';
    let s = String(text);

    // 1) 处理 “。.” 或 “；.” 这种分隔为新的一行的要点
    s = s.replace(/(。|；|！|？|\?|\!)\s*\.\s+/g, '$1\n- ');
    // 2) 处理 “。• ”/“；• ”等情况
    s = s.replace(/(。|；|！|？|\?|\!)\s*[•·・]\s+/g, '$1\n- ');
    // 3) 如果整段没有任何换行，但包含多个“。 ”，把句号后的空格视作换行（仅限中文句号）
    if (!/\n/.test(s) && /。\s*\S/.test(s)) {
      s = s.replace(/。\s*/g, '。\n');
    }
    // 4) 在常见的结尾 CTA 前断行，例如“我帮您…吗？”
    s = s.replace(/\s*(我帮您[^。！？]*[？?])/g, '\n$1');

    // 复用 Markdown 渲染，支持列表与换行
    return renderMarkdown(s);
  }

  // 将后端枚举/英文动作映射为中文可读文本，避免未定义函数导致的运行时错误
  function getActionText(action) {
    const map = {
      buy: '建议购买',
      purchase: '建议购买',
      wait: '建议观望',
      hold: '建议观望',
      avoid: '不建议购买',
      skip: '不建议购买'
    };
    if (!action) return '—';
    const key = String(action).toLowerCase();
    return map[key] || action;
  }

  function getRiskLevelText(level) {
    const map = {
      low: '低风险',
      medium: '中风险',
      mid: '中风险',
      high: '高风险',
      unknown: '未知风险'
    };
    if (!level) return '未知风险';
    const key = String(level).toLowerCase();
    return map[key] || level;
  }

  // 修改聊天流式部分：在 setupViewEventListeners 内的 streaming 逻辑保持不变，这里补充一个全局 hook
  // 重写发送消息时的流式 append：查找现有 streaming-active 的逻辑，在 onDelta 中使用 markdown。
  // 由于原逻辑已在前面定义，这里不重复；只要前面 onDelta 改为 contentDiv.innerHTML = renderMarkdown(rawBuffer);
})();
