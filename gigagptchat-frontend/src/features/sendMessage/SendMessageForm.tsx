import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '@/app/providers/ChatProvider';
import { useModels } from '@/app/providers/ModelProvider';
import { Send, Square } from 'lucide-react';

export const SendMessageForm: React.FC = () => {
  const { sendUserMessage, isStreaming, stopGeneration } = useChat();
  const { selectedModel } = useModels();

  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputValue]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const trimmed = inputValue.trim();
    if (!trimmed || isStreaming) return;

    setInputValue('');

    try {
      await sendUserMessage(trimmed, selectedModel.id);
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-[var(--sber-border)] bg-[var(--sber-bg-primary)] p-4 shadow-lg">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="relative">
          <div className="flex items-end gap-3 bg-[var(--sber-bg-secondary)] border border-[var(--sber-border)] rounded-2xl p-3 shadow-sm focus-within:ring-2 focus-within:ring-[var(--sber-primary)] focus-within:border-transparent transition-all duration-200">
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Напишите сообщение..."
              disabled={isStreaming}
              rows={1}
              className="flex-1 px-2 py-2 bg-transparent border-0 resize-none focus:outline-none text-[var(--sber-text-primary)] placeholder:text-[var(--sber-text-tertiary)] disabled:opacity-50"
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={stopGeneration}
                className="w-10 h-10 rounded-full bg-[var(--sber-error)] hover:bg-red-600 text-white flex items-center justify-center transition-all duration-200 shadow-md hover:shadow-lg flex-shrink-0"
                title="Остановить генерацию"
              >
                <Square size={16} fill="currentColor" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!inputValue.trim()}
                className="w-10 h-10 rounded-full text-white flex items-center justify-center transition-all duration-200 shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none flex-shrink-0"
                style={{ background: 'var(--sber-gradient-primary)' }}
                title="Отправить сообщение"
              >
                <Send size={16} strokeWidth={2.5} className="-rotate-45" />
              </button>
            )}
          </div>
          
          <div className="flex items-center justify-between mt-2 px-2">
            <p className="text-xs text-[var(--sber-text-tertiary)]">
              <kbd className="px-2 py-1 bg-[var(--sber-bg-tertiary)] rounded text-xs font-mono">Enter</kbd> для отправки, <kbd className="px-2 py-1 bg-[var(--sber-bg-tertiary)] rounded text-xs font-mono">Shift+Enter</kbd> для новой строки
            </p>
            <p className="text-xs text-[var(--sber-text-tertiary)]">
              Модель: <span className="font-semibold text-[var(--sber-primary)]">{selectedModel.name}</span>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};