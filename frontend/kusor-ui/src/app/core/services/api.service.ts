import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // Documents
  getDocuments(): Observable<any> { return this.http.get(`${this.baseUrl}/documents/`); }
  deleteDocument(id: string): Observable<any> { return this.http.delete(`${this.baseUrl}/documents/${id}`); }
  uploadDocument(formData: FormData): Observable<any> { return this.http.post(`${this.baseUrl}/documents/`, formData); }

  // Admin & Stats
  getStats(): Observable<any> { return this.http.get(`${this.baseUrl}/admin/stats`); }
  getDigest(): Observable<any> { return this.http.get(`${this.baseUrl}/admin/digest`); }
  triggerSync(): Observable<any> { return this.http.post(`${this.baseUrl}/admin/sync`, {}); }

  // Chat History
  getSessions(): Observable<any> { return this.http.get(`${this.baseUrl}/chat/sessions`); }
  getChatHistory(id: string): Observable<any> { return this.http.get(`${this.baseUrl}/chat/sessions/${id}/history`); }
  sendChatMessage(message: string, sessionId?: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/chat/message`, { message, session_id: sessionId });
  }

  // Graph
  getGraphOverview(): Observable<any> { return this.http.get(`${this.baseUrl}/graph/overview`); }
  getGraphSubgraph(label: string = 'Circular', limit: number = 50): Observable<any> {
    const params = new HttpParams().set('label', label).set('limit', limit.toString());
    return this.http.get(`${this.baseUrl}/graph/subgraph`, { params });
  }
  getTemporalGraph(asOfDate?: string): Observable<any> {
    let params = new HttpParams();
    if (asOfDate) params = params.set('as_of_date', asOfDate);
    return this.http.get(`${this.baseUrl}/graph/temporal`, { params });
  }

  // Modules
  runKycCheck(payload: any): Observable<any> { return this.http.post(`${this.baseUrl}/kyc/check`, payload); }
  analyzeContract(payload: any): Observable<any> { return this.http.post(`${this.baseUrl}/contract/analyze`, payload); }
  prescreenCredit(payload: any): Observable<any> { return this.http.post(`${this.baseUrl}/credit/prescreen`, payload); }
  getImpactReport(circularId: string): Observable<any> { return this.http.get(`${this.baseUrl}/impact/${circularId}`); }

  // SSE Stream
  async streamChatMessage(
    message: string,
    sessionId?: string,
    onToken?: (token: string) => void,
    onSources?: (sources: any[]) => void,
    onDone?: (data: any) => void
  ): Promise<void> {
    const token = localStorage.getItem('kusor_token');
    const response = await fetch(`${this.baseUrl}/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ message, session_id: sessionId, stream: true }),
    });

    if (!response.body) return;
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const payload = JSON.parse(line.slice(6));
            if (payload.event === 'token' && onToken) onToken(payload.data);
            if (payload.event === 'sources' && onSources) onSources(payload.data);
            if (payload.event === 'done' && onDone) onDone(payload.data);
          } catch (e) {
            console.error('SSE parse error', e);
          }
        }
      }
    }
  }
}
