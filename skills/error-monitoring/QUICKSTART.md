# Error Monitoring - Démarrage Rapide

## Installation (5 minutes)

```bash
# 1. Installer Sentry
pip install sentry-sdk

# 2. Installer structlog (optionnel, pour logs JSON)
pip install structlog python-json-logger
```

## Configuration Sentry basique

```python
# settings.py (production uniquement)
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

SENTRY_DSN = os.environ.get('SENTRY_DSN')

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment="production",
        traces_sample_rate=0.1,  # 10% des transactions
        send_default_pii=True,
    )
```

## Health checks essentiels

```python
# health.py
from django.http import JsonResponse
from django.db import connection, DatabaseError
from django.utils import timezone

def health_check(request):
    """Health check basique."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
        })
    except DatabaseError:
        return JsonResponse({
            'status': 'unhealthy',
            'error': 'Database connection failed'
        }, status=503)

def ready(request):
    """Readiness probe pour Kubernetes."""
    return JsonResponse({'status': 'ready'})
```

```python
# urls.py
path('health/', health_check),
path('health/ready/', ready),
```

## Middleware de logging

```python
# middleware.py
import time
import uuid
import logging

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.start_time = time.time()
        request.request_id = str(uuid.uuid4())[:8]
        
        response = self.get_response(request)
        
        duration = time.time() - request.start_time
        
        logger.info(
            f"{request.method} {request.path} {response.status_code} {duration:.3f}s"
        )
        
        response['X-Request-ID'] = request.request_id
        return response
```

```python
# settings.py
MIDDLEWARE = [
    'myapp.middleware.RequestLoggingMiddleware',
    # ... autres middlewares
]
```

## Logging structuré (optionnel)

```python
# settings.py
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
            'formatter': 'json' if ENVIRONMENT == 'production' else 'simple',
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

## Capture manuelle d'erreurs

```python
import sentry_sdk

try:
    risky_operation()
except Exception as e:
    # Capture avec contexte
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("feature", "payment")
        scope.set_context("order", {"id": order_id, "amount": amount})
        sentry_sdk.capture_exception(e)
    
    # Ou simple
    sentry_sdk.capture_exception(e)

# Message personnalisé
sentry_sdk.capture_message("Something happened", level="warning")
```

## Checklist rapide

- [ ] Sentry DSN configuré dans les variables d'environnement
- [ ] `sentry_sdk.init()` dans settings.py
- [ ] Health check `/health/` fonctionnel
- [ ] Middleware de logging des requêtes
- [ ] Logging structuré en production
- [ ] Notifications configurées dans Sentry

## Commandes utiles

```bash
# Tester Sentry
python manage.py shell -c "
import sentry_sdk
sentry_sdk.capture_message('Test message')
print('Message envoyé à Sentry')
"

# Vérifier health check
curl http://localhost:8000/health/

# Voir les logs
tail -f /var/log/django/app.log | jq  # Si JSON
```

## Configuration Sentry UI

1. Aller sur https://sentry.io (ou votre instance self-hosted)
2. Créer un projet Django
3. Copier le DSN dans les variables d'environnement
4. Configurer les alertes:
   - Settings → Alerts → Create Alert Rule
   - When: A new issue is created
   - Then: Send a notification to Slack
