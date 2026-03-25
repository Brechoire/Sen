# Docker Containers - Démarrage Rapide

## Installation (5 minutes)

```bash
# 1. Créer Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 django && chown -R django:django /app
USER django

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "config.wsgi:application"]
EOF

# 2. Créer docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgres://postgres:postgres@db:5432/postgres
    depends_on:
      - db

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

volumes:
  postgres_data:
EOF

# 3. Créer .dockerignore
cat > .dockerignore << 'EOF'
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build
.env
.env.*
.venv
venv/
ENV/
.git
.gitignore
.pytest_cache
.coverage
htmlcov/
.tox
.nox
.hypothesis
.mypy_cache
.dmypy.json
*.md
!README.md
Dockerfile*
docker-compose*
.github
.vscode
.idea
*.swp
*.swo
*~
EOF
```

## Commandes essentielles

```bash
# Build et démarrage
docker-compose up -d              # Démarrer en arrière-plan
docker-compose up --build         # Rebuild et démarrer
docker-compose up                 # Démarrer avec logs

# Arrêt
docker-compose down               # Arrêter
docker-compose down -v            # Arrêter + supprimer volumes

# Logs
docker-compose logs -f            # Logs en temps réel
docker-compose logs -f web        # Logs service web

# Commandes Django
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py createsuperuser

# Shell et base de données
docker-compose exec web bash
docker-compose exec db psql -U postgres

# Informations
docker-compose ps                 # Liste des conteneurs
docker-compose top                # Processus
docker system df                  # Espace utilisé
```

## Makefile pratique

```makefile
# Makefile
.PHONY: build up down logs shell test migrate

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f web

shell:
	docker-compose exec web bash

migrate:
	docker-compose exec web python manage.py migrate

makemigrations:
	docker-compose exec web python manage.py makemigrations

test:
	docker-compose exec web pytest

static:
	docker-compose exec web python manage.py collectstatic --noinput

clean:
	docker-compose down -v
	docker system prune -f
```

## Configuration .env

```bash
# Copier votre .env local
DEBUG=True
SECRET_KEY=dev-secret-key
DATABASE_URL=postgres://postgres:postgres@db:5432/postgres
ALLOWED_HOSTS=*
```

## Déploiement production

```bash
# 1. Build image
docker build -t myapp:latest .

# 2. Tag avec version
docker tag myapp:latest myapp:v1.0.0

# 3. Push registry (optionnel)
docker push myregistry/myapp:v1.0.0

# 4. Production avec docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

```bash
# Conteneur qui ne démarre pas
docker-compose logs web

# Pas de connexion DB
docker-compose restart db
docker-compose exec db pg_isready

# Reset complet
docker-compose down -v
docker-compose up --build

# Clean system
docker system prune -af
docker volume prune -f
```

## Checklist rapide

- [ ] Dockerfile créé
- [ ] docker-compose.yml créé
- [ ] .dockerignore configuré
- [ ] Variables d'environnement en .env
- [ ] Services DB/cache configurés
- [ ] Health check fonctionnel
- [ ] Commandes Makefile ou scripts
- [ ] Testé localement
