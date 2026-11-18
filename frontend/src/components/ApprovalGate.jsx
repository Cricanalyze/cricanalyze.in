import { useState } from "react";
import { toast } from "sonner";
import { ShieldCheck, Clock, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api, errMsg, fmtDateTime } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Card, Badge } from "@/components/Common";

export const needsApproval = (u) => u && ["coach", "academy_admin"].includes(u.role) && ["pending", "rejected"].includes(u.approval_status);

export const ApprovalGate = () => {
  const { user, refresh } = useAuth();
  const [type, setType] = useState("certificate");
  const [busy, setBusy] = useState(false);
  const doc = user.verification_doc;
  const rejected = user.approval_status === "rejected";
  const upload = async (file) => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file); fd.append("doc_type", type);
    setBusy(true);
    try { await api.post("/account/verification-doc", fd); toast.success("Document uploaded. An admin will review it."); await refresh(); }
    catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  return (
    <Card className="max-w-2xl" data-testid="approval-gate">
      <div className="flex items-center gap-3 mb-2"><ShieldCheck className="text-[#00B4D8]" /><h2 className="text-xl font-bold">Coach verification</h2>
        <Badge tone={rejected ? "red" : "amber"} data-testid="approval-status">{rejected ? "Not approved" : doc ? "Under review" : "Document needed"}</Badge></div>
      <p className="text-sm text-slate-400">To protect players, coach and academy accounts are checked by our team before they can analyse videos, create academies or see player data.
        Upload your employee ID or a coaching certificate (PDF, JPG, PNG or WEBP, under 8 MB).</p>
      {rejected && user.approval_note && <p className="text-sm text-red-300 mt-3 flex gap-2"><XCircle size={16} />{user.approval_note}</p>}
      {doc && <p className="text-sm mt-4 flex items-center gap-2" data-testid="approval-doc-info"><Clock size={15} className="text-amber-300" />{doc.label} uploaded {fmtDateTime(doc.uploaded_at)}{!rejected && " — we'll email you once it's reviewed."}</p>}
      <div className="flex flex-wrap gap-3 mt-5 items-center">
        <Select value={type} onValueChange={setType}><SelectTrigger className="w-52" data-testid="approval-doc-type"><SelectValue /></SelectTrigger>
          <SelectContent><SelectItem value="certificate">Coaching certificate</SelectItem><SelectItem value="employee_id">Employee ID</SelectItem></SelectContent></Select>
        <Button asChild disabled={busy} data-testid="approval-upload-btn"><label className="cursor-pointer">{busy ? "Uploading…" : doc ? "Upload a new document" : "Upload document"}
          <input type="file" accept="application/pdf,image/png,image/jpeg,image/webp" className="hidden" onChange={(e) => { upload(e.target.files[0]); e.target.value = ""; }} data-testid="approval-file-input" /></label></Button>
        <Button variant="ghost" onClick={refresh} data-testid="approval-refresh-btn">Check status</Button>
      </div>
    </Card>
  );
};
