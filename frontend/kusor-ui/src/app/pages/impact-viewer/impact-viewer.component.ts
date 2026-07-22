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
    <div class="p-8 max-w-7xl mx-auto space-y-8">
      <div class="glass-card p-8 border-l-4 border-[#E85D04] relative overflow-hidden">
        <div class="absolute -right-20 -top-20 w-80 h-80 bg-[#E85D04]/10 rounded-full blur-3xl pointer-events-none"></div>
        <h1 class="text-3xl font-black brand-gradient-text">Module 5: Analyse de Propagation d'Impact Réglementaire</h1>
        <p class="text-sm text-slate-400 mt-1">Impact aval de la Circulaire BCT N° {{ circularId() }} sur les obligations, processus bancaires et contrats</p>
      </div>

      <div class="glass-card p-8 space-y-8">
        @if (loading()) {
          <div class="flex justify-center items-center h-48 text-slate-400 font-medium">Analyse de la chaîne de propagation...</div>
        } @else if (report()) {
          <div class="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <div class="p-5 rounded-2xl bg-[#090D28] border border-slate-800">
              <div class="text-[10px] text-slate-400 uppercase font-black tracking-wider">Éléments Impactés</div>
              <div class="text-3xl font-black text-[#E85D04] mt-1">{{ report().total_affected }}</div>
            </div>
            <div class="p-5 rounded-2xl bg-[#090D28] border border-slate-800">
              <div class="text-[10px] text-slate-400 uppercase font-black tracking-wider">Impact Critique</div>
              <div class="text-3xl font-black text-rose-400 mt-1">{{ report().critical_count }}</div>
            </div>
            <div class="p-5 rounded-2xl bg-[#090D28] border border-slate-800">
              <div class="text-[10px] text-slate-400 uppercase font-black tracking-wider">Impact Élevé</div>
              <div class="text-3xl font-black text-[#E85D04] mt-1">{{ report().high_count }}</div>
            </div>
            <div class="p-5 rounded-2xl bg-[#090D28] border border-slate-800">
              <div class="text-[10px] text-slate-400 uppercase font-black tracking-wider">Impact Moyen</div>
              <div class="text-3xl font-black text-indigo-400 mt-1">{{ report().medium_count }}</div>
            </div>
          </div>

          <div class="space-y-4">
            <h2 class="text-xs font-black text-slate-300 uppercase tracking-wider">Cartographie des Éléments Impactés</h2>
            @for (item of report().affected_items; track item.entity_id) {
              <div class="p-5 rounded-2xl bg-[#090D28] border border-slate-800 space-y-3 text-xs">
                <div class="flex justify-between items-center">
                  <span class="font-black text-[#E85D04] text-sm uppercase">[{{ item.entity_type }}] {{ item.entity_name }}</span>
                  <app-severity-badge [severity]="item.severity"></app-severity-badge>
                </div>
                <p class="text-slate-300 leading-relaxed">{{ item.impact_description }}</p>
                <div class="text-slate-500 font-medium">Chemin temporel: {{ item.relationship_path?.join(' ➔ ') }}</div>
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
