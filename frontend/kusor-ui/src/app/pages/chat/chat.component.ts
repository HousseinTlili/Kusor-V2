import { Component, OnInit, inject, signal, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { ApiService } from '../../core/services/api.service';
import { ChatSession, ChatMessage, SourceCitation } from '../../core/models/chat.model';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { ConfidenceBadgeComponent } from '../../shared/components/confidence-badge/confidence-badge.component';
import { marked } from 'marked';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingSpinnerComponent, ConfidenceBadgeComponent],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent implements OnInit, AfterViewChecked {
  private apiService = inject(ApiService);
  private sanitizer = inject(DomSanitizer);

  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  sessions = signal<ChatSession[]>([]);
  activeSessionId = signal<string | null>(null);
  messages = signal<ChatMessage[]>([]);
  
  // UI states
  isLoadingHistory = signal<boolean>(false);
  isSending = signal<boolean>(false);
  inputMessage = '';
  
  // Right side panel sources
  activeSources = signal<SourceCitation[]>([]);
  selectedMessageId = signal<string | undefined>(undefined);

  ngOnInit(): void {
    this.loadSessions();
  }

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  loadSessions(): void {
    this.apiService.getChatSessions().subscribe({
      next: (data) => {
        this.sessions.set(data);
        if (data.length > 0 && !this.activeSessionId()) {
          this.selectSession(data[0].id);
        }
      },
      error: (err) => console.error('Error fetching chat sessions', err)
    });
  }

  selectSession(id: string): void {
    this.activeSessionId.set(id);
    this.isLoadingHistory.set(true);
    this.messages.set([]);
    this.activeSources.set([]);
    this.selectedMessageId.set(undefined);

    this.apiService.getChatHistory(id).subscribe({
      next: (history) => {
        this.messages.set(history);
        this.isLoadingHistory.set(false);
        // Default to showing sources for the last assistant response
        this.showLastResponseSources();
      },
      error: (err) => {
        console.error('Error fetching chat history', err);
        this.isLoadingHistory.set(false);
      }
    });
  }

  createNewSession(): void {
    this.activeSessionId.set(null);
    this.messages.set([]);
    this.activeSources.set([]);
    this.selectedMessageId.set(undefined);
    this.inputMessage = '';
  }

  sendMessage(): void {
    if (!this.inputMessage.trim() || this.isSending()) return;

    const messageText = this.inputMessage;
    this.inputMessage = '';
    this.isSending.set(true);

    // Optimistically push user message
    const tempUserMsg: ChatMessage = {
      id: 'temp-user-' + Date.now(),
      role: 'user',
      content: messageText,
      sources: [],
      confidence: 0,
      created_at: new Date().toISOString()
    };
    this.messages.update(prev => [...prev, tempUserMsg]);

    this.apiService.sendMessage(messageText, this.activeSessionId() || undefined).subscribe({
      next: (res) => {
        this.isSending.set(false);
        
        // Push actual response
        const assistantMsg: ChatMessage = {
          id: 'assistant-' + Date.now(),
          role: 'assistant',
          content: res.answer,
          sources: res.sources || [],
          confidence: res.confidence_score,
          created_at: new Date().toISOString()
        };

        this.messages.update(prev => [...prev, assistantMsg]);
        this.activeSources.set(res.sources || []);
        this.selectedMessageId.set(assistantMsg.id);

        if (!this.activeSessionId() && res.session_id) {
          this.activeSessionId.set(res.session_id);
          this.loadSessions();
        }
      },
      error: (err) => {
        console.error('Error sending message', err);
        this.isSending.set(false);
        
        // Push error message
        const errorMsg: ChatMessage = {
          id: 'error-' + Date.now(),
          role: 'assistant',
          content: '⚠️ Une erreur est survenue lors de la communication avec l\'assistant. Veuillez réessayer.',
          sources: [],
          confidence: 0,
          created_at: new Date().toISOString()
        };
        this.messages.update(prev => [...prev, errorMsg]);
      }
    });
  }

  parseMarkdown(content: string): SafeHtml {
    try {
      const parsed = marked.parse(content) as string;
      return this.sanitizer.bypassSecurityTrustHtml(parsed);
    } catch {
      return content;
    }
  }

  showSources(msg: ChatMessage): void {
    if (msg.role === 'assistant' && msg.sources && msg.sources.length > 0) {
      this.activeSources.set(msg.sources);
      this.selectedMessageId.set(msg.id);
    }
  }

  private showLastResponseSources(): void {
    const list = this.messages();
    for (let i = list.length - 1; i >= 0; i--) {
      const msg = list[i];
      if (msg.role === 'assistant') {
        const sources = msg.sources;
        if (sources && sources.length > 0) {
          this.activeSources.set(sources);
          this.selectedMessageId.set(msg.id);
          break;
        }
      }
    }
  }

  private scrollToBottom(): void {
    try {
      this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
    } catch (err) {
      // Container not ready
    }
  }
}
