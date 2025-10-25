# PostgreSQL Migration Summary

## Completed Tasks

### 1. Database Configuration Updated
**File**: `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/config/settings.py`

Changed from SQLite to PostgreSQL with environment variable support:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv('DB_NAME', 'philosophical_debates'),
        "USER": os.getenv('DB_USER', 'postgres'),
        "PASSWORD": os.getenv('DB_PASSWORD'),
        "HOST": os.getenv('DB_HOST', 'localhost'),
        "PORT": os.getenv('DB_PORT', '5432'),
    }
}
```

**Environment Variables**:
- `DB_NAME` - Database name (default: 'philosophical_debates')
- `DB_USER` - Database user (default: 'postgres')
- `DB_PASSWORD` - Database password (required, no default)
- `DB_HOST` - Database host (default: 'localhost')
- `DB_PORT` - Database port (default: '5432')

### 2. Requirements Updated
**File**: `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/requirements.txt`

Added PostgreSQL adapter:
```
psycopg2-binary==2.9.10
```

Installed successfully in virtual environment.

### 3. Database Indexes Added

#### Persona Model
**File**: `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/personas/models.py`

Added index on `birth_year` field for improved query performance:
```python
class Meta:
    ordering = ['birth_year', 'name']
    indexes = [
        models.Index(fields=['category', 'birth_year']),
        models.Index(fields=['slug']),
        models.Index(fields=['birth_year']),  # NEW - for debate ordering
    ]
```

**Migration**: `personas/migrations/0007_persona_personas_pe_birth_y_dce734_idx.py`

#### DebateMessage Model
**File**: `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/debates/models.py`

Added composite index on `['debate', 'round_number', 'persona']`:
```python
class Meta:
    ordering = ['debate', 'round_number', 'persona__birth_year']
    indexes = [
        models.Index(fields=['debate', 'round_number']),
        models.Index(fields=['debate', 'round_number', 'persona']),  # NEW - composite index
    ]
```

**Migration**: `debates/migrations/0004_debatemessage_debates_deb_debate__0ddaf8_idx.py`

### 4. Migration Files Generated

Two new migration files created:

1. **Persona index migration**:
   - File: `personas/migrations/0007_persona_personas_pe_birth_y_dce734_idx.py`
   - Index name: `personas_pe_birth_y_dce734_idx`
   - Fields: `birth_year`

2. **DebateMessage composite index migration**:
   - File: `debates/migrations/0004_debatemessage_debates_deb_debate__0ddaf8_idx.py`
   - Index name: `debates_deb_debate__0ddaf8_idx`
   - Fields: `debate`, `round_number`, `persona`

### 5. Documentation Created

#### Migration Guide
**File**: `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/POSTGRESQL_MIGRATION.md`

Comprehensive guide covering:
- Why migrate from SQLite to PostgreSQL
- Step-by-step installation instructions (macOS, Linux, Windows)
- Database and user creation
- Environment variable configuration
- Data export from SQLite
- Data import to PostgreSQL
- Verification steps
- Troubleshooting common issues
- Rollback procedures

#### Environment Example
**File**: `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/.env.example`

Template for environment variables including:
- Django settings (SECRET_KEY, DEBUG, DJANGO_ENV)
- PostgreSQL configuration (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
- CORS settings
- API keys (Anthropic, Stripe)

## Performance Benefits

### Persona.birth_year Index
- **Improves**: Chronological ordering queries for debate turn order
- **Query example**: `Persona.objects.filter(birth_year__gte=1800).order_by('birth_year')`
- **Impact**: Faster debate participant ordering (critical for all 31 personas)

### DebateMessage Composite Index
- **Improves**: Fetching messages for specific debate rounds
- **Query example**: `DebateMessage.objects.filter(debate=debate, round_number=1).select_related('persona')`
- **Impact**: Faster rendering of debate transcripts round-by-round

## Next Steps

1. **Install PostgreSQL** on your system (see POSTGRESQL_MIGRATION.md)

2. **Create database and user**:
   ```sql
   CREATE DATABASE philosophical_debates;
   CREATE USER debates_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE philosophical_debates TO debates_user;
   ```

3. **Configure environment**:
   - Copy `.env.example` to `.env`
   - Set `DB_PASSWORD` and other required variables

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Export SQLite data** (while SQLite config is active):
   ```bash
   python manage.py dumpdata --natural-foreign --natural-primary \
     --exclude contenttypes --exclude auth.permission > data_export.json
   ```

7. **Import to PostgreSQL** (after switching to PostgreSQL config):
   ```bash
   python manage.py loaddata data_export.json
   ```

8. **Verify migration**:
   ```bash
   python manage.py shell
   # Run verification queries from migration guide
   ```

## Files Modified

1. `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/config/settings.py`
   - Changed DATABASES configuration to PostgreSQL

2. `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/requirements.txt`
   - Added psycopg2-binary==2.9.10

3. `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/personas/models.py`
   - Added birth_year index to Persona model

4. `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/debates/models.py`
   - Added composite index to DebateMessage model

## Files Created

1. `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/POSTGRESQL_MIGRATION.md`
   - Comprehensive migration guide

2. `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/.env.example`
   - Environment variables template

3. `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/personas/migrations/0007_persona_personas_pe_birth_y_dce734_idx.py`
   - Persona index migration

4. `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/debates/migrations/0004_debatemessage_debates_deb_debate__0ddaf8_idx.py`
   - DebateMessage composite index migration

## Important Notes

- **Database password is required**: The `DB_PASSWORD` environment variable must be set
- **Migrations are ready**: Run `python manage.py migrate` after PostgreSQL setup
- **SQLite backup**: Keep `db.sqlite3` as backup until migration is verified
- **Production settings**: Set `DJANGO_ENV=production` and `DEBUG=False` for production
- **Connection pooling**: Consider using `psycopg2` (not binary) for production with connection pooling

## Status

All migration tasks completed successfully:
- ✅ Settings updated to use PostgreSQL
- ✅ psycopg2-binary added to requirements
- ✅ Database indexes added to models
- ✅ Migration files generated
- ✅ Comprehensive migration guide created
- ✅ Environment example file created

The backend is ready for PostgreSQL migration. Follow the steps in `POSTGRESQL_MIGRATION.md` to complete the database migration.
