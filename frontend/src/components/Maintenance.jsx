import { useEffect, useState, useCallback } from "react";
import { useLocation, Link } from "react-router-dom";
import { toast } from "sonner";
import { Wrench, Clock } from "lucide-react";
import { api, errMsg } from "@/lib/api";
import { useAuth, isStaff } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Card, Badge, Logo } from "@/components/Common";

const OPEN_PATHS = ["/login", "/admin"];
const toIST = (iso) => iso ? new Date(new Date(iso).getTime() + 330 * 60000).toISOString().slice(0, 16) : "";
const fmtIST = (iso) => new Date(iso).toLocaleString("en-IN", { timeZone: "Asia/Kolkata", dateStyle: "medium", timeStyle: "short" }) + " IST";

const useMaintenance = () => {
  const [m, setM] = useState(null);
  const load = useCallback(() => api.get("/maintenance").then(({ data }) => { setM(data); return data; }).catch(() => setM((x) => x || { active: false })), []);
  useEffect(() => { load(); const t = setInterval(load, 30000); return () => clearInterval(t); }, [load]);
  return [m, load];
};

const MaintenancePage = ({ m }) => (
  <div className="min-h-screen grid place-items-center px-6 relative overflow-hidden" data-testid="maintenance-page">
    <div className="floor-grid" aria-hidden="true" />
    <div className="glow-orb w-96 h-96 bg-[#00B4D8] -top-20 right-10" aria-hidden="true" />
    <div className="relative z-10 max-w-lg text-center fade-up"><div className="flex justify-center mb-8"><Logo /></div>
      <div className="w-16 h-16 mx-auto rounded-2xl bg-[#10B981]/15 grid place-items-center mb-6 hero-float"><Wrench className="text-[#10B981]" size={30} /></div>
      <h1 className="text-4xl sm:text-5xl font-extrabold mb-4">We'll be right back</h1>
      <p className="text-slate-300 mb-6" data-testid="maintenance-message">{m.message}</p>
      {m.end_at && <div className="inline-flex items-center gap-2 glass rounded-full px-5 py-2 text-sm" data-testid="maintenance-back-at"><Clock size={15} className="text-[#00B4D8]" />Back online by {fmtIST(m.end_at)}</div>}
    </div>
  </div>);

export const MaintenanceGate = ({ children }) => {
  const [m] = useMaintenance();
  const { user, loading } = useAuth();
  const { pathname } = useLocation();
  if (m === null) return <div className="min-h-screen bg-[#070D1E]" />;
  if (!m.active || loading) return children;
  if (isStaff(user)) return <><div className="fixed bottom-3 left-1/2 -translate-x-1/2 z-[70] rounded-full bg-amber-500 text-[#0B132B] text-xs font-semibold px-4 py-1.5 shadow-lg" data-testid="maintenance-staff-banner">Maintenance mode is ON · only admins can use the site</div>{children}</>;
  if (OPEN_PATHS.some((p) => pathname.startsWith(p))) return children;
  return <MaintenancePage m={m} />;
};

export const MaintenanceAdmin = () => {
  const [m, load] = useMaintenance();
  const [f, setF] = useState(null);
  const fromM = (x) => ({ enabled: x.enabled, start_at: toIST(x.start_at), end_at: toIST(x.end_at), message: x.message });
  useEffect(() => { if (m && !f) setF(fromM(m)); }, [m, f]);
  if (!f) return "Loading…";
  const save = async (body) => { try { await api.put("/admin/maintenance", body); toast.success("Maintenance schedule saved."); const d = await load(); if (d) setF(fromM(d)); } catch (e) { toast.error(errMsg(e)); } };
  return (<Card className="max-w-2xl space-y-4" data-testid="maintenance-admin">
    <div className="flex justify-between items-center"><h3 className="font-semibold">Scheduled maintenance</h3>
      {m.active ? <Badge tone="amber">Live now</Badge> : m.enabled ? <Badge tone="teal">Scheduled</Badge> : <Badge>Off</Badge>}</div>
    <p className="text-xs text-slate-400">During this window every page and API is closed to everyone except admins. Admins can still sign in at <Link to="/admin" className="text-[#00B4D8]">/admin</Link>. Times are India time (IST).</p>
    <div className="grid sm:grid-cols-2 gap-3">
      <label className="text-sm space-y-1"><span className="text-slate-400">Starts</span><Input type="datetime-local" value={f.start_at} onChange={(e) => setF({ ...f, start_at: e.target.value })} data-testid="maintenance-start" /></label>
      <label className="text-sm space-y-1"><span className="text-slate-400">Ends (back online)</span><Input type="datetime-local" value={f.end_at} onChange={(e) => setF({ ...f, end_at: e.target.value })} data-testid="maintenance-end" /></label></div>
    <Textarea maxLength={300} placeholder="Message shown to visitors" value={f.message} onChange={(e) => setF({ ...f, message: e.target.value })} data-testid="maintenance-message-input" />
    <label className="flex items-center gap-3 text-sm"><Switch checked={f.enabled} onCheckedChange={(v) => setF({ ...f, enabled: v })} data-testid="maintenance-enabled" />Turn on this schedule</label>
    <div className="flex gap-2"><Button onClick={() => save(f)} data-testid="maintenance-save-btn">Save schedule</Button>
      {m.enabled && <Button variant="ghost" className="text-red-300" onClick={() => save({ ...f, enabled: false })} data-testid="maintenance-end-now-btn">End / cancel now</Button>}</div>
  </Card>);
};
