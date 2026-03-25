# Skill : Docker Containers

## Objectif

Containeriser les applications Django pour assurer la cohérence entre les environnements de développement, test et production.

## Quand utiliser ce skill

- Nouveau projet Django
- Standardisation des environnements d'équipe
- Déploiement en production
- Mise en place de CI/CD
- Isolation des dépendances

## Architecture Docker Django

```
┌─────────────────────────────────────┐
│         docker-compose.yml          │
├─────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌───────┐ │
│  │   Web   │ │   DB    │ │ Cache │ │
│  │ Django  │ │Postgres │ │ Redis │ │
│  │ +Nginx  │ │         │ │       │ │
│  └─────────┘ └─────────┘ └───────┘ │
└─────────────────────────────────────┘
```

## Dockerfile optimisé

### Multi-stage build (recommandé)

```dockerfile
# Dockerfile
#############
# BUILDER   #
#############
FROM python:3.11-slim as builder

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Créer environnement virtuel
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copier et installer dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

#############
# RUNNER    #
#############
FROM python:3.11-slim

# Labels
LABEL maintainer="votre@email.com"
LABEL version="1.0"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    ENVIRONMENT=production

# Créer utilisateur non-root
RUN groupadd -r django && useradd -r -g django django

# Répertoire de travail
WORKDIR /app

# Installer dépendances runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copier environnement virtuel depuis builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copier le code
COPY --chown=django:django . .

# Créer répertoires nécessaires
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R django:django /app

# Changer utilisateur
USER django

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Port exposé
EXPOSE 8000

# Commande par défaut
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "config.wsgi:application"]
```

### Dockerfile simple (développement)

```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Installation des dépendances
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r requirements-dev.txt

# Copie du code (volume monté en dev)
COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## Docker Compose

### Développement

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.dev
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DEBUG=True
      - DATABASE_URL=postgres://postgres:postgres@db:5432/postgres
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    stdin_open: true
    tty: true

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery:
    build:
      context: .
      dockerfile: Dockerfile.dev
    command: celery -A config worker -l info
    volumes:
      - .:/app
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgres://postgres:postgres@db:5432/postgres
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.dev
    command: celery -A config beat -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
```

### Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    image: myapp:${VERSION:-latest}
    command: gunicorn --bind 0.0.0.0:8000 --workers 4 config.wsgi:application
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    env_file:
      - .env.prod
    environment:
      - ENVIRONMENT=production
    depends_on:
      - db
      - redis
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
    depends_on:
      - web
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    env_file:
      - .env.prod
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_prod_data:/data
    restart: unless-stopped

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    image: myapp:${VERSION:-latest}
    command: celery -A config worker -l info --concurrency=4
    env_file:
      - .env.prod
    depends_on:
      - db
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    image: myapp:${VERSION:-latest}
    command: celery -A config beat -l info
    env_file:
      - .env.prod
    depends_on:
      - db
      - redis
    restart: unless-stopped

volumes:
  postgres_prod_data:
  redis_prod_data:
  static_volume:
  media_volume:
```

## Configuration Nginx

```nginx
# nginx/nginx.conf
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name localhost;
    
    # Redirect HTTP to HTTPS in production
    # return 301 https://$server_name$request_uri;

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /app/media/;
        expires 30d;
    }

    # Health check endpoint
    location /health/ {
        access_log off;
        proxy_pass http://django;
    }
}

# HTTPS Configuration (production)
# server {
#     listen 443 ssl http2;
#     server_name example.com;
#     
#     ssl_certificate /etc/nginx/ssl/cert.pem;
#     ssl_certificate_key /etc/nginx/ssl/key.pem;
#     
#     ... same location blocks ...
# }
```

## Scripts utilitaires

### Entrypoint

```bash
#!/bin/bash
# scripts/docker-entrypoint.sh

set -e

echo "🚀 Démarrage de l'application Django..."

# Attendre que la base de données soit prête
echo "⏳ Attente de la base de données..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "✅ Base de données disponible"

# Attendre Redis si configuré
if [ -n "$REDIS_URL" ]; then
    echo "⏳ Attente de Redis..."
    while ! nc -z redis 6379; do
      sleep 0.1
    done
    echo "✅ Redis disponible"
fi

# Collecter les fichiers statiques
echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Appliquer les migrations
echo "🔄 Application des migrations..."
python manage.py migrate --noinput

# Créer le superuser si nécessaire (développement)
if [ "$ENVIRONMENT" = "development" ]; then
    echo "👤 Création du superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser créé: admin/admin')
"
fi

echo "✅ Initialisation terminée!"

# Exécuter la commande passée en argument
exec "$@"
```

### Makefile Docker

```makefile
# Makefile

.PHONY: build up down logs shell test clean

# Build
dev-build:
	docker-compose build

prod-build:
	docker-compose -f docker-compose.prod.yml build

# Run
dev-up:
	docker-compose up -d

dev-up-logs:
	docker-compose up

prod-up:
	docker-compose -f docker-compose.prod.yml up -d

# Stop
dev-down:
	docker-compose down

dev-down-volumes:
	docker-compose down -v

prod-down:
	docker-compose -f docker-compose.prod.yml down

# Logs
dev-logs:
	docker-compose logs -f web

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f web

# Shell
dev-shell:
	docker-compose exec web bash

dev-shell-db:
	docker-compose exec db psql -U postgres

# Django commands
dev-migrate:
	docker-compose exec web python manage.py migrate

dev-makemigrations:
	docker-compose exec web python manage.py makemigrations

dev-shell-plus:
	docker-compose exec web python manage.py shell_plus

dev-test:
	docker-compose exec web pytest

# Clean
clean:
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

# Backup
dev-backup:
	docker-compose exec db pg_dump -U postgres postgres > backup_$(shell date +%Y%m%d_%H%M%S).sql

dev-restore:
	cat $(file) | docker-compose exec -T db psql -U postgres postgres
```

## Bonnes pratiques

### 1. Images légères

```dockerfile
# ✅ Utiliser des images alpines
FROM python:3.11-alpine

# ✅ Multi-stage builds pour réduire la taille
FROM python:3.11-slim as builder
# ... installation des déps

FROM python:3.11-slim
COPY --from=builder /opt/venv /opt/venv

# ✅ Nettoyer le cache
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
```

### 2. Sécurité

```dockerfile
# ✅ Ne pas exécuter en root
RUN groupadd -r django && useradd -r -g django django
USER django

# ✅ Copier avec le bon owner
COPY --chown=django:django . .

# ✅ Health checks
HEALTHCHECK --interval=30s --timeout=5s \
    CMD curl -f http://localhost:8000/health/ || exit 1

# ✅ Variables d'environnement non sensibles uniquement
ENV DEBUG=False
# Les secrets passent par .env ou secrets Docker
```

### 3. Performance

```dockerfile
# ✅ Layer caching optimal
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# ✅ Workers Gunicorn adaptés
# Nombre de workers = 2-4 x nombre de CPU
CMD ["gunicorn", "--workers", "4", "--threads", "2", "config.wsgi:application"]
```

## Commandes Docker utiles

```bash
# Build et lancement
docker-compose up -d                    # Démarrer en arrière-plan
docker-compose up --build               # Rebuild puis démarrer
docker-compose up -d --force-recreate   # Recréer les conteneurs

# Logs
docker-compose logs -f web              # Suivre les logs
docker-compose logs --tail=100 web      # Derniers 100 logs
docker-compose logs -f                  # Tous les services

# Exécution de commandes
docker-compose exec web bash            # Shell dans le conteneur
docker-compose exec web python manage.py migrate
docker-compose exec db psql -U postgres

# Gestion
docker-compose ps                       # Liste des conteneurs
docker-compose stop                     # Arrêter
docker-compose down                     # Arrêter et supprimer
docker-compose down -v                  # + volumes

# Debugging
docker-compose exec web python -m pdb manage.py shell
docker inspect container_name           # Infos détaillées
docker stats                            # Stats en temps réel

# Images et volumes
docker images                           # Liste des images
docker system df                        # Espace utilisé
docker system prune -f                  # Nettoyer
docker volume ls                        # Liste des volumes
```

## Débogage

```bash
# Conteneur qui ne démarre pas
docker-compose logs web

# Shell dans un conteneur planté
docker-compose run --rm web bash

# Tester la configuration
docker-compose config

# Rebuild sans cache
docker-compose build --no-cache

# Vérifier les variables d'environnement
docker-compose exec web env

# Inspecter le réseau
docker network ls
docker network inspect project_default
```

## CI/CD avec Docker

```yaml
# .github/workflows/docker.yml
name: Docker Build and Push

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: myusername/myapp
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Checklist Docker

### Setup initial
- [ ] Dockerfile optimisé (multi-stage)
- [ ] docker-compose.yml pour dev
- [ ] docker-compose.prod.yml pour prod
- [ ] Configuration Nginx
- [ ] .dockerignore configuré

### Sécurité
- [ ] Utilisateur non-root
- [ ] Pas de secrets dans l'image
- [ ] Health checks configurés
- [ ] Variables sensibles en .env

### Développement
- [ ] Volumes pour hot-reload
- [ ] Services dépendances (DB, Redis)
- [ ] Makefile pour commandes courantes
- [ ] Scripts d'entrypoint

### Production
- [ ] Images taguées avec version
- [ ] Restart policies configurées
- [ ] Limites de ressources
- [ ] SSL/TLS configuré
- [ ] Backups automatisés

## Ressources

- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Django Deployment](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [Gunicorn](https://docs.gunicorn.org/)
