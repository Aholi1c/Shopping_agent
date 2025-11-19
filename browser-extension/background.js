/**
 * Background Service Worker
 * Handles background communication and state management
 */

const API_BASE_URL = 'http://localhost:8000';
let currentTabId = null;

// Ensure all API calls are safe
try {
  // Initialize on install or startup
  if (chrome.runtime && chrome.runtime.onInstalled) {
    chrome.runtime.onInstalled.addListener((details) => {
      console.log('Smart Shopping Assistant extension installed', details.reason);
      initializeStorage().catch(error => {
        console.error('Failed to initialize storage:', error);
      });
      
      // Create context menu
      if (chrome.contextMenus && chrome.contextMenus.create) {
        try {
          chrome.contextMenus.create({
            id: 'analyzeProduct',
            title: 'Analyze Current Product',
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
      console.log('Smart Shopping Assistant extension started');
      initializeStorage().catch(error => {
        console.error('Failed to initialize storage:', error);
      });
    });
  }

  // Initialize storage
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

  // Handle tab updates
  if (chrome.tabs && chrome.tabs.onUpdated) {
    chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
      if (changeInfo.status === 'complete' && tab.url) {
        // Check if it's a shopping website
        if (isShoppingSite(tab.url)) {
          currentTabId = tabId;
          
          // Notify content script to extract product information
          try {
            if (chrome.tabs && chrome.tabs.sendMessage) {
              chrome.tabs.sendMessage(tabId, {
                action: 'extractProductInfo'
              }, (response) => {
                if (chrome.runtime.lastError) {
                  // Content script may not be loaded yet, this is normal
                  console.log('Content script not ready:', chrome.runtime.lastError.message);
                }
              });
            }
          } catch (error) {
            console.log('Failed to send extract product info message:', error);
          }
        }
      }
    });
  }

  // Check if it's a shopping website
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

  // Handle messages from content script
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
        // Content script notifies that product information has been extracted
        console.log('Received product information extraction notification:', request.productData);
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
        return true; // Keep message channel open
      }
      
      return true;
    });
  }

  // Handle API requests
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
        // Try to get error details
        let errorMessage = `API request failed: ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          // If unable to parse error response, use default message
        }
        throw new Error(errorMessage);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request error:', error);
      // Return more detailed error information
      throw new Error(`API request failed: ${error.message}`);
    }
  }

  // Helper function to trigger analysis
  async function triggerAnalysis(productData, tabId) {
    if (!productData) {
      console.warn('Product information is empty, unable to trigger analysis');
      return;
    }
    
    try {
      console.log('Triggering analysis, product information:', productData);
      
      // Ensure product information is saved
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
        console.log('Product information saved:', `product_${tabId}`);
      }
      
      // Use storage as intermediary to trigger analysis
      if (chrome.storage && chrome.storage.local) {
        await chrome.storage.local.set({
          [`analysis_request_${tabId}`]: {
            action: 'startAnalysis',
            productData: productData,
            timestamp: Date.now()
          }
        });
        console.log('Analysis request saved to storage');
      }
      
      // Also try to send message directly to sidepanel
      try {
        chrome.runtime.sendMessage({
          action: 'startAnalysis',
          productData: productData
        }, (response) => {
          if (chrome.runtime.lastError) {
            console.log('Failed to send message directly (sidepanel may not be loaded):', chrome.runtime.lastError);
            console.log('Sidepanel will read analysis request from storage when loaded');
          } else {
            console.log('Message sent successfully');
          }
        });
      } catch (err) {
        console.log('Exception sending message:', err);
      }
    } catch (error) {
      console.error('Failed to trigger analysis:', error);
    }
  }

  // Handle product information extraction
  async function handleProductExtraction(productData, tabId) {
    if (!productData) return;
    
    try {
      // Save product information to storage
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
        console.log('Product information saved to storage:', `product_${tabId}`);
      }
      
      // If needed, automatically send to API for analysis
      if (chrome.storage && chrome.storage.sync) {
        const config = await chrome.storage.sync.get(['config']);
        if (config.config?.autoExtract) {
          try {
            const analysis = await handleAPIRequest('/api/shopping/product-analysis', {
              method: 'POST',
              body: productData
            });
            
            // Save analysis result
            if (chrome.storage && chrome.storage.local) {
              await chrome.storage.local.set({
                [`analysis_${tabId}`]: analysis
              });
            }
            
            // Notify content script to display analysis result
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
                console.log('Failed to send analysis result:', error);
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

  // Handle context menu click
  if (chrome.contextMenus && chrome.contextMenus.onClicked) {
    chrome.contextMenus.onClicked.addListener(async (info, tab) => {
      console.log('Context menu clicked:', info.menuItemId, tab);
      if (info.menuItemId === 'analyzeProduct') {
        try {
          // 1. First open the sidepanel
          if (chrome.sidePanel && chrome.sidePanel.open) {
            await chrome.sidePanel.open({ tabId: tab.id });
            console.log('Sidepanel opened');
          }
          
          // 2. Wait a bit for sidepanel to load
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // 3. Try to extract product information directly from content script
          let productData = null;
          
          // First check if product information already exists in storage
          if (chrome.storage && chrome.storage.local) {
            const existingData = await chrome.storage.local.get([`product_${tab.id}`, `product_current`]);
            productData = existingData[`product_${tab.id}`] || existingData[`product_current`];
            if (productData) {
              console.log('Found existing product information in storage:', productData);
            }
          }
          
          // If not found, notify content script to extract
          if (!productData) {
            console.log('Product information not found, requesting content script to extract...');
            if (chrome.tabs && chrome.tabs.sendMessage) {
              try {
                chrome.tabs.sendMessage(tab.id, {
                  action: 'extractProductInfo'
                }, (response) => {
                  if (chrome.runtime.lastError) {
                    console.error('Failed to send extract product info message:', chrome.runtime.lastError);
                  } else {
                    console.log('Extract product info message sent');
                  }
                });
              } catch (error) {
                console.error('Failed to send extract message:', error);
              }
            }
          }
          
          // 4. Also trigger analysis flow
          if (chrome.tabs && chrome.tabs.sendMessage) {
            try {
              chrome.tabs.sendMessage(tab.id, {
                action: 'analyzeCurrentPage'
              }, (response) => {
                if (chrome.runtime.lastError) {
                  console.error('Failed to send analyze message:', chrome.runtime.lastError);
                  // If message sending failed, content script may not be loaded, try waiting and retry
                  setTimeout(() => {
                    chrome.tabs.sendMessage(tab.id, {
                      action: 'analyzeCurrentPage'
                    }, (retryResponse) => {
                      if (chrome.runtime.lastError) {
                        console.error('Retry sending analyze message also failed:', chrome.runtime.lastError);
                      }
                    });
                  }, 2000);
                } else {
                  console.log('Analyze message sent, waiting for response:', response);
                }
              });
            } catch (error) {
              console.error('Failed to send analyze message:', error);
            }
          }
          
          // 5. Wait for content script to extract product information (using polling)
          let attempts = 0;
          const maxAttempts = 5;
          const checkProductInfo = async () => {
            attempts++;
            console.log(`Checking product information (${attempts}/${maxAttempts})...`);
            
            if (chrome.storage && chrome.storage.local) {
              const storageData = await chrome.storage.local.get([`product_${tab.id}`, `product_current`]);
              const foundProduct = storageData[`product_${tab.id}`] || storageData[`product_current`];
              
              if (foundProduct) {
                console.log('Found product information, triggering analysis:', foundProduct);
                productData = foundProduct;
                
                // Trigger sidepanel analysis
                await triggerAnalysis(foundProduct, tab.id);
              } else if (attempts < maxAttempts) {
                // Continue waiting
                setTimeout(checkProductInfo, 500);
              } else {
                console.warn('Timeout waiting, product information not found');
                // Even without product information, open sidepanel for user to manually input
                console.log('Opening sidepanel for user to manually operate');
              }
            }
          };
          
          // Start checking
          setTimeout(checkProductInfo, 500);
        } catch (error) {
          console.error('Context menu handling error:', error);
        }
      }
    });
  }

  // Keyboard shortcut commands - check if API is available
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
  // Even if there are errors, ensure Service Worker can register
}
