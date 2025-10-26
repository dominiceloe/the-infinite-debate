# Contributing to The Infinite Debate

Welcome! This project uses **GitHub Flow** for a simple, effective branching strategy.

---

## 🌿 Branching Strategy: GitHub Flow

We use a simplified workflow with one protected branch:

- **`main`** - Production-ready code (auto-deploys to Vercel + AWS)
- **Feature branches** - All development work

---

## 📋 Workflow

### 1. Create a Feature Branch

```bash
# Pull latest main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

**Branch naming conventions:**
- `feature/add-email-notifications` - New features
- `fix/citation-rendering-bug` - Bug fixes
- `hotfix/critical-stripe-issue` - Urgent production fixes
- `docs/update-quickstart` - Documentation updates
- `refactor/debate-generator` - Code refactoring
- `test/persona-api-coverage` - Test improvements

### 2. Make Changes

```bash
# Make your changes
# Write tests for new code
# Run tests locally

# Backend tests
cd backend
docker compose exec web pytest --cov

# Frontend tests
cd frontend
npm test

# Lint your code
npm run lint  # Frontend
cd backend && make lint  # Backend
```

### 3. Commit Your Changes

Use **conventional commits** for clear history:

```bash
git add .
git commit -m "feat: add email notifications for debate completion"
```

**Commit types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests
- `chore:` - Maintenance tasks

### 4. Push and Create Pull Request

```bash
# Push your branch
git push -u origin feature/your-feature-name
```

Then go to GitHub and create a Pull Request:
1. Visit https://github.com/dominiceloe/the-infinite-debate
2. Click "Compare & pull request"
3. Fill out the PR template
4. Request review (if working with others)
5. Wait for CI checks to pass

### 5. Merge to Main

Once approved and all checks pass:
1. **Squash and merge** (preferred) - Creates clean history
2. Delete the feature branch
3. Pull latest `main` locally:

```bash
git checkout main
git pull origin main
git branch -d feature/your-feature-name  # Delete local branch
```

---

## 🚫 Branch Protection Rules

The `main` branch is protected:

- ✅ **Pull requests required** - No direct pushes
- ✅ **Status checks required** - Tests must pass
- ✅ **Up-to-date branches** - Must be current with main
- ✅ **No force pushes** - History is preserved
- ✅ **No deletions** - Branch cannot be deleted

---

## ✅ Pull Request Checklist

Before creating a PR, ensure:

- [ ] **Tests added/updated** for new code
- [ ] **All tests passing** locally (backend + frontend)
- [ ] **Code linted** with no errors
- [ ] **Documentation updated** (if needed)
- [ ] **No .env files** or secrets committed
- [ ] **Commit messages** follow conventional format
- [ ] **PR description** explains what/why

---

## 🧪 Testing Requirements

All PRs must maintain or improve test coverage:

- **Backend:** Minimum 80% coverage (currently 84%)
- **Frontend:** Minimum 90% coverage (currently 94%)

Run coverage reports:

```bash
# Backend
cd backend
docker compose exec web pytest --cov --cov-report=html
open htmlcov/index.html

# Frontend
cd frontend
npm run test:coverage
```

---

## 🔍 Code Review Guidelines

### For Authors
- Keep PRs focused (one feature/fix per PR)
- Provide context in PR description
- Link related issues
- Respond to feedback promptly

### For Reviewers
- Review within 24-48 hours
- Focus on functionality, tests, and maintainability
- Be constructive and kind
- Approve only when ready for production

---

## 🚀 Deployment

Deployments happen automatically:

**Frontend (Vercel):**
- Merges to `main` → auto-deploy to production
- Feature branches → preview deployments

**Backend (AWS Lightsail):**
- Merges to `main` → manual deploy (for now)
- See [DEPLOYMENT.md](DEPLOYMENT.md) for instructions

---

## 🐛 Hotfixes (Critical Production Issues)

For urgent production fixes:

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-issue-description

# Make minimal fix
# Test thoroughly
# Commit and push

git push -u origin hotfix/critical-issue-description
```

Create PR with `[HOTFIX]` in title for priority review.

---

## 📚 Resources

- **Project Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Getting Started:** [QUICKSTART.md](QUICKSTART.md)
- **Deployment:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **GitHub Setup:** [GITHUB_SETUP.md](GITHUB_SETUP.md)
- **Makefile Commands:** [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)

---

## 🤝 Questions?

Open an issue or reach out to the maintainer.

**Happy coding!** 🎉
