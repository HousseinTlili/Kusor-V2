---
name: angular-banking-ui
description: Specialized Angular 17 & Tailwind CSS design system skill for Attijari Bank Tunisia (KUSOR v3). Enforces modern dark-mode/glassmorphic aesthetics, responsive dashboards, SSE streaming chat components, SVG icons, confidence gauges, and accessibility.
---

# Angular 17 Banking UI & Compliance Design System

This skill guides the construction of modern, state-of-the-art Angular 17 UI components for the KUSOR v3 AI Compliance & Regulatory Intelligence platform at Attijari Bank Tunisia.

---

## 1. Design System & Aesthetics Guidelines

### 1.1 Color Palette & Theme Tokens
- **Background Base**: Slate Deep Dark (`#0B132B`, `#0F172A`, `#1E293B`).
- **Brand Primary**: Attijari Navy (`#0A192F`, `#1E3A8A`) & Corporate Gold/Amber (`#D97706`, `#F59E0B`, `#FBBF24`).
- **Glassmorphism**: Translucent panels with blur (`bg-slate-900/80 backdrop-blur-md border border-amber-500/20 shadow-xl shadow-black/40`).
- **Status Indicators**:
  - **LOW Risk / APPROVE / CONFORMING**: Emerald (`#10B981`, `bg-emerald-500/10 text-emerald-400 border-emerald-500/30`)
  - **MEDIUM Risk / REVIEW / AMBIGUOUS**: Amber (`#F59E0B`, `bg-amber-500/10 text-amber-400 border-amber-500/30`)
  - **HIGH Risk / CRITICAL / REJECT / PROHIBITION**: Crimson (`#EF4444`, `bg-rose-500/10 text-rose-400 border-rose-500/30`)
  - **Temporal Graph / Obligations**: Indigo/Violet (`#818CF8`, `bg-indigo-500/10 text-indigo-400 border-indigo-500/30`)

### 1.2 Typography & Icons
- **Font Family**: Google Font `Inter` or `Outfit` for sleek readability.
- **Icons**: Inline SVG icons (Lucide icon style, 20x20 or 24x24 px, stroke-width=2).

---

## 2. Angular 17 Component Patterns

### 2.1 Control Flow & Signals Syntax
Always use modern Angular 17 standalone syntax:
- Standalone components (`@Component({ standalone: true, imports: [...] })`).
- Control flow directives: `@if (condition) { ... } @else { ... }`, `@for (item of items; track item.id) { ... }`.
- Reactive state with Angular Signals: `readonly count = signal(0);`, `readonly doubled = computed(() => this.count() * 2);`.

### 2.2 Component Blueprint Example: RAG Chat Assistant
```typescript
import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-chat-assistant',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="flex flex-col h-full bg-slate-950 text-slate-100 rounded-2xl border border-slate-800 shadow-2xl overflow-hidden backdrop-blur-md">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-800/80 bg-slate-900/60">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
          </div>
          <div>
            <h2 class="text-lg font-semibold tracking-wide text-amber-400">Assistant Réglementaire KUSOR</h2>
            <p class="text-xs text-slate-400">Intelligence Artificielle BCT & Conformité Attijari Bank</p>
          </div>
        </div>
      </div>

      <!-- Messages Area -->
      <div class="flex-1 overflow-y-auto p-6 space-y-4">
        @for (msg of messages(); track msg.id) {
          <div [class]="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'">
            <div [class]="msg.role === 'user' 
              ? 'max-w-2xl bg-amber-600 text-white rounded-2xl rounded-tr-none p-4 shadow-lg' 
              : 'max-w-3xl bg-slate-900/90 border border-slate-800 text-slate-200 rounded-2xl rounded-tl-none p-5 shadow-xl backdrop-blur-sm'">
              
              <div class="prose prose-invert max-w-none text-sm leading-relaxed whitespace-pre-wrap">
                {{ msg.content }}
              </div>

              @if (msg.role === 'assistant' && msg.confidence) {
                <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                  <div class="flex items-center gap-2">
                    <span class="text-slate-400">Indice de Confiance:</span>
                    <span class="font-bold text-amber-400">{{ (msg.confidence * 100).toFixed(0) }}%</span>
                  </div>
                </div>
              }
            </div>
          </div>
        }
      </div>
    </div>
  `
})
export class ChatAssistantComponent {
  messages = signal<Array<{id: string; role: string; content: string; confidence?: number}>>([]);
}
```

---

## 3. UI Component Catalog Blueprint

1. **Confidence Gauge Bar**: Color-coded progress bar (Green > 75%, Amber 50-75%, Red < 50%).
2. **Regulatory Risk Badges**: Rounded pills with glow borders for `PROHIBITION`, `REQUIREMENT`, `THRESHOLD`, `DEADLINE`.
3. **Temporal Graph Filter Panel**: Date selector (`as_of_date`) with timeline slider.
4. **Compliance Dossier Cards**: Split view with document checklist, risk meter, and action recommendations.
