# Async Tasks - Démarrage Rapide

## Installation (3 minutes)

```bash
# 1. Installer Celery et Redis
pip install celery redis django-celery-results

# 2. Installer Redis (si pas déjà fait)
# Mac: brew install redis && brew services start redis
# Ubuntu: sudo apt-get install redis-server
```

## Configuration rapide

```python
# settings.py
INSTALLED_APPS += ['django_celery_results']

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TASK_SERIALIZER = 'json'
```

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

```python
# config/__init__.py
from .celery import app as celery_app
__all__ = ('celery_app',)
```

## Créer une tâche

```python
# myapp/tasks.py
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_email_task(email):
    send_mail(
        'Sujet',
        'Message',
        'from@example.com',
        [email],
    )
    return f'Email envoyé à {email}'
```

## Appeler une tâche

```python
# views.py
from .tasks import send_email_task

def my_view(request):
    # Exécuter de façon async
    send_email_task.delay('user@example.com')
    
    # Ou avec attente du résultat
    result = send_email_task.delay('user@example.com')
    print(result.get(timeout=10))
    
    return HttpResponse('Tâche lancée')
```

## Démarrer les services

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker
celery -A config worker -l info

# Terminal 3: Django
python manage.py runserver
```

## Docker Compose

```yaml
# docker-compose.yml
services:
  celery:
    build: .
    command: celery -A config worker -l info
    volumes:
      - .:/app
    depends_on:
      - redis
  
  celery-beat:
    build: .
    command: celery -A config beat -l info
    volumes:
      - .:/app
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
```

## Checklist rapide

- [ ] `pip install celery redis`
- [ ] Redis installé et démarré
- [ ] `celery.py` créé
- [ ] Celery importé dans `__init__.py`
- [ ] Tâche créée avec `@shared_task`
- [ ] Worker démarré
- [ ] Test `.delay()` fonctionne

## Commandes essentielles

```bash
# Démarrer worker
celery -A config worker -l info

# Démarrer beat (planificateur)
celery -A config beat -l info

# Worker + Beat
celery -A config worker -B -l info

# Monitorer
celery -A config flower

# Purger la file
celery -A config purge
```
