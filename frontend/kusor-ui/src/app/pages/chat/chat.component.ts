import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  confidence?: number;
  sources?: any[];
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="max-w-7xl mx-auto p-6 h-[calc(100vh-80px)] flex flex-col gap-4">
      <!-- Top header bar -->
      <div class="glass-card p-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
            </svg>
          </div>
          <div>
            <h1 class="text-lg font-bold text-amber-400">Assistant RAG Hybride 4 Canaux</h1>
            <p class="text-xs text-slate-400">Vector + BM25 + Graph + Obligation Cypher</p>
          </div>
        </div>
      </div>

      <!-- Messages container -->
      <div class="flex-1 glass-card p-6 overflow-y-auto space-y-6">
        @for (msg of messages(); track msg.id) {
          <div [class]="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'">
            <div [class]="msg.role === 'user' 
              ? 'max-w-2xl bg-gradient-to-r from-amber-600 to-amber-700 text-white rounded-2xl rounded-tr-none p-4 shadow-lg' 
              : 'max-w-3xl bg-slate-900/90 border border-slate-800 text-slate-200 rounded-2xl rounded-tl-none p-5 shadow-xl backdrop-blur-sm space-y-4'">
              
              <div class="whitespace-pre-wrap leading-relaxed text-sm">
                {{ msg.content }}
              </div>

              @if (msg.role === 'assistant') {
                <div class="pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between text-xs gap-2">
                  <div class="flex items-center gap-2">
                    <span class="text-slate-400">Score de Confiance:</span>
                    <div class="w-24 bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700">
                      <div class="h-full bg-gradient-to-r from-amber-500 to-emerald-400" [style.width.%]="(msg.confidence || 0) * 100"></div>
                    </div>
                    <span class="font-bold text-amber-400">{{ ((msg.confidence || 0) * 100).toFixed(0) }}%</span>
                  </div>

                  @if (msg.sources && msg.sources.length) {
                    <span class="text-slate-400">{{ msg.sources.length }} Source(s) Récupérée(s)</span>
                  }
                </div>
              }
            </div>
          </div>
        }
      </div>

      <!-- Input box -->
      <div class="glass-card p-4">
        <form (ngSubmit)="send()" class="flex gap-3">
          <input type="text" [(ngModel)]="promptText" name="prompt" [disabled]="streaming()" placeholder="Posez une question sur la réglementation BCT..."
            class="flex-1 px-4 py-3.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-all" />
          <button type="submit" [disabled]="streaming() || !promptText.trim()"
            class="px-6 py-3.5 rounded-xl font-bold text-slate-950 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 disabled:opacity-50 shadow-lg shadow-amber-500/20 transition-all">
            {{ streaming() ? 'Génération...' : 'Envoyer' }}
          </button>
        </form>
      </div>
    </div>
  `
})
export class ChatComponent implements OnInit {
  api = inject(ApiService);
  messages = signal<Message[]>([]);
  promptText = '';
  streaming = signal(false);
  activeSessionId?: string;

  ngOnInit() {
    this.messages.set([
      {
        id: '1',
        role: 'assistant',
        content: 'Bonjour ! Je suis KUSOR v3, votre assistant en réglementation bancaire BCT. Comment puis-je vous aider aujourd\'hui ?',
        confidence: 0.99,
      }
    ]);
  }

  async send() {
    const text = this.promptText.trim();
    if (!text || this.streaming()) return;

    this.promptText = '';
    const userMsgId = Date.now().toString();
    const assistantMsgId = (Date.now() + 1).toString();

    this.messages.update(msgs => [
      ...msgs,
      { id: userMsgId, role: 'user', content: text },
      { id: assistantMsgId, role: 'assistant', content: '', confidence: 0, sources: [] }
    ]);

    this.streaming.set(true);

    try {
      await this.api.streamChatMessage(
        text,
        this.activeSessionId,
        (token) => {
          this.messages.update(msgs =>
            msgs.map(m => m.id === assistantMsgId ? { ...m, content: m.content + token } : m)
          );
        },
        (sources) => {
          this.messages.update(msgs =>
            msgs.map(m => m.id === assistantMsgId ? { ...m, sources } : m)
          );
        },
        (doneData) => {
          this.activeSessionId = doneData.session_id;
          this.messages.update(msgs =>
            msgs.map(m => m.id === assistantMsgId ? { ...m, confidence: doneData.confidence_score } : m)
          );
          this.streaming.set(false);
        }
      );
    } catch (err) {
      console.error('Streaming error', err);
      this.streaming.set(false);
    }
  }
}
