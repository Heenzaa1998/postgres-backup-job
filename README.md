# postgres-backup-job

Python automation for PostgreSQL backups with gzip compression.

## Features

- **pg_dump backup** — Full database dump
- **gzip compression** — Reduce backup size by 70-90%
- **SHA256 checksum** — Backup integrity verification
- **Storage strategy** — Local, remote (S3-compatible), or both
- **Retention policy** — Auto-delete backups older than N days
- **Backup verification** — Test restore to validate backup integrity
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
| `VERIFY_ENABLED` | false | Enable backup verification |
| `VERIFY_HOST` | POSTGRES_HOST | Verify database host |
| `VERIFY_PORT` | POSTGRES_PORT | Verify database port |
| `VERIFY_USER` | POSTGRES_USER | Verify database user |
| `VERIFY_PASSWORD` | POSTGRES_PASSWORD | Verify database password |
| `VERIFY_DB` | testdb_verify | Temp database for verification |
| `BACKUP_TARGET` | local | Storage target: local, remote, or all |
| `REMOTE_ENDPOINT` | http://localhost:9000 | S3-compatible endpoint |
| `REMOTE_BUCKET` | test-backup | Bucket name |
| `REMOTE_ACCESS_KEY` | minioadmin | Access key |
| `REMOTE_SECRET_KEY` | minioadmin | Secret key |
| `REMOTE_REGION` | us-east-1 | Region |
| `REMOTE_PATH_FORMAT` | monthly | Path format: flat, monthly, or daily |

> **Production Recommendation:** For production environments, use a **separate PostgreSQL instance** for verification to avoid impacting production performance and to validate backup portability.

<details>
<summary>Example: Separate Verify Instance</summary>

Add to `docker-compose.yml`:

```yaml
postgres-verify:
  image: postgres:16-alpine
  environment:
    POSTGRES_USER: backup_user
    POSTGRES_PASSWORD: backup_password
    POSTGRES_DB: testdb_verify
  ports:
    - "5433:5432"
```

Then set in `.env`:
```bash
VERIFY_HOST=localhost
VERIFY_PORT=5433
```

</details>

> **Remote Retention:** Use S3/MinIO lifecycle policies to automatically delete old backups from remote storage.

### Remote Path Formats

| Format | Example Path |
|--------|--------------|
| `flat` | `backup_2026-01-28.sql.gz` |
| `monthly` | `2026-01/backup_2026-01-28.sql.gz` |
| `daily` | `2026-01-28/backup_2026-01-28.sql.gz` |

## Output

### Normal (no cleanup needed)

```
[INFO] Starting backup script...
[INFO] Connected to testdb@localhost:5432
[INFO] Running pg_dump...
[INFO] Compressing backup with gzip...
[INFO] Backup completed: ./backups/backup_2026-01-28.sql.gz (1.3 KB)
[INFO] Cleaning up backups older than 7 days...
[INFO] No old backups to clean up
[INFO] Verifying backup...
[INFO] Creating temp database: testdb_verify
[INFO] Restoring backup to temp database...
[INFO] Verified: 2 tables found
[INFO] Backup verified successfully
[INFO] Dropping temp database: testdb_verify
```

### With cleanup (old backups deleted)

```
[INFO] Starting backup script...
[INFO] Connected to testdb@localhost:5432
[INFO] Running pg_dump...
[INFO] Compressing backup with gzip...
[INFO] Backup completed: ./backups/backup_2026-01-28.sql.gz (1.3 KB)
[INFO] Cleaning up backups older than 7 days...
[INFO] Deleted old backup: backup_2026-01-20.sql.gz
[INFO] Cleanup complete: 1 file(s) removed
[INFO] Verifying backup...
[INFO] Creating temp database: testdb_verify
[INFO] Restoring backup to temp database...
[INFO] Verified: 2 tables found
[INFO] Backup verified successfully
[INFO] Dropping temp database: testdb_verify
```

## Development Setup

```bash
# Start all services (PostgreSQL + MinIO)
docker compose up -d

# Start only PostgreSQL
docker compose up -d postgres

# Start only MinIO
docker compose up -d minio
```

### Verify Services

```bash
# Check PostgreSQL
docker compose exec postgres psql -U backup_user -d testdb -c "SELECT * FROM users;"

# Check MinIO Console
# Open: http://localhost:9001
# Login: minioadmin / minioadmin
```

## Docker Usage

### Build

```bash
docker build -t postgres-backup-job .
```

### Push

```bash
docker tag postgres-backup-job <your-registry>/postgres-backup-job:v1.0.0
docker push <your-registry>/postgres-backup-job:v1.0.0
```

### Pull

```bash
docker pull <your-registry>/postgres-backup-job:v1.0.0
```

### Run

```bash
docker run --rm --network host \
  --env-file .env \
  <your-registry>/postgres-backup-job:v1.0.0
```

## Verify Backup Integrity

Every backup generates a `.sha256` checksum file:

```bash
# Verify checksum
sha256sum -c backup_2026-01-29_22-14-45.sql.gz.sha256
# Output: backup_2026-01-29_22-14-45.sql.gz: OK
```

