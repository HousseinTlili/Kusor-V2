import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Document, PaginatedResponse, UploadResponse, DocumentStatus } from '../models/document.model';
import { ChatMessage, ChatSession, ChatResponse } from '../models/chat.model';
import { AdminStats, SyncResult } from '../models/admin.model';
import { GraphData, ClusterData, ClusterSubgraphResponse } from '../models/graph.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  constructor(private http: HttpClient) {}

  // --- Documents ---
  getDocuments(page: number = 1, limit: number = 10): Observable<PaginatedResponse<Document>> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('limit', limit.toString());
    return this.http.get<PaginatedResponse<Document>>(`${environment.apiUrl}/documents/`, { params });
  }

  uploadDocument(
    file: File, 
    number?: string, 
    title?: string, 
    category?: string, 
    date?: string
  ): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (number) formData.append('number', number);
    if (title) formData.append('title', title);
    if (category) formData.append('category', category);
    if (date) formData.append('date', date);

    return this.http.post<UploadResponse>(`${environment.apiUrl}/documents/upload`, formData);
  }

  getDocumentStatus(id: string): Observable<DocumentStatus> {
    return this.http.get<DocumentStatus>(`${environment.apiUrl}/documents/${id}/status`);
  }

  deleteDocument(id: string): Observable<{ id: string; number: string; message: string }> {
    return this.http.delete<{ id: string; number: string; message: string }>(`${environment.apiUrl}/documents/${id}`);
  }

  reindexDocument(id: string): Observable<{ id: string; number: string; message: string }> {
    return this.http.post<{ id: string; number: string; message: string }>(`${environment.apiUrl}/documents/${id}/reindex`, {});
  }

  updateDocument(id: string, file: File): Observable<{ id: string; number: string; message: string; chunks_count: number }> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.put<{ id: string; number: string; message: string; chunks_count: number }>(
      `${environment.apiUrl}/documents/${id}/update`, formData
    );
  }


  // --- Search ---
  searchHybrid(query: string, top_k: number = 5): Observable<any[]> {
    return this.http.post<any[]>(`${environment.apiUrl}/search/hybrid`, { query, top_k });
  }

  searchVector(query: string, top_k: number = 5): Observable<any[]> {
    return this.http.post<any[]>(`${environment.apiUrl}/search/vector`, { query, top_k });
  }

  searchGraph(query: string, top_k: number = 5): Observable<any[]> {
    return this.http.post<any[]>(`${environment.apiUrl}/search/graph`, { query, top_k });
  }

  searchClassic(query: string, top_k: number = 5): Observable<any[]> {
    return this.http.post<any[]>(`${environment.apiUrl}/search/classic`, { query, top_k });
  }


  // --- Chat ---
  sendMessage(message: string, sessionId?: string): Observable<ChatResponse> {
    const body: any = { message };
    if (sessionId) {
      body.session_id = sessionId;
    }
    return this.http.post<ChatResponse>(`${environment.apiUrl}/chat/message`, body);
  }

  getChatHistory(sessionId: string): Observable<ChatMessage[]> {
    return this.http.get<ChatMessage[]>(`${environment.apiUrl}/chat/history/${sessionId}`);
  }

  getChatSessions(): Observable<ChatSession[]> {
    return this.http.get<ChatSession[]>(`${environment.apiUrl}/chat/sessions`);
  }

  // --- Admin ---
  getStats(): Observable<AdminStats> {
    return this.http.get<AdminStats>(`${environment.apiUrl}/admin/stats`);
  }

  triggerSync(): Observable<SyncResult> {
    return this.http.post<SyncResult>(`${environment.apiUrl}/admin/sync`, {});
  }

  // --- Graph ---
  getSubgraph(circularNumber?: string): Observable<GraphData> {
    let params = new HttpParams();
    if (circularNumber) {
      params = params.set('circular', circularNumber);
    }
    return this.http.get<GraphData>(`${environment.apiUrl}/graph/subgraph`, { params });
  }

  getGraphOverview(): Observable<ClusterData> {
    return this.http.get<ClusterData>(`${environment.apiUrl}/graph/overview`);
  }

  getClusterSubgraph(year: string): Observable<ClusterSubgraphResponse> {
    const params = new HttpParams().set('year', year);
    return this.http.get<ClusterSubgraphResponse>(`${environment.apiUrl}/graph/cluster`, { params });
  }
}
