import React, { useState, useRef, useEffect } from 'react';
import { useModels } from '@/app/providers/ModelProvider';
import { ChevronDown, Check, Circle } from 'lucide-react';

export const ModelSelector: React.FC = () => {
  const { models, selectedModel, setSelectedModel, isLoading } = useModels();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleSelect = (modelId: string) => {
    setSelectedModel(modelId);
    setIsOpen(false);
  };

  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  if (isLoading) {
    return (
      <div className="px-4 py-2 text-sm text-[var(--sber-text-tertiary)] flex items-center gap-2">
        <span className="w-2 h-2 bg-[var(--sber-primary)] rounded-full animate-pulse-slow"></span>
        Загрузка моделей...
      </div>
    );
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={handleToggle}
        className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--sber-bg-tertiary)] hover:bg-[var(--sber-border-light)] transition-all duration-200 text-sm font-medium text-[var(--sber-text-primary)] border border-[var(--sber-border)]"
        title="Выберите модель GigaChat"
      >
        <span className="font-semibold">{selectedModel.name}</span>
        <ChevronDown 
          size={16} 
          className={`transition-transform duration-200 text-[var(--sber-text-tertiary)] ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-[var(--sber-bg-primary)] border border-[var(--sber-border)] rounded-xl shadow-xl z-50 overflow-hidden animate-fade-in">
          <div className="px-4 py-3 border-b border-[var(--sber-border)]" style={{ background: 'var(--sber-gradient-sidebar)' }}>
            <p className="text-xs font-bold text-[var(--sber-text-secondary)] uppercase tracking-wide">
              Выберите модель
            </p>
          </div>
          
          <div className="max-h-96 overflow-y-auto py-2">
            {models.map((model) => {
              const isActive = model.id === selectedModel.id;
              
              return (
                <button
                  key={model.id}
                  onClick={() => handleSelect(model.id)}
                  className={`
                    w-full text-left px-4 py-3 flex items-start gap-3 transition-all duration-200
                    ${isActive 
                      ? 'bg-[var(--sber-primary-light)]' 
                      : 'hover:bg-[var(--sber-bg-tertiary)]'}
                  `}
                >
                  <div className={`
                    w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
                    ${isActive 
                      ? 'text-white' 
                      : 'bg-[var(--sber-bg-tertiary)] text-[var(--sber-text-secondary)]'}
                  `}
                    style={isActive ? { background: 'var(--sber-gradient-primary)' } : undefined}
                  >
                    {isActive ? <Check size={16} strokeWidth={3} /> : <Circle size={16} />}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm ${isActive ? 'font-bold text-[var(--sber-text-primary)]' : 'font-medium text-[var(--sber-text-secondary)]'}`}>
                      {model.name}
                    </p>
                    {model.description && (
                      <p className="text-xs text-[var(--sber-text-tertiary)] mt-1 leading-relaxed">
                        {model.description}
                      </p>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};