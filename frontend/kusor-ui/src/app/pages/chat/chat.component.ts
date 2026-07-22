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
    <div class="p-8 h-[calc(100vh)] flex flex-col gap-6 max-w-7xl mx-auto bg-[#03071E]">
      <!-- Top Header Bar -->
      <div class="glass-card p-5 flex items-center justify-between bg-[#070A18]">
        <div class="flex items-center gap-3.5">
          <img src="assets/attijari_logo.png" alt="Attijari Logo" class="h-9 w-9 object-cover rounded-xl border border-[#E85D04]/30 shadow-md" />
          <div>
            <h1 class="text-xl font-black brand-gradient-text">Assistant RAG Hybride 4 Canaux</h1>
            <p class="text-xs text-slate-400 font-medium">Vector + BM25 + Graph + Obligation Cypher Search</p>
          </div>
        </div>
      </div>

      <!-- Messages Stream Area -->
      <div class="flex-1 glass-card p-6 overflow-y-auto space-y-6 bg-[#070A18]">
        @for (msg of messages(); track msg.id) {
          <div [class]="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'">
            <div [class]="msg.role === 'user' 
              ? 'max-w-2xl bg-gradient-to-r from-[#E85D04] to-[#DC2F02] text-white rounded-3xl rounded-tr-none p-5 shadow-xl shadow-[#E85D04]/20' 
              : 'max-w-3xl bg-[#03071E] border border-slate-800 text-slate-200 rounded-3xl rounded-tl-none p-6 shadow-2xl space-y-4'">
              
              <div class="whitespace-pre-wrap leading-relaxed text-sm">
                {{ msg.content }}
              </div>

              @if (msg.role === 'assistant' && msg.confidence !== undefined) {
                <div class="pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-xs gap-3">
                  <div class="flex items-center gap-3">
                    <span class="text-slate-400 font-medium">Indice de Confiance:</span>
                    <div class="w-28 bg-[#070A18] rounded-full h-2 overflow-hidden border border-slate-800">
                      <div class="h-full bg-gradient-to-r from-[#E85D04] to-emerald-400 transition-all duration-500" [style.width.%]="(msg.confidence || 0) * 100"></div>
                    </div>
                    <span class="font-black text-[#E85D04]">{{ ((msg.confidence || 0) * 100).toFixed(0) }}%</span>
                  </div>

                  @if (msg.sources && msg.sources.length) {
                    <span class="text-xs text-slate-400 font-medium px-2.5 py-1 rounded-full bg-[#070A18] border border-slate-800">
                      {{ msg.sources.length }} Source(s) Récupérée(s)
                    </span>
                  }
                </div>
              }
            </div>
          </div>
        }
      </div>

      <!-- Input Box -->
      <div class="glass-card p-4 bg-[#070A18]">
        <form (ngSubmit)="send()" class="flex gap-3">
          <input type="text" [(ngModel)]="promptText" name="prompt" [disabled]="streaming()" placeholder="Posez une question sur la réglementation BCT..."
            class="flex-1 px-5 py-4 rounded-2xl bg-[#03071E] border border-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-[#E85D04] transition-all" />
          <button type="submit" [disabled]="streaming() || !promptText.trim()"
            class="px-7 py-4 rounded-2xl font-bold text-white bg-gradient-to-r from-[#FAA307] via-[#E85D04] to-[#DC2F02] hover:from-[#E85D04] hover:to-[#9D0208] disabled:opacity-50 shadow-xl shadow-[#E85D04]/30 transition-all text-sm">
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
