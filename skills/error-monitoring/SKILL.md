# Skill : Error Monitoring

## Objectif

Mettre en place un système de monitoring complet pour détecter, tracer et alerter sur les erreurs et problèmes de performance en production.

## Quand utiliser ce skill

- Application en production
- Besoin de tracer les erreurs 500
- Monitoring de performance
- Alertes en temps réel
- Analyse des tendances d'erreurs

## Architecture de monitoring

```
Application Django
       │
       ├─→ Sentry (erreurs + performance)
       ├─→ Logging structuré (JSON)
       └─→ Health checks
              │
              ▼
       Dashboards et Alertes
       ├─→ Sentry Dashboard
       ├─→ Grafana / Datadog
       └─→ Slack / Email / PagerDuty
```

## Sentry - Configuration complète

### Installation

```bash
pip install sentry-sdk
```

### Configuration de base

```python
# settings.py (production uniquement)
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

SENTRY_DSN = env('SENTRY_DSN', default=None)

if SENTRY_DSN and ENVIRONMENT == 'production':
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        # Environnement
        environment=ENVIRONMENT,
        
        # Release tracking
        release=env('RELEASE_VERSION', default='unknown'),
        
        # Performance monitoring
        traces_sample_rate=0.1,  # 10% des transactions
        
        # Profiling (Python 3.7+)
        profiles_sample_rate=0.1,
        
        # Attacher le stack trace aux logs
        attach_stacktrace=True,
        
        # Envoyer les données personnelles (attention au RGPD)
        send_default_pii=True,
        
        # Filtrer les erreurs avant envoi
        before_send=before_send_event,
        
        # Ignorer certaines erreurs
        ignore_errors=[
            KeyboardInterrupt,
            'django.http.response.Http404',
        ],
    )

def before_send_event(event, hint):
    """Filtrer ou modifier les événements avant envoi."""
    # Ignorer les erreurs de health check
    if 'url' in event.get('request', {}):
        if event['request']['url'].endswith('/health/'):
            return None
    
    # Masquer les informations sensibles
    if 'user' in event:
        user = event['user']
        user.pop('email', None)
        user.pop('ip_address', None)
    
    return event
```

### Capture manuelle d'erreurs

```python
import sentry_sdk
import logging

logger = logging.getLogger(__name__)

# Capture d'exception
try:
    risky_operation()
except Exception as e:
    # Capture automatique avec contexte
    sentry_sdk.capture_exception(e)
    
    # Ou avec tags et contexte supplémentaire
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("feature", "payment")
        scope.set_tag("user_tier", "premium")
        scope.set_context("order", {
            "order_id": order_id,
            "amount": amount,
            "currency": "EUR"
        })
        scope.set_user({"id": user_id})
        sentry_sdk.capture_exception(e)

# Capture de message
sentry_sdk.capture_message("Something went wrong", level="warning")

# Breadcrumbs (historique des actions)
sentry_sdk.add_breadcrumb(
    category="auth",
    message="User logged in",
    level="info",
    data={"user_id": user.id}
)
```

### Transactions et spans

```python
import sentry_sdk

# Transaction personnalisée
def process_order(order_id):
    with sentry_sdk.start_transaction(
        op="task",
        name="Process Order"
    ) as transaction:
        # Span enfant
        with transaction.start_child(op="db", description="Fetch order"):
            order = Order.objects.get(id=order_id)
        
        with transaction.start_child(op="http", description="Payment API"):
            payment_result = process_payment(order)
        
        with transaction.start_child(op="email", description="Send confirmation"):
            send_confirmation_email(order)
        
        transaction.set_tag("order_id", order_id)
        transaction.set_data("amount", order.total)
        
        return payment_result
```

## Logging structuré

### Configuration JSON

```python
# settings.py
import json
from pythonjsonlogger import jsonlogger

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d',
        },
        'verbose': {
            'format': '{asctime} [{levelname}] {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if ENVIRONMENT == 'production' else 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/app.log',
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'app': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Logger personnalisé avec contexte
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Utilisation
logger.info(
    "order_processed",
    order_id=123,
    user_id=456,
    amount=99.99,
    currency="EUR"
)
# Output: {"event": "order_processed", "order_id": 123, ...}
```

## Health Checks

### Configuration des endpoints

```python
# urls.py
from django.urls import path
from . import health

urlpatterns = [
    path('health/', health.health_check, name='health'),
    path('health/ready/', health.readiness_check, name='readiness'),
    path('health/live/', health.liveness_check, name='liveness'),
    path('health/db/', health.db_health_check, name='db_health'),
]
```

### Vues de health check

```python
# health.py
import logging
from django.http import JsonResponse
from django.db import connection, DatabaseError
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

def health_check(request):
    """Health check complet."""
    checks = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': settings.RELEASE_VERSION,
        'environment': settings.ENVIRONMENT,
        'checks': {}
    }
    
    status_code = 200
    
    # Check Database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks['checks']['database'] = {'status': 'ok'}
    except DatabaseError as e:
        checks['checks']['database'] = {'status': 'error', 'message': str(e)}
        checks['status'] = 'unhealthy'
        status_code = 503
    
    # Check Cache
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            checks['checks']['cache'] = {'status': 'ok'}
        else:
            raise Exception("Cache read/write failed")
    except Exception as e:
        checks['checks']['cache'] = {'status': 'error', 'message': str(e)}
        checks['status'] = 'unhealthy'
        status_code = 503
    
    # Check Disk Space
    import shutil
    try:
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)
        if free_gb < 1:
            checks['checks']['disk'] = {
                'status': 'warning',
                'message': f'Only {free_gb}GB free'
            }
        else:
            checks['checks']['disk'] = {
                'status': 'ok',
                'free_gb': free_gb
            }
    except Exception as e:
        checks['checks']['disk'] = {'status': 'error', 'message': str(e)}
    
    return JsonResponse(checks, status=status_code)


def liveness_check(request):
    """Kubernetes liveness probe - application démarre."""
    return JsonResponse({'status': 'alive'})


def readiness_check(request):
    """Kubernetes readiness probe - prêt à recevoir du trafic."""
    try:
        # Vérifier connexions essentielles
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'ready',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'not_ready',
            'error': str(e)
        }, status=503)


def db_health_check(request):
    """Vérification spécifique de la base de données."""
    from django.db import connection
    from django.db.utils import OperationalError
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    count(*) as connection_count,
                    max(now() - backend_start) as oldest_connection
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            row = cursor.fetchone()
            
        return JsonResponse({
            'status': 'ok',
            'connections': row[0],
            'oldest_connection_seconds': row[1].total_seconds() if row[1] else 0
        })
    except OperationalError as e:
        logger.error(f"Database health check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Database connection failed'
        }, status=503)
```

### Middleware pour tracking des requêtes

```python
# middleware.py
import time
import uuid
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(MiddlewareMixin):
    """Log toutes les requêtes avec timing."""
    
    def process_request(self, request):
        request.start_time = time.time()
        request.request_id = str(uuid.uuid4())[:8]
        return None
    
    def process_response(self, request, response):
        if not hasattr(request, 'start_time'):
            return response
        
        duration = time.time() - request.start_time
        
        log_data = {
            'request_id': getattr(request, 'request_id', 'unknown'),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'remote_addr': self.get_client_ip(request),
        }
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            log_data['user_id'] = request.user.id
        
        # Log différent selon le status
        if response.status_code >= 500:
            logger.error('request_error', extra=log_data)
        elif response.status_code >= 400:
            logger.warning('request_warning', extra=log_data)
        elif duration > 1.0:
            logger.warning('slow_request', extra=log_data)
        else:
            logger.info('request', extra=log_data)
        
        # Ajouter headers pour tracing
        response['X-Request-ID'] = log_data['request_id']
        response['X-Request-Duration'] = f"{log_data['duration_ms']}ms"
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class ErrorHandlingMiddleware(MiddlewareMixin):
    """Middleware global pour capturer les erreurs."""
    
    def process_exception(self, request, exception):
        import sentry_sdk
        
        # Ignorer certaines exceptions
        if isinstance(exception, (Http404, PermissionDenied)):
            return None
        
        # Log avec contexte
        logger.error(
            'unhandled_exception',
            extra={
                'exception': str(exception),
                'path': request.path,
                'method': request.method,
            },
            exc_info=True
        )
        
        # Sentry capture automatique si configuré
        # On peut ajouter du contexte supplémentaire
        with sentry_sdk.push_scope() as scope:
            scope.set_context("request", {
                "path": request.path,
                "method": request.method,
                "headers": dict(request.headers),
            })
            sentry_sdk.capture_exception(exception)
        
        return None  # Laisser Django gérer la réponse
```

## Alerting et notification

### Alertes Sentry

```python
# Configuration des alertes dans Sentry UI:
# 1. Aller dans Settings → Alerts
# 2. Créer des règles:
#    - New issue → Slack
#    - Issue with more than 100 events → Email
#    - Performance regression → Slack + Email
```

### Webhooks personnalisés

```python
# views.py
import hashlib
import hmac
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def sentry_webhook(request):
    """Recevoir les webhooks Sentry."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Vérifier la signature (sécurité)
    signature = request.headers.get('Sentry-Hook-Signature', '')
    expected = hmac.new(
        SENTRY_WEBHOOK_SECRET.encode(),
        request.body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected):
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    
    data = json.loads(request.body)
    
    # Traiter l'alerte
    if data.get('action') == 'triggered':
        # Envoyer notification personnalisée
        send_urgent_alert(data)
    
    return JsonResponse({'status': 'ok'})
```

## Scripts de monitoring

```python
#!/usr/bin/env python
# scripts/monitor.py

import requests
import sys
import argparse

def check_health(url):
    """Vérifier le health check."""
    try:
        response = requests.get(f"{url}/health/", timeout=10)
        data = response.json()
        
        if data['status'] == 'healthy':
            print(f"✅ Health check OK")
            return 0
        else:
            print(f"❌ Health check FAILED")
            for check, result in data['checks'].items():
                if result['status'] != 'ok':
                    print(f"  - {check}: {result.get('message', 'error')}")
            return 1
    except Exception as e:
        print(f"❌ Health check ERROR: {e}")
        return 1

def check_errors(sentry_url, auth_token, project, hours=1):
    """Vérifier les erreurs récentes dans Sentry."""
    from datetime import datetime, timedelta
    
    start = (datetime.now() - timedelta(hours=hours)).isoformat()
    
    headers = {'Authorization': f'Bearer {auth_token}'}
    url = f"{sentry_url}/api/0/projects/{project}/issues/"
    
    response = requests.get(url, headers=headers, params={
        'statsPeriod': f'{hours}h'
    })
    
    issues = response.json()
    error_count = len([i for i in issues if i['level'] == 'error'])
    
    if error_count > 10:
        print(f"⚠️  {error_count} erreurs dans les dernières {hours}h")
        return 1
    else:
        print(f"✅ {error_count} erreurs (acceptable)")
        return 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, help='Application URL')
    parser.add_argument('--check', choices=['health', 'errors'], required=True)
    args = parser.parse_args()
    
    if args.check == 'health':
        sys.exit(check_health(args.url))
    elif args.check == 'errors':
        sys.exit(check_errors(args.url, SENTRY_TOKEN, SENTRY_PROJECT))

if __name__ == '__main__':
    main()
```

## Checklist Error Monitoring

### Setup initial
- [ ] Sentry configuré avec DSN
- [ ] Release tracking activé
- [ ] Performance monitoring (traces_sample_rate)
- [ ] Logging structuré JSON en production
- [ ] Health checks endpoints (/health/, /health/ready/, /health/live/)

### Middleware
- [ ] RequestLoggingMiddleware pour timing
- [ ] ErrorHandlingMiddleware pour capture globale
- [ ] Correlation ID pour tracing

### Alertes
- [ ] Règles Sentry configurées
- [ ] Notifications Slack/Email
- [ ] Seuils d'alerte définis
- [ ] Escalade pour erreurs critiques

### Bonnes pratiques
- [ ] Pas de données personnelles dans les logs
- [ ] Filtrer les erreurs de health check
- [ ] Contexte enrichi pour debug
- [ ] Test des alertes régulièrement

## Ressources

- [Sentry Django Integration](https://docs.sentry.io/platforms/python/guides/django/)
- [Django Logging](https://docs.djangoproject.com/en/stable/topics/logging/)
- [Structlog Documentation](https://www.structlog.org/)
- [Kubernetes Health Checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
