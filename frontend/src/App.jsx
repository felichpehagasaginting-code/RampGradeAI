import React, { useState, useEffect, useRef } from 'react';
import HeaderNavigation from './components/layout/HeaderNavigation';
import CameraStreamHUD from './components/grading/CameraStreamHUD';
import StaticInspection from './components/grading/StaticInspection';
import OERMetricsCards from './components/grading/OERMetricsCards';
import EUDRPolygonViewer from './components/traceability/EUDRPolygonViewer';
import DigitalCertificateModal from './components/certificate/DigitalCertificateModal';
import FarmerPortal from './components/farmer/FarmerPortal';
import ActiveLearningHub from './components/active_learning/ActiveLearningHub';
import {
  Camera, UploadCloud, CheckCircle2, AlertTriangle, Layers,
  RefreshCw, Award, Activity, Users, Truck, ArrowRight, Download, FileSpreadsheet
} from 'lucide-react';

export default function App() {
  const [activeNav, setActiveNav] = useState('grading');
  const [inspectionMode, setInspectionMode] = useState('camera'); // 'camera' | 'photo'

  // Camera & Tripwire State
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraDevices, setCameraDevices] = useState([]);
  const [selectedCameraId, setSelectedCameraId] = useState('');
  const [cameraLoading, setCameraLoading] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const [liveResult, setLiveResult] = useState(null);
  const [cameraFPS, setCameraFPS] = useState(0);

  const videoRef = useRef(null);
  const canvasOverlayRef = useRef(null);
  const hiddenCanvasRef = useRef(null);
  const streamRef = useRef(null);
  const isProcessingRef = useRef(false);
  const fpsTrackerRef = useRef({ count: 0, lastTime: performance.now() });

  // Static Photo State
  const [previewImage, setPreviewImage] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [predictionResult, setPredictionResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showOriginal, setShowOriginal] = useState(false);

  // Backend Data
  const [deliveryOrders, setDeliveryOrders] = useState([]);
  const [farmers, setFarmers] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [selectedOrderId, setSelectedOrderId] = useState('');
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    fetchDeliveryOrders();
    fetchFarmers();
    fetchSessions();
    fetchAnalytics();
    updateCameraDevices();

    return () => {
      stopCamera();
    };
  }, []);

  const fetchDeliveryOrders = async () => {
    try {
      const res = await fetch('/api/v1/delivery-orders/');
      if (res.ok) {
        const data = await res.json();
        setDeliveryOrders(data);
        if (data.length > 0 && !selectedOrderId) {
          setSelectedOrderId(data[0].id.toString());
        }
      }
    } catch (e) {
      console.error('Error SPB:', e);
    }
  };

  const fetchFarmers = async () => {
    try {
      const res = await fetch('/api/v1/farmers/');
      if (res.ok) setFarmers(await res.json());
    } catch (e) {
      console.error('Error farmers:', e);
    }
  };

  const fetchSessions = async () => {
    try {
      const res = await fetch('/api/v1/grading/sessions');
      if (res.ok) setSessions(await res.json());
    } catch (e) {
      console.error('Error sessions:', e);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await fetch('/api/v1/analytics/summary');
      if (res.ok) setAnalytics(await res.json());
    } catch (e) {
      console.error('Error analytics:', e);
    }
  };

  // --- Camera Operations ---
  const updateCameraDevices = async () => {
    try {
      if (navigator.mediaDevices?.enumerateDevices) {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoInputs = devices.filter((d) => d.kind === 'videoinput');
        setCameraDevices(videoInputs);
        if (videoInputs.length > 0 && !selectedCameraId) {
          setSelectedCameraId(videoInputs[0].deviceId);
        }
      }
    } catch (e) {
      console.warn('Gagal enumerasi kamera:', e);
    }
  };

  const startCamera = async (deviceId = selectedCameraId) => {
    setCameraLoading(true);
    setCameraError(null);
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
      const constraints = {
        video: deviceId
          ? { deviceId: { exact: deviceId }, width: { ideal: 1280 }, height: { ideal: 720 } }
          : { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          setIsCameraActive(true);
          setCameraLoading(false);
          requestAnimationFrame(processFrameLoop);
        };
      }
    } catch (err) {
      console.error('Kamera error:', err);
      setCameraError('Gagal mengakses kamera: ' + err.message);
      setCameraLoading(false);
      setIsCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setIsCameraActive(false);
    setLiveResult(null);
  };

  const handleResetTripwire = async () => {
    try {
      await fetch('/api/v1/grading/tripwire/reset', { method: 'POST' });
    } catch (e) {
      console.error('Reset tripwire error:', e);
    }
  };

  // Real-time Frame Loop
  const processFrameLoop = async () => {
    if (!videoRef.current || videoRef.current.paused || videoRef.current.ended) return;

    if (!isProcessingRef.current) {
      isProcessingRef.current = true;
      try {
        if (!hiddenCanvasRef.current) {
          hiddenCanvasRef.current = document.createElement('canvas');
        }
        const v = videoRef.current;
        const hc = hiddenCanvasRef.current;
        if (v.videoWidth > 0 && v.videoHeight > 0) {
          hc.width = 640;
          hc.height = 360;
          const ctx = hc.getContext('2d');
          ctx.drawImage(v, 0, 0, hc.width, hc.height);

          const blob = await new Promise((resolve) => hc.toBlob(resolve, 'image/jpeg', 0.75));
          if (blob) {
            const formData = new FormData();
            formData.append('file', blob, 'frame.jpg');
            formData.append('allow_demo_fallback', 'true');
            formData.append('use_tripwire', 'true');

            const res = await fetch('/api/v1/grading/predict-frame', {
              method: 'POST',
              body: formData
            });

            if (res.ok) {
              const data = await res.json();
              setLiveResult(data);
              drawOverlayHUD(data, v.videoWidth, v.videoHeight);

              // Update FPS counter
              const now = performance.now();
              fpsTrackerRef.current.count++;
              if (now - fpsTrackerRef.current.lastTime >= 1000) {
                setCameraFPS(Math.round((fpsTrackerRef.current.count * 1000) / (now - fpsTrackerRef.current.lastTime)));
                fpsTrackerRef.current.count = 0;
                fpsTrackerRef.current.lastTime = now;
              }
            }
          }
        }
      } catch (e) {
        console.warn('Frame processing dropped:', e);
      } finally {
        isProcessingRef.current = false;
      }
    }
    requestAnimationFrame(processFrameLoop);
  };

  // Draw Tripwire & Bounding Boxes on Overlay Canvas
  const drawOverlayHUD = (data, origW, origH) => {
    const canvas = canvasOverlayRef.current;
    if (!canvas) return;
    canvas.width = origW;
    canvas.height = origH;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const scaleX = origW / (data.frame_width || 640);
    const scaleY = origH / (data.frame_height || 360);

    // 1. Gambar Garis Virtual Tripwire (Priority 1)
    if (data.tripwire_y) {
      const lineY = data.tripwire_y * scaleY;
      ctx.beginPath();
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 3;
      ctx.setLineDash([8, 6]);
      ctx.moveTo(0, lineY);
      ctx.lineTo(origW, lineY);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = '#ef4444';
      ctx.font = 'bold 14px monospace';
      ctx.fillText('--- TRIPWIRE COUNTING LINE ---', 20, lineY - 8);
    }

    // 2. Gambar Bounding Boxes
    const colorsMap = {
      unripe: '#475569',
      underripe: '#eab308',
      ripe: '#10b981',
      overripe: '#f43f5e'
    };

    data.detections.forEach((d) => {
      const [x1, y1, x2, y2] = d.bbox;
      const rx1 = x1 * scaleX;
      const ry1 = y1 * scaleY;
      const rw = (x2 - x1) * scaleX;
      const rh = (y2 - y1) * scaleY;
      const c = colorsMap[d.class_name] || '#10b981';

      ctx.strokeStyle = c;
      ctx.lineWidth = 3;
      ctx.strokeRect(rx1, ry1, rw, rh);

      ctx.fillStyle = c;
      ctx.fillRect(rx1, Math.max(0, ry1 - 22), 110, 22);
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 12px sans-serif';
      ctx.fillText(`${d.class_name} ${(d.confidence * 100).toFixed(0)}%`, rx1 + 6, Math.max(0, ry1 - 6));
    });
  };

  // --- Static Photo Operations ---
  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (f) {
      setSelectedFile(f);
      setPreviewImage(URL.createObjectURL(f));
      setPredictionResult(null);
    }
  };

  const handlePredict = async (customFile = null, stalkCount = 0, denseMode = false) => {
    const f = customFile || selectedFile;
    if (!f) return;
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', f);
      if (selectedOrderId) formData.append('delivery_order_id', selectedOrderId);
      formData.append('long_stalk_count', stalkCount.toString());
      formData.append('dense_mode', denseMode ? 'true' : 'false');

      const res = await fetch('/api/v1/grading/predict', { method: 'POST', body: formData });
      if (res.ok) {
        const d = await res.json();
        setPredictionResult(d);
      }
    } catch (e) {
      alert('Gagal memproses gambar: ' + e.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveSession = async () => {
    if (!predictionResult) return;
    try {
      const res = await fetch('/api/v1/grading/commit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_code: predictionResult.session_code,
          delivery_order_id: selectedOrderId ? parseInt(selectedOrderId) : null,
          operator_name: 'Petugas Grader PKS PCWE'
        })
      });
      if (res.ok) {
        alert('Sesi grading berhasil disimpan ke database!');
        fetchSessions();
        setActiveNav('history');
      }
    } catch (e) {
      alert('Gagal menyimpan sesi: ' + e.message);
    }
  };

  const handleDownloadPdf = (sessionId) => {
    window.open(`/api/v1/grading/sessions/${sessionId}/pdf`, '_blank');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <HeaderNavigation activeNav={activeNav} setActiveNav={setActiveNav} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
        {/* TAB 1: INSPEKSI & GRADING */}
        {activeNav === 'grading' && (
          <div className="space-y-6">
            {/* Mode Switcher */}
            <div className="flex items-center justify-between bg-slate-900/90 p-3 rounded-2xl border border-slate-800">
              <div className="flex space-x-2">
                <button
                  onClick={() => { setInspectionMode('camera'); }}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
                    inspectionMode === 'camera'
                      ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-950/40'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Camera className="w-4 h-4" />
                  <span>Mode 1: Kamera Real-time (Virtual Tripwire)</span>
                </button>
                <button
                  onClick={() => { setInspectionMode('photo'); stopCamera(); }}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
                    inspectionMode === 'photo'
                      ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-950/40'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <UploadCloud className="w-4 h-4" />
                  <span>Mode 2: Input Foto Resolusi Tinggi (Truk SPB)</span>
                </button>
              </div>
            </div>

            {/* Mode Viewport */}
            {inspectionMode === 'camera' ? (
              <div className="space-y-6">
                <CameraStreamHUD
                  isCameraActive={isCameraActive}
                  cameraLoading={cameraLoading}
                  cameraError={cameraError}
                  cameraDevices={cameraDevices}
                  selectedCameraId={selectedCameraId}
                  setSelectedCameraId={setSelectedCameraId}
                  startCamera={startCamera}
                  stopCamera={stopCamera}
                  videoRef={videoRef}
                  canvasOverlayRef={canvasOverlayRef}
                  cameraFPS={cameraFPS}
                  liveResult={liveResult}
                  onResetTripwire={handleResetTripwire}
                />
                <OERMetricsCards assessment={liveResult} />
              </div>
            ) : (
              <div className="space-y-6">
                <StaticInspection
                  selectedFile={selectedFile}
                  handleFileChange={handleFileChange}
                  previewImage={previewImage}
                  handlePredict={handlePredict}
                  isLoading={isLoading}
                  predictionResult={predictionResult}
                  showOriginal={showOriginal}
                  setShowOriginal={setShowOriginal}
                  deliveryOrders={deliveryOrders}
                  selectedOrderId={selectedOrderId}
                  setSelectedOrderId={setSelectedOrderId}
                />
                {predictionResult && (
                  <div className="space-y-4">
                    <OERMetricsCards assessment={predictionResult.assessment} />
                    <div className="flex justify-end">
                      <button
                        onClick={handleSaveSession}
                        className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center space-x-2 shadow-lg"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Simpan Sesi Grading & Terbitkan Sertifikat</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: PETA SPASIAL EUDR */}
        {activeNav === 'eudr_map' && (
          <EUDRPolygonViewer farmers={farmers} deliveryOrders={deliveryOrders} />
        )}

        {/* TAB 3: RIWAYAT & SERTIFIKAT */}
        {activeNav === 'history' && (
          <DigitalCertificateModal sessions={sessions} onDownloadPdf={handleDownloadPdf} />
        )}

        {/* TAB 4: PORTAL PETANI PWA */}
        {activeNav === 'farmer_portal' && (
          <FarmerPortal deliveryOrders={deliveryOrders} />
        )}

        {/* TAB 5: ACTIVE LEARNING MLOps */}
        {activeNav === 'active_learning' && (
          <ActiveLearningHub predictionResult={predictionResult} />
        )}

        {/* TAB 6: OVERVIEW & RINGKASAN */}
        {activeNav === 'overview' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between bg-slate-900 p-5 rounded-2xl border border-slate-800 shadow-xl">
              <div>
                <h3 className="text-base font-bold text-white">Laporan Harian Pengolahan (LHP) Pabrik</h3>
                <p className="text-xs text-slate-400">Unduh data rekapitulasi timbangan dan penetapan harga TBS resmi dalam format spreadsheet Excel.</p>
              </div>
              <a
                href="/api/v1/analytics/export/excel"
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center space-x-2 shadow-lg"
              >
                <FileSpreadsheet className="w-4 h-4" />
                <span>Unduh Laporan Excel (.xlsx)</span>
              </a>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-2">
                <span className="text-xs font-semibold text-slate-400">Total Sesi Grading</span>
                <p className="text-3xl font-black text-white font-mono">{sessions.length} Sesi</p>
                <p className="text-xs text-emerald-400">Terdaftar di Loading Ramp</p>
              </div>
              <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-2">
                <span className="text-xs font-semibold text-slate-400">Benchmark OER Pabrik</span>
                <p className="text-3xl font-black text-emerald-400 font-mono">21.50%</p>
                <p className="text-xs text-slate-400">Standar Acuan IOPRI 1997</p>
              </div>
              <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-2">
                <span className="text-xs font-semibold text-slate-400">Kepatuhan Regulasi EUDR</span>
                <p className="text-3xl font-black text-teal-400 font-mono">100%</p>
                <p className="text-xs text-emerald-400">Poligon WGS84 Terverifikasi</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
