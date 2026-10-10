import React, { useState } from 'react';
import { ShieldCheck, MapPin, CheckCircle2, AlertTriangle, Layers, ExternalLink, Globe } from 'lucide-react';

export default function EUDRPolygonViewer({ farmers = [], deliveryOrders = [] }) {
  const [selectedBlockId, setSelectedBlockId] = useState('BLK-RIAU-04A');

  // Contoh data poligon kebun mitra PCWE (WGS84 GeoJSON format)
  const blocks = [
    {
      id: 'BLK-RIAU-04A',
      name: 'Blok 04A - KUD Sawit Sejahtera',
      farmer: 'Bpk. Joko Supriyanto',
      spb: 'SPB-20261008-001',
      variety: 'DxP Marihat',
      area_ha: 4.5,
      legal: 'SHM No. 1042/Riau',
      lat: 0.5386,
      lng: 101.4485,
      cutoff: '31 Desember 2020 (Terverifikasi Bebas Deforestasi)',
      eudr_status: 'VERIFIED',
      polygon: [
        { lat: 0.5372, lng: 101.4465 },
        { lat: 0.5372, lng: 101.4505 },
        { lat: 0.5402, lng: 101.4510 },
        { lat: 0.5405, lng: 101.4470 }
      ]
    },
    {
      id: 'BLK-RIAU-02B',
      name: 'Blok 02B - Pekebun Swadaya',
      farmer: 'Bpk. Herman Nasution',
      spb: 'SPB-20261008-002',
      variety: 'Yangambi',
      area_ha: 2.8,
      legal: 'Girik No. 44/Kampar',
      lat: 0.5412,
      lng: 101.4521,
      cutoff: '31 Desember 2020 (Terverifikasi Bebas Deforestasi)',
      eudr_status: 'VERIFIED',
      polygon: [
        { lat: 0.5401, lng: 101.4508 },
        { lat: 0.5401, lng: 101.4535 },
        { lat: 0.5425, lng: 101.4538 },
        { lat: 0.5426, lng: 101.4511 }
      ]
    }
  ];

  const activeBlock = blocks.find(b => b.id === selectedBlockId) || blocks[0];

  return (
    <div className="space-y-6">
      {/* Header Info EUDR */}
      <div className="bg-gradient-to-r from-emerald-950/80 to-slate-900 p-6 rounded-2xl border border-emerald-800/40 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-emerald-400 mb-1">
              <ShieldCheck className="w-5 h-5" />
              <span className="text-xs font-bold tracking-wider uppercase">Regulasi Uni Eropa 2023/1115 (EUDR Compliance)</span>
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">
              Peta Batas Spasial Poligon Lahan (WGS84) & Ketertelusuran Petani
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              Pasal 9 EUDR mewajibkan data poligon tertutup koordinat WGS84 untuk kebun sawit &gt; 4 Hektar dengan ambang potong deforestasi 31 Desember 2020.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="px-3 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold text-xs flex items-center space-x-1">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>EUDR Cleared</span>
            </span>
            <span className="px-3 py-1.5 rounded-xl bg-blue-500/20 text-blue-300 border border-blue-500/30 font-semibold text-xs flex items-center space-x-1">
              <Globe className="w-4 h-4 text-blue-400" />
              <span>ISPO / RSPO Traceable</span>
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Selector & Detail Card */}
        <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 space-y-4 shadow-xl">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            <span>Pilih Blok Lahan Kebun</span>
          </h3>

          <div className="space-y-2">
            {blocks.map((b) => (
              <button
                key={b.id}
                onClick={() => setSelectedBlockId(b.id)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                  selectedBlockId === b.id
                    ? 'bg-emerald-950/60 border-emerald-500/60 text-white shadow-md'
                    : 'bg-slate-800/40 border-slate-700/50 text-slate-300 hover:bg-slate-800'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-sm">{b.name}</span>
                  <span className="text-xs px-2 py-0.5 rounded-md bg-slate-800 font-mono text-emerald-400">
                    {b.area_ha} Ha
                  </span>
                </div>
                <p className="text-xs text-slate-400">{b.farmer} • {b.legal}</p>
              </button>
            ))}
          </div>

          <div className="pt-4 border-t border-slate-800 space-y-3 text-xs">
            <div>
              <span className="text-slate-400">Pekebun / Koperasi:</span>
              <p className="font-semibold text-slate-200">{activeBlock.farmer}</p>
            </div>
            <div>
              <span className="text-slate-400">Koordinat Titik Acuan:</span>
              <p className="font-mono text-emerald-300">{activeBlock.lat.toFixed(4)}, {activeBlock.lng.toFixed(4)}</p>
            </div>
            <div>
              <span className="text-slate-400">Ketentuan Deforestasi Cut-off:</span>
              <p className="text-emerald-400 font-medium">{activeBlock.cutoff}</p>
            </div>
            <div>
              <span className="text-slate-400">Verifikasi Dokumen Spasial:</span>
              <p className="text-slate-300 font-mono">GeoJSON Poligon 4 Titik Sudut Valid</p>
            </div>
          </div>
        </div>

        {/* Visualizer Peta SVG Koordinat Interaktif */}
        <div className="lg:col-span-2 bg-slate-900 rounded-2xl border border-slate-800 p-5 shadow-xl flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <MapPin className="w-5 h-5 text-emerald-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Visualisasi Batas Bidang Lahan (Polygon Geometry Overlay)
              </h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">WGS84 EPSG:4326</span>
          </div>

          {/* SVG Map Canvas */}
          <div className="relative flex-1 min-h-[380px] bg-slate-950 rounded-xl border border-slate-800 overflow-hidden flex items-center justify-center p-6">
            <svg viewBox="0 0 500 350" className="w-full h-full max-w-lg">
              {/* Grid Background */}
              <defs>
                <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="1" />
                </pattern>
              </defs>
              <rect width="500" height="350" fill="url(#grid)" />

              {/* Polygon Shape */}
              <polygon
                points={
                  activeBlock.id === 'BLK-RIAU-04A'
                    ? "120,80 380,90 410,260 140,280"
                    : "150,110 350,115 360,230 160,240"
                }
                fill="rgba(16, 185, 129, 0.25)"
                stroke="#10b981"
                strokeWidth="3"
                strokeDasharray="6,3"
                className="transition-all duration-500"
              />

              {/* Corner Pin Nodes */}
              {(activeBlock.id === 'BLK-RIAU-04A'
                ? [[120, 80], [380, 90], [410, 260], [140, 280]]
                : [[150, 110], [350, 115], [360, 230], [160, 240]]
              ).map(([cx, cy], idx) => (
                <g key={idx}>
                  <circle cx={cx} cy={cy} r="6" fill="#059669" stroke="#ffffff" strokeWidth="2" />
                  <text x={cx + 10} y={cy - 10} fill="#94a3b8" fontSize="11" fontFamily="monospace">
                    P{idx + 1}
                  </text>
                </g>
              ))}

              {/* Center Marker */}
              <circle cx="260" cy="180" r="8" fill="#eab308" stroke="#ffffff" strokeWidth="2" />
              <text x="275" y="185" fill="#fef08a" fontSize="12" fontWeight="bold">
                Centroid: {activeBlock.id}
              </text>
            </svg>

            {/* Map Info Floating Tag */}
            <div className="absolute bottom-4 left-4 bg-slate-900/90 backdrop-blur-md px-3.5 py-2 rounded-xl border border-slate-700 text-xs space-y-1">
              <div className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                <span className="text-white font-bold">{activeBlock.name}</span>
              </div>
              <p className="text-slate-400">Luas Terverifikasi: {activeBlock.area_ha} Ha • Status: Bersih Deforestasi</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
