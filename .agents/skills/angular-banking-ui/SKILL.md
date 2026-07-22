---
name: angular-banking-ui
description: Specialized Angular 17 & Tailwind CSS design system skill for Attijari Bank Tunisia (KUSOR v3). Enforces modern ultra-dark/black aesthetics (#03071E), vibrant sunset orange accents (#E85D04), vertical sidebar navigation, responsive dashboards, SSE streaming chat components, SVG icons, confidence gauges, and accessibility.
---

# Angular 17 Modern Banking UI & Compliance Design System

This skill specifies the modern, ultra-dark UI design system for the KUSOR v3 AI Compliance platform at Attijari Bank Tunisia.

---

## 1. Design System & Color Tokens

### 1.1 Color Palette
- **Ultra Dark Background**: Deep Night Black (`#03071E`).
- **Surface Cards**: Translucent Charcoal Navy (`#090D28`, `#0F1738`) with blur (`backdrop-blur-xl border border-[#E85D04]/20 shadow-2xl shadow-black/80`).
- **Brand Primary Accent**: Vibrant Sunset Fire (`#E85D04`, `#F48C06`, `#DC2F02`).
- **Status Indicators**:
  - **LOW Risk / APPROVE / CONFORMING**: Emerald (`#10B981`, `bg-emerald-500/10 text-emerald-400 border-emerald-500/30`)
  - **MEDIUM Risk / REVIEW / AMBIGUOUS**: Sunset Fire (`#E85D04`, `bg-[#E85D04]/10 text-[#E85D04] border-[#E85D04]/30`)
  - **HIGH Risk / CRITICAL / REJECT / PROHIBITION**: Crimson (`#DC2F02`, `bg-rose-500/10 text-rose-400 border-rose-500/30`)
  - **Temporal Graph / Obligations**: Violet (`#818CF8`, `bg-indigo-500/10 text-indigo-400 border-indigo-500/30`)

### 1.2 Sidebar Layout Architecture
- Fixed vertical left sidebar (`w-64 bg-[#03071E] border-r border-[#E85D04]/20`).
- Top branding header with logo & glowing `#E85D04` icon.
- Categorized navigation links (General, Compliance Modules, Admin) with active route highlight (`bg-[#E85D04]/15 border-l-4 border-[#E85D04] text-[#E85D04]`).
- Bottom user profile drawer with role badge & quick logout button.
