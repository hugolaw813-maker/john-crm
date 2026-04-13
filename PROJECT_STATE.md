# OpenClaw CRM — Project State

_Last updated: April 13, 2026 (18:20 EDT)_

## Current Milestone
Fix relationship / data integrity and finish migration cleanup

## Next Tasks (in order)
1. [ ] **Test person creation fix** — Verify foreign key constraint fix works; person creation should save successfully
2. [ ] **Add inline group creation to record picker** — Enhance RecordReferencePicker component to support "create new" for groups (or implement workaround)
3. [ ] **Verify relationship integrity** — Run verification scripts in `scripts/migrations/` to confirm person/company/task links are consistent
4. [ ] **Resolve any broken links** — Fix records that fail verification (use or create targeted migration scripts in `scripts/migrations/`)
5. [ ] **Test Railway deployment** — Verify `Dockerfile.railway` and `railway.json` work for staging/production push
6. [ ] **UI/UX polish** — Fix any edge cases in record cards, multiselect categories, and group member derivation

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
- ✅ **Data integrity restoration (April 13)**: Cleaned 21 Person records (removed Household/Family suffixes), established Person↔Group bidirectional links
- ✅ **People attribute updates**: Added Type, Owner, Co-Work fields; deleted Job Title; renamed Location→Address
- ✅ **Frontend slug fixes**: Updated 12 files from `companies` → `groups` slug
- ✅ **Backup system implemented**: Python-based backup with daily cron scheduling
- ✅ **UI verification**: Groups table shows people lists, People table shows clean names with Address column
- ✅ **Foreign key constraint fix**: Updated authentication dev bypass to use real user ID, fixed `records_created_by_users_id_fk` violation

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
