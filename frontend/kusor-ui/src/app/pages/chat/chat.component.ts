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

interface PromptSample {
  label: string;
  text: string;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-6 md:p-8 h-[calc(100vh)] flex flex-col gap-5 max-w-6xl mx-auto">
      
      <!-- Top Header Bar -->
      <div class="glass-card p-4 md:p-5 flex items-center justify-between shadow-sm">
        <div class="flex items-center gap-3.5">
          <img src="assets/attijari_logo.png" alt="Attijari Logo" class="h-9 w-9 object-contain rounded-xl border border-[var(--border-card)] shadow-sm" />
          <div>
            <h1 class="text-lg font-black brand-gradient-text">Assistant RAG Réglementaire BCT</h1>
            <p class="text-xs text-[var(--text-muted)] font-medium">Recherche Hybride 4 Canaux (Vecteurs + BM25 + Graphe Neo4j + Obligations)</p>
          </div>
        </div>

        <div class="hidden sm:flex items-center gap-2">
          <span class="inline-flex items-center px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 text-xs font-semibold border border-emerald-200 dark:border-emerald-800">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-2"></span>
            Modèle kusor-qwen:v1 Actif
          </span>
        </div>
      </div>

      <!-- Quick Suggestion Prompts -->
      <div class="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider whitespace-nowrap mr-1">Questions Types :</span>
        @for (item of samplePrompts; track item.label) {
          <button (click)="usePrompt(item.text)"
            class="px-3 py-1.5 rounded-lg bg-[var(--bg-card)] hover:bg-[#E85D04]/10 hover:border-[#E85D04]/40 border border-[var(--border-card)] text-[var(--text-secondary)] hover:text-[#E85D04] font-medium transition-all whitespace-nowrap shadow-sm">
            {{ item.label }}
          </button>
        }
      </div>

      <!-- Messages Stream Area -->
      <div class="flex-1 glass-card p-6 overflow-y-auto space-y-6 shadow-sm">
        @for (msg of messages(); track msg.id) {
          <div [class]="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'">
            
            @if (msg.role === 'user') {
              <!-- User Message Bubble -->
              <div class="max-w-2xl bg-gradient-to-r from-[#E85D04] to-[#D95000] text-white rounded-2xl rounded-tr-none px-5 py-4 shadow-md text-sm leading-relaxed font-medium">
                {{ msg.content }}
              </div>
            } @else {
              <!-- Assistant Message Bubble -->
              <div class="max-w-3xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-[var(--text-primary)] rounded-2xl rounded-tl-none p-5 shadow-sm space-y-4">
                
                <div class="whitespace-pre-wrap leading-relaxed text-sm text-[var(--text-secondary)] font-normal">
                  {{ msg.content }}
                </div>

                @if (msg.confidence !== undefined) {
                  <div class="pt-3 border-t border-[var(--border-card)] flex flex-wrap items-center justify-between text-xs gap-3">
                    <div class="flex items-center gap-2.5">
                      <span class="text-[var(--text-muted)] font-medium">Indice de Confiance :</span>
                      <div class="w-24 bg-[var(--bg-card)] rounded-full h-2 overflow-hidden border border-[var(--border-card)]">
                        <div class="h-full bg-gradient-to-r from-[#E85D04] to-emerald-500 transition-all duration-500" [style.width.%]="(msg.confidence || 0) * 100"></div>
                      </div>
                      <span class="font-bold text-[#E85D04]">{{ ((msg.confidence || 0) * 100).toFixed(0) }}%</span>
                    </div>

                    @if (msg.sources && msg.sources.length) {
                      <span class="text-[11px] text-[var(--text-muted)] font-medium px-2.5 py-1 rounded-full bg-[var(--bg-card)] border border-[var(--border-card)]">
                        {{ msg.sources.length }} Source(s) BCT
                      </span>
                    }
                  </div>
                }
              </div>
            }

          </div>
        }
      </div>

      <!-- Input Box -->
      <div class="glass-card p-3.5 shadow-sm">
        <form (ngSubmit)="send()" class="flex gap-3">
          <input type="text" [(ngModel)]="promptText" name="prompt" [disabled]="streaming()" placeholder="Posez une question sur la réglementation de la Banque Centrale de Tunisie..."
            class="flex-1 px-4 py-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] placeholder-[var(--text-faint)] text-sm focus:outline-none focus:border-[#E85D04] focus:ring-2 focus:ring-[#E85D04]/20 transition-all" />
          <button type="submit" [disabled]="streaming() || !promptText.trim()"
            class="px-6 py-3 rounded-xl font-bold brand-btn-primary disabled:opacity-50 transition-all text-xs flex items-center gap-2">
            @if (streaming()) {
              <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Génération...</span>
            } @else {
              <span>Envoyer</span>
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/>
              </svg>
            }
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

  samplePrompts: PromptSample[] = [
    {
      label: "💳 Ratio d'endettement max",
      text: "Quelles sont les conditions d'octroi de crédit aux particuliers selon la réglementation BCT et quel est le ratio d'endettement maximal autorisé ?"
    },
    {
      label: "🔍 Obligations PPE & GAFI",
      text: "Quelles sont les obligations de vigilance renforcée envers les Personnes Politiquement Exposées (PPE) selon les circulaires BCT ?"
    },
    {
      label: "🏛️ Ratio de Solvabilité (CAR)",
      text: "Quel est le ratio de solvabilité minimum (CAR) exigé par la Banque Centrale de Tunisie pour les banques commerciales ?"
    },
    {
      label: "⚠️ Impact Réserves BCT",
      text: "Si la BCT modifie le taux des réserves obligatoires, quels départements de la banque sont directement impactés ?"
    }
  ];

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

  usePrompt(prompt: string) {
    this.promptText = prompt;
    this.send();
  }

  async send() {
    const text = this.promptText.trim();
    if (!text || this.streaming()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text
    };

    this.messages.update(msgs => [...msgs, userMsg]);
    this.promptText = '';
    this.streaming.set(true);

    this.api.sendChatMessage(text, this.activeSessionId).subscribe({
      next: (res: any) => {
        this.activeSessionId = res.session_id;
        const assistantMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: res.message || res.response_text || 'Aucune réponse générée.',
          confidence: res.confidence_score,
          sources: res.sources || res.citations
        };
        this.messages.update(msgs => [...msgs, assistantMsg]);
        this.streaming.set(false);
      },
      error: (err: any) => {
        this.streaming.set(false);
        const errorMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Erreur lors du traitement: ${err?.error?.error || 'Service indisponible.'}`,
          confidence: 0.0
        };
        this.messages.update(msgs => [...msgs, errorMsg]);
      }
    });
  }
}
