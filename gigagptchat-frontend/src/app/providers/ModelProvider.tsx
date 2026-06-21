import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { GigaChatModel } from '@/entities/message/types';
import { getModels } from '@/shared/api/gigachat';

const SELECTED_MODEL_KEY = 'gigachat_selected_model';

const DEFAULT_MODEL: GigaChatModel = {
  id: 'GigaChat',
  name: 'GigaChat',
  owned_by: 'Sber',
  description: 'Базовая модель GigaChat',
};

const FALLBACK_MODELS: GigaChatModel[] = [
  {
    id: 'GigaChat',
    name: 'GigaChat',
    owned_by: 'Sber',
    description: 'Базовая модель для общих задач',
  },
  {
    id: 'GigaChat-Plus',
    name: 'GigaChat Plus',
    owned_by: 'Sber',
    description: 'Улучшенная модель с повышенным качеством ответов',
  },
  {
    id: 'GigaChat-Pro',
    name: 'GigaChat Pro',
    owned_by: 'Sber',
    description: 'Профессиональная модель для сложных задач',
  },
  {
    id: 'GigaChat-Max',
    name: 'GigaChat Max',
    owned_by: 'Sber',
    description: 'Максимальная модель с лучшими возможностями',
  },
];

interface ModelContextValue {
  models: GigaChatModel[];
  selectedModel: GigaChatModel;
  isLoading: boolean;
  error: string | null;
  setSelectedModel: (modelId: string) => void;
}

const ModelContext = createContext<ModelContextValue | null>(null);

export const ModelProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [models, setModels] = useState<GigaChatModel[]>(FALLBACK_MODELS);
  
  const [selectedModel, setSelectedModelState] = useState<GigaChatModel>(() => {
    try {
      const stored = localStorage.getItem(SELECTED_MODEL_KEY);
      if (stored) {
        const found = FALLBACK_MODELS.find((m) => m.id === stored);
        if (found) return found;
      }
    } catch (err) {
      console.error('Failed to read selected model from localStorage:', err);
    }
    return DEFAULT_MODEL;
  });
  
  const [isLoading, setIsLoading] = useState(true);
  
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadModels = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const apiModels = await getModels();
        
        if (apiModels && apiModels.length > 0) {
          const mapped: GigaChatModel[] = apiModels.map((m) => ({
            id: m.id,
            name: m.id,
            owned_by: m.owned_by,
          }));
          setModels(mapped);
          
          const stillExists = mapped.some((m) => m.id === selectedModel.id);
          if (!stillExists && mapped.length > 0) {
            setSelectedModelState(mapped[0]);
          }
        }
      } catch (err) {
        console.error('Failed to load models from API, using fallback:', err);
        setError('Не удалось загрузить модели. Используется список по умолчанию.');
      } finally {
        setIsLoading(false);
      }
    };

    loadModels();
  }, []);

  const setSelectedModel = useCallback((modelId: string) => {
    const model = models.find((m) => m.id === modelId);
    if (model) {
      setSelectedModelState(model);
      try {
        localStorage.setItem(SELECTED_MODEL_KEY, modelId);
      } catch (err) {
        console.error('Failed to save selected model to localStorage:', err);
      }
    }
  }, [models]);

  const value: ModelContextValue = {
    models,
    selectedModel,
    isLoading,
    error,
    setSelectedModel,
  };

  return <ModelContext.Provider value={value}>{children}</ModelContext.Provider>;
};

export const useModels = (): ModelContextValue => {
  const context = useContext(ModelContext);
  if (!context) {
    throw new Error('useModels must be used within a ModelProvider');
  }
  return context;
};