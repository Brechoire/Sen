# Skill : Deployment

## Objectif

Déployer des applications Django en production de manière fiable, sécurisée et automatisée sur différentes plateformes cloud.

## Quand utiliser ce skill

- Application prête pour la production
- Mise en place d'environnements multiples
- Automatisation du déploiement
- Scalabilité et haute disponibilité

## Options de déploiement

### 1. Heroku (Simple & Rapide)

```bash
# Installation CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Créer application
heroku create mon-app-django

# Configuration
heroku config:set SECRET_KEY="votre-secret"
heroku config:set DEBUG=False
heroku config:set DATABASE_URL="postgres://..."

# Ajouter addons
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini
heroku addons:create sentry:f1

# Déployer
git push heroku main

# Migrations
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

```python
# Procfile
web: gunicorn config.wsgi:application --workers 4
release: python manage.py migrate
worker: celery -A config worker -l info
beat: celery -A config beat -l info
```

```python
# settings.py (Heroku)
import django_heroku

# Activer Heroku settings
django_heroku.settings(locals(), staticfiles=False)
```

### 2. DigitalOcean App Platform

```yaml
# .do/app.yaml
name: mon-app-django
services:
  - name: web
    source_dir: /
    github:
      repo: mon-user/mon-repo
      branch: main
    build_command: |
      pip install -r requirements.txt
      python manage.py collectstatic --noinput
    run_command: gunicorn config.wsgi:application --workers 4
    environment_slug: python
    instance_count: 2
    instance_size_slug: basic-xs
    envs:
      - key: SECRET_KEY
        value: ${SECRET_KEY}
        type: SECRET
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
      - key: REDIS_URL
        value: ${redis.REDIS_URL}

databases:
  - name: db
    engine: PG
    version: "15"
    size: basic-xs
    num_nodes: 1
```

### 3. AWS (Elastic Beanstalk)

```yaml
# .ebextensions/01_packages.config
packages:
  yum:
    git: []
    postgresql-devel: []
```

```yaml
# .ebextensions/02_python.config
option_settings:
  aws:elasticbeanstalk:application:environment:
    DJANGO_SETTINGS_MODULE: config.settings.production
    SECRET_KEY: {{SECRET_KEY}}
    DATABASE_URL: {{DATABASE_URL}}
  
  aws:elasticbeanstalk:container:python:
    WSGIPath: config.wsgi:application
  
  aws:elasticbeanstalk:environment:process:default:
    DUMMYTAILPATH: /dev/null
  
  aws:elasticbeanstalk:environment:proxy:staticfiles:
    /static: staticfiles
```

```bash
# Configuration EB CLI
pip install awsebcli
eb init -p python-3.11 mon-app-django

créer environnement
eb create production-env

# Déployer
eb deploy

# Logs
eb logs
```

### 4. VPS (DigitalOcean, Linode, Hetzner)

```bash
# scripts/deploy.sh
#!/bin/bash
set -e

SERVER="user@server_ip"
APP_DIR="/var/www/mon-app"

echo "🚀 Déploiement sur $SERVER..."

# Build et push de l'image Docker
docker build -t mon-app:latest .
docker save mon-app:latest | ssh $SERVER 'docker load'

# Déploiement sur le serveur
ssh $SERVER "
    cd $APP_DIR
    
    # Backup base de données
    docker-compose exec -T db pg_dump -U postgres postgres > backup_$(date +%Y%m%d).sql
    
    # Pull et redémarrer
    docker-compose -f docker-compose.prod.yml pull
    docker-compose -f docker-compose.prod.yml up -d
    
    # Migrations
    docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput
    
    # Collect static
    docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
    
    # Cleanup
    docker system prune -f
"

echo "✅ Déploiement terminé!"
```

## Configuration Production Django

```python
# config/settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['.herokuapp.com', '.onrender.com'])

# Base de données
DATABASES = {
    'default': env.db()
}

# Cache
CACHES = {
    'default': env.cache('REDIS_URL')
}

# Email
EMAIL_CONFIG = env.email_url('EMAIL_URL')
vars().update(EMAIL_CONFIG)

# Sécurité
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Whitenoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
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
    },
}
```

## Scripts de déploiement

### Script de backup

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="postgres"
DB_USER="postgres"

# Backup base de données
docker-compose exec -T db pg_dump -U $DB_USER $DB_NAME > "$BACKUP_DIR/db_$DATE.sql"

# Backup médias
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" /app/media/

# Cleanup vieux backups (garder 7 jours)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup terminé: $DATE"
```

### Script de rollback

```bash
#!/bin/bash
# scripts/rollback.sh

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./rollback.sh <version>"
    exit 1
fi

echo "⏮️  Rollback vers $VERSION..."

# Restaurer base de données
docker-compose exec -T db psql -U postgres postgres < "backups/db_$VERSION.sql"

# Redémarrer avec ancienne version
docker-compose -f docker-compose.prod.yml up -d

echo "✅ Rollback terminé!"
```

## Monitoring post-déploiement

### Health checks

```python
# health.py
def deployment_check(request):
    """Vérifier que le déploiement est OK."""
    checks = {
        'database': check_database(),
        'cache': check_cache(),
        'static_files': check_static_files(),
    }
    
    all_ok = all(c['status'] == 'ok' for c in checks.values())
    
    return JsonResponse({
        'status': 'ok' if all_ok else 'error',
        'checks': checks,
        'version': settings.RELEASE_VERSION,
    }, status=200 if all_ok else 503)
```

### Notifications

```python
# notifications.py
import requests

def notify_deployment(version, environment):
    """Notifier Slack du déploiement."""
    webhook_url = settings.SLACK_WEBHOOK_URL
    
    payload = {
        'text': f'🚀 Déploiement réussi',
        'attachments': [{
            'color': 'good',
            'fields': [
                {'title': 'Version', 'value': version, 'short': True},
                {'title': 'Environnement', 'value': environment, 'short': True},
            ]
        }]
    }
    
    requests.post(webhook_url, json=payload)
```

## Checklist Deployment

### Pré-déploiement
- [ ] Tests passent
- [ ] Variables d'environnement configurées
- [ ] Database migrations prêtes
- [ ] Static files compilés
- [ ] Secrets gérés (pas dans le code)

### Déploiement
- [ ] Backup base de données
- [ ] Zero-downtime si possible
- [ ] Health checks après déploiement
- [ ] Rollback planifié

### Post-déploiement
- [ ] Logs vérifiés (pas d'erreurs)
- [ ] Performance OK
- [ ] Notifications envoyées
- [ ] Monitoring activé

## Ressources

- [Heroku Dev Center](https://devcenter.heroku.com/)
- [AWS Elastic Beanstalk](https://docs.aws.amazon.com/elasticbeanstalk/)
- [DigitalOcean App Platform](https://docs.digitalocean.com/products/app-platform/)
- [Django Deployment](https://docs.djangoproject.com/en/stable/howto/deployment/)
