import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api, errMsg, fmtDate, inr } from "@/lib/api";
import { Card, Badge } from "@/components/Common";

const useData = (path) => {
  const [d, setD] = useState(null);
  const load = useCallback(() => api.get(path).then(({ data }) => setD(data)).catch((e) => toast.error(errMsg(e))), [path]);
  useEffect(() => { load(); }, [load]);
  return [d, load];
};
const saveSettings = async (body) => { try { await api.put("/admin/settings", { ...body, confirm: true }); toast.success("Saved."); } catch (e) { toast.error(errMsg(e)); } };

const BLANK = { provider: "anthropic", label: "", key: "", priority: 10, pose_url: "", detect_url: "" };

export const ApiKeys = () => {
  const [d, load] = useData("/admin/api-keys");
  const [f, setF] = useState(BLANK);
  if (!d) return "Loading…";
  const add = async () => { try { await api.post("/admin/api-keys", f); setF({ ...BLANK, provider: f.provider }); load(); toast.success("Key added."); } catch (e) { toast.error(errMsg(e)); } };
  const test = async (k) => { const { data } = await api.post(`/admin/api-keys/${k.id}/test`, null, { params: { provider: k.provider } }); toast[data.ok ? "success" : "error"](data.message); load(); };
  return (<div className="space-y-6">
    <div className="grid md:grid-cols-2 gap-4">{["anthropic", "ultralytics"].map((p) => <Card key={p}><div className="font-semibold capitalize mb-2">{p === "anthropic" ? "Claude (Anthropic)" : "Ultralytics"} key mode</div>
      <Select value={d.modes[`${p}_mode`]} onValueChange={async (v) => { await saveSettings({ keys: { [`${p}_mode`]: v } }); load(); }}><SelectTrigger data-testid={`key-mode-${p}`}><SelectValue /></SelectTrigger>
        <SelectContent><SelectItem value="rotate">Rotate between keys, skip failing ones</SelectItem><SelectItem value="failover">Main key, use backups only on failure</SelectItem></SelectContent></Select>
      <p className="text-xs text-slate-500 mt-2">Rate-limited or rejected keys are paused automatically (1–15 min) and the next key is used.</p></Card>)}</div>
    <Card><h3 className="font-semibold mb-3">Add a key</h3><div className="grid md:grid-cols-6 gap-2">
      <Select value={f.provider} onValueChange={(v) => setF({ ...f, provider: v })}><SelectTrigger data-testid="new-key-provider"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="anthropic">Claude</SelectItem><SelectItem value="ultralytics">Ultralytics</SelectItem></SelectContent></Select>
      <Input placeholder="Label (e.g. Account 2)" value={f.label} onChange={(e) => setF({ ...f, label: e.target.value })} data-testid="new-key-label" />
      <Input className="md:col-span-2" type="password" placeholder="API key" value={f.key} onChange={(e) => setF({ ...f, key: e.target.value })} data-testid="new-key-value" autoComplete="off" />
      <Input type="number" placeholder="Priority" value={f.priority} onChange={(e) => setF({ ...f, priority: +e.target.value })} data-testid="new-key-priority" title="Lower = used first in failover mode" />
      <Button onClick={add} disabled={!f.label || f.key.length < 8} data-testid="new-key-add-btn">Add key</Button>
      {f.provider === "ultralytics" && <><Input className="md:col-span-3" placeholder="Dedicated pose URL (optional)" value={f.pose_url} onChange={(e) => setF({ ...f, pose_url: e.target.value })} data-testid="new-key-pose-url" />
        <Input className="md:col-span-3" placeholder="Dedicated detect URL (optional)" value={f.detect_url} onChange={(e) => setF({ ...f, detect_url: e.target.value })} data-testid="new-key-detect-url" /></>}</div>
      <p className="text-xs text-slate-500 mt-2">Keys are stored encrypted and never shown again. The main environment key is always included.</p></Card>
    <div className="overflow-x-auto glass rounded-xl" data-testid="api-keys-table"><table className="w-full text-sm min-w-[760px]"><thead><tr className="text-left text-slate-400">{["Provider", "Label", "Key", "Priority", "Used ok / failed", "State", ""].map((h) => <th key={h} className="p-3 font-medium">{h}</th>)}</tr></thead>
      <tbody>{d.keys.map((k) => <tr key={k.provider + k.id} className="border-t border-white/5" data-testid={`api-key-row-${k.id}`}><td className="p-3 capitalize">{k.provider}</td><td className="p-3">{k.label}</td><td className="p-3 font-mono text-xs">{k.masked}</td><td className="p-3">{k.priority}</td>
        <td className="p-3">{k.ok} / {k.fail}{k.last_error && <div className="text-[11px] text-red-300 max-w-[200px] truncate" title={k.last_error}>{k.last_error}</div>}</td>
        <td className="p-3">{k.cooling ? <Badge tone="amber">Paused</Badge> : k.active ? <Badge tone="green">Active</Badge> : <Badge>Off</Badge>}</td>
        <td className="p-3"><div className="flex gap-2 items-center"><Button size="sm" variant="ghost" onClick={() => test(k)} data-testid={`test-key-${k.id}`}>Test</Button>
          {!k.env && <><Switch checked={k.active} onCheckedChange={async (v) => { await api.patch(`/admin/api-keys/${k.id}`, { active: v }); load(); }} data-testid={`toggle-key-${k.id}`} />
            <Button size="sm" variant="ghost" className="text-red-300" onClick={async () => { if (window.confirm("Delete this key?")) { await api.delete(`/admin/api-keys/${k.id}`); load(); } }} data-testid={`delete-key-${k.id}`}>Delete</Button></>}</div></td></tr>)}</tbody></table></div>
  </div>);
};

const MODES = [["percent_every", "% of every referred payment"], ["percent_first", "% of first payment only"], ["fixed_per_student", "Fixed ₹ per paying student"]];

export const Commissions = () => {
  const [d, load] = useData("/admin/commissions");
  const [s, setS] = useState(null);
  const [acs, setAcs] = useState([]);
  const [sel, setSel] = useState([]);
  const [ov, setOv] = useState({ aid: "", mode: "percent_every", value: 10 });
  useEffect(() => { api.get("/admin/settings").then(({ data }) => setS(data.commission)); api.get("/admin/academies").then(({ data }) => setAcs(data)); }, []);
  if (!d || !s) return "Loading…";
  const pending = d.rows.filter((r) => r.status === "pending");
  const markPaid = async () => { const ref = window.prompt("Payout reference (UPI / bank ref)") || ""; await api.post("/admin/commissions/mark-paid", { ids: sel, reference: ref }); setSel([]); load(); toast.success("Marked as paid."); };
  return (<div className="space-y-6">
    <Card><h3 className="font-semibold mb-3">Default commission rule</h3><div className="flex flex-wrap gap-2 items-end">
      <Select value={s.mode} onValueChange={(v) => setS({ ...s, mode: v })}><SelectTrigger className="w-72" data-testid="commission-mode"><SelectValue /></SelectTrigger><SelectContent>{MODES.map(([v, l]) => <SelectItem key={v} value={v}>{l}</SelectItem>)}</SelectContent></Select>
      <Input type="number" min={0} className="w-28" value={s.value} onChange={(e) => setS({ ...s, value: e.target.value })} data-testid="commission-value" /><span className="text-sm text-slate-400">{s.mode === "fixed_per_student" ? "₹" : "%"}</span>
      <Button onClick={() => saveSettings({ commission: s })} data-testid="commission-save-btn">Save</Button></div></Card>
    <Card><h3 className="font-semibold mb-3">Override for one academy</h3><div className="flex flex-wrap gap-2 items-end">
      <Select value={ov.aid} onValueChange={(v) => setOv({ ...ov, aid: v })}><SelectTrigger className="w-56" data-testid="override-academy"><SelectValue placeholder="Academy" /></SelectTrigger><SelectContent>{acs.map((a) => <SelectItem key={a.id} value={a.id}>{a.name} ({a.code})</SelectItem>)}</SelectContent></Select>
      <Select value={ov.mode} onValueChange={(v) => setOv({ ...ov, mode: v })}><SelectTrigger className="w-64" data-testid="override-mode"><SelectValue /></SelectTrigger><SelectContent>{MODES.map(([v, l]) => <SelectItem key={v} value={v}>{l}</SelectItem>)}</SelectContent></Select>
      <Input type="number" min={0} className="w-24" value={ov.value} onChange={(e) => setOv({ ...ov, value: e.target.value })} data-testid="override-value" />
      <Button disabled={!ov.aid} onClick={async () => { try { await api.put(`/admin/academies/${ov.aid}/commission`, { mode: ov.mode, value: +ov.value }); toast.success("Override saved."); } catch (e) { toast.error(errMsg(e)); } }} data-testid="override-save-btn">Save override</Button>
      <Button variant="ghost" disabled={!ov.aid} onClick={async () => { await api.put(`/admin/academies/${ov.aid}/commission`, {}); toast.success("Uses default rule now."); }} data-testid="override-clear-btn">Use default</Button></div></Card>
    <div className="grid md:grid-cols-3 gap-3">{d.totals.map((t) => <Card key={t.academy_id}><div className="font-semibold">{t.academy_name}</div><div className="text-sm text-slate-400">Pending {inr(t.pending)} · Paid {inr(t.paid)}</div></Card>)}</div>
    <Card><div className="flex justify-between items-center mb-3"><h3 className="font-semibold">Commission entries</h3><Button size="sm" disabled={!sel.length} onClick={markPaid} data-testid="mark-paid-btn">Mark {sel.length || ""} paid</Button></div>
      {!d.rows.length ? <p className="text-sm text-slate-500">No commissions yet.</p> : d.rows.map((r) => <label key={r.id} className="flex justify-between items-center text-sm border-b border-white/5 py-2 gap-2" data-testid={`commission-${r.id}`}>
        <span className="flex gap-2 items-center">{r.status === "pending" && <input type="checkbox" checked={sel.includes(r.id)} onChange={(e) => setSel(e.target.checked ? [...sel, r.id] : sel.filter((x) => x !== r.id))} />}
          {r.academy_name} ← {r.student_name} · {r.plan_name} ({inr(r.payment_amount_inr)}) · {fmtDate(r.created_at)}</span>
        <span>{inr(r.amount_inr)} <Badge tone={r.status === "paid" ? "green" : r.status === "pending" ? "amber" : "red"}>{r.status}</Badge></span></label>)}
      {pending.length > 0 && <Button size="sm" variant="ghost" className="mt-2" onClick={() => setSel(pending.map((r) => r.id))} data-testid="select-all-pending">Select all pending</Button>}</Card>
  </div>);
};
