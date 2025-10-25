---
description: Complete contribution workflow with planning, implementation, testing, validation, and commit
arguments:
  - name: description
    description: Description of the change to make
    required: true
  - name: type
    description: Change type (feat|fix|refactor|test|docs) - auto-detected if omitted
    required: false
---

You are executing the **`/contribute` command** for the The Infinite Debate project. This command orchestrates a complete contribution workflow from planning through commit.

## Command Purpose

The `/contribute` command ensures all code contributions follow project standards by:
1. Creating detailed implementation plans
2. Implementing changes following Django/Next.js conventions
3. Generating comprehensive tests
4. Validating code quality and test coverage
5. Creating conventional git commits with full documentation

## Agent Reference

Read your full agent definition at: `.claude/agents/contribution-orchestrator.md`

You are the **Contribution Orchestrator** agent responsible for coordinating all specialized agents in the workflow.

## Input Processing

**User provided:**
- Description: `{description argument}`
- Type (optional): `{type argument}`

**Your tasks:**
1. Parse description for intent and scope
2. Determine change type if not provided (feat/fix/refactor/test/docs)
3. Identify affected systems (backend/frontend/both)
4. Generate feature name for directory structure (kebab-case)

## Workflow Phases

You will coordinate 6 specialized agents in sequence:

### 1. Planning Phase
**Agent:** contribution-planner
**Action:** Analyze requirements and create implementation plan
**Output:** `.reports/contributions/YYYY-MM-DD/{feature-name}/plan.md`

### 2. User Approval Gate
**Action:** Present plan summary to user, wait for approval
**Decision:** Proceed if approved, cancel if rejected

### 3. Implementation Phase
**Agent:** contribution-implementer
**Action:** Execute code changes following plan
**Output:** `.reports/contributions/YYYY-MM-DD/{feature-name}/implementation.md`

### 4. Testing Phase
**Agent:** test-maintainer
**Action:** Generate tests for new/modified code
**Output:** `.reports/contributions/YYYY-MM-DD/{feature-name}/tests.md`

### 5. Validation Phase
**Agent:** contribution-validator
**Action:** Run linters, tests, coverage checks
**Output:** `.reports/contributions/YYYY-MM-DD/{feature-name}/validation.md`
**Gate:** Only proceed if validation PASSES

### 6. Commit Phase
**Agent:** contribution-committer
**Action:** Create conventional commit with all changes
**Output:** `.reports/contributions/YYYY-MM-DD/{feature-name}/commit.md`

### 7. Workflow Documentation
**Your Task:** Write workflow.md documenting the entire process

## Usage Examples

### Example 1: Feature Addition (feat)

```bash
/contribute "Add minimum 2-round requirement for debates"
```

**Expected Flow:**
1. Type detected: `feat` (new validation rule)
2. Scope detected: `both` (backend + frontend)
3. Feature name: `minimum-rounds`
4. Planner analyzes: Debate model, serializer, frontend form
5. User approves plan
6. Implementer: Adds validators, updates UI
7. Test maintainer: Creates 5 new tests
8. Validator: All tests pass, coverage +0.5%
9. Committer: `feat(debates): add minimum 2-round requirement`

**Reports Created:**
```
.reports/contributions/2025-10-19/minimum-rounds/
├── workflow.md
├── plan.md
├── implementation.md
├── tests.md
├── validation.md
└── commit.md
```

---

### Example 2: Bug Fix

```bash
/contribute fix "Citation links broken on mobile"
```

**Expected Flow:**
1. Type: `fix` (user specified)
2. Scope: `frontend`
3. Feature name: `citation-links-mobile`
4. Planner: Identifies MessageContent.tsx issue
5. User approves
6. Implementer: Fixes CSS media query
7. Test maintainer: Adds responsive test
8. Validator: Tests pass
9. Committer: `fix(ui): correct citation links on mobile`

---

### Example 3: Refactoring

```bash
/contribute "Extract debate credit calculation to utility function"
```

**Expected Flow:**
1. Type detected: `refactor` (code reorganization)
2. Scope: `backend`
3. Feature name: `extract-credit-calculation`
4. Planner: Move logic from serializer to utils.py
5. User approves
6. Implementer: Creates utils function, updates references
7. Test maintainer: Adds utility tests
8. Validator: No behavior changes, tests pass
9. Committer: `refactor(debates): extract credit calculation to utility`

---

### Example 4: Test Addition

```bash
/contribute test "Add integration tests for Stripe webhooks"
```

**Expected Flow:**
1. Type: `test` (user specified)
2. Scope: `backend`
3. Feature name: `stripe-webhook-tests`
4. Planner: Identifies payments/tests/test_webhooks.py
5. User approves
6. Implementer: Minimal (test file only)
7. Test maintainer: Creates comprehensive webhook tests
8. Validator: New tests pass, coverage +15%
9. Committer: `test(payments): add stripe webhook integration tests`

---

## Quality Standards Enforced

### Test Coverage
- Backend: 60%+ target, no decrease allowed
- Frontend: 60%+ target, no decrease allowed
- New files: Should have 60%+ coverage

### Code Quality
- **Backend:**
  - ESLint: 0 errors
  - TypeScript: Strict mode, 0 type errors
  - No console.log or debugger statements

- **Frontend:**
  - Black: Formatting (if configured)
  - MyPy: Type checking (if configured)
  - No print() or pdb statements

### Commit Format
- **Type:** feat | fix | refactor | test | docs | style | chore
- **Scope:** Django app name or frontend area
- **Subject:** Imperative mood, < 72 chars
- **Body:** Explains what and why
- **Footer:** Co-Authored-By: Claude <noreply@anthropic.com>

### Documentation
- All public functions have docstrings
- Complex logic has inline comments
- README updated for user-facing changes
- Migration files reviewed for correctness

## Report Structure

All workflow outputs are committed to git:

```
.reports/contributions/
└── YYYY-MM-DD/
    └── {feature-name}/
        ├── workflow.md        # Orchestration log (you create)
        ├── plan.md            # From planner
        ├── implementation.md  # From implementer
        ├── tests.md           # From test-maintainer
        ├── validation.md      # From validator
        └── commit.md          # From committer
```

## Error Handling

### Planning Failure
- Log error in workflow.md
- Status: `failed_at_planning`
- Do not proceed

### User Rejects Plan
- Log rejection in workflow.md
- Status: `cancelled_at_planning`
- Preserve plan for reference

### Implementation Failure
- Log error in workflow.md
- Status: `failed_at_implementation`
- Consider rollback

### Validation Failure (FAIL status)
- Present validation issues to user
- Status: `failed_validation`
- Do not commit
- Options: Fix manually, retry, cancel

### Commit Failure
- Log error in workflow.md
- Status: `failed_at_commit`
- Changes made but not committed

## Success Output

When workflow completes successfully, display:

```
✅ Contribution Complete!

Feature: {feature-name}
Type: {feat|fix|refactor|test|docs}
Commit: {hash}

Summary:
- Files modified: X (Y backend, Z frontend)
- Tests added: N
- Coverage: +A% backend, +B% frontend
- All quality gates: PASSED

Reports: .reports/contributions/YYYY-MM-DD/{feature-name}/

Commit Message:
{type}({scope}): {subject}

Next Steps:
- Push to remote: git push origin main
- Monitor CI/CD pipeline
- Create pull request (if applicable)
```

## Troubleshooting

**If agent fails to invoke:**
- Verify agent file exists: `.claude/agents/{agent-name}.md`
- Check Task tool parameters
- Read error message for specific issue

**If tests fail:**
- Review validation.md for detailed errors
- Fix issues manually or re-run implementer
- Consider breaking change into smaller parts

**If validation takes too long:**
- Some tests may be slow (acceptable)
- Check if Docker containers are running
- Ensure database is accessible

**If commit fails:**
- Check git status for conflicts
- Ensure all files are staged
- Verify commit message format

## Important Notes

- **Reports are committed** - They become permanent project history
- **Validation is strict** - Must pass all gates to commit
- **User approval required** - Plan must be approved before implementation
- **No hardcoded values** - Agents discover state dynamically
- **Follow conventions** - Django patterns for backend, Next.js patterns for frontend

---

**Ready to start the contribution workflow!**

Read `.claude/agents/contribution-orchestrator.md` for complete workflow details and begin coordinating the specialized agents.
