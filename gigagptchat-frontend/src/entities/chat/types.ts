import type { ChatMessage } from '@/entities/message/types';

export interface Chat {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

export interface CreateChatDto {
  title?: string;
}