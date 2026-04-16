# OpenClaw CRM — Project State

_Last updated: April 16, 2026 (11:55 EDT)_

## Current Milestone
Fix relationship / data integrity and finish migration cleanup

## Next Tasks (in order)
1. [x] **Test person creation fix** — Verified foreign key constraint fix works; person creation saves successfully (API tested)
2. [x] **Add inline group creation to record picker** — Implemented 'Create new group' button in RecordReferenceEditor; config passed
3. [ ] **Verify relationship integrity** — Run verification scripts in `scripts/migrations/` to confirm person/company/task links are consistent
4. [ ] **Resolve any broken links** — Fix records that fail verification (use or create targeted migration scripts in `scripts/migrations/`)
5. [ ] **Test Railway deployment** — Verify `Dockerfile.railway` and `railway.json` work for staging/production push
6. [ ] **UI/UX polish** — Fix any edge cases in record cards, multiselect categories, and group member derivation
7. [ ] **Test UI fixes** — Verify type selection works and group creation button appears in person edit

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
- ✅ **Select options for 'type' attribute**: Populated select_options table with Client, Agent, Contact, Lead, Other (fixes inability to change type)
- ✅ **Updated 'type' options per user request**: Changed to Client, Prospect, Agent, COI, Professional, BNI; migrated existing values
- ✅ **Inline group creation**: Added 'Create new group' button to record reference picker for company field; config now passed to AttributeEditor
- ✅ **Groups cleanup**: Deleted 16 groups from 'Jahborn Riley Group' down alphabetically (7 groups remain); later deleted all remaining groups (0 groups total)
- ✅ **Groups column rename**: Changed 'Name' column title to 'Group', 'Team' column title to 'Members'
- ✅ **Group field filtering**: Updated RecordReferenceEditor to filter records by target object slug (groups only), no longer showing people and other lists
- ✅ **New Person group creation**: Added inline group creation to RecordReferencePicker in create modal; config passed; filter by target object slug
- ✅ **Notes card layout**: Updated NoteCard to show 2 lines: 1st line with name, note title, date; 2nd line with detailed comment
- ✅ **Notes sorting toggle**: Added interactive sort pill to toggle between Creation date and Last updated; groups update dynamically
- ✅ **Notes action tabs**: Added Log call, Log meeting, Add note, Add task choice tabs on top of Notes section (matching Person card UI)
- ✅ **Note card type badge & editable date**: Added note type badge (call, meeting, zoom, note, task) and click‑to‑edit date on each note card; date changes via PATCH API
- ✅ **Infrastructure fixes (April 16)**: Fixed OpenClaw gateway boot reliability (network.target, TimeoutStartSec), started CRM services (PostgreSQL + Next.js), verified accessibility

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
