# Skill : Performance Optimization

## Objectif

Optimiser les performances des applications Django pour réduire les temps de réponse, minimiser l'utilisation des ressources et améliorer l'expérience utilisateur.

## Quand utiliser ce skill

- Lenteurs détectées en production
- Pages qui mettent > 2s à charger
- Augmentation du load serveur
- N+1 queries dans les logs
- Audit de performance régulier

## Outils de profiling

### Django Debug Toolbar

```python
# settings.py (development uniquement)
INSTALLED_APPS = [
    ...
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    ...
]

INTERNAL_IPS = [
    '127.0.0.1',
]
```

### Django Silk

```python
# settings.py
INSTALLED_APPS = [
    ...
    'silk',
]

MIDDLEWARE = [
    'silk.middleware.SilkyMiddleware',
    ...
]

# URLs
path('silk/', include('silk.urls', namespace='silk')),

# Configuration optionnelle
SILKY_PYTHON_PROFILER = True
SILKY_ANALYZE_QUERIES = True
```

### Django Query Counter

```python
# Middleware personnalisé pour compter les requêtes
class QueryCountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.db import connection
        
        queries_before = len(connection.queries)
        response = self.get_response(request)
        queries_after = len(connection.queries)
        
        query_count = queries_after - queries_before
        
        # Log si trop de requêtes
        if query_count > 20:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"⚠️  {query_count} requêtes SQL sur {request.path}"
            )
        
        response['X-Query-Count'] = str(query_count)
        return response
```

## Optimisation des requêtes SQL

### 1. N+1 Query Problem

```python
# ❌ PROBLÈME N+1
# 1 requête pour les articles + N requêtes pour les auteurs
articles = Article.objects.all()
for article in articles:
    print(article.author.name)  # ← Requête SQL à chaque itération

# ✅ SOLUTION : select_related (ForeignKey, OneToOne)
# 1 seule requête avec JOIN
articles = Article.objects.select_related('author')
for article in articles:
    print(article.author.name)  # ← Pas de requête supplémentaire

# ✅ SOLUTION : prefetch_related (ManyToMany, reverse FK)
# 2 requêtes : une pour les articles, une pour les tags
articles = Article.objects.prefetch_related('tags')
for article in articles:
    for tag in article.tags.all():  # ← Pas de requête supplémentaire
        print(tag.name)

# ✅ Combinaison
articles = Article.objects.select_related('author').prefetch_related('tags', 'comments')
```

### 2. N'appeler .all() que quand nécessaire

```python
# ❌ Mauvais - évalue toute la queryset
if Article.objects.all():  # Charge tous les articles en mémoire
    print("Il y a des articles")

# ✅ Bon - utilise exists()
if Article.objects.exists():  # Une requête COUNT optimisée
    print("Il y a des articles")

# ❌ Mauvais - compte tous les objets
count = len(Article.objects.all())  # Charge tous en mémoire

# ✅ Bon - utilise count()
count = Article.objects.count()  # Requête COUNT SQL
```

### 3. Values et Values_list

```python
# ❌ Charge tous les champs et crée des objets complets
articles = Article.objects.all()
titles = [a.title for a in articles]

# ✅ Ne charge que les champs nécessaires
titles = Article.objects.values_list('title', flat=True)

# ✅ Pour plusieurs champs
data = Article.objects.values('id', 'title', 'author__name')
# Returns: [{'id': 1, 'title': '...', 'author__name': '...'}, ...]
```

### 4. Indexation de base de données

```python
# models.py
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)
    created_at = models.DateTimeField(db_index=True)
    author = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE,
        db_index=True
    )
    
    class Meta:
        # Index composites
        indexes = [
            models.Index(
                fields=['author', 'created_at'],
                name='author_created_idx'
            ),
        ]
```

```python
# Migration pour ajouter un index
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [...]
    
    operations = [
        migrations.AddIndex(
            model_name='article',
            index=models.Index(
                fields=['status', 'published_at'],
                name='status_published_idx'
            ),
        ),
    ]
```

### 5. Pagination efficace

```python
from django.core.paginator import Paginator
from django.db.models import OuterRef, Subquery

# ❌ Mauvais - OFFSET coûteux pour les grandes pages
# Page 10000 doit parcourir 100000 lignes
objects = MyModel.objects.all()[999900:1000000]

# ✅ Bon - Pagination avec curseur (CursorPagination)
# Utilise WHERE id > X au lieu de OFFSET
class CursorPaginator:
    def __init__(self, queryset, page_size=20):
        self.queryset = queryset
        self.page_size = page_size
    
    def get_page(self, cursor=None):
        if cursor:
            queryset = self.queryset.filter(id__gt=cursor)
        else:
            queryset = self.queryset
        
        page = list(queryset[:self.page_size + 1])
        has_next = len(page) > self.page_size
        
        return {
            'items': page[:self.page_size],
            'next_cursor': page[-1].id if has_next else None,
            'has_next': has_next
        }
```

## Caching

### 1. Cache par vue

```python
from django.views.decorators.cache import cache_page
from django.core.cache import cache

# Cache pendant 15 minutes
@cache_page(60 * 15)
def article_list(request):
    articles = Article.objects.select_related('author')
    return render(request, 'articles/list.html', {'articles': articles})

# Cache conditionnel
@cache_page(60 * 60, key_prefix="articles_%s" % get_language())
def article_detail(request, slug):
    ...
```

### 2. Cache de fragments de template

```django
{% load cache %}

{% cache 500 sidebar request.user.id %}
    <!-- Contenu coûteux à générer -->
    {% for item in expensive_query %}
        {{ item }}
    {% endfor %}
{% endcache %}
```

### 3. Cache de bas niveau

```python
from django.core.cache import cache
from django.conf import settings

# Stocker une valeur
cache.set('my_key', 'my_value', timeout=300)  # 5 minutes

# Récupérer une valeur
value = cache.get('my_key')

# Pattern "get or set"
def get_expensive_data():
    cache_key = 'expensive_data'
    data = cache.get(cache_key)
    
    if data is None:
        data = calculate_expensive_data()
        cache.set(cache_key, data, timeout=3600)
    
    return data

# Supprimer du cache
cache.delete('my_key')
cache.delete_many(['key1', 'key2'])
cache.clear()  # Tout vider (attention !)
```

### 4. Cache avec Redis

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        }
    }
}

# Cache des sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

## Optimisation des modèles

### 1. defer() et only()

```python
# ❌ Charge tous les champs
articles = Article.objects.all()

# ✅ N'exclude que les champs lourds (texte, JSON, etc.)
articles = Article.objects.defer('content', 'metadata')

# ✅ Ou n'inclut que les champs nécessaires
articles = Article.objects.only('id', 'title', 'slug')
```

### 2. Bulk operations

```python
# ❌ N requêtes INSERT
for i in range(1000):
    Article.objects.create(title=f"Article {i}")

# ✅ 1 requête INSERT
articles = [Article(title=f"Article {i}") for i in range(1000)]
Article.objects.bulk_create(articles, batch_size=100)

# Mise à jour en masse
Article.objects.filter(status='draft').update(status='published')

# Suppression en masse
Article.objects.filter(created_at__lt=old_date).delete()
```

### 3. Raw SQL (quand nécessaire)

```python
from django.db import connection

# Pour des requêtes complexes non supportées par l'ORM
def get_complex_stats():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                date_trunc('month', created_at) as month,
                count(*) as total,
                avg(price) as avg_price
            FROM orders
            GROUP BY date_trunc('month', created_at)
            ORDER BY month DESC
            LIMIT 12
        """)
        return cursor.fetchall()
```

## Optimisation des vues

### 1. Conditionnalité dans les templates

```python
# ❌ Mauvais - logique complexe dans le template
def dashboard(request):
    all_orders = Order.objects.all()
    return render(request, 'dashboard.html', {'orders': all_orders})

# Template: {% if orders.count > 100 %} ...

# ✅ Bon - préparer les données
from django.db.models import Count

def dashboard(request):
    context = {
        'order_count': Order.objects.count(),
        'has_many_orders': Order.objects.count() > 100,
        'recent_orders': Order.objects.select_related('customer')[:10],
    }
    return render(request, 'dashboard.html', context)
```

### 2. QuerySet dans les serializers (DRF)

```python
from rest_framework import serializers

# ❌ Mauvais - N+1 dans le serializer
class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name')
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'items_count']
    
    def get_items_count(self, obj):
        return obj.items.count()  # ← N requêtes

# ✅ Bon - Annoter dans la view
class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name')
    items_count = serializers.IntegerField()
    
    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'items_count']

# View
from django.db.models import Count

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('customer').annotate(
        items_count=Count('items')
    )
```

## Optimisation des assets

### 1. Compression et minification

```python
# settings.py
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Whitenoise pour servir les fichiers statiques
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    ...
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 2. CDN

```python
# settings.py (production)
STATIC_URL = 'https://cdn.example.com/static/'
MEDIA_URL = 'https://cdn.example.com/media/'

# AWS S3 + CloudFront
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'my-bucket'
AWS_S3_CUSTOM_DOMAIN = 'cdn.example.com'
```

## Monitoring des performances

### 1. Middleware de timing

```python
import time
import logging

logger = logging.getLogger(__name__)

class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Log les requêtes lentes
        if duration > 1.0:
            logger.warning(
                f"🐌 Requête lente: {request.path} ({duration:.2f}s)"
            )
        
        response['X-Request-Duration'] = f'{duration:.3f}s'
        return response
```

### 2. Sentry Performance

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,  # 10% des requêtes
    send_default_pii=True,
    _experiments={
        'profiles_sample_rate': 0.1,  # Profiling
    }
)
```

### 3. Django Admin pour monitoring

```python
# admin.py
from django.contrib import admin
from django.db.models import Avg, Count
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'view_count', 'created_at']
    list_select_related = ['author']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            view_count=Count('views')
        )
```

## Commandes d'audit

```bash
# Analyser les requêtes
python manage.py shell -c "
from django.db import connection
from myapp.models import Article

# Activer le logging
from django.conf import settings
settings.DEBUG = True

# Exécuter la requête
articles = Article.objects.all()
for a in articles[:5]:
    print(a.title)

# Afficher les requêtes
for query in connection.queries:
    print(f'{query['time']}s: {query['sql'][:100]}...')
print(f'Total: {len(connection.queries)} requêtes')
"

# EXPLAIN ANALYZE avec Django
python manage.py dbshell
# Puis: EXPLAIN ANALYZE SELECT ...;

# Utiliser django-debug-toolbar
# Installer et naviguer sur les pages
```

## Checklist Performance

### Base de données
- [ ] N+1 queries identifiées et corrigées (select_related/prefetch_related)
- [ ] Indexes ajoutés sur les champs fréquemment recherchés
- [ ] Pagination par curseur pour les grandes listes
- [ ] bulk_create/bulk_update utilisés pour les imports
- [ ] only()/defer() pour les champs lourds

### Cache
- [ ] Cache configuré (Redis/Memcached)
- [ ] Cache sur les vues lentes
- [ ] Cache des fragments de templates coûteux
- [ ] Cache des sessions
- [ ] Invalidation du cache correctement gérée

### Code
- [ ] exists() utilisé au lieu de all() pour vérifier
- [ ] count() utilisé au lieu de len(all())
- [ ] annotate() pour les agrégations dans DRF
- [ ] Raw SQL uniquement si nécessaire
- [ ] Middleware de performance pour monitoring

### Assets
- [ ] Fichiers statiques compressés
- [ ] CDN configuré en production
- [ ] Images optimisées
- [ ] Lazy loading pour les images

### Monitoring
- [ ] Sentry configuré avec performance
- [ ] Logs des requêtes lentes (>1s)
- [ ] Django Debug Toolbar en dev
- [ ] Silk en dev/staging si besoin

## Ressources

- [Django Performance Optimization](https://docs.djangoproject.com/en/stable/topics/performance/)
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/)
- [Django Silk](https://github.com/jazzband/django-silk)
- [PostgreSQL Query Optimization](https://www.postgresql.org/docs/current/performance-tips.html)
- [Redis Documentation](https://redis.io/documentation)
