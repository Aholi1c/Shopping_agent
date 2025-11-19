/**
 * Background Service Worker
 * 处理后台通信和状态管理
 */

const API_BASE_URL = 'http://localhost:8000';
let currentTabId = null;

// 确保所有API调用都是安全的
try {
  // 安装或启动时的初始化
  if (chrome.runtime && chrome.runtime.onInstalled) {
    chrome.runtime.onInstalled.addListener((details) => {
      console.log('智能购物助手插件已安装', details.reason);
      initializeStorage().catch(error => {
        console.error('Failed to initialize storage:', error);
      });
      
      // 创建右键菜单
      if (chrome.contextMenus && chrome.contextMenus.create) {
        try {
          chrome.contextMenus.create({
            id: 'analyzeProduct',
            title: '分析当前商品',
            contexts: ['page', 'selection']
          }, () => {
            if (chrome.runtime.lastError) {
              console.error('Failed to create context menu:', chrome.runtime.lastError);
            } else {
              console.log('Context menu created successfully');
            }
          });
        } catch (error) {
          console.error('Error creating context menu:', error);
        }
      }
    });
  }

  if (chrome.runtime && chrome.runtime.onStartup) {
    chrome.runtime.onStartup.addListener(() => {
      console.log('智能购物助手插件已启动');
      initializeStorage().catch(error => {
        console.error('Failed to initialize storage:', error);
      });
    });
  }

  // 初始化存储
  async function initializeStorage() {
    try {
      const defaultConfig = {
        apiUrl: API_BASE_URL,
        enabled: true,
        autoExtract: true,
        showPriceComparison: true,
        showRecommendations: true
      };
      
      if (chrome.storage && chrome.storage.sync) {
        const config = await chrome.storage.sync.get(['config']);
        if (!config.config) {
          await chrome.storage.sync.set({ config: defaultConfig });
        }
      }
    } catch (error) {
      console.error('Storage initialization error:', error);
    }
  }

  // 处理标签页更新
  if (chrome.tabs && chrome.tabs.onUpdated) {
    chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
      if (changeInfo.status === 'complete' && tab.url) {
        // 检查是否是购物网站
        if (isShoppingSite(tab.url)) {
          currentTabId = tabId;
          
          // 通知content script提取商品信息
          try {
            if (chrome.tabs && chrome.tabs.sendMessage) {
              chrome.tabs.sendMessage(tabId, {
                action: 'extractProductInfo'
              }, (response) => {
                if (chrome.runtime.lastError) {
                  // Content script可能还未加载，这是正常的
                  console.log('Content script not ready:', chrome.runtime.lastError.message);
                }
              });
            }
          } catch (error) {
            console.log('发送提取商品信息消息失败:', error);
          }
        }
      }
    });
  }

  // 判断是否是购物网站
  function isShoppingSite(url) {
    const shoppingDomains = [
      'jd.com',
      'taobao.com',
      'tmall.com',
      'pdd.com',
      'xiaohongshu.com',
      'douyin.com',
      'amazon.com',
      'amazon.cn',
      'amazon.'
    ];
    
    return shoppingDomains.some(domain => url.includes(domain));
  }

  // 处理来自content script的消息
  if (chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === 'openSidePanel') {
        if (chrome.sidePanel && sender.tab) {
          chrome.sidePanel.open({ tabId: sender.tab.id }).catch(error => {
            console.error('Failed to open side panel:', error);
          });
        }
        sendResponse({ success: true });
      } else if (request.action === 'extractProductInfo') {
        handleProductExtraction(request.data, sender.tab.id).catch(error => {
          console.error('Failed to extract product info:', error);
        });
        sendResponse({ success: true });
      } else if (request.action === 'productInfoExtracted') {
        // content script通知商品信息已提取
        console.log('收到商品信息提取通知:', request.productData);
        if (request.productData && request.tabId) {
          handleProductExtraction(request.productData, request.tabId).catch(error => {
            console.error('Failed to handle extracted product info:', error);
          });
        }
        sendResponse({ success: true });
      } else if (request.action === 'apiRequest') {
        handleAPIRequest(request.endpoint, request.options)
          .then(response => sendResponse({ success: true, data: response }))
          .catch(error => sendResponse({ success: false, error: error.message }));
        return true; // 保持消息通道开放
      }
      
      return true;
    });
  }

  // 处理API请求
  async function handleAPIRequest(endpoint, options = {}) {
    try {
      const config = chrome.storage && chrome.storage.sync 
        ? await chrome.storage.sync.get(['config'])
        : { config: null };
      const apiUrl = config.config?.apiUrl || API_BASE_URL;
      
      const response = await fetch(`${apiUrl}${endpoint}`, {
        method: options.method || 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        body: options.body ? JSON.stringify(options.body) : undefined
      });
      
      if (!response.ok) {
        // 尝试获取错误详情
        let errorMessage = `API request failed: ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          // 如果无法解析错误响应，使用默认消息
        }
        throw new Error(errorMessage);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request error:', error);
      // 返回更详细的错误信息
      throw new Error(`API request failed: ${error.message}`);
    }
  }

  // 触发分析的辅助函数
  async function triggerAnalysis(productData, tabId) {
    if (!productData) {
      console.warn('商品信息为空，无法触发分析');
      return;
    }
    
    try {
      console.log('触发分析，商品信息:', productData);
      
      // 确保商品信息已保存
      if (chrome.storage && chrome.storage.local) {
        const tabInfo = chrome.tabs && chrome.tabs.get
          ? await chrome.tabs.get(tabId).catch(() => ({ url: '' }))
          : { url: '' };
        
        const finalProductData = {
          ...productData,
          timestamp: productData.timestamp || Date.now(),
          url: productData.url || tabInfo.url || ''
        };
        
        await chrome.storage.local.set({
          [`product_${tabId}`]: finalProductData,
          [`product_current`]: finalProductData
        });
        console.log('商品信息已保存:', `product_${tabId}`);
      }
      
      // 使用storage作为中介触发分析
      if (chrome.storage && chrome.storage.local) {
        await chrome.storage.local.set({
          [`analysis_request_${tabId}`]: {
            action: 'startAnalysis',
            productData: productData,
            timestamp: Date.now()
          }
        });
        console.log('分析请求已保存到storage');
      }
      
      // 也尝试直接发送消息给侧边栏
      try {
        chrome.runtime.sendMessage({
          action: 'startAnalysis',
          productData: productData
        }, (response) => {
          if (chrome.runtime.lastError) {
            console.log('直接发送消息失败（侧边栏可能未加载）:', chrome.runtime.lastError);
            console.log('侧边栏将在加载时从storage读取分析请求');
          } else {
            console.log('消息发送成功');
          }
        });
      } catch (err) {
        console.log('发送消息异常:', err);
      }
    } catch (error) {
      console.error('触发分析失败:', error);
    }
  }

  // 处理商品信息提取
  async function handleProductExtraction(productData, tabId) {
    if (!productData) return;
    
    try {
      // 保存商品信息到存储
      if (chrome.storage && chrome.storage.local) {
        const tabInfo = chrome.tabs && chrome.tabs.get
          ? await chrome.tabs.get(tabId).catch(() => ({ url: '' }))
          : { url: '' };
        
        const finalProductData = {
          ...productData,
          timestamp: productData.timestamp || Date.now(),
          url: productData.url || tabInfo.url || ''
        };
        
        await chrome.storage.local.set({
          [`product_${tabId}`]: finalProductData,
          [`product_current`]: finalProductData
        });
        console.log('商品信息已保存到storage:', `product_${tabId}`);
      }
      
      // 如果需要，自动发送到API分析
      if (chrome.storage && chrome.storage.sync) {
        const config = await chrome.storage.sync.get(['config']);
        if (config.config?.autoExtract) {
          try {
            const analysis = await handleAPIRequest('/api/shopping/product-analysis', {
              method: 'POST',
              body: productData
            });
            
            // 保存分析结果
            if (chrome.storage && chrome.storage.local) {
              await chrome.storage.local.set({
                [`analysis_${tabId}`]: analysis
              });
            }
            
            // 通知content script显示分析结果
            if (chrome.tabs && chrome.tabs.sendMessage) {
              try {
                chrome.tabs.sendMessage(tabId, {
                  action: 'showAnalysis',
                  data: analysis
                }, (response) => {
                  if (chrome.runtime.lastError) {
                    console.log('Failed to send analysis to content script:', chrome.runtime.lastError);
                  }
                });
              } catch (error) {
                console.log('发送分析结果失败:', error);
              }
            }
          } catch (error) {
            console.error('Product analysis error:', error);
          }
        }
      }
    } catch (error) {
      console.error('Product extraction error:', error);
    }
  }

  // 处理右键菜单点击
  if (chrome.contextMenus && chrome.contextMenus.onClicked) {
    chrome.contextMenus.onClicked.addListener(async (info, tab) => {
      console.log('右键菜单点击:', info.menuItemId, tab);
      if (info.menuItemId === 'analyzeProduct') {
        try {
          // 1. 首先打开侧边栏
          if (chrome.sidePanel && chrome.sidePanel.open) {
            await chrome.sidePanel.open({ tabId: tab.id });
            console.log('侧边栏已打开');
          }
          
          // 2. 等待一下让侧边栏加载
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // 3. 先尝试直接从content script提取商品信息
          let productData = null;
          
          // 先检查storage中是否已有商品信息
          if (chrome.storage && chrome.storage.local) {
            const existingData = await chrome.storage.local.get([`product_${tab.id}`, `product_current`]);
            productData = existingData[`product_${tab.id}`] || existingData[`product_current`];
            if (productData) {
              console.log('从storage中找到已有商品信息:', productData);
            }
          }
          
          // 如果没有找到，通知content script提取
          if (!productData) {
            console.log('未找到商品信息，请求content script提取...');
            if (chrome.tabs && chrome.tabs.sendMessage) {
              try {
                chrome.tabs.sendMessage(tab.id, {
                  action: 'extractProductInfo'
                }, (response) => {
                  if (chrome.runtime.lastError) {
                    console.error('发送提取商品信息消息失败:', chrome.runtime.lastError);
                  } else {
                    console.log('提取商品信息消息已发送');
                  }
                });
              } catch (error) {
                console.error('Failed to send extract message:', error);
              }
            }
          }
          
          // 4. 同时触发分析流程
          if (chrome.tabs && chrome.tabs.sendMessage) {
            try {
              chrome.tabs.sendMessage(tab.id, {
                action: 'analyzeCurrentPage'
              }, (response) => {
                if (chrome.runtime.lastError) {
                  console.error('发送分析消息失败:', chrome.runtime.lastError);
                  // 如果消息发送失败，说明content script可能未加载，尝试等待后重试
                  setTimeout(() => {
                    chrome.tabs.sendMessage(tab.id, {
                      action: 'analyzeCurrentPage'
                    }, (retryResponse) => {
                      if (chrome.runtime.lastError) {
                        console.error('重试发送分析消息也失败:', chrome.runtime.lastError);
                      }
                    });
                  }, 2000);
                } else {
                  console.log('分析消息已发送，等待响应:', response);
                }
              });
            } catch (error) {
              console.error('Failed to send analyze message:', error);
            }
          }
          
          // 5. 等待content script提取商品信息（使用轮询方式）
          let attempts = 0;
          const maxAttempts = 5;
          const checkProductInfo = async () => {
            attempts++;
            console.log(`检查商品信息 (${attempts}/${maxAttempts})...`);
            
            if (chrome.storage && chrome.storage.local) {
              const storageData = await chrome.storage.local.get([`product_${tab.id}`, `product_current`]);
              const foundProduct = storageData[`product_${tab.id}`] || storageData[`product_current`];
              
              if (foundProduct) {
                console.log('找到商品信息，触发分析:', foundProduct);
                productData = foundProduct;
                
                // 触发侧边栏分析
                await triggerAnalysis(foundProduct, tab.id);
              } else if (attempts < maxAttempts) {
                // 继续等待
                setTimeout(checkProductInfo, 500);
              } else {
                console.warn('等待超时，未找到商品信息');
                // 即使没有商品信息，也打开侧边栏让用户手动输入
                console.log('打开侧边栏，让用户手动操作');
              }
            }
          };
          
          // 开始检查
          setTimeout(checkProductInfo, 500);
        } catch (error) {
          console.error('右键菜单处理错误:', error);
        }
      }
    });
  }

  // 快捷键命令 - 检查API是否可用
  if (chrome.commands && chrome.commands.onCommand) {
    chrome.commands.onCommand.addListener((command) => {
      if (command === 'toggle-sidepanel') {
        if (chrome.tabs && chrome.tabs.query && chrome.sidePanel) {
          chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
              chrome.sidePanel.open({ tabId: tabs[0].id }).catch(error => {
                console.error('Failed to open side panel:', error);
              });
            }
          });
        }
      }
    });
  } else {
    console.warn('chrome.commands API not available');
  }

} catch (error) {
  console.error('Service Worker initialization error:', error);
  // 即使有错误，也要确保Service Worker能够注册
}
