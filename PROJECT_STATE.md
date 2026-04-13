# OpenClaw CRM — Project State

_Last updated: April 13, 2026_

## Current Milestone
Fix relationship / data integrity and finish migration cleanup

## Next Tasks (in order)
1. [ ] **Verify relationship integrity** — Run verification scripts in `scripts/migrations/` to confirm person/company/task links are consistent
2. [ ] **Resolve any broken links** — Fix records that fail verification (use or create targeted migration scripts in `scripts/migrations/`)
3. [ ] **Test Railway deployment** — Verify `Dockerfile.railway` and `railway.json` work for staging/production push
4. [ ] **UI/UX polish** — Fix any edge cases in record cards, multiselect categories, and group member derivation

## Blockers
- None

## Recently Done
- ✅ Table sorting and automatic column filters added to record tables
- ✅ Persistent sidebar pin toggle added
- ✅ Search added to object records pages
- ✅ Record cards open from table row clicks
- ✅ Multiselect categories and group member derivation fixed
- ✅ Task/person relationship logic updated
- ✅ Middleware, AI chat, and record services updated
- ✅ All migration and debug scripts organized into `scripts/migrations/`
- ✅ Railway deployment files (`Dockerfile.railway`, `railway.json`) added
- ✅ Working tree committed and clean

## Running Locally
```bash
cd ~/.openclaw/workspace-dev/openclaw-crm
docker compose up -d   # postgres on port 5433
pnpm dev               # Next.js app
```

## Key Directories
| Path | What |
|------|------|
| `apps/web/src/services/records.ts` | Record CRUD API |
| `apps/web/src/services/ai-chat.ts` | AI chat integration |
| `apps/web/src/components/records/` | Record UI components |
| `apps/web/src/components/tasks/` | Task UI components |
| `apps/web/src/lib/api-utils.ts` | API utilities |
| `scripts/migrations/` | Data fix / migration scripts |

## Notes for Next Session
- Before running migrations, back up the database if it contains live data
- After fixing anything, update this file and commit it
- If a task is too big, break it into smaller tasks here
