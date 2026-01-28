# postgres-backup-job

Python automation for PostgreSQL backups with gzip compression.

## Features

- **pg_dump backup** — Full database dump
- **gzip compression** — Reduce backup size by 70-90%
- **Retention policy** — Auto-delete backups older than N days
- **Connection retry** — Automatic retry on connection failure
- **Configurable** — All settings via environment variables

## Quick Start

```bash
# 1. Configure environment
cp .env.example .env

# 2. Start PostgreSQL (for development)
docker compose up -d

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run backup
python src/backup.py
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | localhost | Database host |
| `POSTGRES_PORT` | 5432 | Database port |
| `POSTGRES_USER` | backup_user | Database username |
| `POSTGRES_PASSWORD` | backup_password | Database password |
| `POSTGRES_DB` | testdb | Database name |
| `BACKUP_DIR` | ./backups | Backup output directory |
| `RETRY_COUNT` | 3 | Connection retry attempts |
| `RETRY_DELAY` | 5 | Seconds between retries |
| `RETENTION_DAYS` | 7 | Delete backups older than N days (0=disable) |

## Output

```
2026-01-28 21:40:58 [INFO] Starting backup script...
2026-01-28 21:40:58 [INFO] Connected to testdb@localhost:5432
2026-01-28 21:40:58 [INFO] Running pg_dump...
2026-01-28 21:40:58 [INFO] Compressing backup with gzip...
2026-01-28 21:40:58 [INFO] Backup completed: ./backups/backup_2026-01-28.sql.gz (1.3 KB)
2026-01-28 21:40:58 [INFO] Cleaning up backups older than 7 days...
2026-01-28 21:40:58 [INFO] Deleted old backup: backup_2026-01-20.sql.gz
2026-01-28 21:40:58 [INFO] Cleanup complete: 1 file(s) removed
```

## Development Setup

```bash
# Start PostgreSQL with sample data
docker compose up -d

# Verify database
docker compose exec postgres psql -U backup_user -d testdb -c "SELECT * FROM users;"
```
