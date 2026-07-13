export interface SourceCitation {
  circular_number: string;
  title: string;
  page: number;
  excerpt: string;
}

export interface ChatMessage {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceCitation[];
  confidence?: number;
  created_at?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  sources: SourceCitation[];
  confidence_score: number;
  related_circulars: string[];
  graph_path_used: boolean;
  question_type: string;
}
