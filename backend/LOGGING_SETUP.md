# Django Structured Logging Setup

## Overview

The Philosophical Debates platform uses comprehensive structured logging to track application behavior, debug issues, and monitor performance. The logging system is configured to handle different environments (development vs production) with appropriate log levels and formats.

## Features

### 1. Multiple Log Handlers

- **Console Output**: Real-time logs displayed in terminal
- **File Rotation**: Automatic log file rotation when size limits are reached
- **Structured JSON**: Machine-readable JSON format in production
- **Separate Log Files**: Different files for different purposes

### 2. Log Files Created

All log files are stored in the `backend/logs/` directory:

| File | Purpose | Max Size | Backups | Format |
|------|---------|----------|---------|--------|
| `django_all.log` | All application logs (INFO+) | 10 MB | 5 | JSON (prod) / Verbose (dev) |
| `django_errors.log` | Errors only (ERROR+) | 10 MB | 10 | JSON (prod) / Verbose (dev) |
| `celery.log` | Celery task execution logs | 10 MB | 5 | JSON (prod) / Verbose (dev) |
| `db_queries.log` | SQL queries (DEBUG mode only) | 10 MB | 3 | Verbose |
| `security.log` | Security events (WARNING+) | 10 MB | 10 | JSON (prod) / Verbose (dev) |

### 3. Log Levels by Environment

**Development (DEBUG=True)**:
- Console: DEBUG level (all messages)
- Files: INFO level
- Database queries logged to `db_queries.log`
- Format: Human-readable verbose format

**Production (DEBUG=False)**:
- Console: INFO level
- Files: INFO level
- Database queries: Not logged (performance)
- Format: JSON structured logging
- Email alerts for critical errors

---

## Log Formats

### Development Format (Verbose)

```
[ERROR] 2025-10-19 14:32:15 django.request views.debate_detail:127 - Debate not found: invalid-slug
```

**Fields**:
- `[ERROR]` - Log level
- `2025-10-19 14:32:15` - Timestamp
- `django.request` - Logger name
- `views.debate_detail:127` - Module, function, and line number
- `Debate not found: invalid-slug` - Message

### Production Format (JSON)

```json
{"timestamp": "2025-10-19T14:32:15+00:00", "level": "ERROR", "logger": "django.request", "module": "views", "function": "debate_detail", "line": 127, "message": "Debate not found: invalid-slug"}
```

**Benefits**:
- Machine-parseable for log aggregation tools (ELK, Splunk, Datadog)
- Easy to search and filter
- Structured data for analytics

---

## Using Logging in Your Code

### 1. Import Logger

```python
import logging

# Get a logger for your module
logger = logging.getLogger(__name__)
```

### 2. Log Messages

```python
# Info level - general information
logger.info(f"Starting debate generation for debate_id={debate.id}")

# Warning level - something unexpected but not an error
logger.warning(f"User {user.id} exceeded rate limit")

# Error level - errors that need attention
logger.error(f"Failed to generate debate: {str(e)}", exc_info=True)

# Debug level - detailed diagnostic information (only in DEBUG mode)
logger.debug(f"Persona selected: {persona.name}")

# Critical level - serious errors requiring immediate attention
logger.critical(f"Database connection lost!")
```

### 3. Include Context

```python
# Bad - not enough context
logger.error("Debate failed")

# Good - includes context
logger.error(f"Debate generation failed for debate_id={debate.id}, user={user.email}: {str(e)}")

# Even better - structured extra data
logger.error(
    "Debate generation failed",
    extra={
        'debate_id': debate.id,
        'user_id': user.id,
        'personas': [p.name for p in personas],
        'error': str(e),
    }
)
```

### 4. Exception Logging

```python
try:
    result = generate_debate(debate_id)
except Exception as e:
    # exc_info=True includes full traceback
    logger.exception(f"Error generating debate {debate_id}: {str(e)}")
    # or explicitly:
    logger.error(f"Error: {str(e)}", exc_info=True)
```

---

## Logger Hierarchy

### Django Loggers

- `django` - Core Django framework
- `django.request` - HTTP request/response handling
- `django.db.backends` - Database queries (DEBUG only)
- `django.security` - Security events (CSRF, auth failures)

### Application Loggers

Each Django app has its own logger:

- `debates` - Debate generation and management
- `personas` - Persona operations
- `texts` - Text processing
- `users` - User authentication and management
- `payments` - Payment processing with Stripe
- `health` - Health check endpoints

### Celery Logger

- `celery` - Background task execution

---

## Viewing Logs

### Real-Time Console Logs

**Local Development**:
```bash
python manage.py runserver
# Logs appear in terminal
```

**Docker**:
```bash
# View web container logs
docker compose logs -f web

# View Celery worker logs
docker compose logs -f celery

# View last 100 lines
docker compose logs --tail=100 web
```

### Log Files

**Tail all logs**:
```bash
tail -f logs/django_all.log
```

**View errors only**:
```bash
tail -f logs/django_errors.log
```

**Watch Celery tasks**:
```bash
tail -f logs/celery.log
```

**Search for specific text**:
```bash
grep "debate_id=123" logs/django_all.log
```

**View JSON logs with formatting**:
```bash
tail -f logs/django_all.log | jq .
```

### Accessing Logs in Docker

**Copy logs from container to local machine**:
```bash
docker compose cp web:/app/logs ./logs_backup
```

**View logs inside container**:
```bash
docker compose exec web bash
cd logs
tail -f django_all.log
```

---

## Production Best Practices

### 1. Log Rotation

Logs automatically rotate when they reach their size limit:

```python
'maxBytes': 10 * 1024 * 1024,  # 10 MB
'backupCount': 5,  # Keep 5 old files
```

**Result**: Files like `django_all.log`, `django_all.log.1`, `django_all.log.2`, etc.

**Total disk usage per log type**:
- `django_all.log`: 10 MB × 6 files = 60 MB max
- `django_errors.log`: 10 MB × 11 files = 110 MB max
- `celery.log`: 10 MB × 6 files = 60 MB max

### 2. Log Levels in Production

**Set appropriate levels**:
- Too verbose (DEBUG) = performance impact, huge files
- Too quiet (ERROR only) = miss important warnings

**Recommended production settings**:
```python
'root': {
    'level': 'INFO',  # Good balance
}

'django.db.backends': {
    'level': 'WARNING',  # Don't log every SQL query
}
```

### 3. Sensitive Data

**Never log**:
- Passwords or password hashes
- API keys or secrets
- Credit card numbers
- Full user sessions
- Personal identifying information (unless required)

**Bad**:
```python
logger.info(f"User login: {user.email}, password: {password}")  # ❌
```

**Good**:
```python
logger.info(f"User login: {user.email}")  # ✅
```

### 4. Performance Considerations

**Avoid logging in tight loops**:
```python
# Bad - logs 1000 times
for item in items:
    logger.debug(f"Processing {item}")

# Good - log summary
logger.info(f"Processing {len(items)} items")
# ... process ...
logger.info(f"Completed processing {len(items)} items")
```

**Use appropriate log levels**:
```python
# Don't use INFO for debugging details
logger.debug(f"Intermediate value: {x}")  # Only in DEBUG mode

# Use INFO for significant events
logger.info(f"Debate {debate.id} completed successfully")
```

---

## Log Aggregation and Monitoring

### Shipping Logs to External Services

For production deployments, consider shipping logs to a log aggregation service:

#### 1. ELK Stack (Elasticsearch, Logstash, Kibana)

Install Filebeat to ship logs:
```bash
# Install Filebeat
apt-get install filebeat

# Configure Filebeat to read JSON logs
cat > /etc/filebeat/filebeat.yml <<EOF
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /app/logs/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
EOF

# Start Filebeat
systemctl start filebeat
```

#### 2. Datadog

```python
# Install Datadog agent
# Add to requirements.txt
ddtrace>=1.0.0

# Add to settings.py
from ddtrace import patch_all
patch_all()
```

#### 3. AWS CloudWatch

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i amazon-cloudwatch-agent.deb

# Configure to ship logs/*.log
```

#### 4. Syslog

```python
# Add syslog handler to settings.py
'handlers': {
    'syslog': {
        'level': 'INFO',
        'class': 'logging.handlers.SysLogHandler',
        'address': ('localhost', 514),
        'formatter': 'json',
    },
}
```

---

## Debugging with Logs

### Common Patterns

**Find all errors in the last hour**:
```bash
# Get logs from last hour
find logs/ -name "*.log" -mmin -60 -exec grep "ERROR" {} +
```

**Track a specific request**:
```bash
# Search for debate_id across all logs
grep -r "debate_id=123" logs/
```

**Count errors by type**:
```bash
# Extract error messages and count
grep "ERROR" logs/django_errors.log | cut -d'"' -f12 | sort | uniq -c | sort -rn
```

**Monitor in real-time**:
```bash
# Watch for errors
watch -n 1 "tail -20 logs/django_errors.log"
```

### Python Debugging

```python
# In your code, add temporary debug logging
import logging
logger = logging.getLogger(__name__)

def my_function():
    logger.debug(f"Function called with args: {locals()}")
    # ... your code ...
    logger.debug(f"Result: {result}")
```

---

## Testing Logging

### 1. Verify Logging Works

```python
# In Django shell
docker compose exec web python manage.py shell

>>> import logging
>>> logger = logging.getLogger('debates')
>>> logger.info("Test INFO message")
>>> logger.warning("Test WARNING message")
>>> logger.error("Test ERROR message")
```

**Check the log file**:
```bash
tail logs/django_all.log
# Should see your test messages
```

### 2. Test Log Rotation

```bash
# Create large log file to trigger rotation
for i in {1..100000}; do
    echo '{"timestamp": "2025-10-19", "level": "INFO", "message": "Test log message '$i'"}' >> logs/django_all.log
done

# Check if rotation occurred
ls -lh logs/
# Should see django_all.log.1, django_all.log.2, etc.
```

### 3. Test Different Environments

```bash
# Test DEBUG mode
DEBUG=True python manage.py check
# Check logs/db_queries.log is created

# Test production mode
DEBUG=False python manage.py check
# Verify JSON format in logs
```

---

## Troubleshooting

### Logs Not Being Created

**Check 1: Logs directory exists**
```bash
ls -la logs/
# Should exist and be writable
```

**Check 2: Permissions**
```bash
# Ensure Django can write to logs/
chmod 755 logs/
```

**Check 3: Logging configuration loaded**
```bash
# Check Django startup output
docker compose logs web | grep "Logging configured"
# Should show: "✅ Logging configured for environment: production"
```

### Log Files Too Large

**Reduce log level**:
```python
# In settings.py
'root': {
    'level': 'WARNING',  # Instead of INFO
}
```

**Reduce retention**:
```python
'backupCount': 3,  # Instead of 5
```

**Exclude noisy loggers**:
```python
'django.db.backends': {
    'handlers': [],  # Don't log SQL queries
}
```

### JSON Logs Not Formatted Correctly

**Verify environment**:
```bash
echo $DJANGO_ENV
# Should be 'production' for JSON logs
```

**Check formatter**:
```python
# In settings.py, verify:
'formatter': 'json' if DJANGO_ENV == 'production' else 'verbose',
```

### Logs Missing in Docker

**Check volume mount**:
```yaml
# In docker-compose.yml
volumes:
  - ./logs:/app/logs  # Ensure this exists
```

**Recreate container**:
```bash
docker compose down
docker compose up -d
```

---

## Environment-Specific Configuration

### Development

```bash
# .env
DEBUG=True
DJANGO_ENV=development
```

**Features**:
- Verbose console output
- DEBUG level logging
- SQL queries logged to `db_queries.log`
- Human-readable format

### Staging

```bash
# .env
DEBUG=False
DJANGO_ENV=staging
```

**Features**:
- INFO level logging
- JSON structured format
- No SQL query logging
- Email alerts for errors

### Production

```bash
# .env
DEBUG=False
DJANGO_ENV=production
```

**Features**:
- INFO level logging
- JSON structured format
- Error aggregation (Sentry integration)
- Email alerts for critical errors
- Log shipping to external service

---

## Integration with Sentry

Logging works alongside Sentry (see `SENTRY_SETUP.md`):

- **Logs**: Capture all events (INFO, WARNING, ERROR)
- **Sentry**: Capture exceptions and performance metrics

**Combined approach**:
```python
import logging
import sentry_sdk

logger = logging.getLogger(__name__)

try:
    result = risky_operation()
except Exception as e:
    # Log to file
    logger.exception(f"Operation failed: {str(e)}")

    # Send to Sentry with extra context
    sentry_sdk.capture_exception(e)
    sentry_sdk.set_context("operation", {
        "user_id": user.id,
        "debate_id": debate.id,
    })
```

---

## Monitoring Checklist

### Initial Setup
- [ ] Logs directory created and writable
- [ ] Log files being created on application start
- [ ] Console output shows "✅ Logging configured"
- [ ] Test logs appear in appropriate files
- [ ] Log rotation working correctly

### Ongoing Monitoring
- [ ] Check error logs daily: `tail -100 logs/django_errors.log`
- [ ] Monitor log file sizes: `du -sh logs/`
- [ ] Review security logs weekly: `tail -100 logs/security.log`
- [ ] Verify log rotation is happening (check for `.1`, `.2` files)
- [ ] Clean up old rotated logs if needed

### Production Deployment
- [ ] Set `DEBUG=False` and `DJANGO_ENV=production`
- [ ] Verify JSON format in production logs
- [ ] Set up log aggregation service (ELK, Datadog, CloudWatch)
- [ ] Configure email alerts for critical errors
- [ ] Test log shipping to external service
- [ ] Set up automated log cleanup (older than 30 days)

---

## Additional Resources

- **Django Logging Documentation**: https://docs.djangoproject.com/en/5.2/topics/logging/
- **Python Logging Cookbook**: https://docs.python.org/3/howto/logging-cookbook.html
- **Log Levels Guide**: https://docs.python.org/3/library/logging.html#logging-levels
- **JSON Logging Best Practices**: https://www.datadoghq.com/blog/json-logging-python/

---

**Last Updated**: October 19, 2025
