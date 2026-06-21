import React from 'react';
import { useChat } from '@/app/providers/ChatProvider';
import { ChatListItem } from './ChatListItem';
import { Button } from '@/shared/ui';
import { Input } from '@/shared/ui';
import { Plus, Search, MessageSquare, Sparkles, Wifi } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { 
    filteredChats, 
    activeChat, 
    createChat, 
    searchQuery, 
    setSearchQuery 
  } = useChat();

  const handleCreateChat = () => {
    createChat();
  };

  return (
    <aside className="w-80 flex flex-col h-full border-r border-[var(--sber-border)]" style={{ background: 'var(--sber-gradient-sidebar)' }}>
      <div className="p-4 border-b border-[var(--sber-border)]">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-md" style={{ background: 'var(--sber-gradient-primary)' }}>
            <Sparkles size={20} strokeWidth={2.5} />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[var(--sber-text-primary)]">GigaGPTChat</h2>
            <p className="text-xs text-[var(--sber-text-tertiary)]">AI Assistant</p>
          </div>
        </div>
        
        <Button 
          onClick={handleCreateChat} 
          variant="primary" 
          size="md"
          className="w-full"
        >
          <Plus size={18} className="mr-2" />
          Новый чат
        </Button>
      </div>

      <div className="p-4 border-b border-[var(--sber-border)]">
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--sber-text-tertiary)]">
            <Search size={16} />
          </span>
          <Input
            type="text"
            placeholder="Поиск по чатам..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {filteredChats.length === 0 ? (
          <div className="text-center text-[var(--sber-text-tertiary)] text-sm py-12">
            <div className="flex justify-center mb-3 opacity-50">
              <MessageSquare size={40} />
            </div>
            <p>{searchQuery ? 'Чаты не найдены' : 'Нет чатов'}</p>
            {!searchQuery && (
              <p className="text-xs mt-2">Создайте новый чат, чтобы начать</p>
            )}
          </div>
        ) : (
          <div className="space-y-1">
            {filteredChats.map((chat) => (
              <ChatListItem
                key={chat.id}
                chat={chat}
                isActive={chat.id === activeChat?.id}
              />
            ))}
          </div>
        )}
      </div>

      <div className="p-4 border-t border-[var(--sber-border)] bg-[var(--sber-bg-tertiary)]">
        <div className="flex items-center justify-between text-xs text-[var(--sber-text-tertiary)]">
          <span>Всего чатов: {filteredChats.length}</span>
          <span className="flex items-center gap-1.5">
            <Wifi size={12} className="text-[var(--sber-primary)]" />
            Онлайн
          </span>
        </div>
      </div>
    </aside>
  );
};