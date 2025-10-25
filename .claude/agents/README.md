# The Infinite Debate - Maintenance Agents

This directory contains specialized AI agents designed to help maintain and enhance **The Infinite Debate**, a platform where users can create debates between historical figures on any topic. Each agent is an expert in a specific domain and can be invoked to automate complex maintenance tasks.

**Product:** The Infinite Debate (theinfinitedebate.com)
**Created:** October 20, 2025
**Platform:** Claude Code (claude.ai/code)
**Tech Stack:** Django + Next.js + PostgreSQL + Anthropic Claude API

---

## 📋 Available Agents

### Contribution Workflow Agents (Required for All Code Changes)

#### 🔧 contribution-orchestrator.md
**Purpose:** Main controller for the `/contribute` command - coordinates all agents in the contribution workflow

**Usage:** Automatically invoked when you run `/contribute "description"`

**What It Does:**
- Interprets contribution request
- Routes to appropriate specialized agents
- Manages approval gates
- Handles errors and rollbacks
- Documents complete workflow

---

#### 📝 contribution-planner.md
**Purpose:** Analyzes contribution requests and creates detailed implementation plans

**Key Capabilities:**
- Discovers current codebase state (Django apps, Next.js pages)
- Identifies affected files and dependencies
- Estimates complexity (LOW/MEDIUM/HIGH)
- Creates actionable implementation checklist
- Assesses breaking changes and risks

---

#### ⚙️ contribution-implementer.md
**Purpose:** Autonomously implements code changes following approved plans

**Key Capabilities:**
- Follows Django patterns (models, serializers, ViewSets, Celery tasks)
- Follows Next.js patterns (App Router, React Query, Material-UI)
- Maintains type safety (Python type hints, TypeScript strict mode)
- Adds proper documentation (docstrings, comments, README updates)
- Creates database migrations when needed

---

#### ✅ contribution-validator.md
**Purpose:** Enforces all quality standards before code is committed

**Key Capabilities:**
- Runs linters (ESLint, TypeScript, Black if configured)
- Executes test suites (pytest backend, Vitest frontend)
- Checks coverage (no decrease allowed)
- Verifies no debug code (console.log, print statements)
- Validates API contract compatibility

---

#### 📦 contribution-committer.md
**Purpose:** Creates conventional git commits with all changes and reports

**Key Capabilities:**
- Generates conventional commit messages (feat/fix/refactor/test/docs)
- Stages all code changes and report files
- Includes Co-Authored-By attribution
- Commits reports to `.reports/contributions/` for project history

---

### Quality Assurance Agents

### 1. 🎯 debate-quality-auditor.md ⭐ **HIGHEST PRIORITY**

**Purpose:** Ensures debate quality by reviewing existing debates from the database and auditing historical authenticity across all persona types (philosophers, scientists, theologians, cultural figures).

**Key Capabilities:**
- Reviews completed debates stored in the database
- Scores each message on 5 criteria (authenticity, style, citations, character, engagement)
- Identifies personas not following their debate style or philosophical positions
- Suggests improvements to persona definitions and system prompts
- Tracks quality trends over time

**When to Use:**
- After updating persona definitions
- After modifying debate generation prompts (`backend/debates/prompts.py`)
- Before production deployment (quality assurance)
- Weekly quality monitoring
- Testing new personas

**Example Usage:**
```bash
# Audit a specific debate by topic/participants
claude-code "Audit the Aquinas vs Sartre debate on God's existence"

# Review all cross-tradition debates
claude-code "Review all debates with theologians debating philosophers"

# Weekly monitoring
claude-code "Audit all debates from the last week"

# Assess specific persona across all their debates
claude-code "How is Luther performing across all his debates?"
```

**Output:**
- Per-debate reports with scores and suggestions
- Aggregate quality summaries
- Persona scorecards
- Action items for improvements

---

### 2. 🧪 test-maintainer.md

**Purpose:** Increases test coverage from current baseline (Backend 15.85%, Frontend 5.61%) to production-ready levels (60%+).

**Key Capabilities:**
- Identifies untested code paths using coverage analysis
- Prioritizes tests by business impact × complexity × coverage gap
- Generates pytest tests for backend (debates, personas, texts, payments, users)
- Generates Vitest tests for frontend (components, pages, API client, contexts)
- Creates reusable fixtures and test utilities
- Tracks coverage progress over time

**When to Use:**
- Preparing for production deployment (NEXT_STEPS.md goal)
- After adding new features (ensure coverage doesn't drop)
- Before major refactoring (regression prevention)
- CI/CD pipeline failures
- Weekly test coverage review

**Example Usage:**
```bash
# Identify coverage gaps
claude-code "Run test-maintainer to identify top 5 untested modules"

# Generate tests for specific module
claude-code "Run test-maintainer to create tests for debates/generator.py"

# Increase coverage to target
claude-code "Run test-maintainer to increase backend coverage from 15% to 40%"

# Audit existing tests
claude-code "Run test-maintainer to audit existing tests for quality"
```

**Output:**
- Coverage gap analysis reports
- Generated test files (pytest/Vitest)
- Fixture definitions
- Coverage progress logs
- Quality audit reports

**Current State:**
- Backend: 15.85% (39 tests) → **Target: 60%+**
- Frontend: 5.61% (34 tests) → **Target: 50%+**

---

### 3. 🎭 persona-manager.md

**Purpose:** Comprehensive persona lifecycle management from creation to database sync.

**Key Capabilities:**
- **Creation:** Generate persona markdown from Wikipedia/Stanford Encyclopedia
- **Validation:** Check all required sections, external links, citation patterns
- **Citation Ingestion:** Link personas to their primary works in the text library (100 texts)
- **Database Sync:** Load personas, verify data integrity, manage tiers
- **Quality Assurance:** Score personas, identify improvements, maintain library health

**When to Use:**
- Adding new personas to the library (currently 196)
- Updating existing personas with better content
- Ingesting primary texts and linking citations
- Syncing markdown files with database
- Rebalancing tier access (Free/Trial/Starter/Pro)
- Auditing persona library quality

**Example Usage:**
```bash
# Create new persona
claude-code "Create persona for Hannah Arendt from Wikipedia and Stanford Encyclopedia"

# Validate all personas
claude-code "Validate all 196 personas and generate quality report"

# Ingest primary text
claude-code "Ingest 'The Republic' from Project Gutenberg and link to Plato"

# Sync database
claude-code "Sync persona database - validate first, then load"

# Optimize tiers
claude-code "Rebalance persona tiers based on debate usage statistics"

# Quality audit
claude-code "Run full persona quality audit and generate improvement roadmap"
```

**Output:**
- Persona markdown files
- Validation reports
- Database sync reports
- Quality scorecards
- Tier distribution analysis

**Persona Library:**
- 196 historical figures across all domains
  - 73 Philosophers (Socrates to de Beauvoir)
  - 73 Theologians (Augustine to Barth)
  - 50 Scientists (Galileo to Bohr)
  - Cultural figures (emerging category)
- 100 primary texts integrated
- 60 personas with citation patterns
- 4 access tiers (Free: 30, Trial: 60, Starter: 96, Pro: 196)

---

## 🔄 Agent Workflow Integration

### Contribution Workflow (All Code Changes)

**Required for ALL code contributions:**

```bash
# Use /contribute command for any code change
/contribute "Add minimum 2-round requirement for debates"
/contribute fix "Citation links broken on mobile"
/contribute "Extract debate credit calculation to utility"
```

**Workflow Phases:**
1. **Planning** - contribution-planner analyzes requirements
2. **Approval** - User reviews and approves plan
3. **Implementation** - contribution-implementer makes changes
4. **Testing** - test-maintainer generates tests
5. **Validation** - contribution-validator runs quality checks
6. **Commit** - contribution-committer creates conventional commit

**Output:** All reports saved to `.reports/contributions/YYYY-MM-DD/feature-name/`

**Standards Enforced:**
- 60%+ test coverage (no decrease)
- Type safety (no @ts-ignore or # type: ignore)
- No debug code (console.log, print statements)
- Conventional commits with co-authorship
- Full documentation (docstrings, comments, README)

---

### Typical Development Workflows

**Adding a New Persona:**
```bash
# Step 1: Create persona
claude-code "Create persona for Simone Weil using Wikipedia and Stanford Encyclopedia"

# Step 2: Validate
claude-code "Validate simone-weil.md"

# Step 3: Sync to database
claude-code "Sync persona database (validate first)"

# Step 4: After users create debates with the persona, review quality
claude-code "Review all debates featuring Simone Weil"

# Step 5: Adjust based on audit
claude-code "Update simone-weil.md based on quality audit feedback"
```

**Pre-Production Quality Check:**
```bash
# Step 1: Run all tests
claude-code "Run test-maintainer to verify 60%+ coverage"

# Step 2: Validate all personas
claude-code "Validate all 196 personas"

# Step 3: Review all completed debates
claude-code "Audit all completed debates and generate quality summary"

# Step 4: Review reports
# - Check test coverage ≥ 60%
# - Check persona validation 100% passed
# - Check debate quality average ≥ 7.5/10

# Step 5: Address any issues before deployment
```

**Weekly Maintenance Routine:**
```bash
# Monday: Quality monitoring
claude-code "Audit all debates from the last week and generate summary"

# Wednesday: Test coverage check
claude-code "Run test-maintainer coverage report"

# Friday: Persona library health
claude-code "Run persona-manager quality audit"
```

**After Updating Debate Prompts:**
```bash
# Step 1: Baseline audit (before changes)
claude-code "Audit recent debates to establish quality baseline"

# Step 2: After prompt update, let users create new debates, then audit
claude-code "Audit debates created after prompt update and compare to baseline"

# Step 3: Review comparison
# - Ensure improvement in authenticity scores
# - Verify no regression in style adherence
# - Check citation quality increased

# Step 4: Update tests if needed
claude-code "Run test-maintainer to update debate generation tests"
```

---

## 📊 Success Metrics

### Platform-Wide Goals

**Quality (debate-quality-auditor):**
- ✅ 85%+ debates pass quality threshold (≥7.0/10)
- ✅ All 196 personas tested at least once per quarter
- ✅ Average score ≥ 7.5/10 across all debates
- ✅ Citation usage ≥ 50% of messages

**Testing (test-maintainer):**
- ✅ Backend coverage ≥ 60% (from 15.85%)
- ✅ Frontend coverage ≥ 50% (from 5.61%)
- ✅ Critical modules ≥ 80% (debates/generator.py, payments/views.py, users/views.py)
- ✅ All tests passing with < 30s execution time

**Personas (persona-manager):**
- ✅ All 196 personas pass validation (100%)
- ✅ Average persona quality score ≥ 8.0/10
- ✅ 100% have Wikipedia links
- ✅ 80%+ have Stanford Encyclopedia links (major figures)
- ✅ 60+ personas linked to primary texts

### Current Status (Oct 19, 2025)

**Testing:**
- Backend: 15.85% coverage (39 tests) ❌ **Needs improvement**
- Frontend: 5.61% coverage (34 tests) ❌ **Needs improvement**

**Personas:**
- 196 total personas ✅
- 100 primary texts in library ✅
- 60 personas with citation patterns ✅

**Quality:**
- No systematic auditing yet ⚠️ **Agent will enable this**

---

## 🎯 Immediate Priorities (Per NEXT_STEPS.md)

### Week 1 (Oct 20-27, 2025)
1. **test-maintainer:** Increase backend coverage to 40%
   - Focus: debates/generator.py, payments/views.py, users/views.py
   - Target: +25% coverage
2. **persona-manager:** Validate all 196 personas
   - Ensure 100% pass validation
   - Fix any critical errors

### Week 2 (Oct 27 - Nov 3, 2025)
1. **test-maintainer:** Increase frontend coverage to 30%
   - Focus: lib/api.ts, contexts/AuthContext.tsx, app/debates/new/page.tsx
   - Target: +25% coverage
2. **debate-quality-auditor:** Run initial baseline audit
   - Test all 196 personas with strategic debates
   - Establish quality baseline scores

### Week 3-4 (Nov 3-17, 2025)
1. **test-maintainer:** Push to 60%+ backend, 50%+ frontend
   - Final sprint to production-ready coverage
2. **debate-quality-auditor:** Run comprehensive test suites
   - Cross-tradition, same-tradition, citation, character tests
   - Address any quality issues before production

### Production Deployment (Nov 18+)
- All agents passing success metrics
- Deploy to AWS Lightsail with confidence
- Enable weekly monitoring routines

---

## 📖 Usage Guide

### How to Invoke Agents

**From Claude Code CLI:**
```bash
claude-code "<agent-name> <task description>"

# Examples:
claude-code "debate-quality-auditor: run cross-tradition test suite"
claude-code "test-maintainer: increase backend coverage to 40%"
claude-code "persona-manager: create persona for Hannah Arendt"
```

**From This Repository:**
```bash
# Claude Code will automatically detect agents in .claude/agents/
# Just reference them by name in natural language

"Run the debate quality auditor on last week's debates"
"Use test-maintainer to identify coverage gaps"
"Have persona-manager validate all personas"
```

### Agent Naming Convention

All agents use kebab-case naming:
- `debate-quality-auditor.md`
- `test-maintainer.md`
- `persona-manager.md`

Future agents should follow the same convention:
- `backend-specialist.md`
- `frontend-specialist.md`
- `e2e-test-manager.md`
- etc.

---

## 🔮 Future Agent Ideas (Phase 2-3)

### Phase 2: Development Lifecycle Support
4. **e2e-test-manager** - Playwright end-to-end testing
5. **backend-specialist** - Django/DRF/Celery/PostgreSQL expert
6. **frontend-specialist** - Next.js/React/Material-UI expert

### Phase 3: Quality & Documentation
7. **storybook-manager** - Component library and visual regression
8. **qa-auditor** - Overall health checks and status file sync

---

## 📁 Directory Structure

```
ideas/philosophical-debates/.claude/agents/
├── README.md                       # This file (agent overview)
│
├── contribution-orchestrator.md    # Contribution workflow coordinator
├── contribution-planner.md         # Implementation planner
├── contribution-implementer.md     # Code implementation
├── contribution-validator.md       # Quality gate enforcement
├── contribution-committer.md       # Git commit creation
│
├── debate-quality-auditor.md       # Debate quality assurance
├── test-maintainer.md              # Test coverage management
└── persona-manager.md              # Persona lifecycle management

Future additions:
├── e2e-test-manager.md             # Playwright testing
├── backend-specialist.md           # Backend expertise
├── frontend-specialist.md          # Frontend expertise
├── storybook-manager.md            # Component documentation
└── qa-auditor.md                   # Overall quality auditing
```

---

## 🤝 Contributing

When creating new agents:

1. **Follow Template Structure:**
   - Purpose and responsibilities
   - Current state and context
   - Workflow and implementation details
   - Usage examples
   - Success metrics
   - Output artifacts

2. **Be Specific to This Project:**
   - Reference actual file paths (backend/debates/generator.py)
   - Include code examples from the codebase
   - Align with project goals (NEXT_STEPS.md, STATUS.md)

3. **Make Agents Actionable:**
   - Clear usage examples
   - Expected outputs defined
   - Integration with other agents
   - Measurable success criteria

4. **Document Everything:**
   - What the agent does
   - When to use it
   - What it produces
   - How it integrates with workflows

---

## 📞 Support

**Project Documentation:**
- `STATUS.md` - Current development status
- `NEXT_STEPS.md` - Production deployment roadmap
- `README.md` - Project overview
- `QUICKSTART.md` - Development setup

**Agent-Specific Help:**
- Read individual agent markdown files for detailed documentation
- All agents include usage examples and expected outputs

## 🚀 Quick Start

### For Code Contributors

**Always use `/contribute` for code changes:**
```bash
/contribute "your change description"
```

This ensures:
- ✅ Proper planning and approval
- ✅ Follows project conventions
- ✅ Tests are generated
- ✅ Quality standards enforced
- ✅ Conventional commits
- ✅ Full documentation

### For Quality Assurance

**Review debate quality:**
```bash
/audit-debate recent           # Most recent debate
/audit-debate week             # Last 7 days
/audit-debate {persona-slug}   # All debates for persona
```

**Check test coverage:**
```bash
# Use test-maintainer agent
claude-code "Run test-maintainer coverage analysis"
```

**Validate personas:**
```bash
# Use persona-manager agent
claude-code "Validate all personas"
```

---

**Last Updated:** October 19, 2025
**Maintained By:** Project contributors using Claude Code
