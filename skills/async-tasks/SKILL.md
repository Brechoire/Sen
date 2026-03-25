# Skill : Async Tasks

## Objectif

Exécuter des tâches en arrière-plan (asynchrones) pour améliorer les performances et la réactivité de l'application Django.

## Quand utiliser ce skill

- Envoi d'emails
- Traitement d'images ou fichiers
- Génération de rapports
- Appels API externes
- Tâches planifiées (cron)
- Traitements lourds

## Architecture

```
Django Web App
       │
       ├─→ Celery Worker (tâches async)
       │
       ├─→ Celery Beat (tâches planifiées)
       │
       └─→ Redis/RabbitMQ (broker de messages)
```

## Installation et configuration

### 1. Installation

```bash
pip install celery redis django-celery-results django-celery-beat
```

### 2. Configuration Django

```python
# settings.py
INSTALLED_APPS = [
    ...
    'django_celery_results',
    'django_celery_beat',
]

# Configuration Celery
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'

# Sérialisation
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Fuseau horaire
CELERY_TIMEZONE = 'Europe/Paris'
CELERY_ENABLE_UTC = True

# Tâches
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Résultats
CELERY_RESULT_EXPIRES = 3600  # 1 heure
CELERY_RESULT_EXTENDED = True
```

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Charger config depuis settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-découverte des tâches
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

```python
# config/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)
```

## Création de tâches

### Tâches basiques

```python
# myapp/tasks.py
from celery import shared_task
from django.core.mail import send_mail
import time

@shared_task
def send_welcome_email(user_id):
    """Envoyer email de bienvenue (async)."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = User.objects.get(id=user_id)
    
    send_mail(
        subject='Bienvenue !',
        message=f'Bonjour {user.username}, bienvenue sur notre site.',
        from_email='noreply@example.com',
        recipient_list=[user.email],
        fail_silently=False,
    )
    
    return f'Email envoyé à {user.email}'

@shared_task(bind=True)
def process_uploaded_file(self, file_path):
    """Traiter un fichier uploadé avec progression."""
    import os
    
    # Mettre à jour le statut
    self.update_state(state='PROGRESS', meta={'progress': 0})
    
    # Traitement
    total_steps = 10
    for i in range(total_steps):
        time.sleep(1)  # Simulation
        self.update_state(
            state='PROGRESS',
            meta={
                'current': i + 1,
                'total': total_steps,
                'progress': int((i + 1) / total_steps * 100)
            }
        )
    
    return {'status': 'completed', 'file': file_path}
```

### Tâches avec retry

```python
from celery import shared_task
from requests.exceptions import RequestException

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    retry_backoff=True,      # Délai exponentiel
)
def call_external_api(self, endpoint, data):
    """Appel API externe avec retry automatique."""
    import requests
    
    try:
        response = requests.post(endpoint, json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    
    except RequestException as exc:
        # Retry si erreur réseau
        raise self.retry(exc=exc)
```

### Chaînage de tâches

```python
from celery import chain, group, chord

# Chaîne : task1 → task2 → task3
workflow = chain(
    process_data.s(data),
    validate_result.s(),
    save_to_database.s()
)
result = workflow.delay()

# Groupe : exécuter en parallèle
job = group(
    process_image.s(image1),
    process_image.s(image2),
    process_image.s(image3),
)
result = job.apply_async()

# Chord : groupe + callback
chord(
    group(process_data.s(i) for i in range(10)),
    aggregate_results.s()
).delay()
```

## Appel des tâches

```python
# Views
from django.http import JsonResponse
from .tasks import send_welcome_email, process_uploaded_file

def register_user(request):
    """Inscription utilisateur avec email async."""
    # Créer utilisateur
    user = User.objects.create_user(...)
    
    # Lancer tâche async (ne bloque pas la réponse)
    send_welcome_email.delay(user.id)
    
    return JsonResponse({'message': 'Inscription réussie'})

def upload_file(request):
    """Upload avec traitement async."""
    file = request.FILES['file']
    
    # Sauvegarder fichier
    file_path = save_file(file)
    
    # Lancer traitement
    task = process_uploaded_file.delay(file_path)
    
    return JsonResponse({
        'task_id': task.id,
        'status': 'processing'
    })

def check_task_status(request, task_id):
    """Vérifier le statut d'une tâche."""
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id)
    
    response = {
        'task_id': task_id,
        'status': result.status,
    }
    
    if result.status == 'PROGRESS':
        response['progress'] = result.info.get('progress', 0)
    elif result.status == 'SUCCESS':
        response['result'] = result.get()
    elif result.status == 'FAILURE':
        response['error'] = str(result.result)
    
    return JsonResponse(response)
```

## Tâches planifiées (Celery Beat)

```python
# settings.py
CELERY_BEAT_SCHEDULE = {
    'send-daily-report': {
        'task': 'myapp.tasks.send_daily_report',
        'schedule': 86400.0,  # 24 heures (en secondes)
    },
    'cleanup-old-logs': {
        'task': 'myapp.tasks.cleanup_logs',
        'schedule': 'crontab(hour=2, minute=0)',  # 2h00 du matin
    },
    'check-expired-subscriptions': {
        'task': 'myapp.tasks.check_subscriptions',
        'schedule': 'crontab(minute=0)',  # Toutes les heures
    },
}
```

```python
# myapp/tasks.py
from celery import shared_task
from django.utils import timezone

@shared_task
def send_daily_report():
    """Envoyer rapport quotidien."""
    from django.core.mail import send_mail
    
    yesterday = timezone.now() - timezone.timedelta(days=1)
    
    # Générer rapport
    stats = calculate_daily_stats(yesterday)
    
    send_mail(
        subject=f'Rapport du {yesterday.date()}',
        message=format_report(stats),
        from_email='reports@example.com',
        recipient_list=['admin@example.com'],
    )

@shared_task
def cleanup_logs():
    """Nettoyer les vieux logs."""
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=30)
    
    deleted_count = LogEntry.objects.filter(
        created_at__lt=cutoff_date
    ).delete()[0]
    
    return f'{deleted_count} logs supprimés'
```

## Monitoring et Flower

```bash
# Installer Flower (interface web pour Celery)
pip install flower

# Lancer Flower
celery -A config flower --port=5555

# Avec authentification
celery -A config flower --basic_auth=user:password
```

```python
# Accéder aux infos dans Django
from celery import current_app
from celery.result import AsyncResult

# Lister tâches actives
inspector = current_app.control.inspect()
active_tasks = inspector.active()

# Statistiques
stats = inspector.stats()
```

## Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - db

  celery-worker:
    build: .
    command: celery -A config worker -l info
    volumes:
      - .:/app
    depends_on:
      - redis
      - db
    environment:
      - C_FORCE_ROOT=true  # Dev only

  celery-beat:
    build: .
    command: celery -A config beat -l info
    volumes:
      - .:/app
    depends_on:
      - redis
      - db

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## Tests

```python
# tests/test_tasks.py
import pytest
from celery import states
from myapp.tasks import send_welcome_email

@pytest.mark.django_db
def test_send_welcome_email(user):
    """Tester la tâche d'envoi d'email."""
    result = send_welcome_email.run(user.id)
    
    assert result == f'Email envoyé à {user.email}'
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == 'Bienvenue !'

@pytest.mark.django_db
def test_task_async(user):
    """Tester l'exécution async."""
    result = send_welcome_email.delay(user.id)
    
    # Attendre le résultat
    result.get(timeout=10)
    
    assert result.status == states.SUCCESS
```

## Commandes essentielles

```bash
# Démarrer worker
celery -A config worker -l info

# Démarrer avec pool (plus performant)
celery -A config worker -l info -P gevent -c 100

# Démarrer beat (planificateur)
celery -A config beat -l info

# Les deux ensemble
celery -A config worker -B -l info

# Flower (monitoring)
celery -A config flower

# Purger la file d'attente
celery -A config purge

# Inspecter
celery -A config inspect active
celery -A config inspect scheduled
celery -A config inspect reserved
```

## Checklist Async Tasks

### Setup
- [ ] Celery + Redis installés
- [ ] Configuration dans settings.py
- [ ] Fichier celery.py créé
- [ ] App importé dans __init__.py

### Tâches
- [ ] Tâches décorées avec @shared_task
- [ ] Gestion des erreurs et retry
- [ ] Progress tracking si nécessaire
- [ ] Tests écrits

### Workers
- [ ] Worker démarré
- [ ] Beat pour tâches planifiées
- [ ] Flower pour monitoring
- [ ] Scaling configuré

### Production
- [ ] Redis sécurisé
- [ ] Persistence activée
- [ ] Monitoring en place
- [ ] Logs configurés

## Ressources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Django Celery](https://docs.celeryproject.org/en/stable/django/)
- [Redis](https://redis.io/documentation)
- [Flower](https://flower.readthedocs.io/)
