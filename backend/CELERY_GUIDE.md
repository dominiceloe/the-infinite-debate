# Celery Worker Setup Guide

This guide explains how to run the Celery worker for asynchronous debate generation.

## Prerequisites

### 1. Install Redis

Redis is required as the message broker and result backend for Celery.

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis:latest
```

### 2. Install Python Dependencies

Ensure all dependencies are installed:
```bash
cd backend
pip install -r requirements.txt
```

## Running Celery

### Development

Start the Celery worker in a separate terminal:

```bash
cd backend
celery -A config worker --loglevel=info
```

This will:
- Connect to Redis at `redis://localhost:6379/0` (default)
- Auto-discover tasks from all Django apps
- Process debate generation tasks in the background

### Production

For production, use a process manager like systemd or supervisord.

**Example systemd service file (`/etc/systemd/system/celery.service`):**

```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=your-user
Group=your-group
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings"
ExecStart=/path/to/venv/bin/celery -A config worker \
    --loglevel=info \
    --pidfile=/var/run/celery/worker.pid \
    --logfile=/var/log/celery/worker.log

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable celery
sudo systemctl start celery
```

## Environment Variables

Configure Redis connection via environment variables:

```bash
# .env file
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0  # Optional, defaults to REDIS_URL
CELERY_RESULT_BACKEND=redis://localhost:6379/0  # Optional, defaults to REDIS_URL
```

## Monitoring Tasks

### Check Task Status

You can monitor task execution:

```bash
# View active tasks
celery -A config inspect active

# View registered tasks
celery -A config inspect registered

# View stats
celery -A config inspect stats
```

### Flower (Web UI)

Install Flower for a web-based monitoring interface:

```bash
pip install flower
celery -A config flower
```

Then visit `http://localhost:5555`

## Running the Full Stack

For development, you'll need three terminal windows:

**Terminal 1 - Django:**
```bash
cd backend
python manage.py runserver
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
celery -A config worker --loglevel=info
```

**Terminal 3 - Redis (if not running as service):**
```bash
redis-server
```

## Testing

To test that Celery is working:

1. Start Redis
2. Start Celery worker
3. Start Django server
4. Create a debate via the API
5. Call the `/api/debates/{slug}/generate/` endpoint
6. Watch the Celery worker logs for task execution

The debate status will update from `pending` → `generating` → `completed` (or `failed`).

## Troubleshooting

### Connection Refused

If you see "Connection refused" errors:
- Ensure Redis is running: `redis-cli ping` (should return "PONG")
- Check Redis URL in settings matches your Redis configuration

### Tasks Not Running

If tasks aren't being processed:
- Verify Celery worker is running
- Check worker logs for errors
- Ensure task is registered: `celery -A config inspect registered`

### Import Errors

If you see import errors:
- Ensure you're in the correct directory (backend/)
- Check DJANGO_SETTINGS_MODULE is set correctly
- Verify all dependencies are installed

## Architecture

The Celery setup consists of:

1. **Redis** - Message broker and result backend
2. **Django** - Web application that dispatches tasks
3. **Celery Worker** - Background process that executes tasks

When a user requests debate generation:
1. Django API creates a debate record
2. Django dispatches a Celery task with the debate ID
3. Django immediately returns a response with task ID
4. Celery worker picks up the task from Redis
5. Worker calls the debate generator
6. Debate status is updated in the database
7. User can poll the debate endpoint to check status
