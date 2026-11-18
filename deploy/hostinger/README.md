# Host CricAnalyze on a Hostinger VPS (cricanalyze.in)

Everything runs on one VPS: website, backend, MongoDB database, and uploaded videos, images and PDFs (saved on the VPS disk at `/var/lib/cricanalyze/storage`).

**VPS to choose:** Hostinger **KVM 2 or higher** (2 vCPU, 8 GB RAM, 100 GB disk). Pick **Ubuntu 24.04** (or 22.04) as the operating system. Video analysis runs on the CPU, so KVM 1 (4 GB) is too small.

---

## 1. Point your domain to the VPS
In **hPanel → Domains → cricanalyze.in → DNS / Nameservers → DNS records**:

| Type | Name | Points to | TTL |
|---|---|---|---|
| A | `@` | your VPS IP | 300 |
| A | `www` | your VPS IP | 300 |

Delete any other `A`, `AAAA` or `CNAME` records for `@` and `www` (for example an old "parked" or website-builder record). DNS can take 5–60 minutes to update.

## 2. Open the VPS terminal
In **hPanel → VPS → Manage → Browser terminal** (or use `ssh root@YOUR_VPS_IP` from your computer).

## 3. Download your code from GitHub
Public repo:
```bash
git clone https://github.com/YOUR_GITHUB_USER/YOUR_REPO.git /opt/cricanalyze
```
Private repo: create a token at GitHub → Settings → Developer settings → Personal access tokens (classic) with the `repo` permission, then:
```bash
git clone https://YOUR_GITHUB_USER:YOUR_TOKEN@github.com/YOUR_GITHUB_USER/YOUR_REPO.git /opt/cricanalyze
```

## 4. Run the setup (about 15–25 minutes)
```bash
cd /opt/cricanalyze && sudo bash deploy/hostinger/setup.sh
```
It asks for:
- domain → press Enter for `cricanalyze.in`
- email → used for the SSL certificate and as the **super admin** account
- Anthropic key, Hostinger mailbox password (for `noreply@cricanalyze.in`), Razorpay Key ID / Secret / Webhook secret. Typing is hidden for secrets. You can press Enter to skip any and add it later (step 7).

The script installs Python, Node, MongoDB, nginx and SSL. It builds the site, starts it, turns on the firewall and sets up daily backups. When it finishes, open **https://cricanalyze.in**.

## 5. Create your super admin
Sign up on the site with the email you gave the setup script (default `cricanalyze.in@gmail.com`). After you verify the email code, that account becomes super admin.

## 6. Razorpay webhook
In the Razorpay Dashboard → **Settings → Webhooks → Add new webhook**:
- URL: `https://cricanalyze.in/api/billing/webhook`
- Secret: the same webhook secret you entered in setup
- Events: `payment.captured`, `payment.failed`, `refund.processed`

When you switch Razorpay from **Test** to **Live** mode, put the live keys in step 7 and add the webhook again in Live mode.

## 7. Change keys later
```bash
sudo nano /opt/cricanalyze/backend/.env      # edit, then Ctrl+O, Enter, Ctrl+X
sudo systemctl restart cricanalyze
```

## 8. Update the site after new changes on GitHub
Push changes to GitHub with "Save to GitHub", then on the VPS:
```bash
sudo bash /opt/cricanalyze/deploy/hostinger/update.sh
```

---

## Useful commands
| What | Command |
|---|---|
| Is the backend running? | `sudo systemctl status cricanalyze` |
| Backend logs | `sudo journalctl -u cricanalyze -n 200 -f` |
| Restart backend | `sudo systemctl restart cricanalyze` |
| Web server logs | `sudo tail -n 100 /var/log/nginx/error.log` |
| Database running? | `sudo systemctl status mongod` |
| Disk space | `df -h` |
| Backups (daily 03:30, kept 7 days) | `ls -lh /var/lib/cricanalyze/backups` |

**Restore a backup**
```bash
sudo mongorestore --gzip --archive=/var/lib/cricanalyze/backups/db-YYYY-MM-DD.gz --drop
sudo tar -xzf /var/lib/cricanalyze/backups/files-YYYY-MM-DD.tgz -C /var/lib/cricanalyze
```
Also download backups to your computer now and then (Hostinger also offers VPS snapshots in hPanel).

## Troubleshooting
- **SSL step failed**: DNS isn't pointing to the VPS yet. Wait, check with `ping cricanalyze.in`, then run `sudo certbot --nginx -d cricanalyze.in -d www.cricanalyze.in --redirect`.
- **Site shows "502 Bad Gateway"**: the backend isn't running. Check `sudo journalctl -u cricanalyze -n 100`. This is usually a typo or a missing key in `.env`.
- **MongoDB won't start ("Illegal instruction")**: the VPS CPU doesn't support MongoDB 8. Ask Hostinger support, or use a MongoDB Atlas link in `MONGO_URL`.
- **Emails not arriving**: check `SMTP_PASS` and that the `noreply@cricanalyze.in` mailbox exists in hPanel → Emails.

## Notes
- This VPS starts with an **empty database**. Accounts, analyses and files from the Emergent preview are not copied over.
- Uploaded files live on the VPS disk. Keep an eye on free space as videos grow (`df -h`).
