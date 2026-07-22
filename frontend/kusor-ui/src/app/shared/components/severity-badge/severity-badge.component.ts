import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-severity-badge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <span [class]="getClasses()">
      {{ severity }}
    </span>
  `
})
export class SeverityBadgeComponent {
  @Input({ required: true }) severity: string = 'LOW';

  getClasses(): string {
    const s = (this.severity || 'LOW').toUpperCase();
    const base = 'px-3 py-1 rounded-full text-xs font-bold tracking-wider border ';
    switch (s) {
      case 'LOW':
      case 'APPROVE':
      case 'CONFORMING':
        return base + 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'MEDIUM':
      case 'REVIEW':
      case 'AMBIGUOUS':
        return base + 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'HIGH':
      case 'CRITICAL':
      case 'REJECT':
      case 'NON_CONFORMING':
      case 'PROHIBITION':
        return base + 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      default:
        return base + 'bg-slate-800 text-slate-300 border-slate-700';
    }
  }
}
