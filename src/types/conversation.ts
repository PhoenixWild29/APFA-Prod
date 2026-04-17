export interface Source {
  document_id: string;
  title: string;
  section?: string;
  excerpt: string;
  relevance_score: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  follow_ups?: string[];
  created_at: string;
  feedback?: 'up' | 'down' | null;
  is_partial?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  preview?: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}
