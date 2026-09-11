import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { ChatMessage } from '../types';
import { User, Bot, Copy, Check } from 'lucide-react';

interface MessageItemProps {
  message: ChatMessage;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const { role, content, isError } = message;
  const isUser = role === 'user';
  
  const [isCopied, setIsCopied] = React.useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div
      className={`
        flex w-full mb-6 animate-fade-in
        ${isUser ? 'justify-end' : 'justify-start'}
      `}
    >
      <div className={`flex gap-3 max-w-[85%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className={`
          w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
          transition-all duration-200
          ${isUser 
            ? 'text-white shadow-md' 
            : 'bg-[var(--sber-bg-tertiary)] text-[var(--sber-text-secondary)] shadow-sm'}
        `}
          style={isUser ? { background: 'var(--sber-gradient-primary)' } : undefined}
        >
          {isUser ? (
            <User size={16} strokeWidth={2.5} />
          ) : (
            <Bot size={16} strokeWidth={2.5} />
          )}
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-[var(--sber-text-tertiary)] px-1">
            {isUser ? 'Вы' : 'GigaChat'}
          </span>
          
          <div
            className={`
              relative group
              ${isUser
                ? 'text-[var(--sber-message-user-text)]'
                : isError
                  ? 'bg-[var(--sber-error-bg)] text-[var(--sber-error)] border border-[var(--sber-error)]'
                  : 'bg-[var(--sber-message-assistant)] text-[var(--sber-message-assistant-text)]'}
              ${isUser ? 'rounded-2xl rounded-tr-sm' : 'rounded-2xl rounded-tl-sm'}
              px-4 py-3 shadow-sm
            `}
            style={isUser ? { background: 'var(--sber-gradient-primary)' } : undefined}
          >
            {isUser ? (
              <p className="whitespace-pre-wrap break-words leading-relaxed">{content}</p>
            ) : (
              <div className="prose prose-sm max-w-none break-words">
                {content ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code(props) {
                        const { children, className, node, ...rest } = props;
                        const match = /language-(\w+)/.exec(className || '');
                        const isBlockCode = match;
                        
                        if (isBlockCode && match) {
                          return (
                            <SyntaxHighlighter
                              style={vscDarkPlus as any}
                              language={match[1]}
                              PreTag="div"
                            >
                              {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                          );
                        }
                        
                        return (
                          <code className={className} {...rest}>
                            {children}
                          </code>
                        );
                      },
                    }}
                  >
                    {content}
                  </ReactMarkdown>
                ) : (
                  <span className="flex gap-1.5 py-2">
                    <span className="w-2 h-2 bg-[var(--sber-text-tertiary)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-[var(--sber-text-tertiary)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-[var(--sber-text-tertiary)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </span>
                )}
              </div>
            )}

            {!isUser && content && (
              <button
                onClick={handleCopy}
                className="absolute -bottom-8 right-0 opacity-0 group-hover:opacity-100 transition-opacity bg-[var(--sber-bg-primary)] border border-[var(--sber-border)] rounded-lg px-2 py-1 shadow-sm text-xs text-[var(--sber-text-secondary)] hover:bg-[var(--sber-bg-tertiary)] flex items-center gap-1.5"
                title="Копировать"
              >
                {isCopied ? (
                  <>
                    <Check size={12} className="text-[var(--sber-primary)]" />
                    <span className="text-[var(--sber-primary)]">Скопировано</span>
                  </>
                ) : (
                  <>
                    <Copy size={12} />
                    <span>Копировать</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};