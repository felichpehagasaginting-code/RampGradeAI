import React, { useRef, useEffect } from 'react';
import { Camera, Video, VideoOff, RefreshCw, Zap, ShieldAlert, Sparkles } from 'lucide-react';

export default function CameraStreamHUD({
  isCameraActive,
  cameraLoading,
  cameraError,
  cameraDevices,
  selectedCameraId,
  setSelectedCameraId,
  startCamera,
  stopCamera,
  videoRef,
  canvasOverlayRef,
  cameraFPS,
  liveResult,
  tripwireActive = true,
  onResetTripwire
}) {
  return (
    <div className="space-y-4">
      {/* Camera Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/90 p-4 rounded-2xl border border-slate-800">
        <div className="flex items-center space-x-3">
          <label className="text-xs font-semibold text-slate-300">Pilih Kamera:</label>
          <select
            value={selectedCameraId}
            onChange={(e) => {
              setSelectedCameraId(e.target.value);
              if (isCameraActive) startCamera(e.target.value);
            }}
            disabled={!isCameraActive || cameraDevices.length === 0}
            className="bg-slate-800 border border-slate-700 text-xs text-white rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {cameraDevices.length === 0 && <option value="">Webcam Default</option>}
            {cameraDevices.map((d, i) => (
              <option key={d.deviceId || i} value={d.deviceId}>
                {d.label || `Kamera ${i + 1}`}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center space-x-2">
          {tripwireActive && onResetTripwire && (
            <button
              onClick={onResetTripwire}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 border border-slate-700 flex items-center space-x-1"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset Counter Garis</span>
            </button>
          )}

          {!isCameraActive ? (
            <button
              onClick={() => startCamera()}
              disabled={cameraLoading}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center space-x-2 shadow-lg shadow-emerald-950/50 transition-all"
            >
              <Video className="w-4 h-4" />
              <span>{cameraLoading ? 'Mengaktifkan...' : 'Mulai Streaming Kamera'}</span>
            </button>
          ) : (
            <button
              onClick={stopCamera}
              className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs flex items-center space-x-2 shadow-lg shadow-rose-950/50 transition-all"
            >
              <VideoOff className="w-4 h-4" />
              <span>Hentikan Kamera</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Video Viewport with Canvas HUD Overlay */}
      <div className="relative aspect-video w-full bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden shadow-2xl flex items-center justify-center">
        {!isCameraActive ? (
          <div className="text-center p-6 space-y-3">
            <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-600">
              <Camera className="w-8 h-8" />
            </div>
            <p className="text-sm font-semibold text-slate-300">Streaming Kamera Real-time Dinonaktifkan</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Klik 'Mulai Streaming Kamera' untuk mengaktifkan deteksi kontinu dan penghitungan tandan via Virtual Tripwire.
            </p>
          </div>
        ) : (
          <>
            <video
              ref={videoRef}
              playsInline
              muted
              autoPlay
              className="absolute inset-0 w-full h-full object-contain"
            />
            <canvas
              ref={canvasOverlayRef}
              className="absolute inset-0 w-full h-full object-contain pointer-events-none"
            />

            {/* Virtual Tripwire HUD Overlay Banner */}
            <div className="absolute top-4 left-4 flex flex-wrap gap-2 pointer-events-none">
              <div className="bg-slate-900/85 backdrop-blur-md border border-slate-700/60 px-3 py-1.5 rounded-xl text-xs text-white font-mono flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span>FPS: {cameraFPS}</span>
              </div>
              <div className="bg-slate-900/85 backdrop-blur-md border border-slate-700/60 px-3 py-1.5 rounded-xl text-xs text-emerald-400 font-mono font-bold">
                Terkumpul Tripwire: {liveResult?.cumulative_counted ?? 0} TBS
              </div>
              <div className="bg-slate-900/85 backdrop-blur-md border border-slate-700/60 px-3 py-1.5 rounded-xl text-xs text-yellow-400 font-mono font-bold">
                Aktif Frame: {liveResult?.total_bunches ?? 0} Bounding Boxes
              </div>
            </div>

            {/* Visual Garis Tripwire Indicator Label */}
            <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none bg-rose-500/80 text-white text-[10px] font-bold px-2 py-0.5 rounded shadow">
              GARIS VIRTUAL PENCACAH (TRIPWIRE)
            </div>
          </>
        )}
      </div>

      {cameraError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{cameraError}</span>
        </div>
      )}
    </div>
  );
}
