import React from 'react';
import { ChatWindow } from '@/widgets/chat/ChatWindow';
import { Sidebar } from '@/widgets/sidebar';

const ChatPage: React.FC = () => {
  return (
    <div className="flex h-screen bg-white">
      <Sidebar />
      
      <main className="flex-1 flex flex-col overflow-hidden">
        <ChatWindow />
      </main>
    </div>
  );
};

export default ChatPage;