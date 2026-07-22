import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { SeverityBadgeComponent } from '../../shared/components/severity-badge/severity-badge.component';

@Component({
  selector: 'app-impact-viewer',
  standalone: true,
  imports: [CommonModule, SeverityBadgeComponent],
  template: `
    <div class="max-w-7xl mx-auto p-6 space-y-6">
      <div class="glass-card p-6 border-l-4 border-amber-500">
        <h1 class="text-2xl font-bold gold-gradient-text">Module 5: Analyse de Propagation d'Impact Réglementaire</h1>
        <p class="text-sm text-slate-400 mt-1">Impact aval de la Circulaire BCT N° {{ circularId() }} sur les obligations, processus bancaires et contrats</p>
      </div>

      <div class="glass-card p-6 space-y-6">
        @if (loading()) {
          <div class="flex justify-center items-center h-48 text-slate-400">Analyse de la chaîne de propagation...</div>
        } @else if (report()) {
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <div class="text-xs text-slate-400 uppercase">Éléments Impactés</div>
              <div class="text-2xl font-extrabold text-amber-400 mt-1">{{ report().total_affected }}</div>
            </div>
            <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <div class="text-xs text-slate-400 uppercase">Impact critique</div>
              <div class="text-2xl font-extrabold text-rose-400 mt-1">{{ report().critical_count }}</div>
            </div>
            <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <div class="text-xs text-slate-400 uppercase">Impact Élevé</div>
              <div class="text-2xl font-extrabold text-amber-500 mt-1">{{ report().high_count }}</div>
            </div>
            <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <div class="text-xs text-slate-400 uppercase">Impact Moyen</div>
              <div class="text-2xl font-extrabold text-indigo-400 mt-1">{{ report().medium_count }}</div>
            </div>
          </div>

          <div class="space-y-4">
            <h2 class="text-lg font-bold text-slate-200">Cartographie des Éléments Impactés</h2>
            @for (item of report().affected_items; track item.entity_id) {
              <div class="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2 text-xs">
                <div class="flex justify-between items-center">
                  <span class="font-bold text-amber-400 uppercase">[{{ item.entity_type }}] {{ item.entity_name }}</span>
                  <app-severity-badge [severity]="item.severity"></app-severity-badge>
                </div>
                <p class="text-slate-300">{{ item.impact_description }}</p>
                <div class="text-slate-500">Chemin temporel: {{ item.relationship_path?.join(' ➔ ') }}</div>
              </div>
            }
          </div>
        }
      </div>
    </div>
  `
})
export class ImpactViewerComponent implements OnInit {
  route = inject(ActivatedRoute);
  api = inject(ApiService);

  circularId = signal('2024-88');
  report = signal<any>(null);
  loading = signal(false);

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('circularId') || '2024-88';
    this.circularId.set(id);
    this.loadImpact(id);
  }

  loadImpact(id: string) {
    this.loading.set(true);
    this.api.getImpactReport(id).subscribe({
      next: (res) => {
        this.report.set(res);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }
}
