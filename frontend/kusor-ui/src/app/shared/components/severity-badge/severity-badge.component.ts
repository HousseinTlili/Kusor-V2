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
    const base = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-bold tracking-wider border ';
    switch (s) {
      case 'LOW':
      case 'APPROVE':
      case 'CONFORMING':
      case 'CONFORME':
        return base + 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800';
      case 'MEDIUM':
      case 'REVIEW':
      case 'AMBIGUOUS':
      case 'VIGILANCE':
        return base + 'bg-amber-50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800';
      case 'HIGH':
      case 'CRITICAL':
      case 'REJECT':
      case 'NON_CONFORMING':
      case 'NON-CONFORME':
      case 'PROHIBITION':
        return base + 'bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800';
      default:
        return base + 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700';
    }
  }
}
