# Production Deployment Guide

## Stack

- Frontend: Next.js 14
- Backend: FastAPI + SQLAlchemy + APScheduler
- Database: PostgreSQL 16
- Reverse proxy: Nginx
- Runtime: Docker Compose

## Files

- `frontend/Dockerfile`: builds and runs the Next.js standalone server
- `backend/Dockerfile`: builds and runs the FastAPI service
- `docker-compose.yml`: orchestrates `frontend`, `backend`, `postgres`, and `nginx`
- `nginx/default.conf`: serves the frontend on port `80` and proxies `/api` to the backend
- `.env.example`: production environment template
- `deploy.sh`: pull, rebuild, restart, and verify deployment

## First-Time Setup

1. Copy the environment template:

```bash
cp .env.example .env
```

2. Update at least these values in `.env`:

- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `CORS_ORIGINS`
- `SCHEDULER_*` if the default schedule is not suitable

## Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```

The script performs:

1. `git pull --ff-only` when the directory is a git work tree
2. `docker compose down`
3. `docker compose build`
4. `docker compose up -d`
5. `docker compose ps`
6. `curl http://localhost/health`

`docker compose down` does not remove the named volume `postgres_data`, so database data is preserved unless `-v` is added manually.

## Service Access

- Frontend: `http://your-server-ip/`
- Backend health: `http://your-server-ip/health`
- Backend API: `http://your-server-ip/api`

## Architecture Notes

- Nginx is the only public entrypoint and listens on port `80`.
- `/api` is reverse proxied to `backend:8000`.
- Frontend browser traffic uses relative path `/api`.
- Frontend server-side rendering uses `INTERNAL_API_BASE_URL` for container-to-container access.
- PostgreSQL data is stored in the named volume `postgres_data`.

## HTTPS Upgrade Path

The current Nginx layout is ready for a follow-up HTTPS rollout:

- keep the existing port `80` server block for redirect or ACME challenge handling
- add a `443` server block with certificates mounted into the Nginx container
- keep `/api` and `/` upstream routing unchanged

## Verification Commands

```bash
docker compose build
docker compose up -d
docker compose ps
curl http://localhost/health
curl -I http://localhost/
```
