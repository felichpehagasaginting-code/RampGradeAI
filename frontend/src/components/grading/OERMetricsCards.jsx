import React from 'react';
import { Activity, Scale, Award, AlertTriangle, TrendingUp, DollarSign } from 'lucide-react';

export default function OERMetricsCards({ assessment }) {
  if (!assessment) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {/* 1. OER Card */}
      <div className="bg-slate-900/90 p-4 rounded-2xl border border-slate-800 shadow-lg">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold">Estimasi OER</span>
          <Activity className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="flex items-baseline space-x-1">
          <span className="text-2xl font-black text-white font-mono">{assessment.estimated_oer_percentage}%</span>
          <span className="text-xs text-slate-400 font-mono">/ 21.5%</span>
        </div>
        <p className="text-[11px] text-emerald-400 mt-1">
          Deviasi: {assessment.oer_variance >= 0 ? `+${assessment.oer_variance}%` : `${assessment.oer_variance}%`}
        </p>
      </div>

      {/* 2. Indeks Mutu */}
      <div className="bg-slate-900/90 p-4 rounded-2xl border border-slate-800 shadow-lg">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold">Indeks Mutu</span>
          <Award className="w-4 h-4 text-teal-400" />
        </div>
        <div className="flex items-baseline space-x-1">
          <span className="text-2xl font-black text-teal-300 font-mono">
            {(assessment.quality_score * 100).toFixed(0)}%
          </span>
          <span className="text-xs text-slate-400">Skor Mutu</span>
        </div>
        <p className="text-[11px] text-slate-400 mt-1">Standar IOPRI 1997</p>
      </div>

      {/* 3. Risiko ALB */}
      <div className="bg-slate-900/90 p-4 rounded-2xl border border-slate-800 shadow-lg">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold">Risiko FFA/ALB</span>
          <AlertTriangle className={`w-4 h-4 ${assessment.ffa_risk_category === 'HIGH' ? 'text-rose-400' : 'text-emerald-400'}`} />
        </div>
        <span className={`text-xl font-bold font-mono ${assessment.ffa_risk_category === 'HIGH' ? 'text-rose-400' : 'text-emerald-400'}`}>
          {assessment.ffa_risk_category}
        </span>
        <p className="text-[11px] text-slate-400 mt-1">Kinetika Lipolisis Pascapanen</p>
      </div>

      {/* 4. Harga Bersih Akhir */}
      <div className="bg-slate-900/90 p-4 rounded-2xl border border-slate-800 shadow-lg">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold">Harga Bersih Akhir</span>
          <DollarSign className="w-4 h-4 text-amber-400" />
        </div>
        <div className="text-xl font-black text-amber-300 font-mono">
          Rp {assessment.final_price_per_kg?.toLocaleString()} <span className="text-xs text-slate-400 font-normal">/kg</span>
        </div>
        <p className="text-[11px] text-rose-400 mt-1">
          Penalti: -{assessment.price_penalty_percentage}% | Tangkai: -{assessment.stalk_penalty_percentage || 0}%
        </p>
      </div>
    </div>
  );
}
