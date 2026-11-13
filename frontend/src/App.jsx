import React, { useState, useEffect, useRef } from "react";
import {
  Upload,
  FileSpreadsheet,
  FileText,
  Code2,
  Download,
  Copy,
  Check,
  Sparkles,
  AlertCircle,
  RefreshCw,
  Cpu,
  Layers,
  Search,
  X,
  Sliders,
  Bot
} from "lucide-react";

export default function App() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [maxTokens, setMaxTokens] = useState(1024);
  const [loading, setLoading] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState("table");
  const [searchQuery, setSearchQuery] = useState("");
  const [copied, setCopied] = useState(false);
  
  // Model & Health state
  const [models, setModels] = useState([
    { id: "qwen2_vl", name: "Qwen2-VL-2B (LoRA İnce Ayarlı)", ready: true, description: "Yeni nesil 2024 Vision-Language LoRA modeli (Önerilen)" },
    { id: "qwen2_vl_base", name: "Qwen2-VL-2B Orijinal (Ham Model)", ready: true, description: "Alibaba'nın orijinal ham Qwen2-VL modeli (LoRA'sız)" },
    { id: "deplot_v2", name: "DePlot LoRA (v2 - İnce Ayarlı)", ready: true, description: "Fine-tune edilmiş DePlot LoRA modeli" },
    { id: "deplot_base", name: "DePlot Orijinal (Yerel Ham Model)", ready: true, description: "Orijinal ham Google DePlot modeli (LoRA'sız)" }
  ]);
  const [selectedModel, setSelectedModel] = useState("qwen2_vl");
  const [health, setHealth] = useState({ status: "checking", device: "...", gpu_name: "...", current_model: "DePlot" });

  const fileInputRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Health check & Models fetch on mount
  useEffect(() => {
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => setHealth(data))
      .catch(() => setHealth({ status: "offline", device: "Bağlanılamadı", gpu_name: "Offline", current_model: "-" }));

    fetch("/api/models")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setModels(data);
        }
      })
      .catch(() => {});
  }, []);

  // Timer for inference duration
  useEffect(() => {
    if (!loading) return;
    const interval = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [loading]);

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      setPreviewUrl(URL.createObjectURL(selected));
      setError(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files?.[0];
    if (dropped && dropped.type.startsWith("image/")) {
      setFile(dropped);
      setPreviewUrl(URL.createObjectURL(dropped));
      setError(null);
    }
  };

  const clearFile = () => {
    setFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleCancel = async () => {
    if (loading) {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      try {
        await fetch("/api/cancel", { method: "POST" });
      } catch (e) {
        console.error("İptal isteği hatası:", e);
      }
      setLoading(false);
      setError("İşlem kullanıcı tarafından durduruldu.");
    } else {
      clearFile();
      setResult(null);
      setError(null);
    }
  };

  const handleProcess = async () => {
    if (!file) {
      setError("Lütfen bir grafik görseli seçin.");
      return;
    }

    setElapsedTime(0);
    setLoading(true);
    setError(null);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("max_tokens", maxTokens);
    formData.append("model_id", selectedModel);

    try {
      const response = await fetch("/api/predict", {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      if (!response.ok) {
        if (response.status === 499) {
          throw new Error("İşlem kullanıcı tarafından iptal edildi.");
        }
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Sunucu hatası: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      if (err.name === "AbortError") {
        setError("İşlem kullanıcı tarafından iptal edildi.");
      } else {
        setError(err.message || "İşlem sırasında bir hata oluştu.");
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  // Export handlers
  const handleDownloadExcel = async () => {
    if (!result) return;
    try {
      const res = await fetch("/api/export/excel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: result.title,
          columns: result.columns,
          rows: result.rows,
        }),
      });
      if (!res.ok) throw new Error("Excel dosyası oluşturulamadı.");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${result.title || "grafik_tablosu"}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("Excel indirme başarısız: " + e.message);
    }
  };

  const handleDownloadCsv = async () => {
    if (!result) return;
    try {
      const res = await fetch("/api/export/csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: result.title,
          columns: result.columns,
          rows: result.rows,
        }),
      });
      if (!res.ok) throw new Error("CSV dosyası oluşturulamadı.");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${result.title || "grafik_tablosu"}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("CSV indirme başarısız: " + e.message);
    }
  };

  const handleDownloadJson = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], {
      type: "application/json;charset=utf-8",
    });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${result.title || "grafik_verisi"}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Filter rows by search
  const filteredRows = result?.rows?.filter((row) =>
    row.some((val) => String(val).toLowerCase().includes(searchQuery.toLowerCase()))
  ) || [];

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col selection:bg-blue-500 selection:text-white">
      {/* Header */}
      <header className="border-b border-slate-800/80 bg-[#0d1322]/80 backdrop-blur sticky top-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <FileSpreadsheet className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-white">ChartToText</h1>
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
                  Çoklu Model Desteği
                </span>
              </div>
              <p className="text-xs text-slate-400">Yapay Zeka Destekli Grafik Tablo Çıkarıcı</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/50 text-xs">
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-slate-400">GPU:</span>
              <span className="text-slate-200 font-medium">{health.gpu_name || health.device}</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse ml-1" />
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto w-full px-6 py-8 flex-1 grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Upload & Settings (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {/* Upload Card */}
          <div className="bg-[#0f172a] rounded-2xl border border-slate-800 p-6 shadow-xl relative overflow-hidden">
            
            {/* Model Seçimi Dropdown */}
            <div className="mb-5 pb-5 border-b border-slate-800">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-2 mb-2">
                <Bot className="w-4 h-4 text-indigo-400" />
                Aktif Yapay Zeka Modeli
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 font-medium focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                {models.map((m) => (
                  <option key={m.id} value={m.id} disabled={!m.ready}>
                    {m.name} {!m.ready ? "(Yakında)" : ""}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-slate-500 mt-1.5">
                {models.find((m) => m.id === selectedModel)?.description || "Model seçimi"}
              </p>
            </div>

            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-3">
              <Upload className="w-4 h-4 text-blue-400" /> Grafik Görseli
            </h2>

            {!previewUrl ? (
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-700/80 hover:border-blue-500/60 rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-200 bg-slate-900/40 hover:bg-slate-900/80 group"
              >
                <div className="w-14 h-14 rounded-full bg-blue-500/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                  <Upload className="w-6 h-6 text-blue-400" />
                </div>
                <p className="text-sm font-medium text-slate-200 mb-1">
                  Görseli sürükleyin veya <span className="text-blue-400 underline">seçin</span>
                </p>
                <p className="text-xs text-slate-500">PNG, JPG, WEBP formatları desteklenir</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </div>
            ) : (
              <div className="relative rounded-xl overflow-hidden border border-slate-700 group bg-slate-950">
                <img
                  src={previewUrl}
                  alt="Önizleme"
                  className="w-full max-h-72 object-contain bg-slate-950"
                />
                <button
                  onClick={clearFile}
                  className="absolute top-3 right-3 p-1.5 rounded-lg bg-black/60 hover:bg-red-600 text-white transition-colors backdrop-blur"
                  title="Görseli Kaldır"
                >
                  <X className="w-4 h-4" />
                </button>
                <div className="p-3 bg-slate-900/90 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                  <span className="truncate max-w-[200px]">{file?.name}</span>
                  <span>{(file?.size / (1024 * 1024)).toFixed(2)} MB</span>
                </div>
              </div>
            )}

            {/* Token Slider */}
            <div className="mt-6 pt-5 border-t border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-blue-400" />
                  Maksimum Token Sınırı
                </label>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-bold">
                  {maxTokens}
                </span>
              </div>
              <input
                type="range"
                min="256"
                max="2048"
                step="64"
                value={maxTokens}
                onChange={(e) => setMaxTokens(Number(e.target.value))}
                className="w-full accent-blue-500 cursor-pointer"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                256 - 2048 arası ayarlanabilir. Geniş grafikler için 1024 - 1536 önerilir.
              </p>
            </div>

            {/* Butonlar: Tabloyu Çıkar ve İptal Et (Yan Yana, Her Zaman Görünür) */}
            <div className="mt-6 flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <button
                  onClick={handleProcess}
                  disabled={loading || !file}
                  className={`flex-1 py-3.5 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all duration-200 shadow-lg ${
                    loading
                      ? "bg-blue-600/40 cursor-not-allowed text-blue-200 border border-blue-500/30"
                      : !file
                      ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50"
                      : "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-blue-500/25 active:scale-[0.99] cursor-pointer"
                  }`}
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin text-white" />
                      <span>İşleniyor ({elapsedTime}s)...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 text-white" />
                      <span>Tabloyu Çıkar</span>
                    </>
                  )}
                </button>

                <button
                  onClick={handleCancel}
                  disabled={!loading && !file && !result}
                  className={`py-3.5 px-5 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all border shadow-lg ${
                    loading
                      ? "bg-rose-600 hover:bg-rose-500 text-white border-rose-500 shadow-rose-600/40 animate-pulse active:scale-95 cursor-pointer ring-2 ring-rose-400"
                      : file || result
                      ? "bg-slate-800/90 hover:bg-rose-600/20 text-slate-300 hover:text-rose-400 border-slate-700 hover:border-rose-500/40 cursor-pointer active:scale-95"
                      : "bg-slate-800/30 text-slate-600 border-slate-800/40 cursor-not-allowed"
                  }`}
                  title={loading ? "Model çıkarımını hemen durdur" : "Görseli ve sonuçları sıfırla"}
                >
                  <X className="w-4 h-4 stroke-[2.5]" />
                  <span>İptal Et</span>
                </button>
              </div>
            </div>
          </div>

          {/* Error message */}
          {error && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-start gap-3">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-red-200">Hata Oluştu</p>
                <p className="mt-0.5 text-red-300/90">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Output Data Studio (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          {result ? (
            <div className="bg-[#0f172a] rounded-2xl border border-slate-800 p-6 shadow-xl flex flex-col">
              {/* Metadata Badges */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mb-6">
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div className="text-[11px] text-slate-400 mb-0.5">Grafik Başlığı</div>
                  <div className="text-xs font-semibold text-slate-200 truncate" title={result.title}>
                    {result.title || "Tespit Edilemedi"}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div className="text-[11px] text-slate-400 mb-0.5">Kullanılan Model</div>
                  <div className="text-xs font-semibold text-indigo-400 truncate" title={result.used_model}>
                    {result.used_model || selectedModel}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div className="text-[11px] text-slate-400 mb-0.5">Satır Sayısı</div>
                  <div className="text-sm font-bold text-blue-400 font-mono">
                    {result.row_count} <span className="text-xs font-normal text-slate-500">satır</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div className="text-[11px] text-slate-400 mb-0.5">Sütun Sayısı</div>
                  <div className="text-sm font-bold text-emerald-400 font-mono">
                    {result.col_count} <span className="text-xs font-normal text-slate-500">sütun</span>
                  </div>
                </div>
              </div>

              {/* Tabs & Search */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800 pb-3 mb-4">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setActiveTab("table")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors ${
                      activeTab === "table"
                        ? "bg-blue-600 text-white"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                    }`}
                  >
                    <FileSpreadsheet className="w-3.5 h-3.5" /> Tablo Görünümü
                  </button>
                  <button
                    onClick={() => setActiveTab("json")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors ${
                      activeTab === "json"
                        ? "bg-blue-600 text-white"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                    }`}
                  >
                    <Code2 className="w-3.5 h-3.5" /> JSON
                  </button>
                  <button
                    onClick={() => setActiveTab("raw")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors ${
                      activeTab === "raw"
                        ? "bg-blue-600 text-white"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                    }`}
                  >
                    <FileText className="w-3.5 h-3.5" /> Ham Metin
                  </button>
                </div>

                {activeTab === "table" && (
                  <div className="relative w-full sm:w-48">
                    <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      placeholder="Tabloda ara..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700/80 rounded-lg pl-8 pr-3 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                )}
              </div>

              {/* Tab Contents */}
              <div className="flex-1 min-h-[340px]">
                {activeTab === "table" && (
                  <div className="overflow-x-auto rounded-xl border border-slate-800 max-h-[420px] overflow-y-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead className="bg-slate-900/90 text-slate-300 font-semibold sticky top-0 border-b border-slate-800 z-10 backdrop-blur">
                        <tr>
                          <th className="py-2.5 px-3 border-r border-slate-800/80 w-10 text-center text-slate-500">
                            #
                          </th>
                          {result.columns.map((col, idx) => (
                            <th key={idx} className="py-2.5 px-4 border-r border-slate-800/80 last:border-r-0">
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono">
                        {filteredRows.length > 0 ? (
                          filteredRows.map((row, rIdx) => (
                            <tr key={rIdx} className="hover:bg-slate-800/40 transition-colors">
                              <td className="py-2 px-3 border-r border-slate-800/80 text-center text-slate-500 font-sans">
                                {rIdx + 1}
                              </td>
                              {row.map((val, cIdx) => (
                                <td key={cIdx} className="py-2 px-4 border-r border-slate-800/80 last:border-r-0 text-slate-200">
                                  {val}
                                </td>
                              ))}
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={result.columns.length + 1} className="py-8 text-center text-slate-500">
                              Eşleşen satır bulunamadı.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}

                {activeTab === "json" && (
                  <div className="relative rounded-xl border border-slate-800 bg-slate-950 p-4 max-h-[420px] overflow-auto">
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(result, null, 2))}
                      className="absolute top-3 right-3 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs flex items-center gap-1"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? "Kopyalandı" : "Kopyala"}</span>
                    </button>
                    <pre className="text-xs font-mono text-emerald-400/90 whitespace-pre">
                      {JSON.stringify(result, null, 2)}
                    </pre>
                  </div>
                )}

                {activeTab === "raw" && (
                  <div className="relative rounded-xl border border-slate-800 bg-slate-950 p-4 max-h-[420px] overflow-auto">
                    <button
                      onClick={() => copyToClipboard(result.raw_text)}
                      className="absolute top-3 right-3 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs flex items-center gap-1"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? "Kopyalandı" : "Kopyala"}</span>
                    </button>
                    <pre className="text-xs font-mono text-slate-300 whitespace-pre-wrap">
                      {result.raw_text}
                    </pre>
                  </div>
                )}
              </div>

              {/* Bottom Export Bar */}
              <div className="mt-6 pt-5 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
                <span className="text-xs font-medium text-slate-400">Veriyi Dışa Aktar:</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleDownloadExcel}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-lg shadow-emerald-600/20 active:scale-95"
                  >
                    <FileSpreadsheet className="w-4 h-4" />
                    <span>Excel (.xlsx) İndir</span>
                  </button>

                  <button
                    onClick={handleDownloadCsv}
                    className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-lg shadow-blue-600/20 active:scale-95"
                  >
                    <Download className="w-4 h-4" />
                    <span>CSV (.csv) İndir</span>
                  </button>

                  <button
                    onClick={handleDownloadJson}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center gap-1.5 transition-all active:scale-95"
                  >
                    <Code2 className="w-4 h-4" />
                    <span>JSON İndir</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full min-h-[460px] rounded-2xl border-2 border-dashed border-slate-800 flex flex-col items-center justify-center p-8 text-center text-slate-500 bg-slate-900/20">
              <div className="w-16 h-16 rounded-2xl bg-slate-900 flex items-center justify-center mb-4 border border-slate-800">
                <Layers className="w-8 h-8 text-slate-600" />
              </div>
              <h3 className="text-sm font-semibold text-slate-300 mb-1">Tablo Çıktısı Bekleniyor</h3>
              <p className="text-xs text-slate-500 max-w-sm">
                Sol taraftan modelinizi ve grafiğinizi seçip "Tabloyu Çıkar" butonuna tıkladığınızda sonuçlar burada belirecektir.
              </p>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#0d1322]/50 text-slate-500 text-[11px] py-4 text-center">
        DePlot & Pix2Struct AI Vision Studio • Çoklu Model ve LoRA Desteği
      </footer>
    </div>
  );
}
