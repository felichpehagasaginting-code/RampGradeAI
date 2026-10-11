import React from 'react';
import { Layers, CheckCircle2, AlertCircle, Ban, Clock, AlertTriangle, Scissors, Zap } from 'lucide-react';

export default function TBSCountsSummary({ assessment, latencyMs = null }) {
  if (!assessment) return null;

  const total = assessment.total_bunches || 0;

  const categories = [
    {
      id: 'ripe',
      label: 'Matang (Ripe)',
      sublabel: 'Fraksi 2 & 3 • Rendemen Prima',
      count: assessment.ripe_count || 0,
      pct: assessment.ripe_percentage || 0,
      icon: CheckCircle2,
      badgeColor: 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400',
      textColor: 'text-emerald-400',
      barColor: 'bg-emerald-500'
    },
    {
      id: 'underripe',
      label: 'Kurang Matang',
      sublabel: 'Fraksi 1 • Potongan Ringan',
      count: assessment.underripe_count || 0,
      pct: assessment.underripe_percentage || 0,
      icon: Clock,
      badgeColor: 'bg-amber-500/15 border-amber-500/40 text-amber-400',
      textColor: 'text-amber-400',
      barColor: 'bg-amber-500'
    },
    {
      id: 'unripe',
      label: 'Mentah (Unripe)',
      sublabel: 'Fraksi 0 • Penalti Bobot',
      count: assessment.unripe_count || 0,
      pct: assessment.unripe_percentage || 0,
      icon: Ban,
      badgeColor: 'bg-slate-500/15 border-slate-500/40 text-slate-300',
      textColor: 'text-slate-300',
      barColor: 'bg-slate-500'
    },
    {
      id: 'overripe',
      label: 'Lewat Matang',
      sublabel: 'Fraksi 4 & 5 • Risiko ALB/FFA',
      count: assessment.overripe_count || 0,
      pct: assessment.overripe_percentage || 0,
      icon: AlertTriangle,
      badgeColor: 'bg-rose-500/15 border-rose-500/40 text-rose-400',
      textColor: 'text-rose-400',
      barColor: 'bg-rose-500'
    },
    {
      id: 'empty_bunch',
      label: 'Janjang Kosong',
      sublabel: 'Tangkai Kosong Brondolan',
      count: assessment.empty_bunch_count || 0,
      pct: assessment.empty_bunch_percentage || 0,
      icon: AlertCircle,
      badgeColor: 'bg-purple-500/15 border-purple-500/40 text-purple-400',
      textColor: 'text-purple-400',
      barColor: 'bg-purple-500'
    },
    {
      id: 'abnormal',
      label: 'Buah Abnormal',
      sublabel: 'Buah Pasir / Partenokarpi',
      count: assessment.abnormal_count || 0,
      pct: assessment.abnormal_percentage || 0,
      icon: AlertCircle,
      badgeColor: 'bg-pink-500/15 border-pink-500/40 text-pink-400',
      textColor: 'text-pink-400',
      barColor: 'bg-pink-500'
    },
    {
      id: 'long_stalk',
      label: 'Gagang Panjang',
      sublabel: '> 2.5 cm • Potongan Berat',
      count: assessment.long_stalk_count || 0,
      pct: assessment.long_stalk_percentage || 0,
      icon: Scissors,
      badgeColor: 'bg-cyan-500/15 border-cyan-500/40 text-cyan-400',
      textColor: 'text-cyan-400',
      barColor: 'bg-cyan-500'
    }
  ];

  return (
    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 shadow-xl space-y-5">
      {/* Header: Total Tandan & Latensi */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-lg shadow-emerald-950/50">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white tracking-tight">
                Rekapitulasi Deteksi TBS
              </h3>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono">
                {total} Tandan Terdeteksi
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Klasifikasi fraksi kematangan berbasis IOPRI 1997 & Computer Vision
            </p>
          </div>
        </div>

        {latencyMs && (
          <div className="flex items-center gap-2 bg-slate-950 px-3.5 py-2 rounded-xl border border-slate-800 text-xs text-slate-300 font-mono">
            <Zap className="w-4 h-4 text-amber-400 shrink-0" />
            <span>Latensi Inferensi: <strong>{latencyMs} ms</strong></span>
          </div>
        )}
      </div>

      {/* Visual Stacked Progress Bar */}
      {total > 0 && (
        <div className="space-y-1.5">
          <div className="flex justify-between text-[11px] font-semibold text-slate-400">
            <span>Komposisi Fraksi Panen</span>
            <span>100% Total Mutu</span>
          </div>
          <div className="h-3 w-full rounded-full bg-slate-950 overflow-hidden flex border border-slate-800">
            {categories.slice(0, 6).map((c) => {
              if (!c.count) return null;
              const widthPct = (c.count / total) * 100;
              return (
                <div
                  key={c.id}
                  style={{ width: `${widthPct}%` }}
                  className={`${c.barColor} transition-all duration-500`}
                  title={`${c.label}: ${c.count} tandan (${c.pct}%)`}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Bento Grid 7 Kartu Kategori */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-3">
        {categories.map((c) => {
          const Icon = c.icon;
          return (
            <div
              key={c.id}
              className={`p-3.5 rounded-xl border transition-all ${c.badgeColor} flex flex-col justify-between`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold truncate max-w-[100px]">{c.label}</span>
                  <Icon className="w-4 h-4 shrink-0 opacity-80" />
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-2xl font-black font-mono leading-none">{c.count}</span>
                  <span className="text-xs font-semibold opacity-70">tandan</span>
                </div>
              </div>
              <div className="mt-2.5 pt-2 border-t border-slate-700/40 flex items-center justify-between text-[10px] font-mono opacity-80">
                <span>{c.pct}%</span>
                <span className="truncate text-[9px] opacity-70">{c.sublabel.split('•')[0]}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
