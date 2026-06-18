# Local Docker deployment

```bash
cp .env.example .env
docker compose up --build
```

Sau khi app len:

```bash
docker compose exec app npx prisma migrate deploy
docker compose exec app npm run seed
```

Production can secret that, TLS, backup va monitoring.
