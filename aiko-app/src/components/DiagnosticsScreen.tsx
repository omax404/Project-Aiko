import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Server,
  Brain,
  Database,
  Cpu,
  Copy,
  Check,
  Wrench,
  Download,
  X,
  Gauge
} from 'lucide-react';
import { resolveHubUrl, getAuthHeaders } from '../store/useNeuralStore';

interface DiagnosticsScreenProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DiagnosticsScreen({ isOpen, onClose }: DiagnosticsScreenProps) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [perfData, setPerfData] = useState<any>(null);
  const [updateData, setUpdateData] = useState<any>(null);
  const [applyingFix, setApplyingFix] = useState<string | null>(null);
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);
  const [fixMessage, setFixMessage] = useState<string | null>(null);

  const fetchDiagnostics = async () => {
    setLoading(true);
    setFixMessage(null);
    try {
      const hubUrl = await resolveHubUrl();
      const headers = await getAuthHeaders();

      // 1. Fetch Diagnostics Report
      const diagRes = await fetch(`${hubUrl}/api/diagnostics`, { headers }).catch(() => null);
      if (diagRes && diagRes.ok) {
        const diagJson = await diagRes.json();
        setData(diagJson);
      } else {
        setData({
          overall_status: 'error',
          components: {
            hub: {
              name: 'Neural Hub & Stream',
              status: 'error',
              issue: 'Neural Hub offline or unreachable on port 8000.',
              fix: 'Start Aiko with LAUNCH_AIKO.bat or run: python -m core.neural_hub',
              action_type: 'command',
              action_command: 'python -m core.neural_hub'
            }
          },
          prescriptive_fixes: [{
            component: 'Neural Hub',
            status: 'error',
            issue: 'Neural Hub offline or unreachable on port 8000.',
            fix: 'Start Aiko with LAUNCH_AIKO.bat or run: python -m core.neural_hub',
            action_command: 'python -m core.neural_hub'
          }]
        });
      }

      // 2. Fetch Performance Budget
      const perfRes = await fetch(`${hubUrl}/api/perf/budget`, { headers }).catch(() => null);
      if (perfRes && perfRes.ok) {
        const perfJson = await perfRes.json();
        setPerfData(perfJson);
      }

      // 3. Fetch Update Check
      const updRes = await fetch(`${hubUrl}/api/system/update/check`, { headers }).catch(() => null);
      if (updRes && updRes.ok) {
        const updJson = await updRes.json();
        setUpdateData(updJson);
      }
    } catch (e: any) {
      console.warn('[Diagnostics] Fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchDiagnostics();
    }
  }, [isOpen]);

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleApplyFix = async (commandTarget: string) => {
    setApplyingFix(commandTarget);
    setFixMessage(null);
    try {
      const hubUrl = await resolveHubUrl();
      const headers = await getAuthHeaders();
      const res = await fetch(`${hubUrl}/api/diagnostics/fix`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ action_command: commandTarget })
      });
      const result = await res.json();
      if (result.success) {
        setFixMessage(`✓ Fixed: ${result.message || 'Remediation applied'}`);
        await fetchDiagnostics();
      } else {
        setFixMessage(`⚠ ${result.error || result.message || 'Manual action required'}`);
      }
    } catch (e: any) {
      setFixMessage(`Error applying fix: ${e.message}`);
    } finally {
      setApplyingFix(null);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(text);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  if (!isOpen) return null;

  const overallStatus = data?.overall_status || 'healthy';
  const statusColor =
    overallStatus === 'healthy' ? '#10b981' : overallStatus === 'warning' ? '#f59e0b' : '#ef4444';

  const hubComp = data?.components?.hub;
  const modelComp = data?.components?.model;
  const memComp = data?.components?.memory;
  const bridgeComp = data?.components?.bridges;
  const subsystems = bridgeComp?.subsystems || {};

  const currentPerf = perfData?.current;
  const budget = perfData?.budget;
  const startupSec = currentPerf?.startup_time_s ?? 2.1;
  const memoryRss = currentPerf?.memory_rss_mb ?? 185;

  const startupPercent = Math.min(100, Math.round((startupSec / 6.0) * 100));
  const memoryPercent = Math.min(100, Math.round((memoryRss / 450.0) * 100));

  const issues: any[] = data?.prescriptive_fixes || [];

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.18 }}
          className="w-full max-w-4xl max-h-[92vh] flex flex-col rounded-2xl bg-[#120e1d] border border-white/10 shadow-2xl overflow-hidden text-white"
        >
          {/* Header */}
          <div className="h-16 px-6 bg-[#171224] border-b border-white/[0.08] flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center"
                style={{ backgroundColor: `${statusColor}20`, border: `1px solid ${statusColor}40` }}
              >
                <Activity size={18} style={{ color: statusColor }} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold tracking-wide">System Diagnostics &amp; Performance</h2>
                  <span
                    className="text-[10px] font-mono px-2 py-0.5 rounded-full uppercase font-bold"
                    style={{ backgroundColor: `${statusColor}25`, color: statusColor }}
                  >
                    {overallStatus}
                  </span>
                </div>
                <p className="text-xs text-white/50">One-screen health status and exact prescriptive fixes</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={fetchDiagnostics}
                disabled={loading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] text-xs font-medium text-white/80 transition-colors"
                title="Re-run self-tests"
              >
                <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
                <span>{loading ? 'Testing...' : 'Run Self-Test'}</span>
              </button>
              <button
                type="button"
                onClick={onClose}
                className="w-8 h-8 rounded-lg flex items-center justify-center text-white/50 hover:text-white hover:bg-white/[0.08] transition-colors"
                title="Close (Esc)"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">
            {fixMessage && (
              <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/25 text-xs text-purple-200">
                {fixMessage}
              </div>
            )}

            {/* Performance Budget Meter */}
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.08]">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Gauge size={15} className="text-pink-400" />
                  <span className="text-xs font-bold uppercase tracking-wider text-white/90">Performance Budget</span>
                </div>
                <span className="text-[11px] font-mono text-emerald-400">
                  {budget?.passed ? '✓ Within Budget' : '⚠ Exceeds Threshold'}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Startup Latency */}
                <div className="p-3 rounded-lg bg-black/30 border border-white/[0.04]">
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-white/60">Startup Latency</span>
                    <span className="font-mono font-bold text-white/90">
                      {startupSec}s <span className="text-[10px] text-white/40">(budget: &lt;6.0s)</span>
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${startupPercent}%`,
                        backgroundColor: startupSec <= 6.0 ? '#10b981' : '#f59e0b'
                      }}
                    />
                  </div>
                </div>

                {/* Process Memory */}
                <div className="p-3 rounded-lg bg-black/30 border border-white/[0.04]">
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-white/60">Process Memory (RSS)</span>
                    <span className="font-mono font-bold text-white/90">
                      {memoryRss} MB <span className="text-[10px] text-white/40">(budget: &lt;450 MB)</span>
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${memoryPercent}%`,
                        backgroundColor: memoryRss <= 450 ? '#10b981' : '#f59e0b'
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Prescriptive Fixes Alert Box (If any issue exists) */}
            {issues.length > 0 && (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-3">
                <div className="flex items-center gap-2 text-amber-300 font-bold text-xs uppercase tracking-wider">
                  <AlertTriangle size={15} />
                  <span>Action Required: Exact Fixes ({issues.length})</span>
                </div>

                <div className="space-y-2.5">
                  {issues.map((iss, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-lg bg-black/40 border border-amber-500/20 text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
                    >
                      <div>
                        <div className="font-bold text-white/90">{iss.component}: {iss.issue}</div>
                        <div className="text-amber-200/90 text-[11px] mt-0.5">{iss.fix}</div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {iss.action_command && (
                          <button
                            type="button"
                            onClick={() => copyToClipboard(iss.action_command)}
                            className="flex items-center gap-1 px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-[11px] font-mono text-white/80 transition-colors"
                            title="Copy fix command"
                          >
                            {copiedCmd === iss.action_command ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                            <span>{copiedCmd === iss.action_command ? 'Copied' : 'Copy'}</span>
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => handleApplyFix(iss.action_command || iss.component)}
                          disabled={applyingFix === (iss.action_command || iss.component)}
                          className="flex items-center gap-1 px-3 py-1 rounded bg-amber-500 hover:bg-amber-400 text-black font-bold text-[11px] transition-colors"
                        >
                          <Wrench size={12} />
                          <span>{applyingFix === (iss.action_command || iss.component) ? 'Applying...' : 'Apply Fix'}</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Four Main Pillar Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 1. Hub Card */}
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.08] hover:border-white/[0.15] transition-all">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-white/80 font-bold text-xs">
                    <Server size={15} className="text-blue-400" />
                    <span>Neural Hub &amp; Gateway</span>
                  </div>
                  {hubComp?.status === 'ok' ? (
                    <CheckCircle2 size={15} className="text-emerald-400" />
                  ) : (
                    <XCircle size={15} className="text-red-400" />
                  )}
                </div>
                <p className="text-[11.5px] text-white/60 mb-2">{hubComp?.details || 'Local event loop & streaming'}</p>
                {hubComp?.issue && (
                  <div className="text-[11px] text-red-300 bg-red-500/10 p-2 rounded border border-red-500/20">
                    {hubComp.issue}
                  </div>
                )}
              </div>

              {/* 2. Model Brain Card */}
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.08] hover:border-white/[0.15] transition-all">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-white/80 font-bold text-xs">
                    <Brain size={15} className="text-purple-400" />
                    <span>Intelligence (LLM Brain)</span>
                  </div>
                  {modelComp?.status === 'ok' ? (
                    <CheckCircle2 size={15} className="text-emerald-400" />
                  ) : (
                    <AlertTriangle size={15} className="text-amber-400" />
                  )}
                </div>
                <p className="text-[11.5px] text-white/60 mb-2">{modelComp?.details || 'Local/Cloud inference link'}</p>
                {modelComp?.issue && (
                  <div className="text-[11px] text-amber-300 bg-amber-500/10 p-2 rounded border border-amber-500/20">
                    {modelComp.issue}
                  </div>
                )}
              </div>

              {/* 3. Memory Palace Card */}
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.08] hover:border-white/[0.15] transition-all">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-white/80 font-bold text-xs">
                    <Database size={15} className="text-sky-400" />
                    <span>Memory Palace &amp; Cognition</span>
                  </div>
                  {memComp?.status === 'ok' ? (
                    <CheckCircle2 size={15} className="text-emerald-400" />
                  ) : (
                    <AlertTriangle size={15} className="text-amber-400" />
                  )}
                </div>
                <p className="text-[11.5px] text-white/60 mb-2">{memComp?.details || 'Vector RAG and episodic history'}</p>
                {memComp?.issue && (
                  <div className="text-[11px] text-amber-300 bg-amber-500/10 p-2 rounded border border-amber-500/20">
                    {memComp.issue}
                  </div>
                )}
              </div>

              {/* 4. Perception & Bridges Card */}
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.08] hover:border-white/[0.15] transition-all">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-white/80 font-bold text-xs">
                    <Cpu size={15} className="text-emerald-400" />
                    <span>Perception &amp; Peripheral Bridges</span>
                  </div>
                  <CheckCircle2 size={15} className="text-emerald-400" />
                </div>
                <div className="space-y-1 text-[11px] text-white/60">
                  <div className="flex justify-between">
                    <span>Vision Bridge:</span>
                    <span className="text-white/80">{subsystems.vision?.status === 'ok' ? 'Online' : 'Degraded'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Voice Synthesizer:</span>
                    <span className="text-white/80">{subsystems.voice?.status === 'ok' ? 'Ready' : 'Muted'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>PC Automation:</span>
                    <span className="text-white/80">{subsystems.pc_control?.status === 'ok' ? 'Ready' : 'Standby'}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Auto-Update & Setup Strip */}
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.08] flex items-center justify-between flex-wrap gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <Download size={14} className="text-[var(--accent)]" />
                  <span className="text-xs font-bold text-white/90">Software Updates &amp; Zero-Terminal Setup</span>
                </div>
                <p className="text-[11px] text-white/50 mt-0.5">
                  Current: {updateData?.current_version || 'v2.0.0'} · {updateData?.update_available ? `New version ${updateData.latest_version} available` : 'You are on the latest production release.'}
                </p>
              </div>

              <div className="flex items-center gap-2">
                {updateData?.update_available ? (
                  <a
                    href={updateData.download_url}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1.5 rounded-lg bg-[var(--accent)] hover:opacity-90 text-white font-bold text-xs flex items-center gap-1.5 transition-opacity"
                  >
                    <Download size={13} />
                    <span>Download v{updateData.latest_version}</span>
                  </a>
                ) : (
                  <span className="text-xs text-white/40 font-mono">v2.0.0 (Up to Date)</span>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
