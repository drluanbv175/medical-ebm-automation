# Backup and Restore Guide

## Scope

Guide nay la mau van hanh cho PostgreSQL local/private server. Production can duoc kiem thu restore that truoc khi dung du lieu nguoi benh.

## Backup

```bash
docker compose exec postgres pg_dump -U clinic_os -d clinic_os --format=custom --file=/tmp/clinic_os.backup
docker compose cp postgres:/tmp/clinic_os.backup ./backups/clinic_os-YYYYMMDD.backup
```

## Restore drill

Chi restore vao moi truong test truoc.

```bash
docker compose cp ./backups/clinic_os-YYYYMMDD.backup postgres:/tmp/clinic_os.backup
docker compose exec postgres dropdb -U clinic_os clinic_os_restore --if-exists
docker compose exec postgres createdb -U clinic_os clinic_os_restore
docker compose exec postgres pg_restore -U clinic_os -d clinic_os_restore /tmp/clinic_os.backup
```

## Verification

- Kiem tra so patient, appointment, care plan, task, audit log.
- Kiem tra audit log khong mat.
- Kiem tra clinical rule approval con nguyen.
- Ghi lai thoi gian restore va loi neu co.

## Production blocker

Neu restore drill chua pass, khong duoc dung production.
