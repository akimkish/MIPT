import { ChatPage } from '@/pages/chat'

import { ErrorBoundary, ChatProvider, ModelProvider } from '@/app/providers'

function App() {
  return (
    <ErrorBoundary>
      <ModelProvider>
        <ChatProvider>
          <ChatPage />
        </ChatProvider>
      </ModelProvider>
    </ErrorBoundary>
  )
}

export default App