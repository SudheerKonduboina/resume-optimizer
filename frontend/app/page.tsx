"use client";

import { useMemo, useRef, useState } from "react";
import { 
  Menu, X, CheckCircle2, AlertCircle, Download, 
  FileText, BarChart3, Search, Layout, Target 
} from "lucide-react";

type StatusResp = {
  status: boolean;
  job_id: string;
  state: string;
  progress: number;
  message: string;
  error?: string | null;
};

const API = "http://localhost:8000";

function cx(...s: (string | false | undefined)[]) {
  return s.filter(Boolean).join(" ");
}

export default function Page() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [jd, setJd] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusResp | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const canSubmit = useMemo(() => !!file && !loading, [file, loading]);

  const acceptFile = (f: File | null | undefined) => {
    if (!f) return;
    const ok = /\.(pdf|docx)$/i.test(f.name);
    if (!ok) return alert("Only PDF or DOCX supported.");
    if (f.size > 10 * 1024 * 1024) return alert("File too large. Max 10MB.");
    setFile(f);
  };

  async function startAnalyze() {
    if (!file) return;
    setLoading(true);
    setResult(null);
    setStatus(null);

    const fd = new FormData();
    fd.append("resume", file);
    if (jd.trim()) fd.append("job_description", jd.trim());

    try {
      const res = await fetch(`${API}/api/analyze`, { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.message || "Upload failed");
      setJobId(data.job_id);
      pollStatus(data.job_id);
    } catch (err: any) {
      setLoading(false);
      alert(err.message);
    }
  }

  function pollStatus(id: string) {
    const timer = setInterval(async () => {
      try {
        const sres = await fetch(`${API}/api/status/${id}`);
        const sdata: StatusResp = await sres.json();
        setStatus(sdata);

        if (sdata.state === "done") {
          clearInterval(timer);
          const rres = await fetch(`${API}/api/result/${id}`);
          const rdata = await rres.json();
          setResult(rdata);
          setLoading(false);
        }
        if (sdata.state === "error") {
          clearInterval(timer);
          setLoading(false);
          alert(sdata.error || "Analysis failed");
        }
      } catch {
        clearInterval(timer);
        setLoading(false);
      }
    }, 800);
  }

  async function downloadPdf() {
    if (!jobId) return;
    const res = await fetch(`${API}/api/download/${jobId}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ATS_Report_${jobId}.pdf`;
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 selection:bg-indigo-100">
      {/* MOBILE RESPONSIVE HEADER */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200">
        <div className="mx-auto max-w-7xl px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-indigo-600 p-1.5 rounded-lg text-white">
              <Target size={22} strokeWidth={2.5} />
            </div>
            <span className="font-bold text-xl tracking-tight text-slate-800">ATS Optimizer</span>
          </div>
          
          <nav className="hidden md:flex gap-8 text-sm font-semibold text-slate-500">
            <a href="#tool" className="hover:text-indigo-600 transition">Analyzer</a>
            <a href="#results" className="hover:text-indigo-600 transition">Preview Results</a>
            <a href="#how" className="hover:text-indigo-600 transition">How it Works</a>
          </nav>

          <button className="md:hidden p-2 text-slate-600" onClick={() => setIsMenuOpen(!isMenuOpen)}>
            {isMenuOpen ? <X /> : <Menu />}
          </button>
        </div>
        {isMenuOpen && (
          <div className="md:hidden bg-white border-b border-slate-200 p-4 flex flex-col gap-4 font-medium animate-in slide-in-from-top-2">
            <a href="#tool" onClick={() => setIsMenuOpen(false)}>Analyzer</a>
            <a href="#results" onClick={() => setIsMenuOpen(false)}>Preview Results</a>
            <a href="#how" onClick={() => setIsMenuOpen(false)}>How it Works</a>
          </div>
        )}
      </header>

      {/* HERO & INPUT SECTION */}
      <section id="tool" className="py-12 lg:py-20 px-4">
        <div className="mx-auto max-w-7xl grid lg:grid-cols-2 gap-16 items-start">
          <div className="lg:sticky lg:top-32">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-bold uppercase tracking-wider mb-6">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
              </span>
              v2.0 Open-Source AI
            </div>
            <h1 className="text-4xl lg:text-6xl font-extrabold text-slate-900 leading-[1.1] mb-6">
              Optimize your resume for the <span className="text-indigo-600">ATS algorithm.</span>
            </h1>
            <p className="text-lg text-slate-600 leading-relaxed mb-8 max-w-xl">
              Upload your resume and the target job description. Our AI analyzes keyword density, 
              formatting integrity, and semantic relevance to boost your interview chances.
            </p>
            <div className="grid sm:grid-cols-2 gap-4">
              <FeatureItem icon={<Search size={18}/>} text="Keyword Gap Analysis" />
              <FeatureItem icon={<Layout size={18}/>} text="Formatting Check" />
              <FeatureItem icon={<Target size={18}/>} text="Semantic Matching" />
              <FeatureItem icon={<FileText size={18}/>} text="Downloadable PDF Report" />
            </div>
          </div>

          <div className="bg-white rounded-[2.5rem] shadow-2xl shadow-slate-200/60 p-6 lg:p-10 border border-slate-100">
            {/* UPLOAD ZONE */}
            <div 
              onDragOver={(e) => {e.preventDefault(); setDragActive(true);}}
              onDragLeave={() => setDragActive(false)}
              onDrop={(e) => {e.preventDefault(); setDragActive(false); acceptFile(e.dataTransfer.files?.[0]);}}
              onClick={() => inputRef.current?.click()}
              className={cx(
                "border-2 border-dashed rounded-3xl p-10 text-center transition-all cursor-pointer group",
                dragActive ? "border-indigo-500 bg-indigo-50/50" : "border-slate-200 bg-slate-50 hover:bg-white hover:border-slate-300"
              )}
            >
              <input ref={inputRef} type="file" className="hidden" onChange={(e) => acceptFile(e.target.files?.[0])} />
              <div className="bg-white w-14 h-14 rounded-2xl shadow-sm flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                <FileText className="text-indigo-600" />
              </div>
              <p className="font-bold text-slate-800 text-lg">{file ? file.name : "Upload Resume"}</p>
              <p className="text-sm text-slate-500 mt-1">PDF or DOCX (Max 10MB)</p>
            </div>

            <div className="mt-8">
              <label className="text-sm font-bold text-slate-700 ml-1 mb-2 block">Job Description (Target Role)</label>
              <textarea 
                className="w-full h-40 rounded-3xl border-slate-200 bg-slate-50 p-5 text-sm focus:ring-4 focus:ring-indigo-50 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-400"
                placeholder="Paste the job description to unlock side-by-side keyword matching..."
                value={jd}
                onChange={(e) => setJd(e.target.value)}
              />
            </div>

            <button 
              disabled={!canSubmit}
              onClick={startAnalyze}
              className={cx(
                "mt-8 w-full py-5 rounded-3xl font-bold text-white shadow-xl transition-all transform active:scale-[0.98] text-lg",
                canSubmit ? "bg-indigo-600 hover:bg-indigo-700 shadow-indigo-200" : "bg-slate-300 cursor-not-allowed"
              )}
            >
              {loading ? "AI is processing..." : "Analyze Compatibility"}
            </button>

            {status && (
              <div className="mt-8 p-6 bg-slate-900 rounded-3xl text-white">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-xs font-black uppercase tracking-widest text-indigo-400">{status.message}</span>
                  <span className="text-lg font-mono font-bold">{status.progress}%</span>
                </div>
                <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all duration-700 ease-out" style={{width: `${status.progress}%`}} />
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* RESULTS SECTION (Side-by-Side & Detailed Preview) */}
      <section id="results" className="py-16 bg-white border-y border-slate-200 px-4">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 mb-12">
            <div>
              <h2 className="text-4xl font-extrabold tracking-tight">Match Report</h2>
              <p className="text-slate-500 mt-2 text-lg">Real-time analysis of your resume vs industry standards.</p>
            </div>
            {result && (
              <button onClick={downloadPdf} className="flex items-center justify-center gap-3 bg-slate-900 text-white px-10 py-4 rounded-2xl font-bold hover:bg-slate-800 transition shadow-2xl hover:-translate-y-1">
                <Download size={20} /> Download PDF Report
              </button>
            )}
          </div>

          {!result ? (
            <div className="py-32 text-center border-4 border-dotted border-slate-100 rounded-[3rem] text-slate-300">
              <BarChart3 size={60} className="mx-auto mb-4 opacity-20" />
              <p className="text-xl font-medium">Results will generate here automatically</p>
            </div>
          ) : (
            <div className="space-y-10">
              {/* SCORE BREAKDOWN */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-indigo-600 p-8 rounded-[2.5rem] text-center shadow-xl shadow-indigo-100">
                  <div className="text-indigo-200 text-xs font-black uppercase tracking-widest mb-2">Overall Match</div>
                  <div className="text-6xl font-black text-white">{result.scores.total}</div>
                </div>
                <MetricCard title="Keywords" value={result.scores.breakdown.keywords} max={45} color="bg-cyan-500" />
                <MetricCard title="Formatting" value={result.scores.breakdown.formatting} max={25} color="bg-emerald-500" />
                <MetricCard title="Content" value={result.scores.breakdown.content} max={30} color="bg-amber-500" />
              </div>

              {/* REQUIREMENT: SIDE-BY-SIDE KEYWORD ANALYSIS */}
              <div className="grid lg:grid-cols-2 gap-8">
                <div className="bg-[#fdfdfd] border border-slate-100 rounded-[2.5rem] p-8 lg:p-10 shadow-sm">
                  <div className="flex items-center justify-between mb-8">
                    <h3 className="text-2xl font-bold flex items-center gap-3">
                      <div className="bg-emerald-100 p-2 rounded-xl text-emerald-600"><CheckCircle2 size={24}/></div>
                      Matching Skills
                    </h3>
                    <span className="text-sm font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full">
                      {result.keyword_analysis.present.length} Found
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2.5">
                    {result.keyword_analysis.present.length > 0 ? (
                      result.keyword_analysis.present.map((kw: string, i: number) => (
                        <span key={i} className="bg-white text-slate-700 px-4 py-2 rounded-2xl text-sm font-semibold border border-slate-200 shadow-sm">{kw}</span>
                      ))
                    ) : <p className="text-slate-400 italic">No direct keyword matches found.</p>}
                  </div>
                </div>

                <div className="bg-[#fdfdfd] border border-slate-100 rounded-[2.5rem] p-8 lg:p-10 shadow-sm">
                  <div className="flex items-center justify-between mb-8">
                    <h3 className="text-2xl font-bold flex items-center gap-3">
                      <div className="bg-rose-100 p-2 rounded-xl text-rose-600"><AlertCircle size={24}/></div>
                      Keyword Gaps
                    </h3>
                    <span className="text-sm font-bold text-rose-600 bg-rose-50 px-3 py-1 rounded-full">
                      {result.keyword_analysis.missing.length} Missing
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2.5">
                    {result.keyword_analysis.missing.length > 0 ? (
                      result.keyword_analysis.missing.map((kw: string, i: number) => (
                        <span key={i} className="bg-rose-50/50 text-rose-700 px-4 py-2 rounded-2xl text-sm font-semibold border border-rose-100">{kw}</span>
                      ))
                    ) : <p className="text-emerald-600 font-medium">Perfect! You have all the core keywords.</p>}
                  </div>
                </div>
              </div>

                            {/* SEMANTIC MATCH PREVIEW */}
              {Array.isArray(result.keyword_analysis.semantic_matches) &&
                result.keyword_analysis.semantic_matches.length > 0 && (
                <div className="bg-white border border-slate-100 rounded-[2.5rem] p-8 lg:p-10 shadow-sm">
                  <h3 className="text-2xl font-bold mb-8 flex items-center gap-3">
                    <div className="bg-indigo-100 p-2 rounded-xl text-indigo-600">
                      <Target size={24} />
                    </div>
                    Semantic Context Matches
                  </h3>

                  <div className="grid md:grid-cols-2 gap-4">
                    {result.keyword_analysis.semantic_matches.slice(0, 4).map((hit: any, i: number) => {
                      const scoreNum = Number(hit?.score);
                      const pct = Number.isFinite(scoreNum) ? Math.round(scoreNum * 100) : null;

                      return (
                        <div key={i} className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-bold text-indigo-600 text-sm uppercase">
                              {hit?.keyword || "—"}
                            </span>
                            <span className="text-[10px] font-black text-slate-400">
                              {pct === null ? "—" : `${pct}% Match`}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 italic line-clamp-2">
                            “{hit.best_line ? hit.best_line : "No matching resume line found"}”
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* AI RECOMMENDATIONS */}
              <div className="bg-slate-900 text-white rounded-[3rem] p-10 lg:p-16 shadow-2xl shadow-slate-300">
                <div className="max-w-3xl">
                  <h3 className="text-3xl font-bold mb-4">Strategic Recommendations</h3>
                  <p className="text-slate-400 mb-12">Our AI identified these high-impact changes to improve your ranking.</p>
                </div>
                <div className="grid md:grid-cols-2 gap-12">
                  {result.suggestions.items.map((item: any, i: number) => (
                    <div key={i} className="flex gap-6">
                      <div className="flex-shrink-0 w-12 h-12 bg-indigo-500/20 rounded-2xl flex items-center justify-center text-indigo-400 border border-indigo-500/30">
                        {item.type === 'formatting' ? <Layout size={24}/> : <CheckCircle2 size={24}/>}
                      </div>
                      <div>
                        <h4 className="text-xl font-bold mb-2">{item.title}</h4>
                        <p className="text-slate-400 text-sm leading-relaxed">{item.detail}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="py-24 px-4 bg-[#f8fafc]">
        <div className="mx-auto max-w-7xl text-center">
          <h2 className="text-4xl font-extrabold mb-16">The Optimization Process</h2>
          <div className="grid md:grid-cols-3 gap-12 relative">
            <div className="hidden lg:block absolute top-1/2 left-1/4 right-1/4 h-0.5 bg-slate-200 -translate-y-1/2 z-0"></div>
            <WorkStep num="01" title="Extract" desc="We parse your PDF/DOCX using open-source PyMuPDF to see what the ATS sees." />
            <WorkStep num="02" title="Analyze" desc="Sentence-Transformers calculate semantic similarity between your experience and the job." />
            <WorkStep num="03" title="Report" desc="Get a downloadable PDF with actionable keyword and formatting suggestions." />
          </div>
        </div>
      </section>

      <footer className="py-12 text-center text-slate-400 text-sm border-t border-slate-200 bg-white">
        <p>© 2024 Resume Optimizer. Built with FastAPI & Next.js. Open-source Tool.</p>
      </footer>
    </div>
  );
}

/* UI COMPONENTS */
function FeatureItem({ icon, text }: { icon: any; text: string }) {
  return (
    <div className="flex items-center gap-3 text-slate-700 font-medium">
      <div className="text-indigo-600">{icon}</div>
      <span>{text}</span>
    </div>
  );
}

function MetricCard({ title, value, max, color }: any) {
  const percentage = (value / max) * 100;
  return (
    <div className="bg-white p-6 rounded-[2.5rem] border border-slate-100 shadow-sm">
      <div className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">{title}</div>
      <div className="flex items-baseline gap-1 mb-4">
        <span className="text-4xl font-bold text-slate-800">{value}</span>
        <span className="text-slate-400 font-bold text-sm">/{max}</span>
      </div>
      <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
        <div className={cx("h-full transition-all duration-1000", color)} style={{width: `${percentage}%`}} />
      </div>
    </div>
  );
}

function WorkStep({ num, title, desc }: any) {
  return (
    <div className="relative z-10 p-10 rounded-[2.5rem] bg-white border border-slate-100 shadow-xl shadow-slate-200/40">
      <div className="w-14 h-14 bg-indigo-600 rounded-2xl text-white flex items-center justify-center font-black text-xl mx-auto mb-6 shadow-lg shadow-indigo-200">{num}</div>
      <h3 className="font-bold text-xl mb-3">{title}</h3>
      <p className="text-slate-500 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}