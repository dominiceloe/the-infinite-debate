# Docker Development Setup

## Overview

This project uses Docker Compose's **override file pattern** for development:

- **`docker-compose.yml`** - Production configuration (committed)
- **`docker-compose.override.yml`** - Development overrides (committed)

Docker Compose automatically merges these files in development, but production can exclude the override.

## Development Mode (Default)

When you run `docker compose up -d` locally:

```bash
cd backend
docker compose up -d
```

**What happens:**
1. Docker Compose reads `docker-compose.yml`
2. Docker Compose reads `docker-compose.override.yml`
3. Automatically **merges** them together
4. Your local code is mounted to `/app` in containers
5. Django uses `runserver` which auto-reloads on code changes

**Benefits:**
- ✅ Edit code locally, see changes immediately
- ✅ No need to rebuild Docker images
- ✅ No need to copy files manually
- ✅ Django auto-reloads on save

## Production Mode

In production, **explicitly exclude** the override file:

```bash
docker compose -f docker-compose.yml up -d
```

The `-f` flag tells Docker Compose to use ONLY the specified file(s).

**What's different in production:**
- Code is baked into the Docker image (not mounted)
- Uses Gunicorn instead of runserver
- No auto-reload
- More stable and performant

## When to Rebuild

You **don't** need to rebuild for:
- ✅ Python code changes (`.py` files)
- ✅ Template changes
- ✅ Test changes

You **do** need to rebuild for:
- ❌ `requirements.txt` changes (new packages)
- ❌ `Dockerfile` changes
- ❌ System dependency changes

```bash
docker compose build web celery
docker compose up -d
```

## File Structure

```
backend/
├── docker-compose.yml          # Base config (production)
├── docker-compose.override.yml # Dev overrides (auto-merged locally)
├── Dockerfile                  # Image definition
└── .env                        # Environment variables
```

## Troubleshooting

### Changes not appearing?

**Check 1:** Is the volume mounted?
```bash
docker compose exec web ls -la /app/debates/
# Should show your local files with recent timestamps
```

**Check 2:** Is the override file being used?
```bash
docker compose config
# Should show merged configuration with volume mounts
```

**Check 3:** Restart services
```bash
docker compose restart web celery
```

### Production deployment accidentally using override?

**Fix:**
Always use the `-f` flag in production:
```bash
# Wrong (uses override)
docker compose up -d

# Correct (production only)
docker compose -f docker-compose.yml up -d
```

## Why Commit the Override File?

**Pros:**
- Team consistency - all devs use same setup
- Official Docker Compose pattern
- Easy to exclude in production with `-f` flag

**Cons:**
- Requires discipline to use `-f` in production

**Alternative:** If you prefer, you can:
1. Add `docker-compose.override.yml` to `.gitignore`
2. Share it separately (wiki, onboarding docs)
3. Each developer creates their own

We've chosen to **commit it** for team consistency, with clear warnings and documentation.

## Quick Reference

| Command | Environment | Override Used? |
|---------|-------------|----------------|
| `docker compose up -d` | Development | ✅ Yes (auto) |
| `docker compose -f docker-compose.yml up -d` | Production | ❌ No |
| `docker compose build` | Both | N/A |
| `docker compose restart` | Current | Current |

## See Also

- Main project docs: `CLAUDE.md`
- Testing guide: `TESTING.md`
- Deployment checklist: `CLAUDE.md` → Deployment section
