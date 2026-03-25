# Skill : Django Query Optimization

## Objectif

Maîtriser l'art de l'optimisation des requêtes SQL dans Django pour des applications ultra-performantes. Réduire les temps de réponse, éliminer les problèmes N+1, et architecturer des systèmes scalables.

## Quand utiliser ce skill

- Pages qui mettent plus de 2 secondes à charger
- Alertes N+1 queries dans les logs
- Temps de réponse dégradés en production
- Optimisation avant mise à l'échelle
- Audit de performance régulier

---

## Table des matières

1. [Diagnostic des problèmes de performance](#1-diagnostic-des-problèmes-de-performance)
2. [Techniques d'optimisation ORM](#2-techniques-doptimisation-orm)
3. [Indexation et base de données](#3-indexation-et-base-de-données)
4. [Stratégies de caching](#4-stratégies-de-caching)
5. [Pagination et traitement en masse](#5-pagination-et-traitement-en-masse)
6. [Raw SQL et optimisations avancées](#6-raw-sql-et-optimisations-avancées)

---

## 1. Diagnostic des problèmes de performance

### 1.1 Outils de profiling

#### Django Debug Toolbar

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

# Configuration avancée
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]
```

#### Django Silk - Profiling avancé

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

# Configuration
SILKY_PYTHON_PROFILER = True
SILKY_ANALYZE_QUERIES = True
SILKY_MAX_REQUEST_BODY_SIZE = -1  # No limit
SILKY_MAX_RESPONSE_BODY_SIZE = 1024  # 1KB
SILKY_META = True
SILKY_INTERCEPT_PERCENT = 100  # Profile 100% of requests
```

#### Middleware de comptage personnalisé

```python
# middleware/query_counter.py
from django.db import connection
from django.conf import settings
import time
import logging

logger = logging.getLogger(__name__)


class QueryCounterMiddleware:
    """
    Middleware qui compte et log les requêtes SQL par vue.
    Avertit si le seuil est dépassé.
    """
    
    QUERY_THRESHOLD = 20  # Seuil d'alerte
    TIME_THRESHOLD = 1.0  # Seuil en secondes
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Compteur avant la requête
        queries_before = len(connection.queries)
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Analyse après la requête
        duration = time.time() - start_time
        queries_after = len(connection.queries)
        query_count = queries_after - queries_before
        
        # Headers de debug
        if settings.DEBUG:
            response['X-Query-Count'] = str(query_count)
            response['X-Request-Duration'] = f'{duration:.3f}s'
        
        # Logging des lenteurs
        if query_count > self.QUERY_THRESHOLD:
            logger.warning(
                f"⚠️  Nombre de requêtes élevé ({query_count}) sur {request.path}",
                extra={
                    'path': request.path,
                    'method': request.method,
                    'query_count': query_count,
                    'duration': duration,
                    'user_id': getattr(request.user, 'id', None),
                }
            )
        
        if duration > self.TIME_THRESHOLD:
            logger.warning(
                f"🐌 Requête lente ({duration:.2f}s) sur {request.path}",
                extra={
                    'path': request.path,
                    'duration': duration,
                    'query_count': query_count,
                }
            )
        
        return response
```

### 1.2 Identification des N+1

```python
# Script de détection N+1
# management/commands/detect_nplus1.py

from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from django.test import RequestFactory
import sys


class Command(BaseCommand):
    help = 'Détecte les problèmes N+1 dans les vues'
    
    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='URL à tester')
        parser.add_argument('--threshold', type=int, default=5, 
                          help='Seuil d\'alerte N+1')
    
    def handle(self, *args, **options):
        from django.urls import resolve
        
        url = options['url']
        threshold = options['threshold']
        
        factory = RequestFactory()
        request = factory.get(url)
        
        # Résoudre la vue
        resolver_match = resolve(url)
        view_func = resolver_match.func
        
        # Exécuter avec comptage
        connection.force_debug_cursor = True
        reset_queries()
        
        try:
            response = view_func(request, **resolver_match.kwargs)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur: {e}"))
            return
        
        queries = connection.queries
        
        # Analyser les requêtes
        query_types = {}
        for query in queries:
            sql = query['sql']
            # Extraire le modèle principal
            if 'FROM' in sql:
                table = sql.split('FROM')[1].split()[0].strip('"')
                query_types[table] = query_types.get(table, 0) + 1
        
        # Afficher les résultats
        self.stdout.write(self.style.HTTP_INFO(f"\n📊 Analyse de {url}"))
        self.stdout.write(f"Total requêtes: {len(queries)}")
        self.stdout.write(f"Temps total: {sum(float(q['time']) for q in queries):.3f}s\n")
        
        # Détecter N+1
        nplus1_detected = False
        for table, count in query_types.items():
            if count > threshold:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  N+1 détecté sur '{table}': {count} requêtes")
                )
                nplus1_detected = True
        
        if not nplus1_detected:
            self.stdout.write(self.style.SUCCESS("✅ Pas de N+1 détecté"))
        
        # Afficher les requêtes les plus lentes
        slow_queries = sorted(queries, key=lambda x: float(x['time']), reverse=True)[:5]
        self.stdout.write("\n🐌 Requêtes les plus lentes:")
        for i, query in enumerate(slow_queries, 1):
            sql = query['sql'][:100]
            self.stdout.write(f"{i}. [{query['time']}s] {sql}...")
```

---

## 2. Techniques d'optimisation ORM

### 2.1 Select Related vs Prefetch Related

```python
# ❌ PROBLÈME N+1 classique
articles = Article.objects.all()
for article in articles:
    print(article.author.username)  # Requête SQL à chaque itération
    print(article.category.name)    # Autre requête SQL


# ✅ SOLUTION avec select_related (JOIN SQL)
# Utiliser pour: ForeignKey, OneToOne
articles = Article.objects.select_related('author', 'category')
for article in articles:
    print(article.author.username)  # Pas de requête supplémentaire
    print(article.category.name)    # Pas de requête supplémentaire

# SQL généré:
# SELECT ... FROM articles 
# INNER JOIN users ON articles.author_id = users.id
# INNER JOIN categories ON articles.category_id = categories.id


# ✅ SOLUTION avec prefetch_related (requêtes séparées + Python)
# Utiliser pour: ManyToMany, reverse ForeignKey
articles = Article.objects.prefetch_related('tags', 'comments')
for article in articles:
    for tag in article.tags.all():  # Déjà chargé en mémoire
        print(tag.name)
    for comment in article.comments.all():  # Déjà chargé
        print(comment.content)

# SQL généré:
# SELECT * FROM articles
# SELECT * FROM tags WHERE article_id IN (1, 2, 3, ...)
# SELECT * FROM comments WHERE article_id IN (1, 2, 3, ...)
```

### 2.2 Prefetch Related avancé avec Prefetch

```python
from django.db.models import Prefetch

# ✅ Prefetch avec queryset personnalisé
articles = Article.objects.prefetch_related(
    Prefetch(
        'comments',
        queryset=Comment.objects.select_related('user')
                               .filter(is_approved=True)
                               .order_by('-created_at')
                               [:5],  # Limite par article
        to_attr='recent_comments'  # Nom de l'attribut
    ),
    'tags',
)

for article in articles:
    # Utiliser l'attribut préfetché
    for comment in article.recent_comments:  # 5 derniers commentaires approuvés
        print(f"{comment.user.username}: {comment.content}")


# ✅ Prefetch avec annotation
articles = Article.objects.prefetch_related(
    Prefetch(
        'comments',
        queryset=Comment.objects.annotate(
            like_count=Count('likes')
        ).filter(like_count__gt=10),
        to_attr='popular_comments'
    )
)
```

### 2.3 Only() et Defer() - Sélection de champs

```python
# ❌ Charge tous les champs
articles = Article.objects.all()
# SELECT id, title, content, excerpt, meta_description, author_id, created_at, updated_at, ...


# ✅ Only() - Charge uniquement les champs spécifiés
articles = Article.objects.only('id', 'title', 'slug', 'created_at')
# SELECT id, title, slug, created_at FROM articles

for article in articles:
    print(article.title)  # OK - champ chargé
    print(article.content)  # ⚠️ Requête supplémentaire !


# ✅ Defer() - Exclut les champs lourds
articles = Article.objects.defer('content', 'meta_description')
# Sélectionne tous les champs SAUF content et meta_description

# Bon pour les champs texte très longs ou JSON lourds


# ✅ Combinaison avec select_related
articles = Article.objects.select_related('author').only(
    'id', 'title', 'author__username', 'created_at'
)
# Charge uniquement les champs nécessaires des articles ET des auteurs
```

### 2.4 Exists() et Count() - Optimisations booléennes

```python
from django.db.models import Exists, OuterRef

# ❌ Mauvais - charge tous les objets
if Article.objects.all():  # SELECT * FROM articles
    print("Il y a des articles")

# ✅ Bon - requête COUNT optimisée
if Article.objects.exists():  # SELECT 1 FROM articles LIMIT 1
    print("Il y a des articles")


# ❌ Mauvais - charge tout en mémoire
count = len(Article.objects.all())  # Charge tous les objets

# ✅ Bon - COUNT SQL
from django.db.models import Count
count = Article.objects.count()  # SELECT COUNT(*) FROM articles


# ❌ Mauvais - vérifie dans Python
has_comments = article.comments.count() > 0

# ✅ Bon - sous-requête EXISTS
from django.db.models import Exists
articles = Article.objects.annotate(
    has_comments=Exists(
        Comment.objects.filter(article_id=OuterRef('pk'))
    )
)

for article in articles:
    if article.has_comments:  # Valeur booléenne calculée en SQL
        print(f"{article.title} a des commentaires")
```

### 2.5 Annotation et agrégations

```python
from django.db.models import Count, Sum, Avg, Max, Min, F, Q

# ✅ Annoter les compteurs
articles = Article.objects.annotate(
    comment_count=Count('comments'),
    tag_count=Count('tags', distinct=True),
    total_likes=Sum('comments__likes'),
)

for article in articles:
    print(f"{article.title}: {article.comment_count} commentaires")


# ✅ Agrégations sur queryset
stats = Article.objects.aggregate(
    total=Count('id'),
    avg_comments=Avg('comments__count'),
    max_likes=Max('likes'),
    oldest=Min('created_at'),
)
# {'total': 150, 'avg_comments': 12.5, 'max_likes': 450, 'oldest': datetime(...)}


# ✅ F() expressions (éviter les race conditions)
from django.db.models import F

# ❌ Mauvais - récupère puis sauvegarde (race condition possible)
article = Article.objects.get(id=1)
article.view_count += 1
article.save()

# ✅ Bon - UPDATE atomique en base
Article.objects.filter(id=1).update(view_count=F('view_count') + 1)
# UPDATE articles SET view_count = view_count + 1 WHERE id = 1


# ✅ Q() objects pour requêtes complexes
articles = Article.objects.filter(
    Q(status='published') & 
    (Q(title__icontains='django') | Q(content__icontains='django')) &
    Q(created_at__year__gte=2024)
)
```

---

## 3. Indexation et base de données

### 3.1 Index Django

```python
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)
    status = models.CharField(max_length=20, db_index=True)
    created_at = models.DateTimeField(db_index=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_index=True,
        related_name='articles'
    )
    
    class Meta:
        # Index composites
        indexes = [
            models.Index(
                fields=['status', 'created_at'],
                name='article_status_created_idx'
            ),
            models.Index(
                fields=['author', 'created_at'],
                name='article_author_created_idx'
            ),
            # Index pour recherche texte
            models.Index(
                fields=['title'],
                name='article_title_idx',
            ),
        ]
        
        # Index partiel (PostgreSQL uniquement)
        constraints = [
            models.UniqueConstraint(
                fields=['slug'],
                name='unique_published_slug',
                condition=Q(status='published'),
            ),
        ]
```

### 3.2 Index avancés PostgreSQL

```python
# Index GIN pour recherche JSON/full-text (PostgreSQL)
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    search_vector = SearchVectorField(null=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        indexes = [
            # Index GIN pour JSON
            GinIndex(fields=['metadata'], name='article_metadata_gin'),
            # Index GIN pour full-text search
            GinIndex(fields=['search_vector'], name='article_search_gin'),
        ]


# Migration pour créer l'index
# python manage.py makemigrations

# Optimisation avec CONCURRENTLY (ne bloque pas la table)
# operations = [
#     migrations.SeparateDatabaseAndState(
#         state_operations=[
#             migrations.AddIndex(...)
#         ],
#         database_operations=[
#             migrations.RunSQL(
#                 "CREATE INDEX CONCURRENTLY ...",
#                 reverse_sql="DROP INDEX ..."
#             )
#         ]
#     )
# ]
```

### 3.3 Analyse et EXPLAIN

```python
# Analyser les requêtes lentes
# shell

from django.db import connection
from myapp.models import Article

# Activer le logging
from django.conf import settings
settings.DEBUG = True

# Exécuter la requête
qs = Article.objects.filter(status='published').select_related('author')
list(qs)  # Force l'évaluation

# Voir les requêtes
for query in connection.queries:
    print(f"{query['time']}s: {query['sql'][:150]}")


# EXPLAIN avec Django
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        SELECT * FROM myapp_article 
        WHERE status = 'published' 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    result = cursor.fetchone()
    import json
    plan = json.loads(result[0])
    print(json.dumps(plan, indent=2))
```

---

## 4. Stratégies de caching

### 4.1 Cache bas niveau

```python
from django.core.cache import cache
from django.conf import settings
import hashlib
import json


class ArticleCacheService:
    """Service de caching pour les articles."""
    
    CACHE_TTL = 300  # 5 minutes
    
    @classmethod
    def _make_key(cls, prefix, *args, **kwargs):
        """Génère une clé de cache unique."""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @classmethod
    def get_popular_articles(cls, limit=10):
        """Récupère les articles populaires (avec cache)."""
        cache_key = cls._make_key('popular_articles', limit)
        
        articles = cache.get(cache_key)
        if articles is None:
            articles = list(
                Article.objects
                .filter(status='published')
                .annotate(view_count=Count('views'))
                .order_by('-view_count')[:limit]
            )
            cache.set(cache_key, articles, cls.CACHE_TTL)
        
        return articles
    
    @classmethod
    def get_article(cls, slug):
        """Récupère un article par slug."""
        cache_key = f"article:{slug}"
        
        article = cache.get(cache_key)
        if article is None:
            try:
                article = Article.objects.select_related('author').get(
                    slug=slug, 
                    status='published'
                )
                cache.set(cache_key, article, cls.CACHE_TTL)
            except Article.DoesNotExist:
                return None
        
        return article
    
    @classmethod
    def invalidate_article(cls, article):
        """Invalide le cache d'un article."""
        # Supprimer les entrées spécifiques
        cache.delete(f"article:{article.slug}")
        cache.delete(f"article:{article.id}")
        
        # Supprimer les listes
        cache.delete_pattern('popular_articles:*')
        cache.delete_pattern('article_list:*')


# Utilisation dans les signaux
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver([post_save, post_delete], sender=Article)
def invalidate_article_cache(sender, instance, **kwargs):
    ArticleCacheService.invalidate_article(instance)
```

### 4.2 Cache de vues et de templates

```python
from django.views.decorators.cache import cache_page
from django.core.cache import cache

# ✅ Cache de vue entière
@cache_page(60 * 15)  # 15 minutes
def article_list(request):
    articles = Article.objects.filter(status='published')
    return render(request, 'articles/list.html', {'articles': articles})


# ✅ Cache conditionnel
from django.views.decorators.vary import vary_on_cookie

@cache_page(60 * 60)  # 1 heure
@vary_on_cookie  # Cache différent par utilisateur
def dashboard(request):
    # Chaque utilisateur voit son propre dashboard en cache
    return render(request, 'dashboard.html')


# ✅ Cache de fragments de template
{% load cache %}

{% cache 500 sidebar request.user.id %}
    <!-- Contenu coûteux à générer -->
    <div class="sidebar">
        {% for category in categories %}
            <a href="{{ category.get_absolute_url }}">{{ category.name }}</a>
        {% endfor %}
    </div>
{% endcache %}


# ✅ Cache de QuerySet (django-cachalot)
# pip install django-cachalot

# settings.py
INSTALLED_APPS = [
    ...
    'cachalot',
]

CACHALOT_ENABLED = True
CACHALOT_TIMEOUT = 3600
CACHALOT_ONLY_CACHED_TABLES = ['myapp_article', 'myapp_category']

# Tous les QuerySets sur ces tables sont automatiquement cachés
articles = Article.objects.filter(status='published')  # Caché automatiquement
```

### 4.3 Cache avec Redis

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
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'myapp',
        'TIMEOUT': 300,
    }
}

# Cache des sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Utilisation avancée
from django_redis import get_redis_connection

redis = get_redis_connection("default")

# Pipeline pour opérations multiples
pipe = redis.pipeline()
for i in range(100):
    pipe.set(f"key:{i}", f"value:{i}")
pipe.execute()  # 1 aller-retour au lieu de 100

# Incrément atomique
redis.incr("page_views")

# Distributed lock
import redis_lock
lock = redis_lock.Lock(redis, "my-task")
if lock.acquire(blocking=False):
    try:
        # Exécuter la tâche
        pass
    finally:
        lock.release()
```

---

## 5. Pagination et traitement en masse

### 5.1 Pagination efficace

```python
from django.core.paginator import Paginator
from django.db.models import OuterRef, Subquery

# ❌ Mauvais - OFFSET coûteux pour les grandes pages
# Page 10000 doit parcourir 100000 lignes avant de retourner les résultats
page = Article.objects.all()[99900:100000]


# ✅ Pagination par curseur (recommandée pour API)
class CursorPaginator:
    """
    Pagination par curseur utilisant WHERE id > X au lieu de OFFSET.
    Beaucoup plus rapide pour les grandes listes.
    """
    
    def __init__(self, queryset, page_size=20, ordering='-created_at'):
        self.queryset = queryset.order_by(ordering)
        self.page_size = page_size
        self.ordering = ordering
    
    def get_page(self, cursor=None):
        """
        cursor: valeur du champ de tri de la dernière page
        """
        if cursor:
            if self.ordering.startswith('-'):
                queryset = self.queryset.filter(
                    **{self.ordering[1:] + '__lt': cursor}
                )
            else:
                queryset = self.queryset.filter(
                    **{self.ordering + '__gt': cursor}
                )
        else:
            queryset = self.queryset
        
        # Récupérer page_size + 1 pour savoir s'il y a une suite
        items = list(queryset[:self.page_size + 1])
        has_next = len(items) > self.page_size
        items = items[:self.page_size]
        
        next_cursor = None
        if items and has_next:
            next_cursor = getattr(items[-1], self.ordering.lstrip('-'))
        
        return {
            'items': items,
            'next_cursor': next_cursor,
            'has_next': has_next,
            'has_previous': cursor is not None,
        }


# Utilisation
paginator = CursorPaginator(
    Article.objects.filter(status='published'),
    page_size=20
)

# Première page
page1 = paginator.get_page()

# Page suivante
page2 = paginator.get_page(cursor=page1['next_cursor'])
```

### 5.2 Traitement en masse

```python
from django.db import transaction
from itertools import islice


class BulkOperations:
    """Opérations en masse optimisées."""
    
    BATCH_SIZE = 1000
    
    @classmethod
    def bulk_create_articles(cls, articles_data):
        """Création en masse."""
        articles = [Article(**data) for data in articles_data]
        
        # Création par lots pour ne pas surcharger la mémoire
        while articles:
            batch = articles[:cls.BATCH_SIZE]
            Article.objects.bulk_create(batch)
            articles = articles[cls.BATCH_SIZE:]
    
    @classmethod
    def bulk_update_status(cls, article_ids, new_status):
        """Mise à jour en masse."""
        # 1 requête UPDATE quel que soit le nombre d'IDs
        Article.objects.filter(id__in=article_ids).update(status=new_status)
    
    @classmethod
    def process_large_queryset(cls, queryset, process_fn):
        """
        Traite un queryset grand en itérant par lots.
        Évite de charger tout en mémoire.
        """
        iterator = queryset.iterator(chunk_size=cls.BATCH_SIZE)
        
        for batch in iter(lambda: list(islice(iterator, cls.BATCH_SIZE)), []):
            with transaction.atomic():
                for item in batch:
                    process_fn(item)
    
    @classmethod
    @transaction.atomic
    def bulk_upsert(cls, articles_data, unique_fields=['slug']):
        """
        Upsert: INSERT ou UPDATE selon l'existence.
        PostgreSQL uniquement.
        """
        from django.db import connection
        
        # Utiliser ON CONFLICT de PostgreSQL
        with connection.cursor() as cursor:
            # Construire la requête bulk
            values = []
            for data in articles_data:
                values.append("(" + ",".join([f"'{v}'" for v in data.values()]) + ")")
            
            sql = f"""
                INSERT INTO myapp_article (title, slug, content, status)
                VALUES {','.join(values)}
                ON CONFLICT (slug) DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    updated_at = NOW()
            """
            cursor.execute(sql)


# Exemple d'utilisation
# Mise à jour de milliers d'articles
BulkOperations.bulk_update_status(range(1, 100000), 'archived')

# Traitement par lots
queryset = Article.objects.filter(status='draft')
BulkOperations.process_large_queryset(
    queryset,
    lambda article: article.publish()
)
```

---

## 6. Raw SQL et optimisations avancées

### 6.1 Raw SQL optimisé

```python
from django.db import connection


class RawSQLQueries:
    """Requêtes SQL brutes pour cas complexes."""
    
    @staticmethod
    def get_monthly_stats():
        """
        Agrégations complexes non supportées par l'ORM.
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    date_trunc('month', created_at) as month,
                    count(*) as total_articles,
                    count(DISTINCT author_id) as unique_authors,
                    avg(length(content)) as avg_content_length,
                    sum(view_count) as total_views
                FROM myapp_article
                WHERE status = 'published'
                GROUP BY date_trunc('month', created_at)
                ORDER BY month DESC
                LIMIT 12
            """)
            
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    @staticmethod
    def get_related_articles(article_id, limit=5):
        """
        Recommandation basée sur les tags communs (PostgreSQL).
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH article_tags AS (
                    SELECT tag_id 
                    FROM myapp_article_tags 
                    WHERE article_id = %s
                )
                SELECT 
                    a.id,
                    a.title,
                    a.slug,
                    count(at.tag_id) as common_tags
                FROM myapp_article a
                JOIN myapp_article_tags at ON a.id = at.article_id
                WHERE at.tag_id IN (SELECT tag_id FROM article_tags)
                AND a.id != %s
                AND a.status = 'published'
                GROUP BY a.id, a.title, a.slug
                ORDER BY common_tags DESC, a.created_at DESC
                LIMIT %s
            """, [article_id, article_id, limit])
            
            return cursor.fetchall()


# Raw QuerySet de Django
articles = Article.objects.raw("""
    SELECT a.*, u.username as author_name
    FROM myapp_article a
    JOIN auth_user u ON a.author_id = u.id
    WHERE a.status = 'published'
    ORDER BY a.created_at DESC
    LIMIT 10
""")

for article in articles:
    print(article.title)
    print(article.author_name)  # Attribut ajouté par la requête
```

### 6.2 CTE (Common Table Expressions)

```python
from django.db import connection


def get_comment_thread(comment_id):
    """
    Récupère un fil de commentaires avec récursivité (PostgreSQL).
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            WITH RECURSIVE comment_tree AS (
                -- Commentaire de départ
                SELECT id, content, parent_id, author_id, created_at, 0 as depth
                FROM myapp_comment
                WHERE id = %s
                
                UNION ALL
                
                -- Commentaires enfants
                SELECT c.id, c.content, c.parent_id, c.author_id, c.created_at, ct.depth + 1
                FROM myapp_comment c
                JOIN comment_tree ct ON c.parent_id = ct.id
            )
            SELECT ct.*, u.username as author_name
            FROM comment_tree ct
            JOIN auth_user u ON ct.author_id = u.id
            ORDER BY ct.created_at
        """, [comment_id])
        
        return cursor.fetchall()


def get_article_hierarchy():
    """
    Hiérarchie de catégories avec agrégations.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            WITH RECURSIVE category_tree AS (
                SELECT id, name, parent_id, 0 as level, ARRAY[id] as path
                FROM myapp_category
                WHERE parent_id IS NULL
                
                UNION ALL
                
                SELECT c.id, c.name, c.parent_id, ct.level + 1, ct.path || c.id
                FROM myapp_category c
                JOIN category_tree ct ON c.parent_id = ct.id
            ),
            category_stats AS (
                SELECT 
                    category_id,
                    count(*) as article_count,
                    sum(view_count) as total_views
                FROM myapp_article
                WHERE status = 'published'
                GROUP BY category_id
            )
            SELECT 
                ct.*,
                COALESCE(cs.article_count, 0) as articles,
                COALESCE(cs.total_views, 0) as views
            FROM category_tree ct
            LEFT JOIN category_stats cs ON ct.id = cs.category_id
            ORDER BY ct.path
        """)
        
        return cursor.fetchall()
```

### 6.3 Window Functions

```python
from django.db import connection


def get_article_rankings():
    """
    Classements avec fonctions de fenêtre PostgreSQL.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                id,
                title,
                view_count,
                created_at,
                
                -- Rang global par vues
                rank() OVER (ORDER BY view_count DESC) as global_rank,
                
                -- Rang dans la catégorie
                rank() OVER (
                    PARTITION BY category_id 
                    ORDER BY view_count DESC
                ) as category_rank,
                
                -- Percentile (top %)
                percent_rank() OVER (ORDER BY view_count DESC) as percentile,
                
                -- Articles précédent/suivant
                lag(id) OVER (ORDER BY created_at) as prev_article_id,
                lead(id) OVER (ORDER BY created_at) as next_article_id,
                
                -- Moyenne mobile sur 7 jours
                avg(view_count) OVER (
                    ORDER BY created_at 
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) as moving_avg_views
                
            FROM myapp_article
            WHERE status = 'published'
            ORDER BY view_count DESC
            LIMIT 100
        """)
        
        return cursor.fetchall()
```

### 6.4 Connection Pooling

```python
# settings/production.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='5432'),
        
        # Connection pooling avec django-db-geventpool (pour async)
        # Ou configuration native PostgreSQL
        'CONN_MAX_AGE': 600,  # Garder les connexions ouvertes 10 minutes
        'OPTIONS': {
            # Pooling au niveau application (psycopg2)
            'MIN_CONNS': 1,
            'MAX_CONNS': 10,
        }
    }
}


# Alternative: django-db-geventpool pour haute concurrence
# pip install django-db-geventpool

DATABASES = {
    'default': {
        'ENGINE': 'django_db_geventpool.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'CONN_MAX_AGE': 0,  # Géré par le pool
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        }
    }
}
```

---

## Checklist complète d'optimisation

### Avant mise en production

- [ ] Django Debug Toolbar installé et configuré
- [ ] Pas de N+1 queries détectés (< 10 requêtes par page)
- [ ] Temps de réponse < 200ms pour les pages principales
- [ ] Indexes ajoutés sur les champs fréquemment filtrés
- [ ] `select_related()` utilisé pour toutes les ForeignKey
- [ ] `prefetch_related()` utilisé pour ManyToMany/reverse FK
- [ ] `only()` utilisé pour les listes (sélection de champs)
- [ ] Cache configuré (Redis/Memcached)
- [ ] Sessions en cache
- [ ] Static files compressés et servis via CDN

### Monitoring continu

- [ ] Sentry configuré avec performance monitoring
- [ ] Logs des requêtes lentes (> 1s)
- [ ] Alertes sur nombre de requêtes excessif (> 20)
- [ ] Tableau de bord de performance (DataDog/New Relic)
- [ ] EXPLAIN ANALYZE régulier sur les requêtes critiques

### Optimisations avancées

- [ ] Pagination par curseur pour les API
- [ ] `bulk_create`/`bulk_update` pour imports massifs
- [ ] Raw SQL pour les requêtes complexes (CTEs, Window Functions)
- [ ] Connection pooling configuré
- [ ] Read replicas pour les requêtes en lecture
- [ ] Materialized views pour les rapports

---

## Commandes utiles

```bash
# Analyser les requêtes d'une vue
python manage.py shell -c "
from django.db import connection
from myapp.views import MyView
connection.queries_log = []
v = MyView()
qs = v.get_queryset()
list(qs)
print(f'Requêtes: {len(connection.queries)}')
"

# EXPLAIN ANALYZE
python manage.py dbshell
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT * FROM myapp_article;

# Vider le cache Redis
redis-cli FLUSHDB

# Stats PostgreSQL
python manage.py dbshell
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(tabid)) 
FROM pg_tables 
WHERE schemaname = 'public';
```

---

## Ressources

- [Django Database Optimization](https://docs.djangoproject.com/en/stable/topics/db/optimization/)
- [PostgreSQL Query Optimization](https://www.postgresql.org/docs/current/performance-tips.html)
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/)
- [Django Silk](https://github.com/jazzband/django-silk)
- [Redis Documentation](https://redis.io/documentation)
- [Use the Index, Luke!](https://use-the-index-luke.com/)
