import apiClient from '@/api/apiClient';
import type { Conversation, ConversationDetail } from '@/types/conversation';

export interface ConversationListResponse {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  preview: string | null;
}

export async function fetchConversations(
  limit = 50,
  offset = 0
): Promise<ConversationListResponse[]> {
  const { data } = await apiClient.get<ConversationListResponse[]>(
    '/conversations',
    { params: { limit, offset } }
  );
  return data;
}

export async function createConversation(
  title?: string
): Promise<ConversationListResponse> {
  const { data } = await apiClient.post<ConversationListResponse>(
    '/conversations',
    { title: title ?? null }
  );
  return data;
}

export async function fetchConversation(
  id: string,
  limit = 50,
  offset = 0
): Promise<ConversationDetail> {
  const { data } = await apiClient.get<ConversationDetail>(
    `/conversations/${id}`,
    { params: { limit, offset } }
  );
  return data;
}

export async function updateConversationTitle(
  id: string,
  title: string
): Promise<ConversationListResponse> {
  const { data } = await apiClient.patch<ConversationListResponse>(
    `/conversations/${id}`,
    { title }
  );
  return data;
}

export async function deleteConversation(id: string): Promise<void> {
  await apiClient.delete(`/conversations/${id}`);
}

export async function setMessageFeedback(
  conversationId: string,
  messageId: string,
  feedback: 'up' | 'down' | null
): Promise<{ id: string; feedback: string | null }> {
  const { data } = await apiClient.put(
    `/conversations/${conversationId}/messages/${messageId}/feedback`,
    { feedback }
  );
  return data;
}
