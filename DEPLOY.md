# Deploying to the Mac mini

Target: **https://urbanenergy-charge.newavera.co.il**
Pattern: Docker Compose (backend + nginx) behind your existing Cloudflare Tunnel,
same as `tact-main` / `customer-site`.

```
Cloudflare Tunnel ──▶ Mac mini localhost:8098 (web/nginx)
                          ├─ /        → built React dashboard
                          └─ /api/*   → backend container (uvicorn :8060)
```

No database is needed yet — the dashboard reads live from Evoltsoft.

---

## 1. Get the code on the Mac mini

```bash
git clone https://github.com/boazeng/urbanenergy-charge.git
cd urbanenergy-charge
# (later updates: git pull)
```

## 2. Create the secrets file

The Evoltsoft credentials are NOT in git. Either copy your local file:

```bash
# from your Windows machine, copy backend/.env to the Mac mini, or recreate it:
cat > backend/.env <<'EOF'
UE_EVOLTSOFT_BASE_URL=https://asia-south1-urbanenergy-prod.cloudfunctions.net
UE_EVOLTSOFT_FIREBASE_API_KEY=<your key>
UE_EVOLTSOFT_EMAIL=<your evoltsoft email>
UE_EVOLTSOFT_PASSWORD=<your evoltsoft password>
UE_EVOLTSOFT_BUSINESS_ORG_ID=Cek3U3qSS1dZ21p4yHSy
EOF
```

(`UE_ENV=prod` and `UE_DATA_SOURCE=evoltsoft` are already set in docker-compose.)

## 3. Build & run

```bash
docker compose up -d --build
docker compose ps          # both services "running"
curl -s localhost:8098/api/ready    # {"ready":true,"dataSource":"evoltsoft"}
```

Open `http://<mac-mini-ip>:8098` on the LAN to sanity-check the dashboard.

If port 8098 is taken, change the host port in `docker-compose.yml` (`web.ports`).

## 4. Point the domain at it (Cloudflare Tunnel)

**If your tunnel uses a config file** (`~/.cloudflared/config.yml`), add an ingress
rule **above** the catch-all:

```yaml
ingress:
  - hostname: urbanenergy-charge.newavera.co.il
    service: http://localhost:8098
  # ... your existing rules ...
  - service: http_status:404
```
Then: `cloudflared tunnel route dns <tunnel-name> urbanenergy-charge.newavera.co.il`
and restart the tunnel (`sudo launchctl kickstart -k system/com.cloudflare.cloudflared`
or however you run it).

**If you manage the tunnel from the Cloudflare dashboard** (Zero Trust → Networks →
Tunnels → your tunnel → Public Hostname → Add):
- Subdomain: `urbanenergy-charge`, Domain: `newavera.co.il`
- Service: `HTTP` → `localhost:8098`

DNS propagates in seconds; then **https://urbanenergy-charge.newavera.co.il** is live.

## 5. 🔒 Protect it (recommended — exposes business data)

The dashboard shows partners, balances and sessions with **no login**. Lock the
hostname with **Cloudflare Access** (Zero Trust → Access → Applications → Add):
- Application domain: `urbanenergy-charge.newavera.co.il`
- Policy: Allow → emails you choose (e.g. your Google Workspace).

This gates the whole site behind Cloudflare's login at the edge — no app changes.
(A built-in auth layer via shared-auth can replace this later.)

## Updating after a code change

```bash
git pull
docker compose up -d --build
```
