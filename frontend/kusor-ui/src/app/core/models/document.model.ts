export interface Document {
  id: string;
  number: string;
  title: string;
  date: string;
  category: string;
  url?: string;
  status: string; // ACTIVE, MODIFIED, ABROGATED
  indexation_state: string; // PENDING, PROCESSING, INDEXED, FAILED
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  pages: number;
  limit: number;
  items: T[];
}

export interface UploadResponse {
  id: string;
  number: string;
  title: string;
  indexation_state: string;
  chunks_count: number;
  message: string;
}

export interface DocumentStatus {
  id: string;
  number: string;
  indexation_state: string;
}
