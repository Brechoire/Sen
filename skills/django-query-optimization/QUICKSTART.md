# Quick Start - Django Query Optimization

Guide rapide pour diagnostiquer et optimiser les requêtes SQL dans Django.

## Installation des outils

```bash
# Debug Toolbar (dev uniquement)
pip install django-debug-toolbar

# Django Silk (profiling avancé)
pip install django-silk

# Caching Redis
pip install django-redis

# Cache automatique des QuerySets
pip install django-cachalot

# Connection pooling (optionnel)
pip install django-db-geventpool
```

## Configuration rapide

### 1. Debug Toolbar

```python
# settings/local.py
INSTALLED_APPS = [
    ...
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    ...
]

INTERNAL_IPS = ['127.0.0.1']
```

### 2. Redis Cache

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

## Commandes de diagnostic

### Compter les requêtes SQL

```bash
# Analyser une vue spécifique
python manage.py shell -c "
from django.db import connection
from myapp.views import ArticleListView

# Simuler une requête
from django.test import RequestFactory
request = RequestFactory().get('/articles/')
view = ArticleListView.as_view()

connection.queries_log = []
response = view(request)

print(f'Requêtes SQL: {len(connection.queries)}')
for q in connection.queries[:5]:
    print(f'  [{q[\"time\"]}s] {q[\"sql\"][:80]}...')
"
```

### Détecter N+1

```python
# Signes de N+1:
# - Plusieurs requêtes identiques avec ID différent
# - Nombre de requêtes proportionnel au nombre d'objets

# ❌ Mauvais (N+1)
articles = Article.objects.all()
for a in articles:
    print(a.author.username)  # Requête par article

# ✅ Bon (2 requêtes seulement)
articles = Article.objects.select_related('author')
for a in articles:
    print(a.author.username)  # Déjà chargé
```

### EXPLAIN PostgreSQL

```bash
# Dans dbshell
python manage.py dbshell

# EXPLAIN simple
EXPLAIN SELECT * FROM myapp_article WHERE status = 'published';

# EXPLAIN détaillé
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT * FROM myapp_article 
WHERE status = 'published' 
ORDER BY created_at DESC;

# Voir les indexes existants
\di myapp_article*

# Stats de la table
SELECT pg_size_pretty(pg_total_relation_size('myapp_article'));
```

## Patterns d'optimisation rapides

### Pattern 1: Liste avec relations

```python
# ❌ Avant (N+1)
class ArticleListView(ListView):
    model = Article
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for article in context['articles']:
            print(article.author.email)  # N requêtes
        return context

# ✅ Après (2 requêtes)
class ArticleListView(ListView):
    model = Article
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'author', 'category'  # ForeignKey/OneToOne
        ).prefetch_related(
            'tags', 'comments'     # ManyToMany/reverse FK
        )
```

### Pattern 2: Sélection de champs

```python
# ❌ Charge tout
Article.objects.all()

# ✅ Liste légère
Article.objects.only('id', 'title', 'slug', 'created_at')

# ✅ Exclusion de champs lourds
Article.objects.defer('content', 'meta_description')
```

### Pattern 3: Agrégations efficaces

```python
from django.db.models import Count, Sum, Exists, OuterRef

# ❌ Compte en Python
count = len(Article.objects.all())

# ✅ Compte en SQL
count = Article.objects.count()

# ✅ Annoter les compteurs
articles = Article.objects.annotate(
    comment_count=Count('comments'),
    total_likes=Sum('comments__likes'),
    has_comments=Exists(
        Comment.objects.filter(article_id=OuterRef('pk'))
    )
)
```

### Pattern 4: Cache basique

```python
from django.core.cache import cache

def get_popular_articles(limit=10):
    cache_key = f'popular_articles_{limit}'
    articles = cache.get(cache_key)
    
    if articles is None:
        articles = list(
            Article.objects
            .filter(status='published')
            .order_by('-view_count')[:limit]
        )
        cache.set(cache_key, articles, 300)  # 5 min
    
    return articles
```

### Pattern 5: Pagination optimisée

```python
# ❌ Offset lent pour grandes pages
page = Article.objects.all()[99900:100000]

# ✅ Pagination par curseur
class CursorPaginator:
    def __init__(self, queryset, page_size=20):
        self.queryset = queryset
        self.page_size = page_size
    
    def get_page(self, cursor=None):
        if cursor:
            qs = self.queryset.filter(id__gt=cursor)
        else:
            qs = self.queryset
        
        items = list(qs[:self.page_size + 1])
        has_next = len(items) > self.page_size
        
        return {
            'items': items[:self.page_size],
            'next_cursor': items[-1].id if has_next else None,
            'has_next': has_next,
        }
```

## Checklist de performance

### Avant chaque déploiement

```bash
# 1. Vérifier les requêtes
python manage.py shell -c "
from myapp.views import *
from django.db import connection
connection.queries_log = []

# Teste chaque vue principale
v = ArticleListView()
v.request = type('Request', (), {'GET': {}, 'user': None})()
list(v.get_queryset())

print(f'⚠️  {len(connection.queries)} requêtes SQL')
assert len(connection.queries) < 10, 'Trop de requêtes!'
"

# 2. Vérifier les indexes
python manage.py dbshell -c "
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'myapp_article';
"

# 3. Lancer les tests de performance
pytest tests/performance/ -v
```

### Points de contrôle

- [ ] N+1 éliminés (utiliser `select_related` + `prefetch_related`)
- [ ] `only()`/`defer()` sur les listes
- [ ] `exists()` au lieu de `if queryset:`
- [ ] `count()` au lieu de `len(queryset)`
- [ ] Pagination par curseur pour API
- [ ] Cache sur données fréquemment accédées
- [ ] Indexes sur champs de filtre/tri
- [ ] `CONN_MAX_AGE` configuré

## Anti-patterns à éviter

```python
# ❌ NEVER DO THIS

# 1. N+1 caché
for article in Article.objects.all():
    print(article.comments.count())  # N requêtes

# 2. Tout charger en mémoire
articles = list(Article.objects.all())  # Charge tout
for a in articles[:10]:  # Utilise seulement 10
    pass

# 3. Filtrer en Python
articles = Article.objects.all()
published = [a for a in articles if a.status == 'published']  # Non!

# 4. Boucle de saves
for article in articles:
    article.view_count += 1
    article.save()  # N requêtes UPDATE

# 5. Raw SQL sans paramètres
cursor.execute(f"SELECT * FROM articles WHERE id = {user_id}")  # SQL Injection!
```

## Optimisations avancées (une seule à la fois)

### 1. Raw SQL pour requêtes complexes

```python
from django.db import connection

def get_complex_stats():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT date_trunc('month', created_at) as month,
                   count(*) as total,
                   avg(view_count) as avg_views
            FROM myapp_article
            GROUP BY date_trunc('month', created_at)
            ORDER BY month DESC
            LIMIT 12
        """)
        return cursor.fetchall()
```

### 2. Bulk operations

```python
# Création en masse
Article.objects.bulk_create([
    Article(title=f'Article {i}')
    for i in range(1000)
], batch_size=100)

# Mise à jour en masse
Article.objects.filter(status='draft').update(status='published')

# Suppression en masse
Article.objects.filter(created_at__lt=old_date).delete()
```

### 3. Cachalot (cache automatique)

```python
# settings.py
INSTALLED_APPS += ['cachalot']

CACHALOT_ENABLED = True
CACHALOT_TIMEOUT = 3600

# Tous les QuerySets sont automatiquement cachés
articles = Article.objects.filter(status='published')  # Caché!
```

## Monitoring en production

```python
# Middleware de monitoring
class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from django.db import connection
        import time
        
        queries_before = len(connection.queries)
        start = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start
        queries = len(connection.queries) - queries_before
        
        # Log si trop de requêtes
        if queries > 20:
            logger.warning(f"⚠️  {queries} requêtes sur {request.path}")
        
        if duration > 1.0:
            logger.warning(f"🐌 {duration:.2f}s sur {request.path}")
        
        return response
```

## Commandes de debug

```bash
# Voir les requêtes SQL en temps réel
python manage.py shell
>>> from django.db import connection
>>> from myapp.models import Article
>>> connection.queries_log = []
>>> list(Article.objects.select_related('author').all())
>>> print(len(connection.queries))

# Vider le cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Stats Redis
redis-cli info stats
redis-cli monitor  # Attention: très verbeux!

# PostgreSQL: requêtes lentes
python manage.py dbshell
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

## Ressources rapides

- [SKILL.md complet](./SKILL.md) - Documentation détaillée
- [Django DB Optimization](https://docs.djangoproject.com/en/stable/topics/db/optimization/)
- [Use the Index, Luke!](https://use-the-index-luke.com/)
- [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/current/sql-explain.html)

---

**Règle d'or**: Mesure avant d'optimiser. Utilise Debug Toolbar pour identifier les vrais problèmes.
