# Database Migrations

## Running Migrations

### Manual SQL Migration

To apply the index migration:

```bash
# Connect to your PostgreSQL database
psql -U your_user -d ai_study_buddy -f migrations/add_indexes.sql

# Or via Docker:
docker exec -i postgres_container psql -U your_user -d ai_study_buddy < migrations/add_indexes.sql
```

### Python Migration (for new databases)

For new databases, indexes will be created automatically from the SQLAlchemy models when running:

```python
from src.models.database import create_tables
create_tables()
```

## Migration History

- **2025-12-23**: `add_user_settings_columns.sql` - Added user settings, preferences, and profile fields (Phase 1.1)
- **2024-12-22**: `add_indexes.sql` - Added indexes for foreign keys and frequently queried columns (HIGH-003)
