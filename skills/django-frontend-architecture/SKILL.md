# Skill : Django Frontend Architecture

## Objectif

Créer des architectures frontend modernes dans Django avec une séparation propre entre HTML, CSS et JavaScript, des requêtes optimisées et une application rigoureuse des principes SOLID.

## Quand utiliser ce skill

- Création d'interfaces utilisateur complexes dans Django
- Refactoring de templates monolithiques
- Optimisation des performances frontend/backend
- Mise en place d'une architecture maintenable et testable
- Intégration de JavaScript moderne avec Django

---

## Table des matières

1. [Architecture HTML/CSS/JS séparée](#1-architecture-htmlcssjs-séparée)
2. [Optimisation des requêtes](#2-optimisation-des-requêtes)
3. [Application des principes SOLID](#3-application-des-principes-solid)
4. [Patterns et anti-patterns](#4-patterns-et-anti-patterns)

---

## 1. Architecture HTML/CSS/JS séparée

### 1.1 Structure de projet recommandée

```
mon_projet/
├── apps/
│   └── mon_app/
│       ├── static/
│       │   └── mon_app/
│       │       ├── css/
│       │       │   ├── components/
│       │       │   │   ├── _buttons.css
│       │       │   │   ├── _forms.css
│       │       │   │   └── _tables.css
│       │       │   ├── layout/
│       │       │   │   ├── _grid.css
│       │       │   │   ├── _header.css
│       │       │   │   └── _sidebar.css
│       │       │   ├── pages/
│       │       │   │   ├── _dashboard.css
│       │       │   │   └── _profile.css
│       │       │   └── main.css          # Point d'entrée CSS
│       │       ├── js/
│       │       │   ├── modules/
│       │       │   │   ├── api.js        # Gestion des appels API
│       │       │   │   ├── forms.js      # Validation et gestion formulaires
│       │       │   │   ├── utils.js      # Utilitaires
│       │       │   │   └── ui.js         # Composants UI interactifs
│       │       │   ├── pages/
│       │       │   │   ├── dashboard.js  # Logique spécifique dashboard
│       │       │   │   └── profile.js    # Logique spécifique profil
│       │       │   └── main.js           # Point d'entrée JS
│       │       └── images/
│       └── templates/
│           └── mon_app/
│               ├── base/                 # Templates de base
│               │   ├── _base.html
│               │   └── _layout.html
│               ├── components/           # Composants réutilisables
│               │   ├── _pagination.html
│               │   ├── _form_field.html
│               │   └── _modal.html
│               └── pages/                # Templates de pages
│                   ├── dashboard.html
│                   └── profile.html
```

### 1.2 Templates Django structurés

#### Template de base (SRP)

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Mon Application{% endblock %}</title>
    
    {% load static %}
    
    <!-- CSS global -->
    <link rel="stylesheet" href="{% static 'css/main.css' %}">
    
    <!-- CSS spécifique à la page -->
    {% block extra_css %}{% endblock %}
    
    <!-- Meta tags dynamiques -->
    {% block meta %}
    <meta name="description" content="{% block meta_description %}{% endblock %}">
    {% endblock %}
</head>
<body data-page="{% block page_name %}default{% endblock %}">
    
    <!-- Header component -->
    {% include 'components/_header.html' %}
    
    <!-- Messages flash -->
    {% if messages %}
        {% include 'components/_messages.html' %}
    {% endif %}
    
    <!-- Contenu principal -->
    <main id="main-content" role="main">
        {% block content %}{% endblock %}
    </main>
    
    <!-- Footer component -->
    {% include 'components/_footer.html' %}
    
    <!-- JavaScript global -->
    <script src="{% static 'js/main.js' %}"></script>
    
    <!-- JavaScript spécifique à la page -->
    {% block extra_js %}{% endblock %}
    
</body>
</html>
```

#### Composants réutilisables

```html
<!-- templates/components/_pagination.html -->
{% if page_obj.has_other_pages %}
<nav class="pagination" aria-label="Pagination">
    <div class="pagination-info">
        Page {{ page_obj.number }} sur {{ page_obj.paginator.num_pages }}
    </div>
    
    <div class="pagination-links">
        {% if page_obj.has_previous %}
            <a href="?page=1{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}" 
               class="pagination-link pagination-first">
                « Première
            </a>
            <a href="?page={{ page_obj.previous_page_number }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}" 
               class="pagination-link pagination-prev">
                ‹ Précédente
            </a>
        {% endif %}
        
        <span class="pagination-current">
            {{ page_obj.number }}
        </span>
        
        {% if page_obj.has_next %}
            <a href="?page={{ page_obj.next_page_number }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}" 
               class="pagination-link pagination-next">
                Suivante ›
            </a>
            <a href="?page={{ page_obj.paginator.num_pages }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}" 
               class="pagination-link pagination-last">
                Dernière »
            </a>
        {% endif %}
    </div>
</nav>
{% endif %}
```

### 1.3 CSS modulaire et maintenable

```css
/* static/css/main.css */

/* Variables CSS (Design System) */
:root {
    /* Couleurs */
    --color-primary: #3b82f6;
    --color-primary-dark: #2563eb;
    --color-secondary: #64748b;
    --color-success: #22c55e;
    --color-warning: #f59e0b;
    --color-error: #ef4444;
    
    /* Typographie */
    --font-sans: system-ui, -apple-system, sans-serif;
    --font-mono: 'Courier New', monospace;
    
    /* Espacements */
    --space-1: 0.25rem;
    --space-2: 0.5rem;
    --space-3: 0.75rem;
    --space-4: 1rem;
    --space-6: 1.5rem;
    --space-8: 2rem;
    
    /* Breakpoints (pour référence) */
    --breakpoint-sm: 640px;
    --breakpoint-md: 768px;
    --breakpoint-lg: 1024px;
    
    /* Ombres */
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    
    /* Transitions */
    --transition-fast: 150ms ease;
    --transition-base: 250ms ease;
}

/* Reset et base */
@import 'base/_reset.css';
@import 'base/_typography.css';

/* Layouts */
@import 'layout/_grid.css';
@import 'layout/_header.css';

/* Composants */
@import 'components/_buttons.css';
@import 'components/_forms.css';
@import 'components/_tables.css';
@import 'components/_pagination.css';
@import 'components/_modal.css';

/* Utilities */
@import 'utilities/_spacing.css';
@import 'utilities/_colors.css';
```

```css
/* static/css/components/_buttons.css */

/* Bouton de base */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    font-family: var(--font-sans);
    font-size: 0.875rem;
    font-weight: 500;
    line-height: 1.5;
    border-radius: 0.375rem;
    border: 1px solid transparent;
    cursor: pointer;
    transition: all var(--transition-fast);
    text-decoration: none;
}

/* Variantes */
.btn--primary {
    background-color: var(--color-primary);
    color: white;
}

.btn--primary:hover:not(:disabled) {
    background-color: var(--color-primary-dark);
}

.btn--secondary {
    background-color: transparent;
    border-color: var(--color-secondary);
    color: var(--color-secondary);
}

.btn--secondary:hover:not(:disabled) {
    background-color: var(--color-secondary);
    color: white;
}

/* États */
.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn--loading {
    position: relative;
    color: transparent;
}

.btn--loading::after {
    content: '';
    position: absolute;
    width: 1rem;
    height: 1rem;
    border: 2px solid transparent;
    border-top-color: currentColor;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Tailles */
.btn--sm {
    padding: var(--space-1) var(--space-3);
    font-size: 0.75rem;
}

.btn--lg {
    padding: var(--space-3) var(--space-6);
    font-size: 1rem;
}
```

### 1.4 JavaScript modulaire (ES6+)

```javascript
// static/js/main.js
import { initForms } from './modules/forms.js';
import { initNavigation } from './modules/navigation.js';
import { initUI } from './modules/ui.js';

/**
 * Initialisation principale de l'application
 * Pattern : Module Pattern + Initialisation conditionnelle
 */
document.addEventListener('DOMContentLoaded', () => {
    // Détection de la page courante
    const currentPage = document.body.dataset.page;
    
    // Initialisation globale
    initNavigation();
    initUI();
    initForms();
    
    // Chargement dynamique du module de page
    if (currentPage) {
        import(`./pages/${currentPage}.js`)
            .then(module => {
                if (module.init) {
                    module.init();
                }
            })
            .catch(() => {
                // Pas de module spécifique pour cette page
            });
    }
});
```

```javascript
// static/js/modules/api.js

/**
 * Module API - Gestion des appels HTTP
 * Pattern : Single Responsibility Principle (SRP)
 */

const API_BASE_URL = '/api';

/**
 * Configuration par défaut pour fetch
 */
const defaultConfig = {
    headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json',
    },
    credentials: 'same-origin',
};

/**
 * Gestionnaire d'erreurs centralisé
 */
class APIError extends Error {
    constructor(message, status, data = null) {
        super(message);
        this.status = status;
        this.data = data;
        this.name = 'APIError';
    }
}

/**
 * Effectue une requête API
 */
async function request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
        ...defaultConfig,
        ...options,
        headers: {
            ...defaultConfig.headers,
            ...options.headers,
        },
    };
    
    // Ajout du CSRF token pour les requêtes non-GET
    if (config.method && config.method !== 'GET') {
        config.headers['X-CSRFToken'] = getCSRFToken();
    }
    
    try {
        const response = await fetch(url, config);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new APIError(
                errorData?.message || `HTTP ${response.status}`,
                response.status,
                errorData
            );
        }
        
        // Vérification si la réponse contient du JSON
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        return await response.text();
        
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Récupère le token CSRF depuis le cookie
 */
function getCSRFToken() {
    const cookie = document.cookie
        .split(';')
        .find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

/**
 * API exposée
 * Pattern : Interface Segregation Principle (ISP)
 */
export const api = {
    get: (endpoint) => request(endpoint, { method: 'GET' }),
    post: (endpoint, data) => request(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }),
    put: (endpoint, data) => request(endpoint, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }),
    patch: (endpoint, data) => request(endpoint, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }),
    delete: (endpoint) => request(endpoint, { method: 'DELETE' }),
};
```

```javascript
// static/js/modules/forms.js

import { api } from './api.js';

/**
 * Module Forms - Gestion et validation des formulaires
 * Pattern : Single Responsibility Principle
 */

/**
 * Initialise tous les formulaires de la page
 */
export function initForms() {
    document.querySelectorAll('form[data-validate]').forEach(form => {
        initFormValidation(form);
    });
    
    document.querySelectorAll('form[data-ajax]').forEach(form => {
        initAjaxForm(form);
    });
}

/**
 * Validation de formulaire
 */
function initFormValidation(form) {
    form.addEventListener('submit', (e) => {
        let isValid = true;
        
        // Validation des champs requis
        form.querySelectorAll('[required]').forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                showFieldError(field, 'Ce champ est requis');
            } else {
                clearFieldError(field);
            }
        });
        
        // Validation email
        form.querySelectorAll('input[type="email"]').forEach(field => {
            if (field.value && !isValidEmail(field.value)) {
                isValid = false;
                showFieldError(field, 'Email invalide');
            }
        });
        
        if (!isValid) {
            e.preventDefault();
        }
    });
}

/**
 * Formulaire AJAX
 */
function initAjaxForm(form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitBtn = form.querySelector('[type="submit"]');
        const originalText = submitBtn.textContent;
        
        try {
            // État de chargement
            submitBtn.disabled = true;
            submitBtn.classList.add('btn--loading');
            
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            const action = form.getAttribute('action') || window.location.pathname;
            const method = form.getAttribute('method') || 'POST';
            
            const response = await api[method.toLowerCase()](action, data);
            
            // Succès
            showNotification('success', response.message || 'Opération réussie');
            
            // Redirection ou reset
            if (response.redirect) {
                window.location.href = response.redirect;
            } else if (!form.dataset.noReset) {
                form.reset();
            }
            
        } catch (error) {
            console.error('Form error:', error);
            showNotification('error', error.message || 'Une erreur est survenue');
            
            // Affichage des erreurs de validation
            if (error.data?.errors) {
                Object.entries(error.data.errors).forEach(([field, messages]) => {
                    const input = form.querySelector(`[name="${field}"]`);
                    if (input) {
                        showFieldError(input, messages[0]);
                    }
                });
            }
        } finally {
            submitBtn.disabled = false;
            submitBtn.classList.remove('btn--loading');
            submitBtn.textContent = originalText;
        }
    });
}

/**
 * Affiche une erreur sur un champ
 */
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('form-field--error');
    
    const errorElement = document.createElement('span');
    errorElement.className = 'form-field__error';
    errorElement.textContent = message;
    
    field.parentNode.appendChild(errorElement);
}

/**
 * Supprime l'erreur d'un champ
 */
function clearFieldError(field) {
    field.classList.remove('form-field--error');
    const error = field.parentNode.querySelector('.form-field__error');
    if (error) {
        error.remove();
    }
}

/**
 * Valide un email
 */
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Affiche une notification
 */
function showNotification(type, message) {
    // Utilisation du module UI
    import('./ui.js').then(({ showToast }) => {
        showToast(type, message);
    });
}
```

---

## 2. Optimisation des requêtes

### 2.1 Views optimisées avec sélection de champs

```python
# apps/mon_app/views.py

from django.views.generic import ListView, DetailView
from django.db.models import Prefetch, Count, Q
from django.core.cache import cache


class OptimizedListView(ListView):
    """
    Vue liste optimisée avec:
    - select_related pour ForeignKey
    - prefetch_related pour ManyToMany et reverse FK
    - only() pour sélectionner uniquement les champs nécessaires
    - Pagination efficace
    """
    model = Article
    template_name = 'mon_app/article_list.html'
    context_object_name = 'articles'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Sélection optimale des relations
        queryset = queryset.select_related('author', 'category')
        
        # Prefetch pour les relations inverses
        queryset = queryset.prefetch_related(
            Prefetch(
                'comments',
                queryset=Comment.objects.select_related('user').only('id', 'content', 'user__username', 'created_at')
            ),
            'tags'
        )
        
        # Sélection des champs nécessaires uniquement
        queryset = queryset.only(
            'id', 'title', 'slug', 'excerpt', 'created_at',
            'author__username', 'author__avatar',
            'category__name', 'category__slug'
        )
        
        # Filtrage
        if self.request.GET.get('q'):
            search_query = self.request.GET.get('q')
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(excerpt__icontains=search_query)
            )
        
        if self.request.GET.get('category'):
            queryset = queryset.filter(category__slug=self.request.GET.get('category'))
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Données de filtrage (cacheables)
        context['categories'] = cache.get('article_categories')
        if not context['categories']:
            context['categories'] = Category.objects.only('name', 'slug')
            cache.set('article_categories', list(context['categories']), 300)
        
        context['search_query'] = self.request.GET.get('q', '')
        return context
```

### 2.2 API endpoints optimisés

```python
# apps/mon_app/api/views.py

from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch, Count, Avg


class ArticleListSerializer(serializers.ModelSerializer):
    """Serializer léger pour les listes."""
    author_name = serializers.CharField(source='author.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'excerpt', 'author_name', 
                  'category_name', 'created_at', 'comment_count']


class ArticleDetailSerializer(serializers.ModelSerializer):
    """Serializer complet pour le détail."""
    author = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    related_articles = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = '__all__'
    
    def get_author(self, obj):
        return {
            'id': obj.author.id,
            'username': obj.author.username,
            'avatar': obj.author.avatar.url if obj.author.avatar else None,
        }
    
    def get_related_articles(self, obj):
        # Articles liés par catégorie (limité à 3)
        return ArticleListSerializer(
            Article.objects.filter(category=obj.category)
            .exclude(id=obj.id)
            .select_related('author')
            [:3],
            many=True
        ).data


class ArticleViewSet(viewsets.ModelViewSet):
    """
    ViewSet avec différents serializers selon l'action
    et optimisations de requêtes.
    """
    queryset = Article.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer
        return ArticleDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.action == 'list':
            # Optimisations pour la liste
            queryset = queryset.select_related('author', 'category')
            queryset = queryset.annotate(comment_count=Count('comments'))
            queryset = queryset.only(
                'id', 'title', 'slug', 'excerpt', 'created_at',
                'author__username', 'category__name'
            )
            
        elif self.action == 'retrieve':
            # Optimisations pour le détail
            queryset = queryset.select_related('author', 'category')
            queryset = queryset.prefetch_related(
                Prefetch(
                    'comments',
                    queryset=Comment.objects.select_related('user')
                ),
                'tags'
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Recherche optimisée avec pagination par curseur."""
        query = request.query_params.get('q', '')
        cursor = request.query_params.get('cursor')
        page_size = int(request.query_params.get('page_size', 20))
        
        queryset = self.get_queryset()
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            )
        
        # Pagination par curseur (plus efficace que OFFSET)
        if cursor:
            queryset = queryset.filter(id__lt=cursor)
        
        articles = list(queryset[:page_size + 1])
        has_next = len(articles) > page_size
        articles = articles[:page_size]
        
        serializer = ArticleListSerializer(articles, many=True)
        
        return Response({
            'results': serializer.data,
            'next_cursor': articles[-1].id if has_next and articles else None,
            'has_next': has_next,
        })
```

### 2.3 Services métier avec caching

```python
# apps/mon_app/services.py

from django.core.cache import cache
from django.db.models import Prefetch
from typing import Optional, List


class ArticleService:
    """
    Service métier pour les articles
    Pattern : Single Responsibility + Dependency Inversion
    """
    
    CACHE_TTL = 300  # 5 minutes
    
    @classmethod
    def get_popular_articles(cls, limit: int = 5) -> List[Article]:
        """
        Récupère les articles populaires (avec cache)
        """
        cache_key = f'popular_articles_{limit}'
        articles = cache.get(cache_key)
        
        if articles is None:
            articles = list(
                Article.objects
                .filter(status='published')
                .select_related('author', 'category')
                .annotate(view_count=Count('views'))
                .order_by('-view_count', '-created_at')
                [:limit]
            )
            cache.set(cache_key, articles, cls.CACHE_TTL)
        
        return articles
    
    @classmethod
    def get_article_detail(cls, slug: str) -> Optional[Article]:
        """
        Récupère un article avec toutes ses relations
        """
        cache_key = f'article_detail_{slug}'
        article = cache.get(cache_key)
        
        if article is None:
            try:
                article = Article.objects.select_related(
                    'author', 'category'
                ).prefetch_related(
                    Prefetch(
                        'comments',
                        queryset=Comment.objects.select_related('user')
                        .order_by('-created_at')
                    ),
                    'tags'
                ).get(slug=slug, status='published')
                
                cache.set(cache_key, article, cls.CACHE_TTL)
            except Article.DoesNotExist:
                return None
        
        return article
    
    @classmethod
    def invalidate_article_cache(cls, article: Article):
        """
        Invalide le cache d'un article
        """
        cache.delete(f'article_detail_{article.slug}')
        cache.delete_pattern('popular_articles_*')
        cache.delete_pattern('article_list_*')
```

---

## 3. Application des principes SOLID

### 3.1 Single Responsibility Principle (SRP)

```python
# ❌ AVANT - Responsabilités mélangées
class ArticleManager:
    def create_article(self, data):
        # Validation
        # Création en base
        # Envoi d'email
        # Génération du slug
        # Indexation dans le moteur de recherche
        pass
    
    def send_newsletter(self):
        # Envoi de newsletter
        pass
    
    def generate_pdf(self):
        # Génération PDF
        pass


# ✅ APRÈS - Responsabilités séparées

# 1. Validation
class ArticleValidator:
    """Responsabilité : valider les données d'article."""
    
    def validate(self, data: dict) -> ValidationResult:
        errors = []
        
        if not data.get('title') or len(data['title']) < 5:
            errors.append("Le titre doit faire au moins 5 caractères")
        
        if not data.get('content'):
            errors.append("Le contenu est requis")
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)


# 2. Persistence
class ArticleRepository:
    """Responsabilité : persistance des articles."""
    
    def create(self, data: dict, author: User) -> Article:
        return Article.objects.create(
            title=data['title'],
            content=data['content'],
            author=author,
            slug=self._generate_slug(data['title'])
        )
    
    def _generate_slug(self, title: str) -> str:
        from django.utils.text import slugify
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        
        while Article.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug


# 3. Notifications
class ArticleNotifier:
    """Responsabilité : notifier lors de la création d'articles."""
    
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
    
    def notify_new_article(self, article: Article):
        subscribers = Subscriber.objects.filter(is_active=True)
        
        for subscriber in subscribers:
            self.email_service.send(
                to=subscriber.email,
                subject=f"Nouvel article : {article.title}",
                template='emails/new_article.html',
                context={'article': article}
            )


# 4. Service orchestrateur
class ArticleCreationService:
    """
    Responsabilité : orchestrer la création d'un article
    Dépend d'abstractions, pas d'implémentations concrètes
    """
    
    def __init__(
        self,
        validator: ArticleValidator,
        repository: ArticleRepository,
        notifier: ArticleNotifier,
        search_indexer: SearchIndexer,
        cache_service: CacheService
    ):
        self.validator = validator
        self.repository = repository
        self.notifier = notifier
        self.search_indexer = search_indexer
        self.cache_service = cache_service
    
    def create(self, data: dict, author: User) -> Article:
        # Validation
        validation = self.validator.validate(data)
        if not validation.valid:
            raise ValidationError(validation.errors)
        
        # Création
        article = self.repository.create(data, author)
        
        # Actions post-création (asynchrones si possible)
        self._on_article_created(article)
        
        return article
    
    def _on_article_created(self, article: Article):
        """Actions déclenchées après création."""
        # Indexation
        self.search_indexer.index_article(article)
        
        # Notification
        self.notifier.notify_new_article(article)
        
        # Invalidation du cache
        self.cache_service.invalidate_article_cache(article)
```

### 3.2 Open/Closed Principle (OCP)

```python
from abc import ABC, abstractmethod
from typing import Protocol


# ✅ Abstraction pour les exporteurs
class ArticleExporter(Protocol):
    """Interface pour tous les exporteurs d'articles."""
    
    def export(self, article: Article) -> str:
        ...
    
    def get_extension(self) -> str:
        ...


# Implémentations concrètes
class PDFExporter:
    """Export PDF - Extension."""
    
    def export(self, article: Article) -> str:
        # Logique d'export PDF
        return f"{article.slug}.pdf"
    
    def get_extension(self) -> str:
        return 'pdf'


class MarkdownExporter:
    """Export Markdown - Extension."""
    
    def export(self, article: Article) -> str:
        content = f"# {article.title}\n\n{article.content}"
        return content
    
    def get_extension(self) -> str:
        return 'md'


class WordExporter:
    """Export Word - Nouvelle extension sans modifier le code existant."""
    
    def export(self, article: Article) -> str:
        # Logique d'export Word
        return f"{article.slug}.docx"
    
    def get_extension(self) -> str:
        return 'docx'


# Service fermé à la modification, ouvert à l'extension
class ExportService:
    """
    Service d'export - fermé à la modification
    Peut exporter dans n'importe quel format sans être modifié
    """
    
    def __init__(self):
        self._exporters: dict[str, ArticleExporter] = {}
    
    def register_exporter(self, format: str, exporter: ArticleExporter):
        """Enregistre un nouvel exporteur (extension)."""
        self._exporters[format] = exporter
    
    def export_article(self, article: Article, format: str) -> str:
        """Exporte un article dans le format spécifié."""
        exporter = self._exporters.get(format)
        if not exporter:
            raise ValueError(f"Format '{format}' non supporté")
        
        return exporter.export(article)
    
    def get_supported_formats(self) -> list[str]:
        """Retourne les formats supportés."""
        return list(self._exporters.keys())


# Utilisation
service = ExportService()
service.register_exporter('pdf', PDFExporter())
service.register_exporter('md', MarkdownExporter())

# Ajout d'un nouveau format sans modifier ExportService
service.register_exporter('docx', WordExporter())

# Fonctionne avec tous les formats
content = service.export_article(article, 'pdf')
```

### 3.3 Liskov Substitution Principle (LSP)

```python
from abc import ABC, abstractmethod


# ✅ Interface commune pour tous les repositories
class ArticleRepositoryInterface(ABC):
    """
    Interface abstraite pour les repositories d'articles.
    Toute implémentation doit pouvoir substituer une autre.
    """
    
    @abstractmethod
    def get_by_id(self, article_id: int) -> Optional[Article]:
        pass
    
    @abstractmethod
    def get_by_slug(self, slug: str) -> Optional[Article]:
        pass
    
    @abstractmethod
    def save(self, article: Article) -> Article:
        pass
    
    @abstractmethod
    def list_published(self, limit: int = 10) -> List[Article]:
        pass


# Implémentation PostgreSQL
class PostgresArticleRepository(ArticleRepositoryInterface):
    """Implémentation avec PostgreSQL/Django ORM."""
    
    def get_by_id(self, article_id: int) -> Optional[Article]:
        try:
            return Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return None
    
    def get_by_slug(self, slug: str) -> Optional[Article]:
        return Article.objects.filter(slug=slug).first()
    
    def save(self, article: Article) -> Article:
        article.save()
        return article
    
    def list_published(self, limit: int = 10) -> List[Article]:
        return list(Article.objects.filter(status='published')[:limit])


# Implémentation en mémoire pour les tests
class InMemoryArticleRepository(ArticleRepositoryInterface):
    """Implémentation en mémoire - substituable à PostgreSQL."""
    
    def __init__(self):
        self._articles: dict[int, Article] = {}
        self._slug_index: dict[str, int] = {}
        self._next_id = 1
    
    def get_by_id(self, article_id: int) -> Optional[Article]:
        return self._articles.get(article_id)
    
    def get_by_slug(self, slug: str) -> Optional[Article]:
        article_id = self._slug_index.get(slug)
        return self._articles.get(article_id) if article_id else None
    
    def save(self, article: Article) -> Article:
        if not article.id:
            article.id = self._next_id
            self._next_id += 1
        
        self._articles[article.id] = article
        self._slug_index[article.slug] = article.id
        return article
    
    def list_published(self, limit: int = 10) -> List[Article]:
        published = [
            a for a in self._articles.values()
            if a.status == 'published'
        ]
        return sorted(published, key=lambda x: x.created_at, reverse=True)[:limit]


# Service qui utilise l'abstraction
class ArticleService:
    """
    Fonctionne avec n'importe quelle implémentation de ArticleRepositoryInterface.
    """
    
    def __init__(self, repository: ArticleRepositoryInterface):
        self._repository = repository
    
    def get_article(self, slug: str) -> Article:
        article = self._repository.get_by_slug(slug)
        if not article:
            raise ArticleNotFoundError(slug)
        return article
    
    def get_latest_articles(self, count: int = 5) -> List[Article]:
        return self._repository.list_published(limit=count)


# ✅ Substitution fonctionne parfaitement
# En production
service_prod = ArticleService(PostgresArticleRepository())

# En test (substitution transparente)
service_test = ArticleService(InMemoryArticleRepository())
```

### 3.4 Interface Segregation Principle (ISP)

```python
from typing import Protocol


# ✅ Petites interfaces spécialisées

class Readable(Protocol):
    """Interface pour la lecture seule."""
    
    def get_by_id(self, id: int) -> Optional[Model]:
        ...
    
    def list_all(self) -> List[Model]:
        ...


class Writable(Protocol):
    """Interface pour l'écriture."""
    
    def create(self, data: dict) -> Model:
        ...
    
    def update(self, id: int, data: dict) -> Model:
        ...
    
    def delete(self, id: int) -> None:
        ...


class Cacheable(Protocol):
    """Interface pour le caching."""
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        ...
    
    def set_cache(self, key: str, value: Any, ttl: int) -> None:
        ...
    
    def invalidate_cache(self, key: str) -> None:
        ...


# Implémentation complète
class ArticleRepository:
    """Implémente Readable + Writable + Cacheable."""
    
    def get_by_id(self, id: int) -> Optional[Article]:
        pass
    
    def list_all(self) -> List[Article]:
        pass
    
    def create(self, data: dict) -> Article:
        pass
    
    def update(self, id: int, data: dict) -> Article:
        pass
    
    def delete(self, id: int) -> None:
        pass
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        pass
    
    def set_cache(self, key: str, value: Any, ttl: int) -> None:
        pass


# Implémentation lecture seule
class ReadOnlyArticleRepository:
    """Implémente uniquement Readable."""
    
    def get_by_id(self, id: int) -> Optional[Article]:
        pass
    
    def list_all(self) -> List[Article]:
        pass


# Fonctions qui utilisent les interfaces spécialisées

def display_article_list(repository: Readable):
    """Accepte tout objet Readable, pas besoin de méthodes d'écriture."""
    articles = repository.list_all()
    for article in articles:
        print(f"- {article.title}")


def create_new_article(repository: Writable, data: dict):
    """Accepte tout objet Writable."""
    return repository.create(data)


def get_cached_data(source: Cacheable, key: str):
    """Accepte tout objet Cacheable."""
    return source.get_from_cache(key)


# Utilisation flexible
full_repo = ArticleRepository()
readonly_repo = ReadOnlyArticleRepository()

# Fonctionne avec les deux
display_article_list(full_repo)
display_article_list(readonly_repo)

# Lecture seule protégée par le type system
# create_new_article(readonly_repo, {})  # ❌ Erreur de type !
```

### 3.5 Dependency Inversion Principle (DIP)

```python
from typing import Protocol
from abc import ABC, abstractmethod


# ✅ Abstractions

class Notifier(Protocol):
    """Interface pour tous les canaux de notification."""
    
    def send(self, recipient: str, message: str) -> bool:
        ...


class PaymentGateway(Protocol):
    """Interface pour les passerelles de paiement."""
    
    def charge(self, amount: float, token: str) -> PaymentResult:
        ...


class Logger(Protocol):
    """Interface pour le logging."""
    
    def log(self, level: str, message: str) -> None:
        ...


# Implémentations concrètes

class EmailNotifier:
    """Notification par email."""
    
    def __init__(self, smtp_config: dict):
        self.smtp = smtp_config
    
    def send(self, recipient: str, message: str) -> bool:
        # Envoi email
        return True


class SMSNotifier:
    """Notification par SMS."""
    
    def __init__(self, twilio_client):
        self.twilio = twilio_client
    
    def send(self, recipient: str, message: str) -> bool:
        # Envoi SMS
        return True


class StripeGateway:
    """Passerelle de paiement Stripe."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def charge(self, amount: float, token: str) -> PaymentResult:
        # Appel API Stripe
        return PaymentResult(success=True)


class ConsoleLogger:
    """Logger vers la console."""
    
    def log(self, level: str, message: str) -> None:
        print(f"[{level.upper()}] {message}")


# Module de haut niveau qui dépend d'abstractions

class OrderService:
    """
    Service de commande - dépend d'abstractions
    Peut fonctionner avec n'importe quelle implémentation
    """
    
    def __init__(
        self,
        payment_gateway: PaymentGateway,
        notifier: Notifier,
        logger: Logger,
        order_repository: OrderRepository
    ):
        self.payment_gateway = payment_gateway
        self.notifier = notifier
        self.logger = logger
        self.order_repository = order_repository
    
    def process_order(self, order_data: dict) -> Order:
        """Traite une commande."""
        self.logger.log('info', f"Processing order for {order_data['customer_email']}")
        
        try:
            # Création de la commande
            order = self.order_repository.create(order_data)
            
            # Paiement
            payment_result = self.payment_gateway.charge(
                order.total,
                order_data['payment_token']
            )
            
            if not payment_result.success:
                order.status = 'payment_failed'
                order.save()
                raise PaymentError("Payment failed")
            
            # Succès
            order.status = 'confirmed'
            order.save()
            
            # Notification
            self.notifier.send(
                order.customer_email,
                f"Votre commande #{order.id} est confirmée"
            )
            
            self.logger.log('info', f"Order {order.id} processed successfully")
            
            return order
            
        except Exception as e:
            self.logger.log('error', f"Order processing failed: {str(e)}")
            raise


# Configuration avec injection de dépendances

def create_production_order_service():
    """Crée le service pour la production."""
    return OrderService(
        payment_gateway=StripeGateway(settings.STRIPE_API_KEY),
        notifier=EmailNotifier(settings.SMTP_CONFIG),
        logger=ConsoleLogger(),
        order_repository=PostgresOrderRepository()
    )


def create_test_order_service():
    """Crée le service pour les tests."""
    return OrderService(
        payment_gateway=MockPaymentGateway(),
        notifier=MockNotifier(),
        logger=MockLogger(),
        order_repository=InMemoryOrderRepository()
    )


# Utilisation
if settings.DEBUG:
    order_service = create_test_order_service()
else:
    order_service = create_production_order_service()
```

---

## 4. Patterns et anti-patterns

### 4.1 Anti-patterns à éviter

```python
# ❌ ANTI-PATTERN : Fat Model
class Article(models.Model):
    # ... champs ...
    
    def send_email_to_author(self):
        # Logique d'email dans le modèle
        pass
    
    def generate_pdf(self):
        # Génération PDF dans le modèle
        pass
    
    def post_to_twitter(self):
        # API externe dans le modèle
        pass
    
    def calculate_seo_score(self):
        # Logique métier complexe dans le modèle
        pass


# ❌ ANTI-PATTERN : God View
class ArticleView(View):
    def get(self, request, *args, **kwargs):
        # Validation
        # Récupération des données
        # Traitement métier
        # Envoi d'email
        # Génération de PDF
        # Rendu template
        pass


# ❌ ANTI-PATTERN : Template avec logique complexe
# Template avec trop de logique
{% for article in articles %}
    {% if article.author.is_active and article.status == 'published' %}
        {% if article.created_at|date:'Y' == '2024' %}
            {% if article.comments.count > 10 %}
                <!-- affichage -->
            {% endif %}
        {% endif %}
    {% endif %}
{% endfor %}


# ❌ ANTI-PATTERN : N+1 Queries non optimisées
def article_list(request):
    articles = Article.objects.all()
    for article in articles:
        print(article.author.username)  # Requête SQL à chaque itération !


# ❌ ANTI-PATTERN : JS inline dans les templates
<button onclick="submitForm()">Envoyer</button>
<script>
    function submitForm() {
        // Logique inline
    }
</script>
```

### 4.2 Patterns recommandés

```python
# ✅ PATTERN : Repository Pattern
class ArticleRepository:
    """Encapsule l'accès aux données."""
    
    def get_published(self):
        return Article.objects.filter(status='published')
    
    def get_by_author(self, author):
        return Article.objects.filter(author=author)


# ✅ PATTERN : Service Pattern
class ArticleService:
    """Encapsule la logique métier."""
    
    def __init__(self, repository: ArticleRepository):
        self.repository = repository
    
    def publish_article(self, article_id: int):
        article = self.repository.get_by_id(article_id)
        article.publish()
        return article


# ✅ PATTERN : Command Pattern
class PublishArticleCommand:
    """Encapsule une action avec ses paramètres."""
    
    def __init__(self, article_id: int, publisher: ArticlePublisher):
        self.article_id = article_id
        self.publisher = publisher
    
    def execute(self):
        return self.publisher.publish(self.article_id)


# ✅ PATTERN : Factory Pattern
def create_article_service() -> ArticleService:
    """Factory pour créer le service avec ses dépendances."""
    repository = ArticleRepository()
    validator = ArticleValidator()
    notifier = ArticleNotifier(EmailService())
    
    return ArticleService(repository, validator, notifier)


# ✅ PATTERN : Strategy Pattern
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, base_price: float) -> float:
        pass

class DiscountPricing(PricingStrategy):
    def calculate_price(self, base_price: float) -> float:
        return base_price * 0.9

class PremiumPricing(PricingStrategy):
    def calculate_price(self, base_price: float) -> float:
        return base_price * 1.2
```

---

## Checklist complète

### Architecture HTML/CSS/JS
- [ ] Templates avec héritage et blocs clairement définis
- [ ] Composants réutilisables extraits dans des includes
- [ ] CSS modulaire avec imports organisés
- [ ] Variables CSS pour la cohérence du design system
- [ ] JavaScript modulaire avec imports/exports ES6
- [ ] Pas de JavaScript inline dans les templates
- [ ] Séparation claire des responsabilités (SRP)

### Optimisation des requêtes
- [ ] `select_related()` pour les ForeignKey/OneToOne
- [ ] `prefetch_related()` pour ManyToMany et FK inverses
- [ ] `only()`/`defer()` pour sélectionner les champs nécessaires
- [ ] Pagination par curseur pour les grandes listes
- [ ] Caching des données fréquemment accédées
- [ ] Indexation des champs fréquemment filtrés
- [ ] Utilisation de `exists()` et `count()` au lieu de `len(all())`

### Principes SOLID
- [ ] **SRP** : Une classe = une responsabilité
- [ ] **OCP** : Extensions via polymorphisme, pas de modification
- [ ] **LSP** : Classes filles substituables aux classes parent
- [ ] **ISP** : Petites interfaces spécialisées
- [ ] **DIP** : Dépendances vers abstractions, pas d'implémentations

### Performance générale
- [ ] Debug toolbar activé en dev pour surveiller les requêtes
- [ ] Pas de N+1 queries détectées
- [ ] Temps de réponse < 200ms pour les pages principales
- [ ] Assets CSS/JS minifiés et compressés
- [ ] Images optimisées et lazy-loaded

---

## Ressources

- [Django Best Practices](https://django-best-practices.readthedocs.io/)
- [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x)
- [MDN Web Docs - JavaScript](https://developer.mozilla.org/fr/docs/Web/JavaScript)
- [CSS Architecture](https://philipwalton.com/articles/css-architecture/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
