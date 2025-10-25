# GitHub Repository Setup Guide

**Project:** The Infinite Debate
**Last Updated:** October 25, 2025

This guide walks you through setting up the GitHub repository with all necessary configurations, workflows, and templates.

---

## Table of Contents

1. [Initial Repository Setup](#initial-repository-setup)
2. [Repository Settings](#repository-settings)
3. [Branch Protection Rules](#branch-protection-rules)
4. [GitHub Actions Workflows](#github-actions-workflows)
5. [Issue & PR Templates](#issue--pr-templates)
6. [GitHub Secrets Configuration](#github-secrets-configuration)
7. [GitHub Pages (Documentation)](#github-pages-documentation)
8. [Webhooks Configuration](#webhooks-configuration)
9. [Repository Labels](#repository-labels)
10. [Collaborator Access](#collaborator-access)

---

## Initial Repository Setup

### Create Repository on GitHub

1. **Navigate to GitHub:**
   - Go to https://github.com/new
   - Or from your profile: Repositories → New

2. **Repository Configuration:**
   ```
   Repository name: philosophical-debates
   Description: AI-powered debates between historical thinkers with full-text primary source integration

   Visibility:
   - [ ] Public (recommended for open-source)
   - [x] Private (if keeping proprietary)

   Initialize repository:
   - [ ] Do NOT add README (we have one)
   - [ ] Do NOT add .gitignore (we have one)
   - [ ] Do NOT add license yet
   ```

3. **Click "Create repository"**

### Push Existing Code to GitHub

```bash
# From your project root
cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates

# Initialize git (if not already)
git init

# Add all files
git add .

# Create initial commit
git commit -m "feat: initial commit - production-ready debate platform"

# Add GitHub remote (replace with your username)
git remote add origin https://github.com/yourusername/philosophical-debates.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Create Production Branch

```bash
# Create production branch for deployments
git checkout -b production
git push -u origin production

# Return to main
git checkout main
```

---

## Repository Settings

### General Settings

Navigate to: **Settings → General**

#### Features
- ✅ **Issues** - Enable for bug tracking
- ✅ **Projects** - Enable for project management
- ✅ **Discussions** - Optional (for community Q&A)
- ✅ **Wiki** - Optional (external docs are in repo)

#### Pull Requests
- ✅ **Allow merge commits**
- ✅ **Allow squash merging** (recommended)
- ✅ **Allow rebase merging**
- ✅ **Automatically delete head branches** (cleanup after merge)
- ✅ **Allow auto-merge**

#### Default Branch
- Set to: `main`

### Security Settings

Navigate to: **Settings → Code security and analysis**

#### Dependabot
- ✅ **Dependabot alerts** - Enable
- ✅ **Dependabot security updates** - Enable
- ✅ **Dependabot version updates** - Enable

**Create `.github/dependabot.yml`:**
```yaml
version: 2
updates:
  # Backend Python dependencies
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    reviewers:
      - "yourusername"
    labels:
      - "dependencies"
      - "backend"

  # Frontend npm dependencies
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    reviewers:
      - "yourusername"
    labels:
      - "dependencies"
      - "frontend"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

#### Code Scanning
- ✅ **CodeQL analysis** - Enable (GitHub Advanced Security)

**Create `.github/workflows/codeql.yml`:**
```yaml
name: "CodeQL"

on:
  push:
    branches: [ main, production ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 6 AM

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [ 'javascript', 'python' ]

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v3
      with:
        languages: ${{ matrix.language }}

    - name: Autobuild
      uses: github/codeql-action/autobuild@v3

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v3
```

---

## Branch Protection Rules

Navigate to: **Settings → Branches → Add branch protection rule**

### Protect `main` Branch

**Branch name pattern:** `main`

#### Protect matching branches
- ✅ **Require a pull request before merging**
  - ✅ Require approvals: 1 (or 2 for team projects)
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require review from Code Owners (if using CODEOWNERS)

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - **Required checks:**
    - `backend-tests`
    - `frontend-tests`
    - `lint-backend`
    - `lint-frontend`

- ✅ **Require conversation resolution before merging**
- ✅ **Require linear history** (enforces rebase/squash)
- ✅ **Include administrators** (enforce rules for everyone)

#### Rules applied to everyone including administrators
- ✅ **Allow force pushes** - Disable
- ✅ **Allow deletions** - Disable

### Protect `production` Branch

**Branch name pattern:** `production`

Same as `main`, but add:
- ✅ **Require deployments to succeed before merging**
  - Environment: `production` (configure in Environments)

---

## GitHub Actions Workflows

### Create `.github/workflows/` Directory

```bash
mkdir -p .github/workflows
```

### 1. Backend CI/CD Workflow

**Create `.github/workflows/backend-ci.yml`:**

```yaml
name: Backend CI

on:
  push:
    branches: [ main, production ]
    paths:
      - 'backend/**'
      - '.github/workflows/backend-ci.yml'
  pull_request:
    branches: [ main ]
    paths:
      - 'backend/**'

jobs:
  lint:
    name: Lint Backend
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
        cache: 'pip'

    - name: Install dependencies
      run: |
        cd backend
        pip install flake8 black isort
        pip install -r requirements.txt

    - name: Run Black
      run: cd backend && black --check .

    - name: Run isort
      run: cd backend && isort --check-only .

    - name: Run Flake8
      run: cd backend && flake8 .

  test:
    name: Backend Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
        cache: 'pip'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-django

    - name: Run tests with coverage
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key
        DEBUG: True
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      run: |
        cd backend
        pytest --cov=. --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: backend/coverage.xml
        flags: backend
        name: backend-coverage

  security:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Run Bandit security scan
      run: |
        pip install bandit
        cd backend
        bandit -r . -f json -o bandit-report.json || true

    - name: Upload Bandit results
      uses: actions/upload-artifact@v4
      with:
        name: bandit-results
        path: backend/bandit-report.json
```

### 2. Frontend CI/CD Workflow

**Create `.github/workflows/frontend-ci.yml`:**

```yaml
name: Frontend CI

on:
  push:
    branches: [ main, production ]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-ci.yml'
  pull_request:
    branches: [ main ]
    paths:
      - 'frontend/**'

jobs:
  lint:
    name: Lint Frontend
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install dependencies
      run: |
        cd frontend
        npm ci

    - name: Run ESLint
      run: |
        cd frontend
        npm run lint

  test:
    name: Frontend Tests
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install dependencies
      run: |
        cd frontend
        npm ci

    - name: Run tests with coverage
      run: |
        cd frontend
        npm test -- --run --coverage

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: frontend/coverage/coverage-final.json
        flags: frontend
        name: frontend-coverage

  build:
    name: Build Frontend
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install dependencies
      run: |
        cd frontend
        npm ci

    - name: Build
      run: |
        cd frontend
        npm run build
      env:
        NEXT_PUBLIC_API_URL: https://api.theinfinitedebate.com/api
```

### 3. Combined CI Workflow (All Tests)

**Create `.github/workflows/ci.yml`:**

```yaml
name: CI

on:
  push:
    branches: [ main, production ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    uses: ./.github/workflows/backend-ci.yml
    secrets: inherit

  frontend-tests:
    uses: ./.github/workflows/frontend-ci.yml

  all-tests-passed:
    name: All Tests Passed
    needs: [backend-tests, frontend-tests]
    runs-on: ubuntu-latest
    steps:
      - name: Success
        run: echo "All CI checks passed!"
```

### 4. Auto-Deploy to Production

**Create `.github/workflows/deploy-production.yml`:**

```yaml
name: Deploy to Production

on:
  push:
    branches: [ production ]

jobs:
  deploy-backend:
    name: Deploy Backend to AWS Lightsail
    runs-on: ubuntu-latest
    environment: production

    steps:
    - uses: actions/checkout@v4

    - name: Configure SSH
      run: |
        mkdir -p ~/.ssh
        echo "${{ secrets.LIGHTSAIL_SSH_KEY }}" > ~/.ssh/lightsail.pem
        chmod 600 ~/.ssh/lightsail.pem
        ssh-keyscan -H ${{ secrets.LIGHTSAIL_HOST }} >> ~/.ssh/known_hosts

    - name: Deploy to server
      run: |
        ssh -i ~/.ssh/lightsail.pem ubuntu@${{ secrets.LIGHTSAIL_HOST }} << 'EOF'
          cd /opt/the-infinite-debate
          git pull origin production
          cd backend
          docker compose -f docker-compose.yml -f docker-compose.prod.yml build
          docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
          docker compose exec -T web python manage.py migrate
          docker compose exec -T web python manage.py collectstatic --noinput
        EOF

    - name: Verify deployment
      run: |
        sleep 10
        curl -f https://api.theinfinitedebate.com/health/ || exit 1

  deploy-frontend:
    name: Deploy Frontend to Vercel
    runs-on: ubuntu-latest
    environment: production

    steps:
    - name: Trigger Vercel deployment
      run: |
        curl -X POST "https://api.vercel.com/v1/integrations/deploy/${{ secrets.VERCEL_DEPLOY_HOOK }}"

    - name: Wait for deployment
      run: sleep 60

    - name: Verify frontend
      run: |
        curl -f https://theinfinitedebate.com || exit 1
```

---

## Issue & PR Templates

### Create Issue Templates

**Create `.github/ISSUE_TEMPLATE/bug_report.md`:**

```markdown
---
name: Bug Report
about: Report a bug to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
A clear and concise description of the bug.

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Screenshots
If applicable, add screenshots.

## Environment
- **Browser:** [e.g., Chrome 120]
- **OS:** [e.g., macOS 14]
- **Device:** [e.g., iPhone 12, Desktop]
- **Version:** [e.g., v1.0.0]

## Additional Context
Any other relevant information.

## Possible Solution
Optional: Suggest a fix or reason for the bug.
```

**Create `.github/ISSUE_TEMPLATE/feature_request.md`:**

```markdown
---
name: Feature Request
about: Suggest a new feature
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## Feature Description
Clear description of the feature you'd like to see.

## Problem It Solves
What problem does this feature address?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Other approaches you've thought about.

## User Stories
- As a [user type], I want [goal] so that [benefit]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Additional Context
Screenshots, mockups, or examples.

## Priority
- [ ] Critical (blocking)
- [ ] High (important)
- [ ] Medium (nice to have)
- [ ] Low (future consideration)
```

**Create `.github/ISSUE_TEMPLATE/persona_request.md`:**

```markdown
---
name: Persona Request
about: Request addition of a new historical figure
title: '[PERSONA] '
labels: persona, enhancement
assignees: ''
---

## Persona Details
- **Name:** [Full name]
- **Era:** [e.g., 1643-1727]
- **Category:** [Philosopher / Theologian / Scientist]
- **Subcategory:** [e.g., Modern Western, Christianity, Physics]

## Relevance
Why should this persona be added?

## Primary Works
Key texts authored by this figure:
1.
2.
3.

## Debate Style
Brief description of how they would argue (optional):

## External Links
- Wikipedia:
- Stanford Encyclopedia:
- Other:

## Tier Suggestion
- [ ] Free (30 total)
- [ ] Starter (60 total)
- [ ] Pro (90 total)
- [ ] Enterprise (196 total)

Reasoning:
```

### Create Pull Request Template

**Create `.github/PULL_REQUEST_TEMPLATE.md`:**

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Test coverage improvement

## Related Issue
Closes #[issue number]

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
How was this tested?

### Test Coverage
- [ ] Backend tests added/updated
- [ ] Frontend tests added/updated
- [ ] All tests passing locally
- [ ] Coverage maintained/improved

### Manual Testing
- [ ] Tested on Chrome
- [ ] Tested on Firefox
- [ ] Tested on Safari
- [ ] Tested on mobile

## Screenshots
If applicable, add screenshots.

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added proving fix/feature works
- [ ] Dependent changes merged and published

## Deployment Notes
Any special deployment steps or environment variable changes?

## Rollback Plan
How to rollback if this breaks production?
```

---

## GitHub Secrets Configuration

Navigate to: **Settings → Secrets and variables → Actions**

### Repository Secrets

Add these secrets for GitHub Actions:

**Backend/API:**
- `ANTHROPIC_API_KEY` - Anthropic API key for tests
- `SECRET_KEY` - Django secret key for production
- `DATABASE_URL` - Production database URL (optional)

**Deployment:**
- `LIGHTSAIL_SSH_KEY` - Private SSH key for AWS Lightsail
- `LIGHTSAIL_HOST` - Lightsail server IP or hostname
- `VERCEL_DEPLOY_HOOK` - Vercel deploy hook URL

**Monitoring:**
- `SENTRY_AUTH_TOKEN` - Sentry authentication token
- `SENTRY_DSN` - Sentry project DSN

**External Services:**
- `CODECOV_TOKEN` - Codecov upload token (optional)

### Environment Secrets

Create environment: **Settings → Environments → New environment**

**Name:** `production`

**Environment secrets** (same as above but for production deployment):
- All production API keys
- Deployment credentials

**Protection rules:**
- ✅ Required reviewers: 1
- ✅ Wait timer: 0 minutes (or 5 for extra safety)

---

## GitHub Pages (Documentation)

Optional: Host documentation on GitHub Pages

### Enable GitHub Pages

Navigate to: **Settings → Pages**

**Source:** Deploy from a branch
**Branch:** `main` / `docs` folder (or `/` if using root)
**Custom domain:** docs.theinfinitedebate.com (optional)

### Create Documentation Site

**Create `docs/index.html`:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Infinite Debate - Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .doc-link {
            display: block;
            padding: 10px;
            margin: 10px 0;
            background: #f5f5f5;
            border-left: 4px solid #0066cc;
            text-decoration: none;
            color: #333;
        }
    </style>
</head>
<body>
    <h1>The Infinite Debate - Documentation</h1>

    <h2>Getting Started</h2>
    <a href="../README.md" class="doc-link">📖 README</a>
    <a href="../QUICKSTART.md" class="doc-link">🚀 Quick Start Guide</a>

    <h2>Architecture</h2>
    <a href="../ARCHITECTURE.md" class="doc-link">🏗️ Architecture Overview</a>
    <a href="../CLAUDE.md" class="doc-link">🤖 Claude Code Guide</a>

    <h2>Deployment</h2>
    <a href="../DEPLOYMENT.md" class="doc-link">☁️ Production Deployment</a>
    <a href="../AWS_SETUP_STEPS.md" class="doc-link">🌐 AWS Setup</a>

    <h2>Development</h2>
    <a href="../MAKEFILE_GUIDE.md" class="doc-link">⚙️ Makefile Commands</a>
    <a href="../STATUS.md" class="doc-link">📊 Project Status</a>
    <a href="../NEXT_STEPS.md" class="doc-link">📝 Roadmap</a>
</body>
</html>
```

---

## Webhooks Configuration

### Stripe Webhooks

Navigate to: **Stripe Dashboard → Webhooks**

**Endpoint URL:** `https://api.theinfinitedebate.com/api/payments/webhook/`

**Events to listen for:**
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

**Webhook secret:** Copy to `.env` as `STRIPE_WEBHOOK_SECRET`

### Sentry Webhooks (Optional)

Navigate to: **Sentry → Project Settings → Webhooks**

**Callback URL:** `https://api.theinfinitedebate.com/api/webhooks/sentry/`

**Events:** Issue alerts

---

## Repository Labels

Navigate to: **Issues → Labels**

### Create Standard Labels

**Priority:**
- `priority: critical` (red) - Blocking production
- `priority: high` (orange) - Important
- `priority: medium` (yellow) - Normal
- `priority: low` (green) - Future

**Type:**
- `type: bug` (red) - Something isn't working
- `type: feature` (blue) - New feature request
- `type: enhancement` (blue) - Improvement to existing feature
- `type: refactor` (yellow) - Code refactoring
- `type: docs` (green) - Documentation
- `type: security` (red) - Security issue

**Component:**
- `backend` (purple) - Backend/Django changes
- `frontend` (purple) - Frontend/Next.js changes
- `api` (purple) - API changes
- `database` (purple) - Database/migrations
- `ui/ux` (pink) - User interface/experience
- `personas` (teal) - Persona system
- `debates` (teal) - Debate generation
- `payments` (teal) - Stripe/subscriptions

**Status:**
- `status: in progress` (yellow) - Currently being worked on
- `status: blocked` (red) - Blocked by external dependency
- `status: needs review` (orange) - Awaiting review
- `status: wontfix` (gray) - Won't be addressed

**Meta:**
- `good first issue` (green) - Good for newcomers
- `help wanted` (green) - Extra attention needed
- `dependencies` (blue) - Dependency updates

---

## Collaborator Access

Navigate to: **Settings → Collaborators and teams**

### Access Levels

**Admin** (Full access):
- Your account

**Write** (Push, pull, create PRs):
- Trusted contributors

**Triage** (Manage issues/PRs):
- Community moderators

**Read** (View and clone):
- External contributors (if private repo)

### Create CODEOWNERS File

**Create `.github/CODEOWNERS`:**

```plaintext
# Default owner for everything
* @yourusername

# Backend owners
/backend/ @yourusername
/backend/debates/ @yourusername
/backend/personas/ @yourusername

# Frontend owners
/frontend/ @yourusername
/frontend/app/ @yourusername
/frontend/components/ @yourusername

# Infrastructure
/docker-compose*.yml @yourusername
/.github/workflows/ @yourusername
/Makefile @yourusername

# Documentation
*.md @yourusername
/docs/ @yourusername

# Configuration
/.github/ @yourusername
```

---

## Post-Setup Verification

### Checklist

- [ ] Repository created on GitHub
- [ ] Code pushed to `main` branch
- [ ] `production` branch created
- [ ] Branch protection rules configured
- [ ] GitHub Actions workflows added
- [ ] Issue/PR templates created
- [ ] Repository secrets configured
- [ ] Labels created
- [ ] Dependabot configured
- [ ] CodeQL security scanning enabled
- [ ] CODEOWNERS file added
- [ ] Webhooks configured (Stripe, Sentry)

### Test Workflows

```bash
# Trigger CI workflow
git checkout -b test/ci-workflow
echo "test" >> README.md
git add README.md
git commit -m "test: trigger CI workflow"
git push origin test/ci-workflow

# Create PR and verify:
# - All checks run (backend, frontend, lint)
# - Branch protection prevents merge if tests fail
# - PR template appears
```

### Verify GitHub Pages

Visit: `https://yourusername.github.io/philosophical-debates/`

---

## Maintenance

### Weekly Tasks
- [ ] Review Dependabot PRs
- [ ] Check failed workflow runs
- [ ] Review open issues

### Monthly Tasks
- [ ] Update GitHub Actions versions
- [ ] Review and update labels
- [ ] Audit secrets (rotate if needed)
- [ ] Review CodeQL security alerts

---

## Additional Resources

- **GitHub Actions Documentation:** https://docs.github.com/en/actions
- **Branch Protection:** https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches
- **Dependabot:** https://docs.github.com/en/code-security/dependabot
- **CodeQL:** https://codeql.github.com/docs/

---

**Last Updated:** October 25, 2025
**Maintained By:** @yourusername
