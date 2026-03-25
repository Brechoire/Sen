# Skill : Environment Management

## Objectif

Gérer de manière sécurisée et efficace les configurations et secrets selon les environnements (développement, test, production).

## Quand utiliser ce skill

- Initialisation d'un nouveau projet
- Configuration des environnements (dev/staging/prod)
- Gestion des secrets et clés API
- Déploiement sur différents serveurs
- Rotation des credentials

## Principe fondamental : 12-Factor App

```
⚠️  GOLDEN RULE : Une base de code = Multiples déploiements
    Les configurations changent, le code reste identique
```

## Structure des environnements

### Fichiers de configuration

```
project/
├── .env                      # Variables locales (NON versionné)
├── .env.example              # Template (versionné)
├── .env.development          # Config dev (optionnel)
├── .env.staging              # Config staging (optionnel)
├── .env.production           # Config production (optionnel)
├── config/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py          # Configuration commune
│   │   ├── development.py   # Configuration dev
│   │   ├── staging.py       # Configuration staging
│   │   └── production.py    # Configuration production
```

### Configuration Django

```python
# config/settings/base.py
import os
from pathlib import Path
import environ

# Initialiser django-environ
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Lire le fichier .env
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Configuration commune
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Base de données
DATABASES = {
    'default': env.db(),
}

# Cache
CACHES = {
    'default': env.cache(),
}

# Email
EMAIL_CONFIG = env.email_url('EMAIL_URL', default=None)
if EMAIL_CONFIG:
    vars().update(EMAIL_CONFIG)
```

```python
# config/settings/development.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Base de données SQLite pour dev
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Debug toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE

# Logging verbeux
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

```python
# config/settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Sécurité
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Base de données PostgreSQL
DATABASES = {
    'default': env.db(),
}

# Cache Redis
CACHES = {
    'default': env.cache('REDIS_URL'),
}

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging structuré
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'app': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

## Gestion des variables d'environnement

### Template .env.example

```bash
# ============================================
# Environment Configuration Template
# Copy to .env and fill in your values
# NEVER commit .env file!
# ============================================

# Django
SECRET_KEY=change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3
# OR PostgreSQL:
# DATABASE_URL=postgres://user:password@localhost:5432/dbname

# Cache (optionnel)
# REDIS_URL=redis://localhost:6379/0

# Email (optionnel)
# EMAIL_URL=smtp://user:password@smtp.gmail.com:587/?tls=True

# API Keys (remplacer par vos vraies clés)
# STRIPE_PUBLIC_KEY=pk_test_...
# STRIPE_SECRET_KEY=sk_test_...
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
# SENTRY_DSN=...

# OAuth (optionnel)
# GOOGLE_CLIENT_ID=...
# GOOGLE_CLIENT_SECRET=...
# GITHUB_CLIENT_ID=...
# GITHUB_CLIENT_SECRET=...
```

### Utilisation dans le code

```python
# ❌ Mauvais - hardcodé
STRIPE_API_KEY = "sk_test_123456789"

# ❌ Mauvais - os.environ direct
import os
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')

# ✅ Bon - avec django-environ
import environ
env = environ.Env()
STRIPE_API_KEY = env('STRIPE_API_KEY')  # Lève une erreur si non défini

# ✅ Bon - avec valeur par défaut
DEBUG = env.bool('DEBUG', default=False)

# ✅ Bon - parsing automatique
# DATABASE_URL=postgres://user:pass@localhost:5432/dbname
DATABASES = {'default': env.db()}  # Parse automatiquement

# ✅ Bon - cache URL
# REDIS_URL=redis://:password@localhost:6379/0
CACHES = {'default': env.cache('REDIS_URL')}

# ✅ Bon - email URL
# EMAIL_URL=smtp://user:pass@smtp.gmail.com:587/?tls=True
email_config = env.email_url('EMAIL_URL')
vars().update(email_config)
```

## Sécurité des secrets

### 1. Ne jamais commiter .env

```bash
# .gitignore
.env
.env.local
.env.*.local
*.env
credentials.json
secrets.yaml
secrets.yml
```

### 2. Rotation des secrets

```bash
#!/bin/bash
# scripts/rotate-secrets.sh

echo "🔑 Rotation des secrets..."

# Générer nouveau SECRET_KEY
NEW_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
echo "Nouveau SECRET_KEY généré"

# Mettre à jour les variables d'environnement
# (selon votre plateforme de déploiement)
case "$1" in
  "heroku")
    heroku config:set SECRET_KEY="$NEW_SECRET"
    ;;
  "aws")
    aws ssm put-parameter --name "/app/secret-key" --value "$NEW_SECRET" --type SecureString --overwrite
    ;;
  "local")
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env
    ;;
esac

echo "✅ Secrets rotés avec succès"
echo "⚠️  Redémarrage de l'application nécessaire"
```

### 3. Variables sensibles vs non-sensibles

**SENSIBLES (ne jamais logger/exposer) :**
- SECRET_KEY
- DATABASE_URL (contient mot de passe)
- API keys (Stripe, AWS, etc.)
- OAuth credentials
- JWT signing keys

**NON-SENSIBLES (peuvent être logguées) :**
- DEBUG
- ALLOWED_HOSTS
- TIME_ZONE
- LANGUAGE_CODE
- STATIC_URL

```python
# ✅ Masquer les secrets dans les logs
def mask_sensitive(value, visible_chars=4):
    if not value or len(value) <= visible_chars * 2:
        return '*' * len(value)
    return value[:visible_chars] + '*' * (len(value) - visible_chars * 2) + value[-visible_chars:]

# Utilisation
logger.info(f"API Key: {mask_sensitive(api_key)}")
# Output: API Key: sk_t...test
```

## Environnements multiples

### Développement

```bash
# .env.development
DEBUG=True
SECRET_KEY=dev-secret-not-for-production
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=*
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Staging

```bash
# .env.staging
DEBUG=False
SECRET_KEY=staging-secret-key
DATABASE_URL=postgres://staging_user:pass@staging-db:5432/staging_db
ALLOWED_HOSTS=staging.example.com
EMAIL_URL=smtp://smtp.mailtrap.io:2525
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

### Production

```bash
# .env.production
DEBUG=False
SECRET_KEY=votre-vrai-secret-key-production
DATABASE_URL=postgres://prod_user:strong-pass@prod-db:5432/prod_db
ALLOWED_HOSTS=example.com,www.example.com
EMAIL_URL=smtp://user:pass@smtp.sendgrid.net:587/?tls=True
REDIS_URL=redis://:pass@redis:6379/0
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
SENTRY_DSN=https://...@sentry.io/...
```

## Scripts utilitaires

### Vérification de la configuration

```python
#!/usr/bin/env python
# scripts/check-env.py

import os
import sys

REQUIRED_VARS = [
    'SECRET_KEY',
    'DATABASE_URL',
]

OPTIONAL_VARS = [
    'REDIS_URL',
    'EMAIL_URL',
    'SENTRY_DSN',
]

def check_environment():
    print("🔍 Vérification de la configuration...\n")
    
    errors = []
    warnings = []
    
    # Vérifier variables requises
    for var in REQUIRED_VARS:
        value = os.environ.get(var)
        if not value:
            errors.append(f"❌ {var} non défini")
        elif 'change-me' in value.lower() or 'your-' in value.lower():
            errors.append(f"❌ {var} utilise une valeur par défaut non sécurisée")
        else:
            print(f"✅ {var} configuré")
    
    # Vérifier variables optionnelles
    for var in OPTIONAL_VARS:
        value = os.environ.get(var)
        if value:
            print(f"ℹ️  {var} configuré (optionnel)")
        else:
            warnings.append(f"⚠️  {var} non défini (optionnel)")
    
    # Vérifier DEBUG en production
    debug = os.environ.get('DEBUG', '').lower()
    env = os.environ.get('ENVIRONMENT', '').lower()
    
    if env == 'production' and debug in ['true', '1', 'yes']:
        errors.append("❌ DEBUG=True en production !")
    
    # Afficher résultats
    print("\n" + "="*50)
    
    if errors:
        print("\n❌ Erreurs:")
        for error in errors:
            print(f"  {error}")
    
    if warnings:
        print("\n⚠️  Avertissements:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not errors and not warnings:
        print("\n✅ Configuration OK!")
        return 0
    elif not errors:
        print("\n✅ Configuration acceptable (avec avertissements)")
        return 0
    else:
        print("\n❌ Configuration invalide")
        return 1

if __name__ == '__main__':
    sys.exit(check_environment())
```

### Chargement conditionnel

```python
# config/settings/__init__.py
import os

environment = os.environ.get('ENVIRONMENT', 'development')

if environment == 'production':
    from .production import *
elif environment == 'staging':
    from .staging import *
else:
    from .development import *
```

## Docker et environnements

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Variables d'environnement par défaut
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . .

# Commande par défaut
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### docker-compose.yml

```yaml
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
      - .env.development
    environment:
      - DEBUG=True
      - DATABASE_URL=postgres://postgres:postgres@db:5432/postgres
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
```

## CI/CD et environnements

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Verify environment variables
        run: |
          python scripts/check-env.py
        env:
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
      
      - name: Deploy
        run: |
          # Commandes de déploiement
          echo "Déploiement en production..."
        env:
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          ENVIRONMENT: production
```

### GitHub Environments

```
Settings → Environments → New environment

Environments recommandés:
- development
- staging
- production

Secrets par environnement:
- SECRET_KEY
- DATABASE_URL
- API keys
```

## Bonnes pratiques

### 1. Validation au démarrage

```python
# config/__init__.py ou manage.py
import os

def validate_environment():
    """Valide les variables critiques au démarrage."""
    required = ['SECRET_KEY', 'DATABASE_URL']
    missing = [var for var in required if not os.environ.get(var)]
    
    if missing:
        raise EnvironmentError(
            f"Variables d'environnement manquantes: {', '.join(missing)}"
        )
    
    # Vérifier que SECRET_KEY n'est pas la valeur par défaut
    secret_key = os.environ.get('SECRET_KEY', '')
    if 'change' in secret_key.lower() or 'django' in secret_key.lower():
        raise EnvironmentError(
            "SECRET_KEY utilise une valeur par défaut non sécurisée"
        )

# Appeler au démarrage
validate_environment()
```

### 2. Séparation des configurations

```python
# ❌ Mauvais - conditions partout
if os.environ.get('ENVIRONMENT') == 'production':
    DEBUG = False
else:
    DEBUG = True

# ✅ Bon - fichiers séparés
# config/settings/production.py
DEBUG = False

# config/settings/development.py
DEBUG = True
```

### 3. Documentation des variables

```python
# config/settings/base.py
"""
Variables d'environnement requises:

Required:
  SECRET_KEY: Clé secrète Django (générer avec secrets.token_urlsafe(50))
  DATABASE_URL: URL de connexion à la base de données

Optional:
  DEBUG: Mode debug (default: False)
  ALLOWED_HOSTS: Liste des hôtes autorisés (default: [])
  REDIS_URL: URL Redis pour le cache (default: None)
  EMAIL_URL: URL SMTP pour l'envoi d'emails (default: None)
  SENTRY_DSN: DSN Sentry pour le monitoring (default: None)
"""
```

## Checklist Environment Management

### Initialisation du projet
- [ ] Créer `.env.example` avec toutes les variables
- [ ] Ajouter `.env` au `.gitignore`
- [ ] Configurer django-environ ou python-dotenv
- [ ] Créer settings modulaires (base/dev/prod)
- [ ] Documenter toutes les variables

### Développement
- [ ] Copier `.env.example` vers `.env`
- [ ] Configurer variables locales
- [ ] Utiliser valeurs de test pour les API keys
- [ ] Ne jamais commiter `.env`

### Déploiement
- [ ] Configurer variables sur la plateforme de déploiement
- [ ] Utiliser des secrets forts (pas de "change-me")
- [ ] Vérifier DEBUG=False en production
- [ ] Configurer ALLOWED_HOSTS correctement
- [ ] Activer les headers de sécurité

### Maintenance
- [ ] Rotation régulière des secrets
- [ ] Audit des accès aux variables sensibles
- [ ] Revue des permissions
- [ ] Sauvegardes des configurations

## Ressources

- [django-environ](https://django-environ.readthedocs.io/)
- [python-dotenv](https://saurabh-kumar.com/python-dotenv/)
- [12-Factor App - Config](https://12factor.net/config)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
