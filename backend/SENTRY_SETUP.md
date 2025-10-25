# Sentry Error Tracking & Performance Monitoring Setup

## Overview

Sentry is configured for error tracking, performance monitoring, and profiling in the Philosophical Debates platform. It integrates with Django, Celery, and Redis to provide comprehensive observability.

## Features Configured

### 1. Error Tracking
- **Automatic exception capture** in Django views, models, and Celery tasks
- **Stack traces** with local variables
- **Breadcrumbs** showing events leading to errors
- **User context** (when available)
- **Request data** (HTTP method, URL, headers, body)

### 2. Performance Monitoring
- **Transaction tracking** for API endpoints
- **Database query performance**
- **External API calls** (Anthropic, Stripe)
- **Celery task duration**
- **Custom performance metrics**

### 3. Profiling
- **Code-level profiling** for slow transactions
- **Function call stacks** with timing
- **Hot path identification**

### 4. Integrations
- **DjangoIntegration**: Captures Django-specific errors and performance
- **CeleryIntegration**: Monitors background task execution
- **RedisIntegration**: Tracks Redis operations

---

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Enable Sentry (set to True in production)
SENTRY_ENABLED=True

# Sentry DSN (get from sentry.io project settings)
SENTRY_DSN=https://your-key@your-org.ingest.sentry.io/project-id

# Sample rates (adjust based on traffic volume)
SENTRY_TRACES_SAMPLE_RATE=0.1      # 10% of transactions
SENTRY_PROFILES_SAMPLE_RATE=0.1    # 10% of sampled transactions

# Release tracking (use git SHA or version)
SENTRY_RELEASE=philosophical-debates@1.0.0
```

### Sample Rates Explained

**SENTRY_TRACES_SAMPLE_RATE:**
- `0.1` (10%) - Recommended for production with moderate traffic
- `1.0` (100%) - Use in staging/testing environments
- `0.01` (1%) - Use for very high traffic applications (>1M requests/day)

**SENTRY_PROFILES_SAMPLE_RATE:**
- Profiles are captured from **sampled transactions**
- `0.1` means 10% of the 10% sampled transactions = 1% total profiling
- Profiling has minimal performance impact but generates more data

---

## Getting Your Sentry DSN

### 1. Create a Sentry Account

Go to [sentry.io](https://sentry.io) and sign up (free tier available).

### 2. Create a New Project

1. Click **"Create Project"**
2. Select **"Django"** as the platform
3. Name it **"philosophical-debates"**
4. Click **"Create Project"**

### 3. Get Your DSN

After project creation, you'll see:

```
Your DSN: https://examplePublicKey@o0.ingest.sentry.io/0
```

Copy this entire URL and add it to your `.env` file.

---

## Testing Sentry

### 1. Test Error Capture (Manual)

Create a test endpoint to trigger an error:

```python
# In any views.py file (or create a test view)
from django.http import HttpResponse

def sentry_test(request):
    division_by_zero = 1 / 0  # This will raise an exception
    return HttpResponse("This line will never execute")
```

Add to `urls.py`:
```python
path('sentry-debug/', sentry_test),
```

Visit: `http://localhost/sentry-debug/`

Check Sentry dashboard - you should see the error within seconds!

### 2. Test from Django Shell

```python
docker compose --env-file .env.docker exec web python manage.py shell

# In Django shell:
import sentry_sdk
sentry_sdk.capture_message("Test message from Django shell", level="info")
sentry_sdk.capture_exception(Exception("Test exception from shell"))
```

### 3. Test Celery Integration

Trigger a debate generation task and check Sentry for:
- Task start event
- Task completion/failure
- Performance data
- Any errors during execution

### 4. Test Performance Monitoring

Make API requests and check Sentry's **Performance** tab:
- `/api/personas/` - Should show database query performance
- `/api/debates/` - Should show transaction duration
- Slow endpoints will be highlighted

---

## Sentry Dashboard Tour

### Issues Tab
- **All Errors**: Grouped by type and frequency
- **Unresolved**: Errors that need attention
- **For Review**: New errors
- **Ignored**: Muted errors

### Performance Tab
- **Transactions Overview**: API endpoint performance
- **Database Queries**: Slow queries identified
- **External Calls**: Anthropic API, Stripe calls
- **Frontend Performance** (if configured)

### Releases Tab
- Track deployments
- See which errors appeared in which releases
- Compare error rates between versions

### Alerts Tab
- Configure notifications (email, Slack, PagerDuty)
- Set thresholds (e.g., alert if error rate > 10/min)
- Create custom rules

---

## Production Best Practices

### 1. Filter Out Noise

The configuration already filters:
- ✅ Health check endpoints (`/health/`, `/ready/`)
- ✅ CSRF errors (often false positives)

Add more filters as needed in `settings.py`:

```python
ignore_errors=[
    'django.middleware.csrf.CsrfViewMiddleware',
    'rest_framework.exceptions.NotAuthenticated',  # Expected auth failures
    # Add more here
],
```

### 2. Sample Rates for Production

**Low Traffic (<10K requests/day):**
```bash
SENTRY_TRACES_SAMPLE_RATE=1.0    # 100%
SENTRY_PROFILES_SAMPLE_RATE=0.5  # 50% of traces
```

**Medium Traffic (10K-100K requests/day):**
```bash
SENTRY_TRACES_SAMPLE_RATE=0.1    # 10%
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% of traces
```

**High Traffic (>100K requests/day):**
```bash
SENTRY_TRACES_SAMPLE_RATE=0.01   # 1%
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% of traces
```

### 3. Release Tracking

Update `SENTRY_RELEASE` on each deployment:

```bash
# Use git commit SHA
SENTRY_RELEASE=philosophical-debates@$(git rev-parse --short HEAD)

# Or semantic version
SENTRY_RELEASE=philosophical-debates@1.2.3
```

This enables:
- Error tracking per release
- Regression detection
- Deployment change tracking

### 4. User Context (Optional)

If you want to track which users experience errors, enable PII:

```python
# In settings.py Sentry configuration
send_default_pii=True,
```

⚠️ **Privacy Warning**: This captures user IPs, emails, and usernames. Ensure compliance with privacy policies (GDPR, CCPA).

### 5. Custom Context

Add custom data to error reports:

```python
from sentry_sdk import configure_scope

with configure_scope() as scope:
    scope.set_tag("debate_id", debate.id)
    scope.set_context("debate_details", {
        "topic": debate.topic,
        "participants": [p.name for p in debate.participants.all()],
        "status": debate.status,
    })
    # Now any error will include this context
```

---

## Monitoring Checklist

### Initial Setup
- [ ] Sentry account created
- [ ] Project created (Django platform)
- [ ] DSN added to `.env`
- [ ] `SENTRY_ENABLED=True` in production `.env`
- [ ] Test error captured successfully
- [ ] Performance data visible in dashboard

### Ongoing Monitoring
- [ ] Check Sentry daily for new errors
- [ ] Set up Slack/email alerts for critical errors
- [ ] Review performance degradation alerts
- [ ] Monitor error rate trends
- [ ] Investigate slow transactions (>1s)
- [ ] Update ignored errors list as needed

### Release Process
- [ ] Update `SENTRY_RELEASE` on each deployment
- [ ] Monitor new release for error spikes
- [ ] Compare performance vs. previous release
- [ ] Mark releases in Sentry dashboard

---

## Troubleshooting

### Sentry Not Capturing Errors

**Check 1: Sentry Enabled?**
```bash
docker compose logs web | grep -i sentry
# Should show: "✅ Sentry initialized for environment: production"
# Not: "⚠️  Sentry disabled"
```

**Check 2: DSN Configured?**
```bash
echo $SENTRY_DSN
# Should show your actual DSN URL
```

**Check 3: Internet Connectivity**
```bash
docker compose exec web curl -I https://sentry.io
# Should return 200 OK
```

### No Performance Data

**Check sample rate:**
```bash
# Must be > 0
SENTRY_TRACES_SAMPLE_RATE=0.1
```

**Check transaction names:**
- Ensure endpoints have unique names
- Check Sentry Performance tab filters

### Too Much Data / High Costs

**Reduce sample rates:**
```bash
SENTRY_TRACES_SAMPLE_RATE=0.01   # 1%
SENTRY_PROFILES_SAMPLE_RATE=0.01 # 1%
```

**Filter more aggressively:**
```python
# In settings.py
before_send=lambda event, hint: (
    None if should_ignore(event) else event
),
```

---

## Cost Optimization

### Sentry Pricing (as of 2024)

**Free Tier:**
- 5,000 errors/month
- 10,000 performance units/month
- 1 project
- 1 user

**Team Plan ($26/month):**
- 50,000 errors/month
- 100,000 performance units/month
- Unlimited projects
- Unlimited users

**Business Plan ($80/month):**
- 100,000 errors/month
- 250,000 performance units/month
- Advanced features

### Staying in Free Tier

1. **Reduce sample rates** (0.01 = 1%)
2. **Filter noise** (health checks, expected errors)
3. **Limit projects** (combine staging + prod if needed)
4. **Archive old issues** regularly

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
- name: Create Sentry Release
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
    SENTRY_ORG: your-org
    SENTRY_PROJECT: philosophical-debates
  run: |
    curl -sL https://sentry.io/get-cli/ | bash
    export SENTRY_RELEASE=$(sentry-cli releases propose-version)
    sentry-cli releases new -p $SENTRY_PROJECT $SENTRY_RELEASE
    sentry-cli releases set-commits --auto $SENTRY_RELEASE
    sentry-cli releases finalize $SENTRY_RELEASE
```

---

## Support

- **Sentry Documentation**: https://docs.sentry.io/platforms/python/guides/django/
- **Discord**: https://discord.gg/sentry
- **Status Page**: https://status.sentry.io/

---

**Last Updated**: October 19, 2025
