# Deployment

## Local

```bash
npm install
npx prisma migrate dev
npm run seed
npm run dev
```

## Docker Compose

```bash
docker compose up --build
```

## Production checklist

- Configure `DATABASE_URL`.
- Configure Auth.js secret and trusted hosts.
- Enable TLS.
- Enable backup schedule.
- Configure structured log sink.
- Disable demo role selector.
- Keep `AI_DRAFTS_ENABLED=false` until governance approval.
- Review all clinical rules and SOPs.
