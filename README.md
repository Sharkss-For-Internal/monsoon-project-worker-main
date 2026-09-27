# Monsoon Early Warning — Worker

Scheduled jobs for the SIH 2026 **Hyperlocal Monsoon Onset & Break Prediction System** (PRD §19):

| Job | When (IST) | PRD |
|---|---|---|
| Daily pipeline — download data → monsoon phase → predictions → advice → alerts | 06:00 | §11.1 |
| Rapid check — next-72-hour forecast + satellite rain → urgent alerts | every 3 hours | §11.9 |
| Officer daily summary | 07:15 | §14.7 |
| Fallback check, pause auto-resume, weekly digest, maintenance | various | §19 |

The worker uses the **same database** as the backend and reuses the backend's code (models, config,
services) by installing the backend repo as a package — nothing is copied.
**It never changes the database schema** — migrations live only in the backend repo.

**Stack:** Python 3.12+ · APScheduler · the backend package (`app.…`)

---

## Quick start

You need **[uv](https://docs.astral.sh/uv/)**, and the **backend repo cloned next to this one** with its
database running (see the backend README):

```
SHARKSS-INTERNAL/
├── monsoon-backend-main/          ← backend (database must be running: docker compose up -d db)
└── monsoon-project-worker-main/   ← this repo
```

```bash
cp .env.example .env               # Windows PowerShell: copy .env.example .env
uv sync                            # installs APScheduler + the backend package from ../monsoon-backend-main
uv run python -m jobs.scheduler    # start the worker
```

With `SCHEDULER_ENABLED=false` (the default) it starts and exits without scheduling anything.
Set `SCHEDULER_ENABLED=true` in `.env` to run the jobs.

The backend is installed in **editable** mode, so changes in the backend repo are picked up immediately —
no reinstall needed.

---

## Settings

Copy `.env.example` → `.env`. Keep shared values (database, phone keys, WhatsApp/SMS) **the same as the
backend's `.env`**.

| Variable | Default | What it is |
|---|---|---|
| `SCHEDULER_ENABLED` | `false` | Turn job scheduling on |
| `PIPELINE_CRON` | `0 6 * * *` | Daily pipeline |
| `RAPID_CHECK_CRON` | `0 */3 * * *` | Rapid check |
| `OFFICER_SUMMARY_CRON` | `15 7 * * *` | Officer daily summary |
| `DATABASE_URL` | local Docker DB | Same database as the backend |

## Layout

```
jobs/
  scheduler.py     entry point — register jobs in register_jobs()
  config.py        worker-only settings (scheduler on/off, cron times)
  pipeline.py      run_daily_pipeline(date), run_rapid_check()          ← to build
  steps/           plain, idempotent job functions (ingest, forecast, advise, alert, dispatch …)  ← to build
```

Use the backend's code directly, e.g. `from app.core.db import SessionLocal`, `from app.models import ForecastRun`.

**Rule:** every job is a plain function taking `(issue_date)` / `(run_id)` / `(message_id)` and is safe to
re-run (idempotent) — so moving to Celery later means wrapping them, not rewriting them (PRD §19).

## Docker

Build from the **parent folder** that contains both repos (the image needs the backend package too):

```bash
docker build -f monsoon-project-worker-main/Dockerfile -t monsoon-worker .
docker run --rm --env-file monsoon-project-worker-main/.env monsoon-worker
```

`Dockerfile.dockerignore` makes sure only the two repos' code is sent to Docker.
