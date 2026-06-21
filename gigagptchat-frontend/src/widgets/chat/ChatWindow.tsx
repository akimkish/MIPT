import React, { useEffect, useRef } from 'react';
import { useChat } from '@/app/providers/ChatProvider';
import { MessageItem } from '@/entities/message/ui/MessageItem';
import { SendMessageForm } from '@/features/sendMessage/SendMessageForm';
import { ModelSelector } from './ModelSelector';
import { Sparkles, MessageSquare } from 'lucide-react';

export const ChatWindow: React.FC = () => {
  const { activeChat } = useChat();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeChat?.messages]);

  const hasActiveChat = activeChat !== null;
  const hasMessages = hasActiveChat && activeChat!.messages.length > 0;

  return (
    <div className="flex flex-col h-full bg-[var(--sber-bg-primary)]">
      <div className="px-6 py-4 border-b border-[var(--sber-border)] bg-[var(--sber-bg-primary)] flex items-center justify-between shadow-sm">
        <div className="flex-1">
          {hasActiveChat ? (
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[var(--sber-primary-light)] flex items-center justify-center text-[var(--sber-primary)]">
                <MessageSquare size={20} />
              </div>
              <div>
                <h1 className="text-lg font-bold text-[var(--sber-text-primary)]">{activeChat!.title}</h1>
                <p className="text-xs text-[var(--sber-text-tertiary)]">
                  {activeChat!.messages.length} сообщений
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-md" style={{ background: 'var(--sber-gradient-primary)' }}>
                <Sparkles size={20} strokeWidth={2.5} />
              </div>
              <div>
                <h1 className="text-lg font-bold text-[var(--sber-text-primary)]">Новый чат</h1>
                <p className="text-xs text-[var(--sber-text-tertiary)]">Выберите модель и начните диалог</p>
              </div>
            </div>
          )}
        </div>
        
        <ModelSelector />
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6" style={{ background: 'var(--sber-bg-secondary)' }}>
        <div className="max-w-4xl mx-auto">
          {!hasMessages ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-20">
              <div className="w-24 h-24 rounded-3xl flex items-center justify-center text-white mb-8 shadow-xl" style={{ background: 'var(--sber-gradient-primary)' }}>
                <Sparkles size={48} strokeWidth={2} />
              </div>
              
              <h2 className="text-5xl font-bold text-[var(--sber-text-primary)] mb-4">
                GigaGPTChat
              </h2>
              
              <p className="text-xl text-[var(--sber-text-secondary)] mb-12 max-w-md leading-relaxed">
                Ваш интеллектуальный помощник на базе искусственного интеллекта Сбера
              </p>
            </div>
          ) : (
            <>
              {activeChat!.messages.map((message) => (
                <MessageItem key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      <SendMessageForm />
    </div>
  );
};