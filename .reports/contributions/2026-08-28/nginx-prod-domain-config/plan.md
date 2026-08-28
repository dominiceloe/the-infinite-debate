# Plan: Fix Production nginx Config Domain (promptthepast.com → theinfinitedebate.com)

**Date:** 2026-08-28
**Type:** fix
**Complexity:** SMALL (2 files, ~10 lines)
**Scope:** backend (infrastructure config only — no application code)
**Branch:** `fix/nginx-prod-domain-config` (branched from `origin/main` @ 0e48b2f)

## Context / Why

Production outage post-mortem (2026-08-28). The site went down twice:

1. **First outage:** api.theinfinitedebate.com served an SSL certificate that expired
   2026-03-25. Certbot had been renewing correctly the whole time; nginx (up 6
   months) never reloaded, so it served the stale cert from memory.
2. **Second outage (after server reboot):** port 443 went dark entirely. Root cause:
   the nginx container was started with the dev override merged
   (`docker-compose.yml` + `docker-compose.override.yml`), bind-mounting
   `nginx-dev.conf` (HTTP-only) as `/etc/nginx/nginx.conf`. It had only worked
   before because the container held a stale bind-mount inode containing an old
   hand-fixed SSL config; the reboot re-resolved the mount to the real dev file.

The repo's production `backend/nginx.conf` could not be used as a drop-in fix
because it still references the project's **old domain** `promptthepast.com` —
the Let's Encrypt certs on the server are for `api.theinfinitedebate.com`.
A corrected config was hot-fixed onto the server (written over the mounted file
and reloaded; site verified up). This contribution makes the repo match reality
so the hotfix isn't clobbered by a future `git pull` + container restart.

## Changes

### 1. `backend/nginx.conf` (4 lines)

Replace all `promptthepast.com` domain references with `theinfinitedebate.com`:

| Line | Before | After |
|---|---|---|
| 27 | `server_name api.promptthepast.com promptthepast.com www.promptthepast.com;` | `server_name api.theinfinitedebate.com theinfinitedebate.com www.theinfinitedebate.com;` |
| 43 | `server_name api.promptthepast.com;` | `server_name api.theinfinitedebate.com;` |
| 46 | `ssl_certificate /etc/letsencrypt/live/api.promptthepast.com/fullchain.pem;` | `.../live/api.theinfinitedebate.com/fullchain.pem;` |
| 47 | `ssl_certificate_key /etc/letsencrypt/live/api.promptthepast.com/privkey.pem;` | `.../live/api.theinfinitedebate.com/privkey.pem;` |

This exact resulting config is what is now live on the production server
(validated there with `nginx -t` and serving traffic).

### 2. `backend/docker-compose.yml` (1 line)

Add `restart: unless-stopped` to the `certbot` service. Every other service has
it; certbot did not, meaning a host reboot silently kills certificate renewal.
(Already applied to the live container via `docker update` during the incident.)

## Out of Scope

- `listen 443 ssl http2` deprecation warning (cosmetic; works on nginx:alpine)
- Automating nginx reload after cert renewal (host cron added during incident;
  a compose-level deploy-hook is a possible future improvement)
- `promptthepast.com` mentions in `archive/docs/` (historical records)
- Recreating the production stack with `-f docker-compose.yml` (server-side
  operational task, documented in incident notes, not a repo change)

## Testing

No application code changed — pytest/Vitest do not apply. Validation is:
1. Config syntax already proven: identical content passed `nginx -t` in the
   production nginx container and is serving traffic now.
2. `docker compose config` parses cleanly with the restart-policy addition (if
   Docker available locally; otherwise YAML review).
3. Grep confirms no remaining `promptthepast` references outside `archive/`.

## Success Criteria

- `backend/nginx.conf` contains only `theinfinitedebate.com` domains
- `certbot` service has `restart: unless-stopped`
- No other files modified
- Conventional commit on `fix/nginx-prod-domain-config`, pushed for PR to main

## Approval

Change and branching strategy explicitly requested/approved by user in
conversation ("yes, we are on an odd branch tho so make sure to branch off of
main") after incident walkthrough.
