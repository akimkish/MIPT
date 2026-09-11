import React, { createContext, useContext, useReducer, useEffect, useCallback, useRef, useMemo } from 'react';
import type { Chat } from '@/entities/chat/types';
import type { ChatMessage } from '@/entities/message/types';
import { sendChatCompletionStream, sendChatCompletion } from '@/shared/api/gigachat';

type ChatAction =
  | { type: 'LOAD_CHATS'; payload: { chats: Chat[]; activeChatId: string | null } }
  | { type: 'CREATE_CHAT'; payload: Chat }
  | { type: 'SET_ACTIVE_CHAT'; payload: string | null }
  | { type: 'UPDATE_CHAT'; payload: { id: string; updates: Partial<Chat> } }
  | { type: 'DELETE_CHAT'; payload: string }
  | { type: 'ADD_MESSAGE'; payload: { chatId: string; message: ChatMessage } }
  | { type: 'UPDATE_MESSAGE'; payload: { chatId: string; messageId: string; updates: Partial<ChatMessage> } }
  | { type: 'APPEND_TO_MESSAGE'; payload: { chatId: string; messageId: string; content: string } }
  | { type: 'MARK_INITIALIZED' };

interface ChatState {
  chats: Chat[];
  activeChatId: string | null;
  isLoading: boolean;
  error: string | null;
  isInitialized: boolean;
}

const STORAGE_KEY = 'gigachat_chats';

const loadInitialState = (): ChatState => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    
    if (stored) {
      const data = JSON.parse(stored) as { chats: Chat[]; activeChatId: string | null };
      
      const activeChatExists = data.activeChatId && data.chats.some((c) => c.id === data.activeChatId);
      
      return {
        chats: data.chats || [],
        activeChatId: activeChatExists ? data.activeChatId : null,
        isLoading: false,
        error: null,
        isInitialized: true,
      };
    }
  } catch (err) {
    console.error('Failed to load chats from localStorage:', err);
  }
  
  return {
    chats: [],
    activeChatId: null,
    isLoading: false,
    error: null,
    isInitialized: true,
  };
};

const chatReducer = (state: ChatState, action: ChatAction): ChatState => {
  switch (action.type) {
    case 'LOAD_CHATS':
      return { 
        ...state, 
        chats: action.payload.chats,
        activeChatId: action.payload.activeChatId,
        isInitialized: true,
      };

    case 'MARK_INITIALIZED':
      return { ...state, isInitialized: true };

    case 'CREATE_CHAT':
      return {
        ...state,
        chats: [action.payload, ...state.chats],
        activeChatId: action.payload.id,
      };

    case 'SET_ACTIVE_CHAT':
      return { ...state, activeChatId: action.payload };

    case 'UPDATE_CHAT':
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.id ? { ...chat, ...action.payload.updates } : chat
        ),
      };

    case 'DELETE_CHAT':
      return {
        ...state,
        chats: state.chats.filter((chat) => chat.id !== action.payload),
        activeChatId: state.activeChatId === action.payload ? null : state.activeChatId,
      };

    case 'ADD_MESSAGE':
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.chatId
            ? { ...chat, messages: [...chat.messages, action.payload.message], updatedAt: Date.now() }
            : chat
        ),
      };

    case 'UPDATE_MESSAGE':
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.chatId
            ? {
                ...chat,
                messages: chat.messages.map((msg) =>
                  msg.id === action.payload.messageId ? { ...msg, ...action.payload.updates } : msg
                ),
              }
            : chat
        ),
      };

    case 'APPEND_TO_MESSAGE':
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.chatId
            ? {
                ...chat,
                messages: chat.messages.map((msg) =>
                  msg.id === action.payload.messageId
                    ? { ...msg, content: msg.content + action.payload.content }
                    : msg
                ),
              }
            : chat
        ),
      };

    default:
      return state;
  }
};

interface ChatContextValue {
  state: ChatState;
  activeChat: Chat | null;
  isStreaming: boolean;
  searchQuery: string;
  filteredChats: Chat[];
  createChat: () => string;
  setActiveChat: (id: string | null) => void;
  updateChatTitle: (id: string, title: string) => void;
  deleteChat: (id: string) => void;
  sendUserMessage: (content: string, modelId: string) => Promise<void>;
  stopGeneration: () => void;
  setSearchQuery: (query: string) => void;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(chatReducer, undefined, loadInitialState);
  
  const abortControllerRef = useRef<AbortController | null>(null);
  
  const [isStreaming, setIsStreaming] = React.useState(false);
  
  const [searchQuery, setSearchQuery] = React.useState('');

  const activeChat = state.chats.find((c) => c.id === state.activeChatId) || null;

  const filteredChats = useMemo(() => {
    if (!searchQuery.trim()) {
      return state.chats;
    }

    const query = searchQuery.toLowerCase();

    return state.chats.filter((chat) => {
      const titleMatch = chat.title.toLowerCase().includes(query);
      const contentMatch = chat.messages.some((msg) =>
        msg.content.toLowerCase().includes(query)
      );
      return titleMatch || contentMatch;
    });
  }, [state.chats, searchQuery]);

  useEffect(() => {
    if (!state.isInitialized) {
      return;
    }

    try {
      const dataToSave = {
        chats: state.chats,
        activeChatId: state.activeChatId,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(dataToSave));
    } catch (err) {
      console.error('Failed to save chats to localStorage:', err);
    }
  }, [state.chats, state.activeChatId, state.isInitialized]);

  const createChat = useCallback((): string => {
    const newChat: Chat = {
      id: `chat_${Date.now()}_${Math.random().toString(36).slice(2)}`,
      title: 'Новый чат',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    dispatch({ type: 'CREATE_CHAT', payload: newChat });
    return newChat.id;
  }, []);

  const setActiveChat = useCallback((id: string | null) => {
    dispatch({ type: 'SET_ACTIVE_CHAT', payload: id });
  }, []);

  const updateChatTitle = useCallback((id: string, title: string) => {
    dispatch({ type: 'UPDATE_CHAT', payload: { id, updates: { title } } });
  }, []);

  const deleteChat = useCallback((id: string) => {
    const chatIndex = state.chats.findIndex((c) => c.id === id);
    dispatch({ type: 'DELETE_CHAT', payload: id });

    if (state.activeChatId === id && state.chats.length > 1) {
      const nextChatIndex = chatIndex === state.chats.length - 1 ? chatIndex - 1 : chatIndex;
      const nextChat = state.chats[nextChatIndex];
      if (nextChat && nextChat.id !== id) {
        dispatch({ type: 'SET_ACTIVE_CHAT', payload: nextChat.id });
      }
    }
  }, [state.activeChatId, state.chats]);

  const sendUserMessage = useCallback(async (content: string, modelId: string) => {
    let chatId = state.activeChatId;

    if (!chatId) {
      chatId = createChat();
    }

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content,
      timestamp: Date.now(),
    };
    dispatch({ type: 'ADD_MESSAGE', payload: { chatId, message: userMessage } });

    const assistantMessageId = `msg_${Date.now()}_assistant`;
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    };
    dispatch({ type: 'ADD_MESSAGE', payload: { chatId, message: assistantMessage } });

    setIsStreaming(true);
    abortControllerRef.current = new AbortController();

    try {
      const currentChat = state.chats.find((c) => c.id === chatId);
      const contextMessages = [...(currentChat?.messages || []), userMessage]
        .filter((m) => m.role !== 'system' || m.content)
        .map(({ role, content }) => ({ role, content }));

      await sendChatCompletionStream(
        { messages: contextMessages, model: modelId },
        (token) => {
          dispatch({
            type: 'APPEND_TO_MESSAGE',
            payload: {
              chatId,
              messageId: assistantMessageId,
              content: token,
            },
          });
        },
        abortControllerRef.current.signal
      );

      const messagesCount = (currentChat?.messages.length || 0) + 1;
      if (messagesCount === 1) {
        const words = content.split(/\s+/).slice(0, 3).join(' ');
        const newTitle = words + (content.split(/\s+/).length > 3 ? '...' : '');
        updateChatTitle(chatId, newTitle || 'Новый чат');
      }
    } catch (err) {
      
      if (err instanceof Error && err.name === 'AbortError') {
        console.log('Generation stopped by user');
      } else {
        console.warn('SSE failed, falling back to REST:', err);
        
        try {
          dispatch({
            type: 'UPDATE_MESSAGE',
            payload: {
              chatId,
              messageId: assistantMessageId,
              updates: { content: '' },
            },
          });

          const currentChat = state.chats.find((c) => c.id === chatId);
          const contextMessages = [...(currentChat?.messages || []), userMessage]
            .filter((m) => m.role !== 'system' || m.content)
            .map(({ role, content }) => ({ role, content }));

          const responseText = await sendChatCompletion({
            messages: contextMessages,
            model: modelId,
          });

          dispatch({
            type: 'UPDATE_MESSAGE',
            payload: {
              chatId,
              messageId: assistantMessageId,
              updates: { content: responseText },
            },
          });

          const messagesCount = (currentChat?.messages.length || 0) + 1;
          if (messagesCount === 1) {
            const words = content.split(/\s+/).slice(0, 3).join(' ');
            const newTitle = words + (content.split(/\s+/).length > 3 ? '...' : '');
            updateChatTitle(chatId, newTitle || 'Новый чат');
          }

          console.log('Fallback to REST successful');
        } catch (restErr) {
          console.error('Both SSE and REST failed:', restErr);
          const errorMessage = restErr instanceof Error ? restErr.message : 'Неизвестная ошибка';
          dispatch({
            type: 'UPDATE_MESSAGE',
            payload: {
              chatId,
              messageId: assistantMessageId,
              updates: {
                content: `❌ Ошибка при получении ответа: ${errorMessage}`,
                isError: true,
              },
            },
          });
        }
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, [state.activeChatId, state.chats, createChat, updateChatTitle]);

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  const value: ChatContextValue = {
    state,
    activeChat,
    isStreaming,
    searchQuery,
    filteredChats,
    createChat,
    setActiveChat,
    updateChatTitle,
    deleteChat,
    sendUserMessage,
    stopGeneration,
    setSearchQuery,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};

export const useChat = (): ChatContextValue => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};