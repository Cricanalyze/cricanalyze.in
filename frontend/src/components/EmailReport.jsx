import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Mail, CalendarClock, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { api, errMsg, fmtDateTime } from "@/lib/api";

export const EmailReport = ({ jobId }) => {
  const [open, setOpen] = useState(false);
  const [when, setWhen] = useState("");
  const [d, setD] = useState(null);
  const [busy, setBusy] = useState(false);
  const load = useCallback(() => api.get(`/analyses/${jobId}/email-schedules`).then(({ data }) => setD(data)).catch(() => {}), [jobId]);
  useEffect(() => { if (open) load(); }, [open, load]);
  const send = async (scheduled) => {
    setBusy(true);
    try {
      const { data } = await api.post(`/analyses/${jobId}/email`, scheduled ? { send_at: when } : {});
      toast.success(data.sent ? "Report emailed to you (with PDF and shareable link)." : `Scheduled for ${fmtDateTime(data.send_at)}.`);
      setWhen(""); load();
    } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  const cancel = async (sid) => { try { await api.delete(`/report-schedules/${sid}`); load(); } catch (e) { toast.error(errMsg(e)); } };
  const pending = (d?.schedules || []).filter((s) => s.status === "pending");
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild><Button variant="secondary" data-testid="report-email-btn"><Mail size={16} className="mr-1" />Email</Button></DialogTrigger>
      <DialogContent data-testid="email-report-dialog">
        <DialogHeader><DialogTitle>Email this report</DialogTitle></DialogHeader>
        <p className="text-sm text-slate-400">We send the report link, a shareable link and the PDF (if your plan includes PDF export) to your account email.</p>
        <Button onClick={() => send(false)} disabled={busy} className="bg-[#10B981] hover:bg-[#059669] text-[#0B132B]" data-testid="email-now-btn"><Mail size={16} className="mr-1" />Send now</Button>
        <div className="border-t border-white/10 pt-4"><div className="text-sm font-medium mb-2 flex items-center gap-2"><CalendarClock size={16} />Schedule for later (IST)</div>
          <div className="flex gap-2"><Input type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} data-testid="email-schedule-input" />
            <Button variant="secondary" disabled={!when || busy} onClick={() => send(true)} data-testid="email-schedule-btn">Schedule</Button></div></div>
        {pending.length > 0 && <div className="space-y-1" data-testid="email-schedule-list">{pending.map((s) => <div key={s.id} className="flex justify-between text-sm"><span>{fmtDateTime(s.send_at)}</span>
          <button onClick={() => cancel(s.id)} className="text-red-300 flex items-center gap-1 text-xs" data-testid={`cancel-schedule-${s.id}`}><X size={12} />Cancel</button></div>)}</div>}
        {d?.last_emailed_at && <p className="text-xs text-slate-500">Last emailed {fmtDateTime(d.last_emailed_at)}</p>}
      </DialogContent>
    </Dialog>
  );
};
