import React, { useState } from 'react';
import MainLayout from './components/layout/MainLayout';
import { ChatInterface } from './components/ChatInterface';
import { ShoppingAssistant } from './components/ShoppingAssistant';
import { Dashboard } from './components/Dashboard';
import { MemorySystem } from './components/MemorySystem';
import { MultiAgentSystem } from './components/MultiAgentSystem';
import { Analytics } from './components/Analytics';
import { Settings } from './components/Settings';
import { websocketService } from './services/websocket';

function App() {
  const [activeView, setActiveView] = useState<'chat' | 'shopping' | 'dashboard' | 'memory' | 'agents' | 'analytics' | 'settings'>('dashboard');
  const [cartItemsCount] = useState(3);

  React.useEffect(() => {
    // Connect to WebSocket
    websocketService.connect().catch(console.error);

    // Start periodic ping to keep connection alive
    websocketService.startPeriodicPing();

    return () => {
      websocketService.disconnect();
    };
  }, []);

  const renderContent = () => {
    switch (activeView) {
      case 'dashboard':
        return (
          <Dashboard onViewChange={(view: string) => setActiveView(view as any)} />
        );
      case 'chat':
        return (
          <ChatInterface
            onConversationChange={(conversation) => {
              console.log('Conversation changed:', conversation);
            }}
          />
        );
      case 'shopping':
        return (
          <div style={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <ShoppingAssistant userId={1} />
          </div>
        );
      case 'memory':
        return <MemorySystem userId={1} />;
      case 'agents':
        return <MultiAgentSystem userId={1} />;
      case 'analytics':
        return <Analytics userId={1} />;
      case 'settings':
        return <Settings userId={1} />;
      default:
        return (
          <Dashboard onViewChange={(view: string) => setActiveView(view as any)} />
        );
    }
  };

  return (
    <MainLayout
      activeView={activeView}
      onViewChange={setActiveView}
      cartItemsCount={cartItemsCount}
    >
      {renderContent()}
    </MainLayout>
  );
}

export default App;
