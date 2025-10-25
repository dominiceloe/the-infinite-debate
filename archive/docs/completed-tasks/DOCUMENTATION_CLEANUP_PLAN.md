# Documentation Cleanup Plan

**Date:** October 19, 2025

## Current State Analysis

**Total .md files found:** 27 files (excluding node_modules/venv)

### File Categories

#### ✅ KEEP - Core Documentation (9 files)
These are actively maintained and essential:

1. **README.md** - Main project overview
2. **QUICKSTART.md** - Setup instructions
3. **STATUS.md** - Current development status (just updated Oct 19)
4. **NEXT_STEPS.md** - Action plan and roadmap
5. **backend/CELERY_GUIDE.md** - Infrastructure documentation
6. **backend/POSTGRESQL_MIGRATION.md** - Migration guide
7. **backend/SECURITY_HARDENING.md** - Security documentation
8. **backend/SENTRY_SETUP.md** - Monitoring setup (just created)
9. **backend/LOGGING_SETUP.md** - Logging setup (just created)

#### 📦 ARCHIVE - Historical/Completed Task Documentation (8 files)
Keep for reference but move to `/archive/docs/` directory:

1. **OCT_19_EVALUATION.md** - One-time technical evaluation (historical record)
2. **IMPLEMENTATION_PLAN.md** - Completed infrastructure upgrade plan
3. **backend/MIGRATION_SUMMARY.md** - Summary (redundant with POSTGRESQL_MIGRATION.md)
4. **WORKING_STATUS_10_18_25_0848.md** - Timestamped snapshot (outdated)
5. **backend/CITATION_FIX_SUMMARY.md** - Completed task documentation
6. **TEXT_INGESTION_REPORT.md** - Completed ingestion report
7. **TEXT_INGESTION_REPORT_FIXED.md** - Fixed version of above
8. **CITATION_VALIDATION_REPORT.md** - Generated validation report

#### 🗑️ DELETE - Outdated/Superseded (3 files)
These can be safely deleted:

1. **DEPLOYMENT_STATUS.md** - Old deployment plan (superseded by NEXT_STEPS.md)
2. **ADMIN_STATUS.md** - Basic admin documentation (trivial info)
3. **CITATION_VALIDATOR_README.md** - Redundant with citation reports

#### 🤔 REVIEW - Content Tracking (4 files)
Need user decision on whether these are still actively used:

1. **PERSONAS_IMAGE_TRACKER.md** (284 lines) - Persona image status tracking
2. **PERSONAS_TEXT_TRACKER.md** (533 lines) - Persona text status tracking
3. **PRE_1928_TEXTS_LIST.md** (411 lines) - Public domain texts list
4. **TEXTS_PLAN.md** - Text library planning document

**Question:** Are these tracking files still being actively updated, or are they historical records?

#### 💡 CONSOLIDATE - Planning/Brainstorming (2 files)
Can be merged into single file or archived:

1. **brainstorm.md** - Original vision/ideas
2. **persona-ideas.md** - Persona suggestions

**Recommendation:** Combine into `PLANNING_NOTES.md` or archive both

#### ℹ️ OTHER (1 file)
1. **frontend/README.md** - Frontend-specific readme (KEEP)

---

## Proposed Actions

### Step 1: Create Archive Structure
```bash
mkdir -p archive/docs/completed-tasks
mkdir -p archive/docs/evaluations
mkdir -p archive/docs/planning
```

### Step 2: Move Historical Documentation
```bash
# Completed tasks
mv backend/CITATION_FIX_SUMMARY.md archive/docs/completed-tasks/
mv TEXT_INGESTION_REPORT.md archive/docs/completed-tasks/
mv TEXT_INGESTION_REPORT_FIXED.md archive/docs/completed-tasks/
mv CITATION_VALIDATION_REPORT.md archive/docs/completed-tasks/
mv IMPLEMENTATION_PLAN.md archive/docs/completed-tasks/
mv backend/MIGRATION_SUMMARY.md archive/docs/completed-tasks/

# Evaluations and snapshots
mv OCT_19_EVALUATION.md archive/docs/evaluations/
mv WORKING_STATUS_10_18_25_0848.md archive/docs/evaluations/

# Planning/brainstorming
mv brainstorm.md archive/docs/planning/
mv persona-ideas.md archive/docs/planning/
```

### Step 3: Delete Outdated Files
```bash
rm DEPLOYMENT_STATUS.md
rm ADMIN_STATUS.md
rm CITATION_VALIDATOR_README.md
```

### Step 4: Content Tracking Files
**Option A:** Archive if no longer actively maintained
```bash
mv PERSONAS_IMAGE_TRACKER.md archive/docs/tracking/
mv PERSONAS_TEXT_TRACKER.md archive/docs/tracking/
mv PRE_1928_TEXTS_LIST.md archive/docs/tracking/
mv TEXTS_PLAN.md archive/docs/tracking/
```

**Option B:** Keep if still actively used
- Leave in root directory for easy access

### Step 5: Update Cross-References
Update any remaining docs that reference moved/deleted files:
- Update README.md links
- Update STATUS.md links
- Update NEXT_STEPS.md links

---

## Final Documentation Structure

```
/philosophical-debates/
├── README.md                          # Main overview
├── QUICKSTART.md                      # Setup guide
├── STATUS.md                          # Current status
├── NEXT_STEPS.md                      # Roadmap
├── frontend/
│   └── README.md                      # Frontend-specific
├── backend/
│   ├── CELERY_GUIDE.md               # Infrastructure
│   ├── POSTGRESQL_MIGRATION.md       # Database setup
│   ├── SECURITY_HARDENING.md         # Security config
│   ├── SENTRY_SETUP.md               # Monitoring
│   └── LOGGING_SETUP.md              # Logging
└── archive/
    └── docs/
        ├── completed-tasks/           # Finished work documentation
        ├── evaluations/               # Historical evaluations
        ├── planning/                  # Brainstorming notes
        └── tracking/                  # Content tracking (optional)
```

---

## Benefits

1. **Clarity:** Clear distinction between active and historical documentation
2. **Maintainability:** Easier to keep current docs up to date
3. **Discoverability:** New contributors find relevant docs faster
4. **History Preservation:** Important context retained in archive
5. **Reduced Clutter:** Less overwhelming for users exploring the project

---

## Decision Needed

**User Input Required:** What should we do with the tracking files?
- PERSONAS_IMAGE_TRACKER.md
- PERSONAS_TEXT_TRACKER.md
- PRE_1928_TEXTS_LIST.md
- TEXTS_PLAN.md

**Questions:**
1. Are you still actively updating these tracking files?
2. Are they reference materials you consult regularly?
3. Or are they historical records of completed work?

**Recommendation:** If not actively maintained, archive them. You can always retrieve from archive if needed later.

---

**Ready to execute?** Let me know if you approve this plan, and I'll execute the cleanup.
