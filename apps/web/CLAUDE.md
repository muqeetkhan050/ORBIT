@AGENTS.md
# AURA (repo: orbit) — project context

Personal AI operating system: connects a user's Google/Slack/etc., builds unified
context, and an agent understands → prioritizes → plans → acts (with approval).

## Monorepo roles
- `apps/web` — Next.js 16 (App Router, TypeScript, Tailwind; shadcn/ui planned). The dashboard.
- `apps/api` — FastAPI (Python, managed with **uv**). Backend, OAuth, and the agent later.
- `apps/worker` — background workers (sync, embeddings, webhooks). Not started.

## Where we are
- Dashboard UI exists. **Auth is not wired up yet.**
- Currently building **Milestone 3: Google OAuth → Calendar**.
- Done:
  - Calendar connect page: `apps/web/src/app/dashboard/calendar/page.tsx`
  - Google Cloud OAuth client created (Web app, External/testing, scopes below)
  - FastAPI backend with `/connect`, `/callback`, `/status` in `apps/api/app/`
    (`main.py`, `config.py`, `google_oauth.py`)
- In progress: verifying the connect loop end-to-end.

## Key decisions & dev shortcuts — DON'T "fix" these without asking
- **No database yet.** Google tokens are saved to `apps/api/.tokens.json` (gitignored),
  a temporary single-user store. Next step is Postgres `integrations` table, encrypted,
  keyed by `user_id`.
- **No auth yet.** Single implicit user. Planned model: "Sign in with Google"
  (openid/email/profile) for login, then a *separate* "Connect Google" consent for
  sensitive Gmail/Calendar scopes (incremental authorization).
- **Calendar is read-only** (`calendar.readonly`). Event creation later needs `calendar.events`.
- The calendar page reads `?connected=true` from the OAuth callback redirect to show its
  connected state — temporary until `/status` is wired into the page.

## Conventions
- Backend secrets live in `apps/api/.env`. Never in `apps/web` or any `NEXT_PUBLIC_*` var.
- Google OAuth routes are under `/api/v1/integrations/google/*`.
- The redirect URI must match Google Cloud **exactly**:
  `http://localhost:8000/api/v1/integrations/google/callback`
- Scopes enabled: `openid`, `userinfo.email`, `userinfo.profile`, `calendar.readonly`.

## Run
- Frontend: `cd apps/web && npm run dev` → http://localhost:3000
- Backend: `cd apps/api && uv run fastapi dev app/main.py --port 8000`
  → http://localhost:8000 (interactive docs at `/docs`)

## Next steps
1. Use the stored token to fetch + render calendar events on the page.
2. Move token storage from `.tokens.json` to Postgres (`integrations`, encrypted).
3. Postgres + SQLAlchemy models + Alembic migrations.
4. Real auth (Google login) → attach integrations to a real `user_id`.
5. Then: Slack, approvals, memory (pgvector), agent (LangGraph).
