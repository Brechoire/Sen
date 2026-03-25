# Skill : Bonnes Pratiques Django

## Objectif

Ce skill permet de maintenir une qualité de code Django optimale en suivant les meilleures pratiques de la communauté. Il couvre la structure de projet, la sécurité, les performances, les tests et le déploiement.

## Quand utiliser ce skill

- Lors de la création d'un nouveau projet Django
- Avant de refactoriser du code existant
- Lors de la revue de code
- Pour configurer l'intégration continue (CI/CD)
- Pour optimiser les performances

## Architecture recommandée

### Structure de projet moderne

```
mon_projet/
├── config/                    # Configuration du projet
│   ├── __init__.py
│   ├── settings/             # Settings par environnement
│   │   ├── __init__.py
│   │   ├── base.py          # Configuration de base
│   │   ├── local.py         # Développement local
│   │   ├── staging.py       # Pré-production
│   │   └── production.py    # Production
│   ├── urls.py              # URLs principales
│   ├── wsgi.py              # WSGI
│   └── asgi.py              # ASGI
├── apps/                     # Applications Django
│   ├── __init__.py
│   ├── users/               # Ex: gestion des utilisateurs
│   ├── blog/                # Ex: blog
│   └── api/                 # Ex: API REST
├── static/                   # Fichiers statiques
│   ├── css/
│   ├── js/
│   └── images/
├── media/                    # Fichiers uploadés (dev)
├── templates/                # Templates de base
│   └── base.html
├── requirements/             # Dépendances par environnement
│   ├── base.txt
│   ├── local.txt
│   └── production.txt
├── locale/                   # Fichiers de traduction
├── tests/                    # Tests globaux
│   ├── __init__.py
│   ├── conftest.py          # Configuration pytest
│   └── factories.py         # Factories pour tests
├── manage.py
├── .env.example             # Exemple de variables d'environnement
├── .env                     # Variables d'environnement (non versionné)
├── pyproject.toml           # Configuration des outils
└── docker-compose.yml       # Docker (optionnel)
```

### Configuration des settings

**config/settings/base.py** :
```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'django_extensions',
    'debug_toolbar',
    'crispy_forms',
    'crispy_bootstrap5',
]

LOCAL_APPS = [
    'apps.users',
    'apps.blog',
    'apps.api',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Login/Logout redirects
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**config/settings/local.py** :
```python
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

# Database locale (SQLite pour dev rapide)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email backend pour dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug Toolbar
INTERNAL_IPS = ['127.0.0.1']

# Caching en mémoire
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

## Bonnes pratiques par composant

### 1. Modèles (Models)

**Structure recommandée** :
```python
from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils import timezone
from django.urls import reverse


class Post(models.Model):
    """Représente un article de blog."""
    
    # Choices comme constantes de classe
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('archived', 'Archivé'),
    ]
    
    # Champs
    title = models.CharField(
        max_length=200,
        verbose_name="Titre",
        validators=[MinLengthValidator(5)],
        help_text="Titre de l'article (minimum 5 caractères)"
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        db_index=True,
        validators=[RegexValidator(r'^[a-z0-9-]+$')]
    )
    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="Auteur"
    )
    content = models.TextField(verbose_name="Contenu")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Meta options
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(published_at__isnull=True) | 
                      models.Q(published_at__lte=models.F('created_at')),
                name='valid_publication_date'
            ),
        ]
    
    def __str__(self) -> str:
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        
        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
    
    @property
    def is_published(self) -> bool:
        return self.status == 'published' and self.published_at <= timezone.now()
    
    def publish(self):
        """Publie l'article."""
        self.status = 'published'
        self.published_at = timezone.now()
        self.save()
```

**Checklist modèles** :
- [ ] Utiliser `verbose_name` et `verbose_name_plural`
- [ ] Ajouter des `related_name` explicites sur les ForeignKey
- [ ] Utiliser des `indexes` pour les champs fréquemment filtrés
- [ ] Ajouter des `validators` sur les champs critiques
- [ ] Implémenter `get_absolute_url()`
- [ ] Ajouter des `help_text` descriptifs
- [ ] Utiliser `auto_now_add` et `auto_now` pour les timestamps
- [ ] Définir les `choices` comme constantes de classe
- [ ] Ajouter des type hints sur les méthodes
- [ ] Utiliser des `constraints` pour la logique métier

### 2. Vues (Views)

**Préférer les Class-Based Views (CBV)** :
```python
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count
from .models import Post


class PostListView(ListView):
    """Liste des articles publiés."""
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    queryset = Post.objects.filter(status='published').select_related('author')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class PostDetailView(DetailView):
    """Détail d'un article."""
    model = Post
    template_name = 'blog/post_detail.html'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Post.objects.filter(status='published').select_related('author')


class PostCreateView(LoginRequiredMixin, CreateView):
    """Création d'un article."""
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    success_url = reverse_lazy('blog:post_list')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, "Article créé avec succès !")
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Modification d'un article."""
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff
    
    def get_success_url(self):
        messages.success(self.request, "Article mis à jour !")
        return self.object.get_absolute_url()


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Suppression d'un article."""
    model = Post
    success_url = reverse_lazy('blog:post_list')
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Article supprimé.")
        return super().delete(request, *args, **kwargs)
```

**Checklist vues** :
- [ ] Utiliser `LoginRequiredMixin` pour les vues protégées
- [ ] Utiliser `UserPassesTestMixin` pour les permissions spécifiques
- [ ] Ajouter `select_related` et `prefetch_related` pour optimiser les requêtes
- [ ] Utiliser `messages` pour les notifications utilisateur
- [ ] Implémenter `get_queryset()` pour filtrer les données
- [ ] Utiliser `get_success_url()` plutôt que `success_url` statique
- [ ] Ajouter des docstrings aux classes

### 3. Formulaires (Forms)

```python
from django import forms
from django.core.exceptions import ValidationError
from .models import Post


class PostForm(forms.ModelForm):
    """Formulaire de création/modification d'article."""
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de l\'article'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Contenu de l\'article...'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'title': 'Titre',
            'content': 'Contenu',
            'status': 'Statut',
        }
        help_texts = {
            'title': 'Minimum 5 caractères',
            'status': 'Les articles en brouillon ne sont pas visibles',
        }
    
    def clean_title(self):
        """Validation personnalisée du titre."""
        title = self.cleaned_data['title']
        if 'spam' in title.lower():
            raise ValidationError("Le titre ne peut pas contenir 'spam'.")
        return title
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        content = cleaned_data.get('content')
        
        if title and content and title in content:
            raise ValidationError(
                "Le titre ne doit pas être répété dans le contenu."
            )
        
        return cleaned_data
```

### 4. Templates

**Structure de base** :
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{% block meta_description %}Mon super site{% endblock %}">
    <title>{% block title %}Mon Site{% endblock %}</title>
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar">
        <a href="{% url 'home' %}">Accueil</a>
        {% if user.is_authenticated %}
            <span>Bonjour, {{ user.username }}</span>
            <form method="post" action="{% url 'logout' %}">
                {% csrf_token %}
                <button type="submit">Déconnexion</button>
            </form>
        {% else %}
            <a href="{% url 'login' %}">Connexion</a>
        {% endif %}
    </nav>
    
    <main>
        {% if messages %}
            <div class="messages">
                {% for message in messages %}
                    <div class="alert alert-{{ message.tags }}">
                        {{ message }}
                    </div>
                {% endfor %}
            </div>
        {% endif %}
        
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; {% now "Y" %} Mon Site</p>
    </footer>
    
    <script src="{% static 'js/main.js' %}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

**Template d'héritage** :
```html
<!-- templates/blog/post_list.html -->
{% extends 'base.html' %}
{% load humanize %}

{% block title %}Articles - {{ block.super }}{% endblock %}
{% block meta_description %}Liste des articles de blog{% endblock %}

{% block content %}
<h1>Articles</h1>

<form method="get" action="{% url 'blog:post_list' %}">
    <input type="text" name="q" value="{{ search_query }}" placeholder="Rechercher...">
    <button type="submit">Rechercher</button>
</form>

{% if posts %}
    <div class="post-list">
        {% for post in posts %}
            <article class="post">
                <h2><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></h2>
                <p class="meta">
                    Par {{ post.author }} 
                    le {{ post.created_at|date:"j F Y" }}
                    ({{ post.created_at|naturaltime }})
                </p>
                <p>{{ post.content|truncatewords:30 }}</p>
            </article>
        {% endfor %}
    </div>
    
    {% include 'includes/pagination.html' with page_obj=page_obj %}
{% else %}
    <p>Aucun article trouvé.</p>
{% endif %}
{% endblock %}
```

**Checklist templates** :
- [ ] Utiliser l'héritage de templates (`{% extends %}`)
- [ ] Toujours inclure `{% csrf_token %}` dans les formulaires
- [ ] Utiliser `{% url %}` plutôt que des URLs en dur
- [ ] Échapper les variables avec `{{ variable }}`
- [ ] Utiliser des template tags personnalisés pour la logique complexe
- [ ] Séparer les includes réutilisables
- [ ] Ajouter des meta descriptions
- [ ] Utiliser `{{ block.super }}` pour étendre les blocs parents

### 5. URLs

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.blog.urls', namespace='blog')),
    path('users/', include('apps.users.urls', namespace='users')),
    path('api/', include('apps.api.urls', namespace='api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    import debug_toolbar
    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
```

```python
# apps/blog/urls.py
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/create/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<slug:slug>/update/', views.PostUpdateView.as_view(), name='post_update'),
    path('post/<slug:slug>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
]
```

### 6. Tests

**Configuration pytest** :
```python
# tests/conftest.py
import pytest
from django.contrib.auth import get_user_model
from apps.blog.models import Post

User = get_user_model()


@pytest.fixture
def user(db):
    """Fixture pour créer un utilisateur."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def post(db, user):
    """Fixture pour créer un article."""
    return Post.objects.create(
        title='Test Post',
        content='Test content',
        author=user,
        status='published'
    )
```

**Tests des modèles** :
```python
# apps/blog/tests/test_models.py
import pytest
from django.utils.text import slugify
from apps.blog.models import Post


@pytest.mark.django_db
class TestPostModel:
    """Tests du modèle Post."""
    
    def test_post_creation(self, post):
        """Test la création d'un article."""
        assert post.title == 'Test Post'
        assert post.slug == slugify(post.title)
        assert post.status == 'published'
    
    def test_get_absolute_url(self, post):
        """Test la méthode get_absolute_url."""
        assert post.get_absolute_url() == f'/post/{post.slug}/'
    
    def test_is_published_property(self, post):
        """Test la propriété is_published."""
        assert post.is_published is True
        
        post.status = 'draft'
        post.save()
        assert post.is_published is False
    
    def test_post_ordering(self, user):
        """Test l'ordre de tri des articles."""
        Post.objects.create(title='Old', author=user, status='published')
        Post.objects.create(title='New', author=user, status='published')
        
        posts = Post.objects.all()
        assert posts[0].title == 'New'
        assert posts[1].title == 'Old'
```

**Tests des vues** :
```python
# apps/blog/tests/test_views.py
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestPostListView:
    """Tests de la vue PostListView."""
    
    def test_post_list_view(self, client, post):
        """Test l'affichage de la liste des articles."""
        url = reverse('blog:post_list')
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'posts' in response.context
        assert post.title in response.content.decode()
    
    def test_post_list_search(self, client, post):
        """Test la recherche d'articles."""
        url = reverse('blog:post_list')
        response = client.get(url, {'q': 'Test'})
        
        assert response.status_code == 200
        assert post in response.context['posts']
    
    def test_pagination(self, client, user):
        """Test la pagination."""
        # Créer 15 articles
        for i in range(15):
            Post.objects.create(
                title=f'Post {i}',
                author=user,
                status='published'
            )
        
        url = reverse('blog:post_list')
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.context['posts']) == 10  # paginate_by = 10


@pytest.mark.django_db
class TestPostCreateView:
    """Tests de la vue PostCreateView."""
    
    def test_create_post_requires_login(self, client):
        """Test que la création nécessite une connexion."""
        url = reverse('blog:post_create')
        response = client.get(url)
        
        assert response.status_code == 302  # Redirection vers login
    
    def test_create_post_success(self, client, user):
        """Test la création réussie d'un article."""
        client.force_login(user)
        url = reverse('blog:post_create')
        
        data = {
            'title': 'New Post',
            'content': 'New content',
            'status': 'published'
        }
        response = client.post(url, data)
        
        assert response.status_code == 302  # Redirection après succès
        assert Post.objects.filter(title='New Post').exists()
```

**Checklist tests** :
- [ ] Tester chaque méthode des modèles
- [ ] Tester les validations des formulaires
- [ ] Tester les permissions des vues
- [ ] Tester les URLs
- [ ] Utiliser `pytest-django` et `pytest-cov`
- [ ] Utiliser des fixtures pour les données de test
- [ ] Tester les cas d'erreur (404, 403, etc.)
- [ ] Vérifier la couverture de code (`pytest --cov`)

### 7. Sécurité

**Configuration de base** :
```python
# config/settings/production.py
from .base import *

DEBUG = False

ALLOWED_HOSTS = ['mon-site.com', 'www.mon-site.com']

# Security middleware settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Password hashing (use Argon2)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# Logging for security events
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'level': 'WARNING',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

**Protection CSRF dans les templates** :
```html
<form method="post">
    {% csrf_token %}
    <!-- champs du formulaire -->
</form>
```

**Protection XSS** :
- Toujours utiliser `{{ variable }}` (échappement automatique)
- Utiliser `|safe` uniquement avec des données de confiance
- Pour du HTML riche, utiliser `bleach` :

```python
import bleach
from django import template

register = template.Library()

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'a', 'ul', 'ol', 'li']
ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}

@register.filter
def safe_html(value):
    return bleach.clean(value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
```

**Protection SQL Injection** :
- Toujours utiliser l'ORM Django (jamais de raw SQL avec concaténation)
- Si raw SQL nécessaire, utiliser des paramètres nommés :

```python
# ❌ DANGEREUX
Post.objects.raw(f"SELECT * FROM blog_post WHERE title = '{user_input}'")

# ✅ SÛR
Post.objects.raw("SELECT * FROM blog_post WHERE title = %s", [user_input])

# ✅ Encore mieux : utiliser l'ORM
Post.objects.filter(title=user_input)
```

**Protection contre le clickjacking** :
```python
# Déjà configuré par défaut avec le middleware
# X_FRAME_OPTIONS = 'DENY' dans settings

# Pour permettre l'intégration iframe spécifique
from django.views.decorators.clickjacking import xframe_options_exempt

@xframe_options_exempt
def my_view(request):
    pass
```

**Checklist sécurité** :
- [ ] `DEBUG = False` en production
- [ ] `ALLOWED_HOSTS` correctement configuré
- [ ] HTTPS forcé (`SECURE_SSL_REDIRECT`)
- [ ] Cookies sécurisés (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`)
- [ ] Headers de sécurité (HSTS, XSS, Content-Type)
- [ ] Mot de passe fort (Argon2 recommandé)
- [ ] Protection CSRF activée
- [ ] Échappement automatique des templates
- [ ] Validation des fichiers uploadés
- [ ] Rate limiting sur les vues sensibles

### 8. Performance

**Optimisation des requêtes N+1** :
```python
# ❌ Problème N+1 : requête pour chaque auteur
posts = Post.objects.all()
for post in posts:
    print(post.author.username)  # 1 requête par post !

# ✅ Solution : select_related (pour ForeignKey, OneToOne)
posts = Post.objects.select_related('author').all()

# ✅ Solution : prefetch_related (pour ManyToMany, reverse FK)
posts = Post.objects.prefetch_related('comments', 'tags').all()
```

**Caching** :
```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.db.models.signals import post_save
from django.dispatch import receiver

# Cache de vue
@cache_page(60 * 15)  # 15 minutes
def post_list_view(request):
    pass

# Cache manuel
def get_popular_posts():
    cache_key = 'popular_posts'
    posts = cache.get(cache_key)
    
    if posts is None:
        posts = Post.objects.filter(status='published').order_by('-views')[:10]
        cache.set(cache_key, posts, timeout=300)  # 5 minutes
    
    return posts

# Invalidation du cache
@receiver(post_save, sender=Post)
def invalidate_post_cache(sender, instance, **kwargs):
    cache.delete('popular_posts')
```

**Database optimization** :
```python
# Indexer les champs fréquemment filtrés
class Post(models.Model):
    status = models.CharField(max_length=20, db_index=True)
    created_at = models.DateTimeField(db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

# Utiliser values() pour réduire les données transférées
Post.objects.values('id', 'title', 'slug')

# Utiliser only() pour sélectionner uniquement certains champs
Post.objects.only('title', 'slug')

# Utiliser defer() pour exclure les champs lourds
Post.objects.defer('content')  # Exclut le contenu textuel lourd
```

**Checklist performance** :
- [ ] Utiliser `select_related` pour les ForeignKey
- [ ] Utiliser `prefetch_related` pour les ManyToMany
- [ ] Ajouter des indexes sur les champs filtrés
- [ ] Utiliser le caching (template, view, low-level)
- [ ] Activer le compression des assets (WhiteNoise)
- [ ] Utiliser `django-debug-toolbar` en dev
- [ ] Configurer le connection pooling
- [ ] Utiliser `bulk_create` et `bulk_update`
- [ ] Optimiser les images

## Installation et configuration

### Dépendances

**requirements/base.txt** :
```
Django>=4.2,<5.0
psycopg2-binary>=2.9.0
Pillow>=10.0.0
django-extensions>=3.2.0
django-crispy-forms>=2.0
crispy-bootstrap5>=0.7
whitenoise>=6.5.0
python-dotenv>=1.0.0
gunicorn>=21.0.0
bleach>=6.0.0
```

**requirements/local.txt** :
```
-r base.txt
django-debug-toolbar>=4.2.0
pytest-django>=4.5.0
pytest-cov>=4.1.0
django-stubs>=4.2.0
factory-boy>=3.3.0
ipython>=8.0.0
django-browser-reload>=1.0.0
```

### Configuration pyproject.toml

```toml
[tool.django]
settings_module = "config.settings.local"

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.local"
python_files = ["tests.py", "test_*.py", "*_tests.py"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]

[tool.coverage.run]
source = ["apps"]
omit = ["*/migrations/*", "*/tests/*", "*/admin.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]

[tool.mypy]
plugins = ["mypy_django_plugin.main"]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[tool.django-stubs]
django_settings_module = "config.settings.local"
```

## Workflow quotidien

### 1. Créer une nouvelle app

```bash
# Créer l'app dans le dossier apps
python manage.py startapp mon_app apps/mon_app

# Créer la structure
mkdir -p apps/mon_app/{migrations,templates/mon_app,static/mon_app/{css,js},templatetags}
touch apps/mon_app/{forms.py,urls.py,signals.py}
touch apps/mon_app/templatetags/__init__.py
```

### 2. Créer un modèle avec migrations

```bash
# Créer les migrations
python manage.py makemigrations

# Vérifier les migrations SQL (sans exécuter)
python manage.py sqlmigrate mon_app 0001

# Appliquer les migrations
python manage.py migrate

# Vérifier l'état des migrations
python manage.py showmigrations
```

### 3. Lancer les tests

```bash
# Tous les tests
pytest

# Tests avec couverture
pytest --cov=apps --cov-report=html

# Tests spécifiques
pytest apps/blog/tests/test_models.py

# Tests rapides uniquement
pytest -m "not slow"

# Mode verbeux
pytest -v

# Arrêter au premier échec
pytest -x
```

### 4. Vérifications avant commit

```bash
# Vérifier les migrations
python manage.py makemigrations --check

# Vérifier les erreurs
python manage.py check --deploy

# Lancer les tests
pytest

# Vérifier la sécurité (voir skill security-check)
bandit -r apps/
detect-secrets scan --baseline .secrets.baseline
```

## Pièges à éviter

### 1. Modèles

**Problème** : Oublier `related_name` sur les ForeignKey
```python
# ❌ Problème
author = models.ForeignKey(User, on_delete=models.CASCADE)
# Accès : user.post_set.all() (pas clair)

# ✅ Solution
author = models.ForeignKey(
    User, 
    on_delete=models.CASCADE,
    related_name='posts'
)
# Accès : user.posts.all() (clair)
```

**Problème** : Ne pas utiliser `on_delete`
```python
# ❌ Depuis Django 2.0, on_delete est obligatoire
author = models.ForeignKey(User)

# ✅ Toujours spécifier on_delete
author = models.ForeignKey(User, on_delete=models.CASCADE)
```

### 2. Vues

**Problème** : Ne pas protéger les vues sensibles
```python
# ❌ Dangereux : tout le monde peut créer
class PostCreateView(CreateView):
    pass

# ✅ Protéger avec LoginRequiredMixin
class PostCreateView(LoginRequiredMixin, CreateView):
    pass
```

**Problème** : Requêtes N+1
```python
# ❌ Problème
posts = Post.objects.all()
for post in posts:
    print(post.author.username)  # N+1 requêtes

# ✅ Solution
posts = Post.objects.select_related('author').all()
```

### 3. Templates

**Problème** : Ne pas échapper les données utilisateur
```html
<!-- ❌ DANGEREUX : XSS possible -->
<div>{{ post.content|safe }}</div>

<!-- ✅ SÛR : échappement automatique -->
<div>{{ post.content }}</div>

<!-- ✅ Si HTML nécessaire, utiliser bleach -->
<div>{{ post.content|safe_html }}</div>
```

### 4. Formulaires

**Problème** : Validation uniquement dans le template
```python
# ❌ Validation client uniquement (contournable)
<input type="email" required>

# ✅ Validation serveur obligatoire
class MonForm(forms.Form):
    email = forms.EmailField(required=True)
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("Cet email est déjà utilisé.")
        return email
```

### 5. Sécurité

**Problème** : Secrets dans les settings
```python
# ❌ JAMAIS faire ça
SECRET_KEY = 'ma-cle-super-secrete-12345'

# ✅ Utiliser les variables d'environnement
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
```

**Problème** : DEBUG en production
```python
# ❌ Catastrophique
DEBUG = True  # En production

# ✅ Toujours False en prod
DEBUG = False
```

### 6. Performance

**Problème** : Ne pas utiliser le cache
```python
# ❌ Recalculé à chaque requête
def get_stats():
    return User.objects.annotate(
        post_count=Count('posts')
    ).order_by('-post_count')[:10]

# ✅ Utiliser le cache
def get_stats():
    stats = cache.get('user_stats')
    if stats is None:
        stats = User.objects.annotate(
            post_count=Count('posts')
        ).order_by('-post_count')[:10]
        cache.set('user_stats', stats, 300)
    return stats
```

## Checklist avant mise en production

- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS` configuré
- [ ] `SECRET_KEY` dans variable d'environnement
- [ ] HTTPS activé (`SECURE_SSL_REDIRECT`)
- [ ] Cookies sécurisés
- [ ] Headers de sécurité configurés
- [ ] Base de données PostgreSQL (pas SQLite)
- [ ] Static files collectés (`collectstatic`)
- [ ] Migrations appliquées
- [ ] Tests passent
- [ ] Pas de secrets dans le code
- [ ] Logging configuré
- [ ] Backup automatique configuré
- [ ] Monitoring activé
- [ ] Documentation à jour

## Ressources

- [Documentation Django](https://docs.djangoproject.com/)
- [Django Best Practices](https://django-best-practices.readthedocs.io/)
- [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x)
- [Django for Professionals](https://djangoforprofessionals.com/)
- [Django Packages](https://djangopackages.org/)
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/)
- [Django REST Framework](https://www.django-rest-framework.org/)

## Commandes utiles

```bash
# Créer un superuser
python manage.py createsuperuser

# Shell Django avec auto-import
python manage.py shell_plus --print-sql

# Vérifier les requêtes SQL
python manage.py shell_plus --print-sql

# Générer un graphique des modèles
python manage.py graph_models -a -o models.png

# Réinitialiser les migrations (attention !)
python manage.py migrate mon_app zero
rm apps/mon_app/migrations/000*.py
python manage.py makemigrations
python manage.py migrate

# Dump et load des données
python manage.py dumpdata mon_app > mon_app.json
python manage.py loaddata mon_app.json

# Collecter les static files
python manage.py collectstatic --noinput

# Vérifier les erreurs
python manage.py check
python manage.py check --deploy
```
