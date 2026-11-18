import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Search, Trophy, Copy, UserCheck, UserX, IndianRupee, KeyRound, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, errMsg, fmtDate, inr } from "@/lib/api";
import { Card, Badge, statusTone } from "@/components/Common";

const copy = (t) => { navigator.clipboard?.writeText(t); toast.success("Copied."); };

export const JoinAcademy = ({ onJoined }) => {
  const [code, setCode] = useState("");
  const [found, setFound] = useState(null);
  const [reqs, setReqs] = useState([]);
  const loadReqs = useCallback(() => api.get("/academy-requests/mine").then(({ data }) => setReqs(data)).catch(() => {}), []);
  useEffect(() => { loadReqs(); }, [loadReqs]);
  const search = async (e) => { e.preventDefault(); setFound(null); try { setFound((await api.get("/academies-lookup", { params: { code } })).data); } catch (er) { toast.error(errMsg(er)); } };
  const join = async () => { try { const { data } = await api.post("/academies-join", { code }); toast.success(`Request sent to ${data.academy}. You'll get an email once they accept.`); setFound(null); setCode(""); loadReqs(); onJoined?.(); } catch (e) { toast.error(errMsg(e)); } };
  return (
    <Card className="mb-6 max-w-2xl" data-testid="join-academy-card">
      <h3 className="font-semibold mb-1 flex items-center gap-2"><KeyRound size={16} className="text-[#00B4D8]" />Join your academy</h3>
      <p className="text-xs text-slate-400 mb-3">Enter the 6-character code your academy gave you. Academies are private — only the exact code finds one.</p>
      <form onSubmit={search} className="flex gap-2"><Input placeholder="Academy code e.g. K7M2QX" value={code} maxLength={8} onChange={(e) => setCode(e.target.value.toUpperCase())} className="font-mono tracking-widest" data-testid="academy-code-input" />
        <Button type="submit" disabled={code.length < 6} data-testid="academy-code-search-btn"><Search size={15} className="mr-1" />Find</Button></form>
      {found && <div className="mt-4 rounded-lg border border-white/10 p-4 flex flex-wrap justify-between items-center gap-3" data-testid="academy-found">
        <div><div className="font-semibold">{found.name}</div><div className="text-xs text-slate-400">{found.city}{found.description ? ` · ${found.description}` : ""}</div></div>
        {found.is_member ? <Badge tone="green">You're a member</Badge> : found.request_pending ? <Badge tone="amber">Request pending</Badge> :
          <Button onClick={join} data-testid="academy-join-btn">Request to join</Button>}</div>}
      {reqs.length > 0 && <div className="mt-4 space-y-1">{reqs.map((r) => <div key={r.id} className="flex justify-between text-sm" data-testid={`my-request-${r.id}`}><span>{r.academy_name}</span><Badge tone={r.status === "approved" ? "green" : r.status === "pending" ? "amber" : "red"}>{r.status}</Badge></div>)}</div>}
    </Card>
  );
};

export const AcademyCodeCard = ({ aid }) => {
  const [e, setE] = useState(null);
  useEffect(() => { api.get(`/academies/${aid}/earnings`).then(({ data }) => setE(data)).catch(() => {}); }, [aid]);
  if (!e) return null;
  const link = `${window.location.origin}/signup?ref=${e.code}`;
  const c = e.commission || {};
  const rule = c.mode === "fixed_per_student" ? `${inr(c.value)} per paying student (once)` : c.mode === "percent_first" ? `${c.value}% of a student's first payment` : `${c.value}% of every payment`;
  return (
    <div className="grid md:grid-cols-2 gap-5">
      <Card data-testid="academy-code-card"><h3 className="font-semibold mb-2">Academy code</h3>
        <div className="flex items-center gap-3"><span className="font-mono text-3xl tracking-[0.3em] text-[#10B981]" data-testid="academy-code">{e.code}</span><Button size="icon" variant="ghost" onClick={() => copy(e.code)} aria-label="Copy code" data-testid="copy-code-btn"><Copy size={15} /></Button></div>
        <p className="text-xs text-slate-400 mt-2">Players enter this code to request to join. You approve each request.</p>
        <div className="flex gap-2 mt-3"><Input readOnly value={link} className="text-xs" data-testid="referral-link" /><Button size="sm" variant="secondary" onClick={() => copy(link)} data-testid="copy-referral-btn">Copy</Button></div>
        <p className="text-xs text-slate-500 mt-1">Referral sign-up link — new players who sign up with it are credited to your academy.</p></Card>
      <Card data-testid="academy-earnings-card"><h3 className="font-semibold mb-2 flex items-center gap-2"><IndianRupee size={16} />Referral commission</h3>
        <p className="text-xs text-slate-400 mb-3">Current rule: {rule}. Set by CricAnalyze; payouts are made by our team.</p>
        <div className="grid grid-cols-3 gap-3 text-center">{[["Referred", e.referred_students], ["Pending", inr(e.pending_inr)], ["Paid", inr(e.paid_inr)]].map(([l, v]) =>
          <div key={l} className="rounded-lg bg-white/5 p-3"><div className="text-xs text-slate-400">{l}</div><div className="font-bold text-lg" data-testid={`earnings-${l.toLowerCase()}`}>{v}</div></div>)}</div>
        <div className="max-h-40 overflow-y-auto mt-3">{e.rows.map((r) => <div key={r.id} className="flex justify-between text-xs border-b border-white/5 py-1.5"><span>{r.student_name} · {r.plan_name} · {fmtDate(r.created_at)}</span><span>{inr(r.amount_inr)} <Badge tone={statusTone(r.status === "pending" ? "queued" : r.status)}>{r.status}</Badge></span></div>)}</div></Card>
    </div>
  );
};

export const JoinRequests = ({ aid, onChange }) => {
  const [rows, setRows] = useState(null);
  const load = useCallback(() => api.get(`/academies/${aid}/requests`).then(({ data }) => setRows(data)).catch(() => setRows([])), [aid]);
  useEffect(() => { load(); }, [load]);
  const decide = async (r, approve) => { try { await api.post(`/academies/${aid}/requests/${r.id}`, { approve }); toast.success(approve ? `${r.full_name} added.` : "Request declined."); load(); onChange?.(); } catch (e) { toast.error(errMsg(e)); } };
  if (!rows?.length) return null;
  return (
    <Card data-testid="join-requests-card"><h3 className="font-semibold mb-3">Join requests ({rows.length})</h3>
      {rows.map((r) => <div key={r.id} className="flex flex-wrap justify-between items-center gap-2 py-2 border-b border-white/5" data-testid={`join-request-${r.id}`}>
        <div className="text-sm"><b>{r.full_name}</b> <span className="text-slate-400">{r.email}{r.playing_role ? ` · ${r.playing_role}` : ""} · {fmtDate(r.created_at)}</span></div>
        <div className="flex gap-2"><Button size="sm" onClick={() => decide(r, true)} data-testid={`approve-request-${r.id}`}><UserCheck size={14} className="mr-1" />Accept</Button>
          <Button size="sm" variant="ghost" onClick={() => decide(r, false)} data-testid={`reject-request-${r.id}`}><UserX size={14} className="mr-1" />Decline</Button></div></div>)}
    </Card>
  );
};

export const Leaderboard = ({ aid }) => {
  const [type, setType] = useState("batting");
  const [rows, setRows] = useState(null);
  useEffect(() => { setRows(null); api.get(`/academies/${aid}/leaderboard`, { params: { type } }).then(({ data }) => setRows(data)).catch(() => setRows([])); }, [aid, type]);
  return (
    <Card data-testid="academy-leaderboard">
      <div className="flex flex-wrap justify-between items-center gap-2 mb-3"><h3 className="font-semibold flex items-center gap-2"><Trophy size={16} className="text-amber-300" />Leaderboard</h3>
        <div className="flex rounded-lg border border-white/10 p-1">{["batting", "bowling"].map((t) => <button key={t} onClick={() => setType(t)} data-testid={`leaderboard-${t}`} className={`px-3 py-1 text-sm rounded-md capitalize ${type === t ? "bg-[#00B4D8] text-[#0B132B]" : "text-slate-300"}`}>{t}</button>)}</div></div>
      <p className="text-xs text-slate-500 mb-3">Ranked by each player's latest {type} technique score. Provisional scores are marked.</p>
      {rows === null ? <p className="text-sm text-slate-400">Loading…</p> : !rows.length ? <p className="text-sm text-slate-500" data-testid="leaderboard-empty">No scored {type} analyses yet.</p> :
        rows.map((r) => <div key={r.user_id} className="flex items-center justify-between py-2 border-b border-white/5" data-testid={`leaderboard-row-${r.rank}`}>
          <div className="flex items-center gap-3"><span className={`w-7 h-7 grid place-items-center rounded-full text-xs font-bold ${r.rank === 1 ? "bg-amber-400 text-[#0B132B]" : r.rank === 2 ? "bg-slate-300 text-[#0B132B]" : r.rank === 3 ? "bg-amber-700 text-white" : "bg-white/10"}`}>{r.rank}</span>
            <div><div className="text-sm font-medium">{r.name}</div><div className="text-[11px] text-slate-500">{fmtDate(r.analysed_at)}</div></div></div>
          <div className="text-right">{r.job_id ? <a href={`/app/analyses/${r.job_id}`} className="font-bold text-lg hover:text-[#00B4D8]">{r.score}</a> : <span className="font-bold text-lg">{r.score}</span>}<span className="text-xs text-slate-500">/100</span>
            {r.provisional && <div className="text-[10px] text-amber-300">provisional</div>}</div></div>)}
    </Card>
  );
};

export const NicknameEdit = ({ aid, m, onSaved }) => {
  const [edit, setEdit] = useState(false);
  const [v, setV] = useState(m.nickname || "");
  const save = async () => { try { await api.patch(`/academies/${aid}/members/${m.user_id}/nickname`, { nickname: v }); setEdit(false); onSaved?.(); } catch (e) { toast.error(errMsg(e)); } };
  if (!edit) return <button onClick={() => setEdit(true)} className="text-xs text-slate-400 hover:text-white flex items-center gap-1" data-testid={`nickname-edit-${m.user_id}`}><Pencil size={11} />{m.nickname || "Add nickname"}</button>;
  return <span className="flex gap-1"><Input value={v} maxLength={40} onChange={(e) => setV(e.target.value)} className="h-7 w-28 text-xs" data-testid={`nickname-input-${m.user_id}`} />
    <Button size="sm" className="h-7" onClick={save} data-testid={`nickname-save-${m.user_id}`}>Save</Button></span>;
};
