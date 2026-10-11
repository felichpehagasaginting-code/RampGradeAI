import React from 'react';
import {
  LayoutDashboard, Camera, ShieldCheck, BarChart3, Users, Layers, Award
} from 'lucide-react';

export default function HeaderNavigation({ activeNav, setActiveNav, systemOnline = true }) {
  const navItems = [
    { id: 'overview', label: 'Ringkasan & Metrik', icon: LayoutDashboard },
    { id: 'grading', label: 'Inspeksi & Grading', icon: Camera },
    { id: 'eudr_map', label: 'Peta Spasial EUDR', icon: ShieldCheck },
    { id: 'farmer_portal', label: 'Portal Petani PWA', icon: Users },
    { id: 'active_learning', label: 'Active Learning AI', icon: Layers },
    { id: 'history', label: 'Riwayat & Sertifikat', icon: Award }
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          <div className="flex items-center gap-3 shrink-0">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center text-white shadow-lg shadow-emerald-900/30 shrink-0">
              <Layers className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg sm:text-xl font-bold tracking-tight text-white whitespace-nowrap">SMART GRADE</span>
                <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30 whitespace-nowrap">
                  ONNX EDGE
                </span>
              </div>
              <p className="text-[11px] text-slate-400 whitespace-nowrap">Politeknik Citra Widya Edukasi (PCWE) • BPDP 2026</p>
            </div>
          </div>

          <nav className="flex items-center gap-1.5 overflow-x-auto py-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeNav === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveNav(item.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs md:text-sm font-semibold transition-all whitespace-nowrap ${
                    isActive
                      ? 'bg-emerald-600 text-white shadow-md shadow-emerald-950/40'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/80'
                  }`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span className="hidden xl:inline">{item.label}</span>
                </button>
              );
            })}
          </nav>

          <div className="hidden 2xl:flex items-center gap-2 text-xs shrink-0">
            <span className={`w-2.5 h-2.5 rounded-full ${systemOnline ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-slate-300 font-medium whitespace-nowrap">Sistem Aktif (IOPRI 1997)</span>
          </div>
        </div>
      </div>
    </header>
  );
}
