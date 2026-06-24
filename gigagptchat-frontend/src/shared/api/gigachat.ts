import { API_CONFIG } from './config';
import { getAccessToken } from './auth';
import type { Message, ChatCompletionResponse } from '@/entities/message/types';

export interface ChatCompletionParams {
  model?: string;
  messages: Message[];
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  repetition_penalty?: number;
  stream?: boolean;
}

export interface Model {
  id: string;
  object: string;
  owned_by: string;
}

export interface ModelsResponse {
  object: string;
  data: Model[];
}

const ensureSystemMessage = (messages: Message[]): Message[] => {
  const hasSystem = messages.some((m) => m.role === 'system');
  
  if (hasSystem) {
    return messages;
  }
  
  return [
    { role: 'system', content: API_CONFIG.SYSTEM_PROMPT },
    ...messages,
  ];
};

export const sendChatCompletion = async (params: ChatCompletionParams): Promise<string> => {
  const token = await getAccessToken();

  const messagesWithSystem = ensureSystemMessage(params.messages);

  const requestBody: ChatCompletionParams = {
    model: API_CONFIG.DEFAULT_MODEL,
    temperature: API_CONFIG.defaultParams.temperature,
    top_p: API_CONFIG.defaultParams.top_p,
    max_tokens: API_CONFIG.defaultParams.max_tokens,
    stream: false,
    ...params,
    messages: messagesWithSystem,
  };

  const response = await fetch(`${API_CONFIG.BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`GigaChat API error (${response.status}): ${errorText}`);
  }

  const data: ChatCompletionResponse = await response.json();
  return data.choices[0]?.message?.content || '';
};

export const sendMessage = (messages: Message[], model?: string): Promise<string> => {
  return sendChatCompletion({ messages, model });
};

export const getModels = async (): Promise<Model[]> => {
  const token = await getAccessToken();

  const response = await fetch(`${API_CONFIG.BASE_URL}/models`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch models (${response.status}): ${errorText}`);
  }

  const data: ModelsResponse = await response.json();
  return data.data || [];
};

export type StreamCallback = (token: string) => void;

export const sendChatCompletionStream = async (
  params: ChatCompletionParams,
  onToken: StreamCallback,
  signal?: AbortSignal
): Promise<void> => {
  const token = await getAccessToken();

  const messagesWithSystem = ensureSystemMessage(params.messages);

  const requestBody: ChatCompletionParams = {
    model: API_CONFIG.DEFAULT_MODEL,
    temperature: API_CONFIG.defaultParams.temperature,
    top_p: API_CONFIG.defaultParams.top_p,
    max_tokens: API_CONFIG.defaultParams.max_tokens,
    stream: true,
    ...params,
    messages: messagesWithSystem,
  };

  const response = await fetch(`${API_CONFIG.BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(requestBody),
    signal,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`GigaChat API error (${response.status}): ${errorText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Response body is not readable');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim() || line.startsWith(':')) continue;

        if (line.startsWith('data: ')) {
          const data = line.slice(6);

          if (data === '[DONE]') {
            return;
          }

          try {
            const parsed = JSON.parse(data);
            
            const content = parsed.choices?.[0]?.delta?.content;
            
            if (content) {
              onToken(content);
            }
          } catch (err) {
            console.error('Failed to parse SSE data:', err);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
};