import { Component, input, computed } from '@angular/core';

@Component({
  selector: 'app-confidence-badge',
  standalone: true,
  templateUrl: './confidence-badge.component.html',
  styleUrl: './confidence-badge.component.scss'
})
export class ConfidenceBadgeComponent {
  score = input<number>(0);

  label = computed(() => {
    const val = this.score() * 100;
    return `${val.toFixed(0)}%`;
  });

  statusClass = computed(() => {
    const s = this.score();
    if (s >= 0.8) return 'status-high';
    if (s >= 0.5) return 'status-medium';
    return 'status-low';
  });

  statusText = computed(() => {
    const s = this.score();
    if (s >= 0.8) return 'Fiabilité élevée';
    if (s >= 0.5) return 'Fiabilité moyenne';
    return 'Fiabilité faible';
  });
}
