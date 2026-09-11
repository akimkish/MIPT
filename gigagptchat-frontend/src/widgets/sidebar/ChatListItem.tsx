import React, { useState } from 'react';
import { useChat } from '@/app/providers/ChatProvider';
import type { Chat } from '@/entities/chat/types';
import { MessageSquare, Pencil, Trash2 } from 'lucide-react';

interface ChatListItemProps {
  chat: Chat;
  isActive: boolean;
}

export const ChatListItem: React.FC<ChatListItemProps> = ({ chat, isActive }) => {
  const { setActiveChat, updateChatTitle, deleteChat } = useChat();
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(chat.title);

  const handleClick = () => {
    if (!isEditing) {
      setActiveChat(chat.id);
    }
  };

  const handleSave = () => {
    const trimmed = editTitle.trim();
    
    if (trimmed && trimmed !== chat.title) {
      updateChatTitle(chat.id, trimmed);
    } else {
      setEditTitle(chat.title);
    }
    
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      setEditTitle(chat.title);
      setIsEditing(false);
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    const confirmed = window.confirm(`Удалить чат "${chat.title}"?`);
    
    if (confirmed) {
      deleteChat(chat.id);
    }
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
  };

  return (
    <div
      onClick={handleClick}
      className={`
        group relative flex items-center gap-3 px-3 py-3 rounded-xl cursor-pointer
        transition-all duration-200
        ${isActive 
          ? 'bg-[var(--sber-primary-light)] shadow-sm' 
          : 'hover:bg-[var(--sber-bg-tertiary)]'}
      `}
    >
      {isActive && (
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full" style={{ background: 'var(--sber-primary)' }}></div>
      )}
      
      <div className={`
        w-8 h-8 rounded-lg flex items-center justify-center
        transition-colors duration-200
        ${isActive 
          ? 'text-white' 
          : 'bg-[var(--sber-bg-tertiary)] text-[var(--sber-text-secondary)]'}
      `}
        style={isActive ? { background: 'var(--sber-gradient-primary)' } : undefined}
      >
        <MessageSquare size={16} strokeWidth={2} />
      </div>
      
      {isEditing ? (
        <input
          type="text"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleSave}
          autoFocus
          className="flex-1 px-2 py-1 border border-[var(--sber-primary)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--sber-primary)]"
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <div className="flex-1 min-w-0">
          <p className={`
            truncate text-sm font-medium
            ${isActive ? 'text-[var(--sber-text-primary)]' : 'text-[var(--sber-text-secondary)]'}
          `}>
            {chat.title}
          </p>
          <p className="text-xs text-[var(--sber-text-tertiary)] mt-0.5">
            {chat.messages.length} {chat.messages.length === 1 ? 'сообщение' : 'сообщений'}
          </p>
        </div>
      )}

      {!isEditing && (
        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleEdit}
            className="p-1.5 hover:bg-[var(--sber-bg-secondary)] rounded-lg text-[var(--sber-text-secondary)] hover:text-[var(--sber-primary)] transition-colors"
            title="Редактировать"
          >
            <Pencil size={14} />
          </button>
          <button
            onClick={handleDelete}
            className="p-1.5 hover:bg-[var(--sber-error-bg)] rounded-lg text-[var(--sber-text-secondary)] hover:text-[var(--sber-error)] transition-colors"
            title="Удалить"
          >
            <Trash2 size={14} />
          </button>
        </div>
      )}
    </div>
  );
};