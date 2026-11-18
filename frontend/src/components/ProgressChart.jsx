import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { TrendingUp, TrendingDown } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from "recharts";
import { api, errMsg, fmtDateTime } from "@/lib/api";
import { Card } from "@/components/Common";

const TYPES = [["batting", "Batting"], ["bowling", "Bowling"]];

const Stat = ({ label, value, testid, children }) => (
  <div className="rounded-lg bg-white/5 px-4 py-3"><div className="text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
    <div className="text-2xl font-display font-bold mt-0.5 flex items-center gap-1.5" data-testid={testid}>{value}{children}</div></div>
);

const Change = ({ d }) => {
  if (d == null) return <Stat label="Change" value="—" testid="progress-change" />;
  const Icon = d > 0 ? TrendingUp : d < 0 ? TrendingDown : null;
  const c = d > 0 ? "text-[#10B981]" : d < 0 ? "text-red-400" : "text-slate-300";
  return <Stat label="Change" value={<span className={c}>{d > 0 ? "+" : ""}{d}</span>} testid="progress-change">{Icon ? <Icon size={18} className={c} /> : <span className="text-xs font-normal text-slate-400">no change</span>}</Stat>;
};

const Dot = ({ cx, cy, payload, index, onOpen }) => cx == null || payload.value == null ? null :
  <circle key={index} cx={cx} cy={cy} r={6} stroke="#10B981" strokeWidth={2} fill={payload.status === "provisional" ? "#0B132B" : "#10B981"} style={{ cursor: "pointer" }}
    onClick={(e) => { e.stopPropagation(); onOpen(payload.job); }} data-testid={`progress-point-${index + 1}`} />;

export const ProgressChart = ({ defaultType = "batting" }) => {
  const nav = useNavigate();
  const [type, setType] = useState(defaultType);
  const [d, setD] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => { setType(defaultType); }, [defaultType]);
  useEffect(() => { setD(null); setErr(null); api.get("/timeline", { params: { type } }).then(({ data }) => setD(data)).catch((e) => setErr(errMsg(e))); }, [type]);
  const rows = (d?.reports || []).map((r, i) => ({ n: i + 1, tick: `#${i + 1}`, date: fmtDateTime(r.created_at), job: r.job_id, value: r.technique_score?.value ?? null, status: r.technique_score?.status }));
  const scored = rows.filter((r) => r.value != null);
  const latest = scored.at(-1)?.value, best = scored.length ? Math.max(...scored.map((r) => r.value)) : null;
  const change = scored.length > 1 ? Math.round((latest - scored[0].value) * 10) / 10 : null;
  const go = (job) => job && nav(`/app/analyses/${job}`);
  const open = (st) => { const i = Number(st?.activeTooltipIndex ?? st?.activeIndex); go((st?.activePayload?.[0]?.payload || rows[i])?.job); };
  return (
    <Card className="mb-8" data-testid="progress-chart-card">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div><h2 className="text-lg font-semibold">Technique score progress</h2><p className="text-xs text-slate-400">Every completed report, oldest (#1) to newest. Change is latest vs first. Tap a point to open that report.</p></div>
        <div className="flex gap-1 rounded-full bg-white/5 p-1">{TYPES.map(([v, l]) => <button key={v} onClick={() => setType(v)} data-testid={`progress-type-${v}`}
          className={`px-4 py-1.5 rounded-full text-sm transition-colors ${type === v ? "bg-[#10B981] text-[#0B132B] font-semibold" : "text-slate-300 hover:text-white"}`}>{l}</button>)}</div>
      </div>
      {err ? <p className="text-sm text-slate-400" data-testid="progress-chart-locked">{err}</p> : !d ? <p className="text-sm text-slate-400">Loading…</p> :
        !rows.length ? <p className="text-sm text-slate-400" data-testid="progress-chart-empty">No {type} reports yet. Your first completed {type} analysis becomes your baseline.</p> : <>
          <div className="grid grid-cols-3 gap-3 mb-4"><Stat label="Latest" value={latest ?? "—"} testid="progress-latest" /><Stat label="Best" value={best ?? "—"} testid="progress-best" /><Change d={change} /></div>
          <div className="h-64" data-testid="progress-chart"><ResponsiveContainer><AreaChart data={rows} onClick={open} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
            <defs><linearGradient id="pgFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#10B981" stopOpacity={0.35} /><stop offset="100%" stopColor="#10B981" stopOpacity={0} /></linearGradient></defs>
            <CartesianGrid stroke="#1e293b" vertical={false} /><XAxis dataKey="tick" stroke="#64748b" fontSize={11} tickLine={false} /><YAxis domain={[0, 100]} stroke="#64748b" fontSize={11} tickLine={false} />
            {best != null && <ReferenceLine y={best} stroke="#F59E0B" strokeDasharray="4 4" label={{ value: "Best", fill: "#F59E0B", fontSize: 10, position: "insideTopRight" }} />}
            <Tooltip contentStyle={{ background: "#1C2541", border: "none", borderRadius: 8 }} labelFormatter={(l, p) => `Report ${l} · ${p?.[0]?.payload?.date ?? ""}`}
              formatter={(v, n, p) => [v == null ? "No score" : p.payload.status === "provisional" ? `${v} (provisional)` : v, "Technique score"]} />
            <Area type="monotone" dataKey="value" stroke="#10B981" strokeWidth={2.5} fill="url(#pgFill)" connectNulls dot={<Dot onOpen={go} />} activeDot={{ r: 8, style: { cursor: "pointer" } }} isAnimationActive />
          </AreaChart></ResponsiveContainer></div>
          <p className="text-[11px] text-slate-500 mt-2">{d.baseline ? "Baseline only — add another analysis to see change over time." : "Hollow dots are provisional scores (fewer measurements). Scores depend on filming too, so keep the same camera angle for fair comparisons."}</p>
        </>}
    </Card>
  );
};
