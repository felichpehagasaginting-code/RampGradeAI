import React, { useState, useEffect } from 'react';
import { Cpu, RefreshCw, CheckCircle2, Sparkles, UploadCloud, Layers, AlertCircle, ArrowUpRight } from 'lucide-react';

export default function ActiveLearningHub({ predictionResult }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [msg, setMsg] = useState(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/v1/active-learning/status');
      if (res.ok) setStatus(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 4000);
    return () => clearInterval(timer);
  }, []);

  const handleTriggerRetrain = async () => {
    setTriggering(true);
    setMsg(null);
    try {
      const form = new FormData();
      form.append('epochs', '15');
      form.append('batch_size', '8');
      const res = await fetch('/api/v1/active-learning/trigger-retrain', {
        method: 'POST',
        body: form
      });
      const data = await res.json();
      setMsg(data.message);
      fetchStatus();
    } catch (e) {
      setMsg('Gagal memicu retraining: ' + e.message);
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Banner Hub */}
      <div className="bg-gradient-to-r from-violet-950/80 via-slate-900 to-slate-900 p-6 rounded-3xl border border-violet-800/40 shadow-2xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-violet-400 mb-1">
              <Sparkles className="w-5 h-5" />
              <span className="text-xs font-bold tracking-wider uppercase">MLOps Active Learning & Continuous Improvement</span>
            </div>
            <h2 className="text-2xl font-black text-white tracking-tight">
              Sistem AI Mandiri (Self-Improving Pipeline)
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Ketika grader mengoreksi hasil klasifikasi buah mentah atau janjang kosong, citra otomatis diproses dalam format YOLO untuk memperbarui model tanpa merestart server.
            </p>
          </div>

          <button
            onClick={handleTriggerRetrain}
            disabled={triggering || status?.is_training}
            className="px-5 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold text-xs flex items-center space-x-2 shadow-lg shadow-violet-950/50 disabled:opacity-50 self-start md:self-auto transition-all"
          >
            <Cpu className="w-4 h-4" />
            <span>{status?.is_training ? 'Sedang Melatih Ulang...' : 'Mulai Background Retraining'}</span>
          </button>
        </div>
      </div>

      {msg && (
        <div className="p-4 rounded-2xl bg-violet-500/10 border border-violet-500/30 text-violet-300 text-xs">
          {msg}
        </div>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 shadow-xl space-y-1">
          <span className="text-xs text-slate-400">Sampel Koreksi Terkumpul</span>
          <p className="text-3xl font-black text-white font-mono">{status?.samples_count || 0}</p>
          <span className="text-[11px] text-violet-400 font-medium">Format Anotasi Standar YOLO txt</span>
        </div>

        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 shadow-xl space-y-1">
          <span className="text-xs text-slate-400">Ambang Batas Auto-Retrain</span>
          <p className="text-3xl font-black text-emerald-400 font-mono">20 Sampel</p>
          <span className="text-[11px] text-slate-500">Bisa di-trigger manual kapan saja</span>
        </div>

        <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800 shadow-xl space-y-1">
          <span className="text-xs text-slate-400">Status Engine Retraining</span>
          <div className="flex items-center space-x-2 pt-1">
            <span className={`w-3 h-3 rounded-full ${status?.is_training ? 'bg-amber-400 animate-ping' : 'bg-emerald-400'}`} />
            <span className="text-base font-bold text-white">
              {status?.is_training ? 'Sedang Training (Epochs)' : 'Siap / Standby'}
            </span>
          </div>
          <span className="text-[11px] text-slate-500">Hot-reload model ONNX otomatis</span>
        </div>
      </div>

      {/* Training Log Feed */}
      <div className="bg-slate-900 rounded-2xl border border-slate-800 p-5 shadow-xl space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Log Aktivitas Pipeline MLOps
          </span>
          <button onClick={fetchStatus} className="text-slate-500 hover:text-white">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs font-mono text-slate-300">
          {status?.last_training_log || 'Menunggu sampel koreksi baru dari operator grader...'}
        </div>
      </div>
    </div>
  );
}
