# PostgreSQL Migration Guide

This guide explains how to migrate the philosophical debates backend from SQLite to PostgreSQL.

## Why PostgreSQL?

SQLite limitations for production:
- **No concurrent writes**: Only one write operation at a time
- **Poor performance**: Large datasets (69MB+) cause slowdowns
- **Limited scalability**: Not suitable for multiple simultaneous users
- **Missing features**: No advanced indexing, limited data types

PostgreSQL benefits:
- **Production-ready**: Handles concurrent connections efficiently
- **Better performance**: Advanced query optimization and indexing
- **Scalability**: Supports multiple users and large datasets
- **Rich features**: Full-text search, JSON queries, advanced data types

## Prerequisites

- PostgreSQL 14+ installed on your system
- Python 3.10+ with virtualenv
- Existing SQLite database (db.sqlite3)

## Step 1: Install PostgreSQL

### macOS (using Homebrew)
```bash
brew install postgresql@14
brew services start postgresql@14
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Windows
Download and install from: https://www.postgresql.org/download/windows/

## Step 2: Create Database and User

Connect to PostgreSQL as the postgres user:

```bash
# macOS/Linux
sudo -u postgres psql

# Windows (open psql from Start Menu)
```

Run the following SQL commands:

```sql
-- Create database
CREATE DATABASE philosophical_debates;

-- Create user with password
CREATE USER debates_user WITH PASSWORD 'your_secure_password_here';

-- Grant privileges
ALTER ROLE debates_user SET client_encoding TO 'utf8';
ALTER ROLE debates_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE debates_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE philosophical_debates TO debates_user;

-- Exit psql
\q
```

## Step 3: Install Python PostgreSQL Adapter

Activate your virtual environment and install psycopg2-binary:

```bash
cd /path/to/backend
source venv/bin/activate
pip install psycopg2-binary==2.9.10
```

Or install all requirements (already updated):

```bash
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

Create or update your `.env` file in the backend directory:

```env
# Database Configuration (PostgreSQL)
DB_NAME=philosophical_debates
DB_USER=debates_user
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432

# Django Settings
SECRET_KEY=your_django_secret_key
DEBUG=True
DJANGO_ENV=development

# API Keys
ANTHROPIC_API_KEY=your_anthropic_key

# Other settings
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**IMPORTANT**: Make sure to:
1. Set a strong password for DB_PASSWORD
2. Never commit the .env file to version control
3. Add `.env` to your `.gitignore` file

## Step 5: Run Migrations

Apply all migrations to create tables in PostgreSQL:

```bash
python manage.py migrate
```

This will create all tables with the new indexes:
- `personas_persona`: Index on `birth_year` for debate ordering
- `debates_debatemessage`: Composite index on `['debate', 'round_number', 'persona']`

## Step 6: Export Data from SQLite

### Option A: Using Django dumpdata (Recommended)

Export all data from SQLite:

```bash
# Temporarily switch back to SQLite in settings.py or use a separate settings file
python manage.py dumpdata --natural-foreign --natural-primary \
  --exclude contenttypes --exclude auth.permission \
  --exclude admin.logentry --exclude sessions.session \
  --exclude rest_framework_simplejwt.tokenblacklist \
  > data_export.json
```

### Option B: Export specific apps only

If you only want to migrate certain data:

```bash
# Export personas, debates, users, texts, and payments
python manage.py dumpdata users personas debates texts payments \
  --natural-foreign --natural-primary > data_export.json
```

## Step 7: Import Data into PostgreSQL

Switch to PostgreSQL configuration (already done in settings.py), then load the data:

```bash
python manage.py loaddata data_export.json
```

### If you encounter errors:

1. **Foreign key violations**: Load data in order
   ```bash
   python manage.py loaddata users_export.json
   python manage.py loaddata personas_export.json
   python manage.py loaddata debates_export.json
   python manage.py loaddata texts_export.json
   python manage.py loaddata payments_export.json
   ```

2. **Duplicate keys**: Reset sequences after import
   ```bash
   python manage.py sqlsequencereset users personas debates texts payments | python manage.py dbshell
   ```

## Step 8: Verify Migration

Run these checks to ensure everything migrated correctly:

```bash
# Django shell
python manage.py shell
```

```python
from personas.models import Persona
from debates.models import Debate, DebateMessage
from users.models import User

# Check counts
print(f"Users: {User.objects.count()}")
print(f"Personas: {Persona.objects.count()}")
print(f"Debates: {Debate.objects.count()}")
print(f"Messages: {DebateMessage.objects.count()}")

# Test queries with new indexes
# Should be fast due to birth_year index
personas = Persona.objects.filter(birth_year__gte=1800).order_by('birth_year')
print(f"Modern personas: {personas.count()}")

# Test composite index on DebateMessage
if Debate.objects.exists():
    debate = Debate.objects.first()
    messages = DebateMessage.objects.filter(
        debate=debate,
        round_number=1
    ).select_related('persona')
    print(f"Round 1 messages: {messages.count()}")
```

## Step 9: Create Superuser (if needed)

If you need to create a new admin user:

```bash
python manage.py createsuperuser
```

## Step 10: Backup the Old SQLite Database

Once you've verified the migration is successful:

```bash
# Keep the SQLite file as backup
mv db.sqlite3 db.sqlite3.backup

# Or compress it
gzip db.sqlite3
```

## Step 11: Update Production Environment

For production deployment:

1. **Update environment variables** in your hosting platform:
   - Set `DJANGO_ENV=production`
   - Set `DEBUG=False`
   - Use strong passwords
   - Configure allowed hosts

2. **Use connection pooling** (optional, for high traffic):
   ```bash
   pip install psycopg2
   ```

3. **Enable database backups**:
   ```bash
   # Example backup command
   pg_dump -U debates_user philosophical_debates > backup_$(date +%Y%m%d).sql
   ```

## Troubleshooting

### Can't connect to PostgreSQL

1. Check if PostgreSQL is running:
   ```bash
   # macOS/Linux
   sudo systemctl status postgresql
   # or
   brew services list
   ```

2. Verify connection settings:
   ```bash
   psql -U debates_user -d philosophical_debates -h localhost -p 5432
   ```

### Migration errors

1. **Table already exists**: Run `python manage.py migrate --fake-initial`

2. **Permission denied**: Grant proper privileges:
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE philosophical_debates TO debates_user;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO debates_user;
   GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO debates_user;
   ```

### Performance issues

1. **Enable query logging** (development only):
   ```python
   # settings.py
   LOGGING = {
       'version': 1,
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
           },
       },
       'loggers': {
           'django.db.backends': {
               'handlers': ['console'],
               'level': 'DEBUG',
           },
       },
   }
   ```

2. **Analyze queries**:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM personas_persona WHERE birth_year > 1800;
   ```

## Index Information

New indexes added for performance:

### Persona Model
- `birth_year`: Single field index for chronological queries and debate ordering

### DebateMessage Model
- `['debate', 'round_number', 'persona']`: Composite index for filtering messages by debate round and speaker

These indexes significantly improve query performance when:
- Ordering personas chronologically for debates
- Fetching messages for specific debate rounds
- Looking up which persona spoke in which round

## Rollback Plan

If you need to rollback to SQLite:

1. Stop the Django server
2. Edit `config/settings.py`:
   ```python
   DATABASES = {
       "default": {
           "ENGINE": "django.db.backends.sqlite3",
           "NAME": BASE_DIR / "db.sqlite3.backup",
       }
   }
   ```
3. Restart the server

## Next Steps

After successful migration:

1. Monitor database performance
2. Set up automated backups
3. Configure connection pooling for production
4. Review and optimize slow queries
5. Consider read replicas for scaling

## Resources

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Django PostgreSQL Notes: https://docs.djangoproject.com/en/5.2/ref/databases/#postgresql-notes
- psycopg2 Documentation: https://www.psycopg.org/docs/
