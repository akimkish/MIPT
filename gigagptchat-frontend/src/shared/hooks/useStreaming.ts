import { useState, useRef, useCallback } from 'react';
import { sendChatCompletionStream } from '@/shared/api/gigachat';
import type { Message } from '@/entities/message/types';

export interface UseStreamingReturn {
  isStreaming: boolean;
  streamedContent: string;
  startStreaming: (messages: Message[]) => Promise<void>;
  stopStreaming: () => void;
  resetStreamedContent: () => void;
}

export const useStreaming = (): UseStreamingReturn => {
  const [isStreaming, setIsStreaming] = useState(false);
  
  const [streamedContent, setStreamedContent] = useState('');
  
  const abortControllerRef = useRef<AbortController | null>(null);

  const startStreaming = useCallback(async (messages: Message[]) => {
    abortControllerRef.current = new AbortController();
    
    setIsStreaming(true);
    setStreamedContent('');

    try {
      await sendChatCompletionStream(
        { messages },
        (token) => {
          setStreamedContent((prev) => prev + token);
        },
        abortControllerRef.current.signal
      );
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        console.log('Streaming was aborted');
      } else {
        throw err;
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, []);

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  const resetStreamedContent = useCallback(() => {
    setStreamedContent('');
  }, []);

  return {
    isStreaming,
    streamedContent,
    startStreaming,
    stopStreaming,
    resetStreamedContent,
  };
};