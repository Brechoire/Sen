# Environment Management - Démarrage Rapide

## Installation (5 minutes)

```bash
# 1. Installer django-environ
pip install django-environ

# 2. Créer .env.example
cat > .env.example << 'EOF'
# Django
SECRET_KEY=change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Optional
# REDIS_URL=redis://localhost:6379/0
# EMAIL_URL=smtp://localhost:587
# SENTRY_DSN=
EOF

# 3. Créer .env.local (non versionné)
cp .env.example .env

# 4. Ajouter au .gitignore
echo -e "\n# Environment\n.env\n.env.local\n.env.*.local" >> .gitignore
```

## Configuration Django

```python
# settings.py
import environ
import os

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Charger .env
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Utiliser les variables
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Base de données auto-parsée
DATABASES = {'default': env.db()}

# Cache (optionnel)
# CACHES = {'default': env.cache('REDIS_URL')}
```

## Structure recommandée

```
config/
├── settings/
│   ├── __init__.py      # Charge selon ENVIRONMENT
│   ├── base.py          # Configuration commune
│   ├── development.py   # Dev settings
│   └── production.py    # Prod settings
```

```python
# config/settings/__init__.py
import os

env = os.environ.get('ENVIRONMENT', 'development')

if env == 'production':
    from .production import *
elif env == 'staging':
    from .staging import *
else:
    from .development import *
```

## Variables par environnement

### Développement (.env)

```bash
DEBUG=True
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=*
```

### Production (secrets)

```bash
DEBUG=False
SECRET_KEY=vrai-secret-production-50-caracteres-plus
DATABASE_URL=postgres://user:pass@host:5432/db
ALLOWED_HOSTS=example.com
REDIS_URL=redis://:pass@host:6379/0
```

## Utilisation dans le code

```python
import environ

env = environ.Env()

# Variable requise
SECRET_KEY = env('SECRET_KEY')  # Erreur si non définie

# Avec valeur par défaut
DEBUG = env.bool('DEBUG', default=False)

# Parsing automatique
DATABASES = {'default': env.db()}  # Depuis DATABASE_URL
CACHES = {'default': env.cache('REDIS_URL')}
```

## Commandes essentielles

```bash
# Générer un SECRET_KEY sécurisé
python -c "import secrets; print(secrets.token_urlsafe(50))"

# Vérifier les variables
grep -E "^[A-Z]" .env | sort

# Charger .env temporairement
export $(cat .env | xargs)
python manage.py runserver

# Vérifier configuration Django
python manage.py diffsettings
```

## Checklist rapide

### Setup initial
- [ ] `pip install django-environ`
- [ ] Créer `.env.example` (versionné)
- [ ] Créer `.env` (non versionné)
- [ ] Ajouter `.env` au `.gitignore`
- [ ] Configurer settings.py

### Développement
- [ ] `cp .env.example .env`
- [ ] Remplir les valeurs locales
- [ ] Vérifier DEBUG=True
- [ ] Utiliser SQLite ou DB locale

### Production
- [ ] DEBUG=False
- [ ] SECRET_KEY fort (50+ caractères)
- [ ] ALLOWED_HOSTS configuré
- [ ] Database URL sécurisé
- [ ] Variables dans le vault/plateforme

### Sécurité
- [ ] `.env` dans `.gitignore`
- [ ] Pas de secrets dans le code
- [ ] Rotation régulière des clés
- [ ] Séparation dev/staging/prod

## Exemples complets

### Fichier .env.example complet

```bash
# ============================================
# Django Core
# ============================================
SECRET_KEY=change-me-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# ============================================
# Database
# ============================================
# SQLite (dev)
DATABASE_URL=sqlite:///db.sqlite3
# PostgreSQL (prod)
# DATABASE_URL=postgres://user:password@localhost:5432/dbname

# ============================================
# Cache & Queue (optionnel)
# ============================================
# REDIS_URL=redis://localhost:6379/0

# ============================================
# Email (optionnel)
# ============================================
# EMAIL_URL=smtp://user:password@smtp.gmail.com:587/?tls=True

# ============================================
# API Keys (optionnel)
# ============================================
# STRIPE_PUBLIC_KEY=pk_test_...
# STRIPE_SECRET_KEY=sk_test_...
# SENTRY_DSN=https://...@sentry.io/...
```

### Script de vérification

```bash
#!/bin/bash
# check-env.sh

echo "🔍 Vérification de l'environnement..."

# Vérifier si .env existe
if [ ! -f .env ]; then
    echo "❌ Fichier .env manquant"
    echo "💡 Copiez .env.example vers .env et configurez les variables"
    exit 1
fi

# Vérifier variables requises
REQUIRED="SECRET_KEY DATABASE_URL"
MISSING=""

for VAR in $REQUIRED; do
    if ! grep -q "^${VAR}=" .env; then
        MISSING="$MISSING $VAR"
    fi
done

if [ -n "$MISSING" ]; then
    echo "❌ Variables manquantes:$MISSING"
    exit 1
fi

echo "✅ Environnement configuré"
```

## Erreurs courantes

```bash
# ❌ SECRET_KEY trop court/faible
SECRET_KEY=abc123

# ✅ SECRET_KEY sécurisé
SECRET_KEY=django-insecure-votre-cle-ici-50-caracteres-minimum

# ❌ DEBUG en production
DEBUG=True

# ✅ DEBUG désactivé
DEBUG=False

# ❌ ALLOWED_HOSTS vide en prod
ALLOWED_HOSTS=

# ✅ ALLOWED_HOSTS configuré
ALLOWED_HOSTS=example.com,www.example.com

# ❌ Base de données non sécurisée
DATABASE_URL=postgres://postgres:password@localhost/db

# ✅ Utiliser des secrets forts
DATABASE_URL=postgres://app_user:strong_random_pass@localhost/db
```
