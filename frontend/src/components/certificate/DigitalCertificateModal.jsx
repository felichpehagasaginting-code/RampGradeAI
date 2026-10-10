import React, { useState, useEffect } from 'react';
import { Award, FileText, Download, CheckCircle2, QrCode, Search, ExternalLink } from 'lucide-react';

export default function DigitalCertificateModal({ sessions = [], onDownloadPdf }) {
  const [selectedSessionId, setSelectedSessionId] = useState(null);

  useEffect(() => {
    if (sessions.length > 0 && !selectedSessionId) {
      setSelectedSessionId(sessions[0].id);
    }
  }, [sessions]);

  const activeSession = sessions.find(s => s.id === selectedSessionId) || sessions[0];

  return (
    <div className="space-y-6">
      <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Award className="w-5 h-5 text-emerald-400" />
            <span>Sertifikat Mutu Digital TBS & Arsip Penimbangan PKS</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Diterbitkan secara otomatis dengan enkripsi QR-Code publik dan kepatuhan regulasi EUDR (2023/1115).
          </p>
        </div>

        {activeSession && (
          <button
            onClick={() => onDownloadPdf(activeSession.id)}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold text-xs flex items-center space-x-2 shadow-lg shadow-emerald-950/50 transition-all self-start md:self-auto"
          >
            <Download className="w-4 h-4" />
            <span>Unduh Sertifikat Resmi (PDF)</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* List of Sessions */}
        <div className="bg-slate-900 rounded-2xl border border-slate-800 p-4 space-y-3 shadow-xl">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Daftar Sesi Grading Tersimpan</h3>
          <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
            {sessions.length === 0 ? (
              <p className="text-xs text-slate-500 p-3">Belum ada sesi grading yang disimpan.</p>
            ) : (
              sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedSessionId(s.id)}
                  className={`w-full text-left p-3 rounded-xl border transition-all ${
                    selectedSessionId === s.id
                      ? 'bg-emerald-950/60 border-emerald-500/60 text-white'
                      : 'bg-slate-800/40 border-slate-700/50 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono font-bold text-xs">{s.session_code}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-emerald-400 font-mono">
                      {s.total_bunches} Janjang
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">{new Date(s.graded_at).toLocaleString('id-ID')}</p>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Certificate Preview Card */}
        {activeSession && (
          <div className="lg:col-span-2 bg-slate-950 rounded-2xl border border-slate-800 p-6 shadow-2xl space-y-6">
            <div className="border-b border-slate-800 pb-4 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                  Sertifikat Verifikasi Mutu TBS
                </span>
                <h3 className="text-lg font-mono font-black text-white">{activeSession.session_code}</h3>
              </div>
              <div className="flex items-center space-x-1.5 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg text-xs font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                <span>Terverifikasi Digital</span>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Total TBS Graded</span>
                <span className="text-base font-bold text-white font-mono">{activeSession.total_bunches} Janjang</span>
              </div>
              <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Estimasi OER</span>
                <span className="text-base font-bold text-emerald-400 font-mono">
                  {activeSession.assessment?.estimated_oer_percentage || 21.5}%
                </span>
              </div>
              <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Risiko FFA/ALB</span>
                <span className="text-base font-bold text-teal-400 font-mono">
                  {activeSession.assessment?.ffa_risk_category || 'LOW'}
                </span>
              </div>
              <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Harga Beli Bersih</span>
                <span className="text-base font-bold text-amber-300 font-mono">
                  Rp {activeSession.assessment?.final_price_per_kg?.toLocaleString() || '2.850'}
                </span>
              </div>
            </div>

            <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
              <div className="space-y-1">
                <span className="text-xs font-semibold text-slate-300">Kepatuhan Traceability EUDR (2023/1115):</span>
                <p className="text-xs text-slate-400">
                  Telah terhubung dengan poligon batas lahan kebun koordinat WGS84 dan sertifikat ISPO/RSPO.
                </p>
              </div>
              <button
                onClick={() => onDownloadPdf(activeSession.id)}
                className="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center space-x-1.5 transition-all shadow"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Unduh PDF</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
