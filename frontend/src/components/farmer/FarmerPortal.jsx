import React, { useState } from 'react';
import { Smartphone, Search, CheckCircle2, ShieldCheck, Download, Truck, Calendar, MapPin, DollarSign, Activity } from 'lucide-react';

export default function FarmerPortal({ deliveryOrders = [] }) {
  const [searchQuery, setSearchQuery] = useState('SPB-20261008-001');
  const [auditResult, setAuditResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/analytics/audit/${encodeURIComponent(searchQuery.trim())}`);
      if (!res.ok) throw new Error("Nomor SPB tidak ditemukan dalam sistem PKS.");
      const data = await res.json();
      setAuditResult(data);
    } catch (e) {
      setError(e.message);
      setAuditResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Mobile-Friendly Hero Header */}
      <div className="bg-gradient-to-br from-emerald-900 to-slate-900 p-6 rounded-3xl border border-emerald-700/40 shadow-2xl text-center space-y-2">
        <div className="w-12 h-12 bg-emerald-500/20 text-emerald-400 rounded-2xl flex items-center justify-center mx-auto mb-2 border border-emerald-500/30">
          <Smartphone className="w-6 h-6" />
        </div>
        <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
          Portal Transparansi Pekebun Sawit
        </h2>
        <p className="text-xs text-slate-300 max-w-md mx-auto">
          Cek kejujuran hasil grading timbangan PKS, rincian potongan fraksi, foto bukti AI, dan estimasi penerimaan rupiah langsung dari ponsel Anda.
        </p>

        {/* Search Bar Input */}
        <div className="pt-4 max-w-md mx-auto flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Masukkan No. SPB (mis: SPB-20261008-001)"
            className="flex-1 bg-slate-950/80 border border-slate-700 rounded-2xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
          />
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-5 py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center space-x-1 shadow-lg shadow-emerald-950/50"
          >
            <Search className="w-4 h-4" />
            <span>{loading ? 'Mencari...' : 'Periksa'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs text-center">
          {error}
        </div>
      )}

      {/* Result Card */}
      {auditResult && (
        <div className="bg-slate-900 rounded-3xl border border-slate-800 p-6 shadow-2xl space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                Surat Pengantar Buah (SPB) Terverifikasi
              </span>
              <h3 className="text-lg font-black text-white font-mono">{auditResult.audit_ticket.spb_number}</h3>
            </div>
            <div className="px-3 py-1 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-bold flex items-center space-x-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Selesai Graded</span>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800">
              <span className="text-[11px] text-slate-400 block mb-1">Tonase Netto</span>
              <span className="text-base font-bold text-white font-mono">
                {auditResult.audit_ticket.net_weight_kg.toLocaleString()} Kg
              </span>
            </div>
            <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800">
              <span className="text-[11px] text-slate-400 block mb-1">Estimasi OER</span>
              <span className="text-base font-bold text-emerald-400 font-mono">
                {auditResult.oer_and_commercial.estimated_oer_percentage}%
              </span>
            </div>
            <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800">
              <span className="text-[11px] text-slate-400 block mb-1">Harga Beli Akhir</span>
              <span className="text-base font-bold text-amber-300 font-mono">
                Rp {auditResult.oer_and_commercial.final_price_per_kg.toLocaleString()}
              </span>
            </div>
            <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800">
              <span className="text-[11px] text-slate-400 block mb-1">Total Payout</span>
              <span className="text-base font-bold text-emerald-300 font-mono">
                Rp {auditResult.oer_and_commercial.total_payout_rp.toLocaleString()}
              </span>
            </div>
          </div>

          {/* Bukti Foto AI */}
          {auditResult.grading_evidence.image_url && (
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-300">Foto Bukti Inspeksi AI di Jembatan Timbang:</span>
              <div className="aspect-video w-full rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 flex items-center justify-center">
                <img
                  src={auditResult.grading_evidence.image_url}
                  alt="Bukti Grading AI"
                  className="max-h-full max-w-full object-contain"
                />
              </div>
            </div>
          )}

          {/* Rincian Petani & Legalitas Kebun */}
          <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-2 text-xs">
            <div className="flex justify-between text-slate-300">
              <span className="text-slate-500">Pekebun:</span>
              <span className="font-bold">{auditResult.traceability_origin.farmer_name}</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span className="text-slate-500">Koperasi / KUD:</span>
              <span>{auditResult.traceability_origin.cooperative}</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span className="text-slate-500">Kepatuhan EUDR & ISPO:</span>
              <span className="text-emerald-400 font-semibold">Terverifikasi Bebas Deforestasi</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
