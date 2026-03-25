# Deployment - Démarrage Rapide

## Déploiement Heroku (10 minutes)

```bash
# 1. Installer CLI et login
brew install heroku  # Mac
# curl https://cli-assets.heroku.com/install.sh | sh  # Linux

heroku login

# 2. Créer app
heroku create mon-app-django

# 3. Configurer variables
heroku config:set SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
heroku config:set DEBUG=False

# 4. Ajouter PostgreSQL
heroku addons:create heroku-postgresql:mini

# 5. Créer Procfile
echo "web: gunicorn config.wsgi:application --workers 4" > Procfile
echo "release: python manage.py migrate" >> Procfile

# 6. Déployer
git push heroku main

# 7. Créer superuser
heroku run python manage.py createsuperuser
```

## Déploiement VPS avec Docker

```bash
# 1. Build image
docker build -t mon-app:latest .

# 2. Sauvegarder et transférer
docker save mon-app:latest | gzip > mon-app.tar.gz
scp mon-app.tar.gz user@server:/tmp/

# 3. Sur le serveur
ssh user@server "
    cd /var/www/mon-app
    gunzip -c /tmp/mon-app.tar.gz | docker load
    docker-compose -f docker-compose.prod.yml up -d
    docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
"
```

## Configuration minimale production

```python
# config/settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['.herokuapp.com', 'votre-domaine.com']

DATABASES = {'default': env.db()}

# Whitenoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Sécurité
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
```

## Checklist rapide

- [ ] DEBUG=False
- [ ] SECRET_KEY fort
- [ ] ALLOWED_HOSTS configuré
- [ ] Base de données configurée
- [ ] Whitenoise pour statics
- [ ] Variables d'environnement
- [ ] Migrations appliquées
- [ ] Superuser créé
- [ ] Health check fonctionnel

## Commandes essentielles

```bash
# Heroku
heroku logs --tail
heroku run python manage.py shell
heroku config
heroku ps:scale web=2

# Docker
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```
