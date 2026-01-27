# postgres-backup-job

Python automation for PostgreSQL backups.
Supports local storage and object storage (S3) synchronization.

## Development Setup

```bash
# 1. Configure environment
cp .env.example .env

# 2. Start PostgreSQL
docker compose up -d

# 3. Verify
docker compose exec postgres psql -U backup_user -d testdb -c "SELECT * FROM users;"
```
