# Performance Optimization - Démarrage Rapide

## Installation des outils (3 minutes)

```bash
# 1. Django Debug Toolbar (dev uniquement)
pip install django-debug-toolbar

# 2. Django Silk (profiling avancé)
pip install django-silk

# 3. Django Redis Cache
pip install django-redis
```

## Configuration rapide

```python
# settings.py (development)

# Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
INTERNAL_IPS = ['127.0.0.1']

# Silk
INSTALLED_APPS += ['silk']
MIDDLEWARE += ['silk.middleware.SilkyMiddleware']

# Cache Redis (pour tous les environnements)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

```python
# urls.py
path('__debug__/', include('debug_toolbar.urls')),
path('silk/', include('silk.urls', namespace='silk')),
```

## Commandes essentielles

### Identifier les problèmes N+1

```python
# ❌ Mauvais - N+1 queries
articles = Article.objects.all()
for article in articles:
    print(article.author.name)  # N requêtes supplémentaires

# ✅ Solution - select_related
articles = Article.objects.select_related('author')
for article in articles:
    print(article.author.name)  # 0 requête supplémentaire

# ✅ Solution - prefetch_related (ManyToMany)
articles = Article.objects.prefetch_related('tags')
for article in articles:
    for tag in article.tags.all():
        print(tag.name)
```

### Optimiser les requêtes courantes

```python
# ✅ exists() au lieu de all()
if Article.objects.exists():  # COUNT optimisé
    pass

# ✅ count() au lieu de len()
count = Article.objects.count()  # SQL COUNT

# ✅ values_list() pour quelques champs
titles = Article.objects.values_list('title', flat=True)

# ✅ annotate() pour les agrégations
from django.db.models import Count
articles = Article.objects.annotate(comment_count=Count('comments'))
```

### Mise en cache

```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page

# Cache de vue
@cache_page(60 * 15)  # 15 minutes
def my_view(request):
    return render(request, 'template.html')

# Cache de bas niveau
def get_data():
    data = cache.get('my_data')
    if data is None:
        data = expensive_operation()
        cache.set('my_data', data, 3600)  # 1 heure
    return data

# Supprimer du cache
cache.delete('my_data')
```

### Bulk operations

```python
# ✅ Création en masse
articles = [Article(title=f"Article {i}") for i in range(1000)]
Article.objects.bulk_create(articles, batch_size=100)

# ✅ Mise à jour en masse
Article.objects.filter(status='draft').update(status='published')
```

## Template pour debug

```python
# Middleware simple pour compter les requêtes
class QueryCountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.db import connection
        queries_before = len(connection.queries)
        
        response = self.get_response(request)
        
        queries_after = len(connection.queries)
        count = queries_after - queries_before
        
        print(f"📊 {count} requêtes SQL pour {request.path}")
        
        if count > 20:
            print(f"⚠️  Trop de requêtes! Détails:")
            for q in connection.queries[queries_before:queries_after]:
                print(f"  {q['time']}s: {q['sql'][:80]}...")
        
        return response
```

## Checklist rapide

### Base de données
- [ ] `select_related()` sur les ForeignKey
- [ ] `prefetch_related()` sur les ManyToMany
- [ ] `exists()` pour vérifier présence
- [ ] `count()` au lieu de `len(all())`
- [ ] Index sur les champs recherchés

### Cache
- [ ] Cache configuré (Redis/Memcached)
- [ ] Cache sur les vues lentes
- [ ] Cache des données coûteuses
- [ ] Invalidation correcte

### Optimisations rapides
- [ ] `only()`/`defer()` pour les champs lourds
- [ ] `bulk_create()` pour les imports
- [ ] Pagination sur les listes longues
- [ ] Whitenoise pour les statics

### Monitoring
- [ ] Debug Toolbar installé
- [ ] Silk pour profiling
- [ ] Sentry avec performance
- [ ] Logs des requêtes lentes

## Résoudre les problèmes courants

### Requête lente ?
```bash
# Activer le logging SQL
python manage.py shell -c "
from django.conf import settings
settings.DEBUG = True
# Exécuter votre code
"

# Voir dans Debug Toolbar ou:
from django.db import connection
print(connection.queries)
```

### Trop de requêtes ?
```python
# Ajouter ce middleware temporairement
# Voir le nombre exact de requêtes par page
```

### Cache ne fonctionne pas ?
```bash
# Vérifier Redis
redis-cli ping

# Vérifier la configuration Django
python manage.py shell -c "
from django.core.cache import cache
cache.set('test', 'value', 10)
print(cache.get('test'))
"
```
