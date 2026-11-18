import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Flag } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { api, errMsg, fmtDate } from "@/lib/api";
import { Card, Badge } from "@/components/Common";

const REASONS = [["harassment", "Harassment or bullying"], ["inappropriate", "Inappropriate messages or content"], ["fake", "Fake or impersonated coach"],
  ["payment", "Asked for money outside CricAnalyze"], ["privacy", "Misused my videos or data"], ["other", "Something else"]];
const ACADEMY = "__academy__";

export const ReportCoachButton = ({ aid }) => {
  const [open, setOpen] = useState(false);
  const [staff, setStaff] = useState([]);
  const [f, setF] = useState({ target: ACADEMY, reason: "", details: "" });
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (open) api.get(`/academies/${aid}/staff`).then(({ data }) => setStaff(data)).catch(() => setStaff([])); }, [open, aid]);
  const submit = async () => {
    setBusy(true);
    try {
      await api.post("/abuse-reports", { academy_id: aid, target_user_id: f.target === ACADEMY ? null : f.target, reason: f.reason, details: f.details });
      toast.success("Report sent. Our team will review it."); setOpen(false); setF({ target: ACADEMY, reason: "", details: "" });
    } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  return (<>
    <Button size="sm" variant="ghost" className="text-red-300 hover:text-red-200" onClick={() => setOpen(true)} data-testid="report-coach-btn"><Flag size={14} className="mr-1" />Report a coach</Button>
    <Dialog open={open} onOpenChange={setOpen}><DialogContent data-testid="report-coach-dialog"><DialogHeader><DialogTitle>Report a coach or academy</DialogTitle></DialogHeader>
      <p className="text-sm text-slate-400">Reports go privately to the CricAnalyze team. The coach is not told who reported them.</p>
      <Select value={f.target} onValueChange={(v) => setF({ ...f, target: v })}><SelectTrigger data-testid="report-target-select"><SelectValue /></SelectTrigger>
        <SelectContent><SelectItem value={ACADEMY}>The academy itself</SelectItem>{staff.map((s) => <SelectItem key={s.user_id} value={s.user_id}>{s.name} · {s.role === "academy_admin" ? "academy admin" : "coach"}</SelectItem>)}</SelectContent></Select>
      <Select value={f.reason} onValueChange={(v) => setF({ ...f, reason: v })}><SelectTrigger data-testid="report-reason-select"><SelectValue placeholder="Reason" /></SelectTrigger>
        <SelectContent>{REASONS.map(([v, l]) => <SelectItem key={v} value={v}>{l}</SelectItem>)}</SelectContent></Select>
      <Textarea placeholder="What happened? (at least 10 characters)" value={f.details} onChange={(e) => setF({ ...f, details: e.target.value })} maxLength={2000} data-testid="report-details-input" />
      <Button onClick={submit} disabled={busy || !f.reason || f.details.trim().length < 10} className="bg-red-500 hover:bg-red-600 text-white" data-testid="report-submit-btn">{busy ? "Sending…" : "Send report"}</Button>
    </DialogContent></Dialog>
  </>);
};

export const AbuseReportsAdmin = () => {
  const [rows, setRows] = useState(null);
  const [status, setStatus] = useState("open");
  const load = useCallback(() => api.get("/admin/abuse-reports", { params: { status: status === "all" ? undefined : status } }).then(({ data }) => setRows(data)).catch((e) => toast.error(errMsg(e))), [status]);
  useEffect(() => { load(); }, [load]);
  const act = async (id, s) => { try { await api.post(`/admin/abuse-reports/${id}`, { status: s }); toast.success(`Marked ${s}.`); load(); } catch (e) { toast.error(errMsg(e)); } };
  return (<div className="space-y-4" data-testid="admin-abuse-reports">
    <div className="flex gap-2">{["open", "resolved", "dismissed", "all"].map((s) => <Button key={s} size="sm" variant={status === s ? "default" : "secondary"} onClick={() => setStatus(s)} className="capitalize" data-testid={`abuse-filter-${s}`}>{s}</Button>)}</div>
    {rows && !rows.length && <p className="text-sm text-slate-500" data-testid="abuse-empty">No reports here.</p>}
    {rows?.map((r) => <Card key={r.id} data-testid={`abuse-${r.id}`}>
      <div className="flex flex-wrap justify-between gap-2"><div><b>{r.target_name || "Academy"}</b>{r.target_email && <span className="text-xs text-slate-400"> · {r.target_email}</span>} <span className="text-sm text-slate-400">in {r.academy_name}</span></div><Badge tone={{ open: "amber", resolved: "green", dismissed: "slate" }[r.status]}>{r.status}</Badge></div>
      <p className="text-sm mt-2"><span className="text-amber-300">{r.reason_label}</span> — {r.details}</p>
      <p className="text-xs text-slate-500 mt-2">Reported by {r.reporter_name} ({r.reporter_email}) · {fmtDate(r.created_at)}</p>
      {r.status === "open" && <div className="flex gap-2 mt-3"><Button size="sm" onClick={() => act(r.id, "resolved")} data-testid={`abuse-resolve-${r.id}`}>Mark resolved</Button><Button size="sm" variant="secondary" onClick={() => act(r.id, "dismissed")} data-testid={`abuse-dismiss-${r.id}`}>Dismiss</Button></div>}
    </Card>)}
  </div>);
};
