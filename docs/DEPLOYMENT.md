# Deployment Guide

Two ways to run Mirage:

- **[Docker Compose](#option-a-docker-compose-recommended)** — everything (MySQL, Redis, API, worker, scheduler) in containers. Recommended.
- **[Manual deploy to a Linux server](#option-b-manual-deploy-windows--ubuntu)** — build the frontend locally, ship it to Ubuntu, serve with Nginx.

Before either, read [Environment variables](#environment-variables).

---

## Environment variables

All backend configuration lives in `backend/.env`. Start from the template:

```bash
cd backend
cp .env.example .env
```

`.env` is gitignored. **Never commit real credentials.**

Generate the two Flask secrets with real entropy:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

| Group | Variables | Required |
|---|---|---|
| Flask | `SECRET_KEY`, `FLASK_ENV`, `FLASK_DEBUG` | Yes |
| JWT | `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRES` | Yes |
| MySQL | `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`, `DATABASE_URI` | Yes |
| Redis | `REDIS_PASSWORD`, `REDIS_URL` | Yes |
| Bootstrap admin | `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Yes — `init_db.py` **aborts** if `ADMIN_PASSWORD` is unset |
| Demo user | `DEMO_USER_EMAIL`, `DEMO_USER_PASSWORD` | No — falls back to the admin password |
| Upstream provider | `OPENAI_API_KEY`, `SORA_API_BASE_URL` | Seeds the first API-key pool entry; can also be added later from the admin console |
| Email (verification codes) | `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` | Needed for registration |
| Cloudflare R2 | `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL` | Needed for uploads and result persistence |
| GeeTest CAPTCHA | `GEETEST_ID`, `GEETEST_KEY` | Optional — **verification is skipped entirely when unset** |

> **GeeTest fails open.** If `GEETEST_ID` / `GEETEST_KEY` are empty, `app/utils/geetest.py` returns success without calling the upstream service. That is convenient locally and dangerous in production — set both before exposing registration to the internet.

The frontend has its own template at `frontend/.env.example`. Only public identifiers belong there: anything prefixed `VITE_` is compiled into the browser bundle and is readable by every visitor.

---

## Option A: Docker Compose (recommended)

### Requirements

Docker Engine 20.10+ and Docker Compose v2.

### Services

`backend/docker-compose.yml` defines six services:

| Service | Container | Notes |
|---|---|---|
| `mysql` | `sora_mysql` | MySQL 8.0, utf8mb4, bound to `127.0.0.1:3306` |
| `redis` | `sora_redis` | Redis 7 with `requirepass` + AOF; `FLUSHALL` / `FLUSHDB` / `CONFIG` are renamed away |
| `api` | `sora_api` | Gunicorn on port 5000, `/health` healthcheck |
| `worker` | `sora_worker` | `worker_gevent.py --workers 100` |
| `scheduler` | `sora_scheduler` | `scheduler.py` — stats sync, watchdog, cleanup, point expiry |
| `phpmyadmin` | `sora_phpmyadmin` | Bound to `127.0.0.1:8080`; reach it over an SSH tunnel, never expose it |

### Start

```bash
cd backend
cp .env.example .env     # then fill in real values
docker-compose up -d --build
docker-compose ps
docker-compose logs -f api
```

`docker-entrypoint.sh` waits up to 60s for MySQL, then initializes the schema **only if the database is empty**. If it cannot determine the state, it skips initialization rather than risk destroying data.

Verify:

```bash
curl http://127.0.0.1:5000/health
```

### First accounts

`init_db.py` creates the bootstrap admin from `ADMIN_EMAIL` / `ADMIN_PASSWORD` and a demo user from `DEMO_USER_EMAIL` / `DEMO_USER_PASSWORD`. There are no hardcoded default credentials — if `ADMIN_PASSWORD` is missing, initialization raises and stops.

Sign in to the admin console at `/wadminw/login`.

### Common operations

```bash
# Tail a service
docker-compose logs -f worker

# Restart after a code change
docker-compose restart api worker

# Re-run migrations
docker-compose exec api flask db upgrade

# MySQL shell (prompts for MYSQL_PASSWORD)
docker-compose exec mysql mysql -u "$MYSQL_USER" -p "$MYSQL_DATABASE"

# Back up
docker-compose exec mysql mysqldump -u root -p "$MYSQL_DATABASE" > backup_$(date +%Y%m%d).sql

# Stop (keeps volumes)
docker-compose down

# Stop and DELETE all data
docker-compose down -v
```

### Hardening before production

The shipped compose file leans toward development. Change these:

- `api` runs `gunicorn --reload -w 2` — drop `--reload` and raise the worker count.
- `api` and `worker` bind-mount the source tree (`.:/app`) — remove the mount so the image is the source of truth.
- `worker` sets `extra_hosts: host.docker.internal:10.1.64.2`, which only makes sense on the original author's network. Change or remove it.
- Remove the `phpmyadmin` service unless you actually need it.

### Self-hosted ComfyUI workflows (optional)

Models whose key starts with `workflow-` are not sent to a commercial provider. `worker.py` round-robins them across a hardcoded three-node ComfyUI cluster:

```
http://host.docker.internal:8188
http://host.docker.internal:8189
http://host.docker.internal:8190
```

These nodes are called with **no authentication headers**, and the DB-configured `api_base` is ignored for them. Unless you run ComfyUI at those addresses, either stand up equivalent nodes or avoid `workflow-*` models. Edit the list in `backend/worker.py` to point elsewhere.

---

## Option B: Manual deploy (Windows → Ubuntu)

For serving a static frontend build behind Nginx with the backend in Docker.

### Stage 1 — build locally (Windows)

```powershell
cd frontend
npm install
npm run build
```

`npm run build` type-checks first (`tsc --noEmit`) and fails the build on any TypeScript error. Confirm `frontend/dist` was produced.

### Stage 2 — upload

```powershell
ssh root@your-server-ip "mkdir -p /var/www/mirage/frontend /var/www/mirage/backend"

# Frontend build output
scp -r .\frontend\dist\* root@your-server-ip:/var/www/mirage/frontend/

# Backend source
scp -r .\backend\* root@your-server-ip:/var/www/mirage/backend/
```

Do **not** copy `.env.example` into place as your `.env` and leave it — create `.env` on the server and fill in real values there.

### Stage 3 — server setup (Ubuntu)

```bash
ssh root@your-server-ip

sudo apt update
sudo apt install nginx docker.io docker-compose-plugin -y
sudo systemctl enable --now docker
```

Bring up the backend:

```bash
cd /var/www/mirage/backend
cp .env.example .env
nano .env                      # fill in real values
docker compose up -d --build
curl 127.0.0.1:5000/health
```

### Stage 4 — Nginx

A complete reference config is provided at [`docs/nginx.conf.example`](./nginx.conf.example) — it covers the HTTP→HTTPS redirect, TLS settings, SPA `try_files` fallback, the `/api` reverse proxy, and the Cloudflare `real_ip` block.

```bash
# Copy the example, then replace every placeholder in it
sudo cp /var/www/mirage/backend/../docs/nginx.conf.example /etc/nginx/sites-available/mirage
sudo nano /etc/nginx/sites-available/mirage

sudo ln -s /etc/nginx/sites-available/mirage /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl reload nginx
```

Fix file permissions, otherwise Nginx returns `403 Forbidden`:

```bash
sudo chown -R www-data:www-data /var/www/mirage
sudo chmod -R 755 /var/www/mirage
```

### Stage 5 — verify

1. Open `https://your-domain.com` — the SPA should load.
2. Open DevTools and confirm `/api/*` requests return data rather than 502.
3. `curl https://your-domain.com/api/health`.

---

## Database migrations

Schema changes go through Flask-Migrate (Alembic):

```bash
docker-compose exec api flask db migrate -m "describe the change"
docker-compose exec api flask db upgrade
```

`backend/migrations/` also contains standalone one-off scripts for changes that predate the Alembic setup:

- `add_activity_point_grants.py`
- `add_consecutive_days_to_users.py`

Run these directly with Python if you are upgrading an older deployment.

---

## Scheduled jobs

`scheduler.py` runs these on the `schedule` library (not cron):

| Job | Cadence | Purpose |
|---|---|---|
| `sync_stats_job` | every 5 min | Flush Redis API-key counters to MySQL |
| `watchdog_job` | every 1 min | Detect and recover queue deadlock |
| `cleanup_tasks_job` | daily 02:00 | Delete tasks and their R2 objects older than 3 days |
| `expire_points_job` | hourly | Expire activity point grants |
| `expire_recharge_job` | daily 00:00 | Expire recharge balance |

Stats sync and the watchdog also run once at startup. All timestamps use `Asia/Shanghai`; change `ZoneInfo("Asia/Shanghai")` in the models and worker if you need a different timezone.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| API exits on boot | MySQL not reachable within 60s | `docker-compose logs mysql`; check `DATABASE_URI` credentials |
| Tasks stay `pending` forever | No healthy API key for that model, or the worker is down | `docker-compose logs worker`; check the key pool in the admin console |
| Tasks fail with a storage error | R2 not configured | Storage methods return `{'success': False, 'error': 'R2 storage not configured'}` when creds are missing — fill in the `R2_*` variables |
| Registration accepts any CAPTCHA | `GEETEST_ID` / `GEETEST_KEY` unset | Verification fails open by design; set both |
| `403 Forbidden` on the frontend | Nginx cannot read `/var/www/mirage` | Re-run the `chown` / `chmod` above |
| SPA 404s on refresh | Missing `try_files` | Use the provided `nginx.conf.example` |
| Logged out unexpectedly | Single-session mutex | Signing in elsewhere invalidates the previous session — this is intended |
