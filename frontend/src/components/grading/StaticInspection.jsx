import React, { useState } from 'react';
import { UploadCloud, Play, Sparkles, Image as ImageIcon, ToggleLeft, ToggleRight, Scale, Layers } from 'lucide-react';

export default function StaticInspection({
  selectedFile,
  handleFileChange,
  previewImage,
  handlePredict,
  isLoading,
  predictionResult,
  showOriginal,
  setShowOriginal,
  deliveryOrders,
  selectedOrderId,
  setSelectedOrderId
}) {
  const [longStalkCount, setLongStalkCount] = useState(0);
  const [denseMode, setDenseMode] = useState(false);

  return (
    <div className="space-y-6">
      {/* Upload & Form Controls */}
      <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              Pilih Dokumen Tiket Timbang (SPB):
            </label>
            <select
              value={selectedOrderId}
              onChange={(e) => setSelectedOrderId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">-- Tanpa SPB (Grading Lepas) --</option>
              {deliveryOrders.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.spb_number} ({o.truck_plate_number} - {o.net_weight_kg.toLocaleString()} kg)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              Estimasi TBS Tangkai Panjang (&gt; 2.5 cm):
            </label>
            <input
              type="number"
              min="0"
              value={longStalkCount}
              onChange={(e) => setLongStalkCount(Math.max(0, parseInt(e.target.value) || 0))}
              className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
              placeholder="Jumlah janjang gagang panjang"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              Mode Analisis Citra:
            </label>
            <button
              type="button"
              onClick={() => setDenseMode(!denseMode)}
              className={`w-full py-2.5 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center space-x-2 transition-all ${
                denseMode
                  ? 'bg-amber-500/20 border-amber-500/50 text-amber-300 shadow-lg shadow-amber-950/30'
                  : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>{denseMode ? 'Mode Tumpukan Padat (SAHI)' : 'Mode Standar (Cepat)'}</span>
            </button>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => handlePredict(null, longStalkCount, denseMode)}
              disabled={isLoading || (!selectedFile && !previewImage)}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold text-xs flex items-center justify-center space-x-2 shadow-lg shadow-emerald-950/50 disabled:opacity-50 transition-all"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isLoading ? 'Memproses Hyper-Inference...' : 'Jalankan Grading AI'}</span>
            </button>
          </div>
        </div>

        {/* File Dropzone */}
        <label className="flex flex-col items-center justify-center border-2 border-dashed border-slate-700 hover:border-emerald-500/60 rounded-xl p-6 cursor-pointer bg-slate-950/40 transition-colors">
          <UploadCloud className="w-8 h-8 text-emerald-400 mb-2" />
          <span className="text-xs font-semibold text-slate-200">
            {selectedFile ? selectedFile.name : 'Pilih atau Tarik Citra TBS Sawit (Format JPG/PNG)'}
          </span>
          <span className="text-[11px] text-slate-500 mt-1">Mendukung citra resolusi tinggi dari kamera loading ramp</span>
          <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
        </label>
      </div>

      {/* Visualizer Display Box */}
      {previewImage && (
        <div className="bg-slate-900 rounded-2xl border border-slate-800 p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ImageIcon className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-white">Pratinjau Hasil Anotasi & Bounding Box</h3>
            </div>

            {predictionResult && (
              <button
                onClick={() => setShowOriginal(!showOriginal)}
                className="flex items-center space-x-2 text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
              >
                <span>{showOriginal ? 'Tampilkan Teranotasi' : 'Tampilkan Asli'}</span>
              </button>
            )}
          </div>

          <div className="relative aspect-video max-h-[500px] w-full bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center">
            <img
              src={showOriginal ? previewImage : (predictionResult?.annotated_image_url || previewImage)}
              alt="Pratinjau TBS"
              className="max-h-full max-w-full object-contain"
            />
          </div>
        </div>
      )}
    </div>
  );
}
