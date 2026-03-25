# Quick Start - Django Frontend Architecture

Guide rapide pour démarrer avec une architecture frontend moderne dans Django.

## Installation rapide

```bash
# Structure recommandée pour une nouvelle app
mkdir -p apps/mon_app/static/mon_app/{css/{components,layout,pages},js/{modules,pages},images}
mkdir -p apps/mon_app/templates/mon_app/{base,components,pages}

# Fichiers à créer
touch apps/mon_app/static/mon_app/css/main.css
touch apps/mon_app/static/mon_app/js/main.js
touch apps/mon_app/templates/mon_app/base/_base.html
```

## Checklist de démarrage

### 1. Structure de base

#### Template de base (`templates/base.html`)

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Mon Site{% endblock %}</title>
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/main.css' %}">
    {% block extra_css %}{% endblock %}
</head>
<body data-page="{% block page_name %}default{% endblock %}">
    
    {% include 'components/_header.html' %}
    
    <main role="main">
        {% if messages %}
            {% include 'components/_messages.html' %}
        {% endif %}
        
        {% block content %}{% endblock %}
    </main>
    
    {% include 'components/_footer.html' %}
    
    <script src="{% static 'js/main.js' %}" type="module"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

#### CSS de base (`static/css/main.css`)

```css
/* Variables */
:root {
    --color-primary: #3b82f6;
    --color-secondary: #64748b;
    --color-success: #22c55e;
    --color-error: #ef4444;
    
    --font-sans: system-ui, -apple-system, sans-serif;
    
    --space-1: 0.25rem;
    --space-2: 0.5rem;
    --space-4: 1rem;
    --space-8: 2rem;
}

/* Reset minimal */
*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

/* Base */
body {
    font-family: var(--font-sans);
    line-height: 1.5;
}

/* Layout */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: var(--space-4);
}

/* Composants */
.btn {
    display: inline-flex;
    align-items: center;
    padding: var(--space-2) var(--space-4);
    background-color: var(--color-primary);
    color: white;
    border: none;
    border-radius: 0.375rem;
    cursor: pointer;
    transition: opacity 0.15s ease;
}

.btn:hover:not(:disabled) {
    opacity: 0.9;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
```

#### JavaScript de base (`static/js/main.js`)

```javascript
// Point d'entrée principal
document.addEventListener('DOMContentLoaded', () => {
    const currentPage = document.body.dataset.page;
    
    // Initialisation globale
    initNavigation();
    initForms();
    
    // Chargement du module de page
    if (currentPage) {
        import(`./pages/${currentPage}.js`)
            .then(module => module.init?.())
            .catch(() => console.log(`No module for page: ${currentPage}`));
    }
});

// Navigation
function initNavigation() {
    // Logique de navigation
}

// Formulaires
function initForms() {
    document.querySelectorAll('form[data-ajax]').forEach(form => {
        form.addEventListener('submit', handleAjaxSubmit);
    });
}

async function handleAjaxSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const submitBtn = form.querySelector('[type="submit"]');
    
    try {
        submitBtn.disabled = true;
        
        const response = await fetch(form.action, {
            method: form.method || 'POST',
            body: new FormData(form),
            headers: {
                'X-CSRFToken': getCSRFToken(),
            },
        });
        
        if (!response.ok) throw new Error('Request failed');
        
        const data = await response.json();
        showNotification('success', data.message || 'Success!');
        
    } catch (error) {
        showNotification('error', error.message);
    } finally {
        submitBtn.disabled = false;
    }
}

function getCSRFToken() {
    return document.cookie
        .split(';')
        .find(c => c.trim().startsWith('csrftoken='))
        ?.split('=')[1] || '';
}

function showNotification(type, message) {
    // Afficher une notification toast
    console.log(`[${type.toUpperCase()}] ${message}`);
}
```

### 2. Vue optimisée (checklist)

```python
# views.py
from django.views.generic import ListView
from django.db.models import Prefetch

class OptimizedListView(ListView):
    model = Article
    template_name = 'mon_app/article_list.html'
    paginate_by = 20
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'author', 'category'  # ✅ ForeignKey
        ).prefetch_related(
            'comments', 'tags'     # ✅ ManyToMany
        ).only(
            'id', 'title', 'slug', 'created_at',  # ✅ Champs nécessaires
            'author__username',
            'category__name'
        )
```

### 3. Vérifications avant commit

```bash
# Vérifier les requêtes N+1
python manage.py shell -c "
from django.db import connection
from myapp.models import Article
connection.queries_log = []
articles = Article.objects.all()
for a in articles[:5]:
    print(a.author.username)
print(f'Requêtes: {len(connection.queries)}')
"

# Devrait afficher 2 requêtes maximum (1 pour articles + 1 pour auteurs)
# Si plus de 2, utiliser select_related() ou prefetch_related()

# Lancer les tests
pytest

# Vérifier le style
black apps/ tests/
flake8 apps/ tests/
```

## Commandes utiles

### Développement

```bash
# Lancer le serveur de développement
python manage.py runserver

# Créer une nouvelle app structurée
python manage.py startapp mon_app apps/mon_app
mkdir -p apps/mon_app/{static/mon_app/{css/{components,layout,pages},js/{modules,pages}},templates/mon_app/{base,components,pages}}

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Mode production (pour tester les assets)
DEBUG=False python manage.py runserver
```

### Optimisation

```bash
# Analyser les performances
python manage.py shell -c "
from django.db import connection
from myapp.views import MyView
view = MyView()
view.request = type('Request', (), {'GET': {}})()
connection.queries_log = []
qs = view.get_queryset()
list(qs)  # Force l'évaluation
print(f'Requêtes: {len(connection.queries)}')
for q in connection.queries[:3]:
    print(q['sql'][:100])
"
```

## Patterns SOLID - Référence rapide

### SRP (Single Responsibility)

```python
# ✅ Une classe = une responsabilité
class ArticleValidator:
    def validate(self, data): pass

class ArticleRepository:
    def save(self, article): pass

class ArticleNotifier:
    def notify(self, article): pass

# ❌ Éviter
class ArticleManager:  # Trop de responsabilités
    def validate(self): pass
    def save(self): pass
    def notify(self): pass
    def generate_pdf(self): pass
```

### OCP (Open/Closed)

```python
# ✅ Extensions via polymorphisme
class Exporter(ABC):
    @abstractmethod
    def export(self, data): pass

class PDFExporter(Exporter):
    def export(self, data): pass

class CSVExporter(Exporter):
    def export(self, data): pass

# Service fermé à la modification
class ExportService:
    def export(self, data, exporter: Exporter):
        return exporter.export(data)
```

### LSP (Liskov Substitution)

```python
# ✅ Implémentations substituables
class Repository(ABC):
    @abstractmethod
    def get(self, id): pass

class PostgresRepository(Repository):
    def get(self, id): pass

class MemoryRepository(Repository):
    def get(self, id): pass

# Fonctionne avec les deux
service = MyService(PostgresRepository())  # Production
service = MyService(MemoryRepository())     # Tests
```

### ISP (Interface Segregation)

```python
# ✅ Petites interfaces
class Readable(Protocol):
    def read(self): pass

class Writable(Protocol):
    def write(self, data): pass

# Utiliser uniquement ce qui est nécessaire
def display_data(source: Readable): pass  # Pas besoin de write
def save_data(target: Writable): pass     # Pas besoin de read
```

### DIP (Dependency Inversion)

```python
# ✅ Dépendre d'abstractions
class PaymentGateway(Protocol):
    def charge(self, amount): pass

class OrderService:
    def __init__(self, gateway: PaymentGateway):
        self.gateway = gateway

# Injecter les dépendances
service = OrderService(StripeGateway())   # Production
service = OrderService(MockGateway())     # Tests
```

## Checklist finale

### Avant chaque commit

- [ ] Templates avec héritage (`{% extends %}`)
- [ ] Pas de JavaScript inline
- [ ] CSS dans des fichiers séparés
- [ ] Requêtes optimisées (vérifier avec debug toolbar)
- [ ] Pas de N+1 queries
- [ ] Services suivent SOLID
- [ ] Tests passent (`pytest`)
- [ ] Code formaté (`black`)

### Avant mise en production

- [ ] `DEBUG = False`
- [ ] Static files collectés (`collectstatic`)
- [ ] CSS/JS minifiés
- [ ] Images optimisées
- [ ] Cache configuré
- [ ] Compression activée (WhiteNoise)

## Ressources

- [Documentation complète](./SKILL.md)
- [Django Best Practices](../django-best-practices/SKILL.md)
- [Performance Optimization](../performance-optimization/SKILL.md)
- [SOLID Principles](../solid/SKILL.md)
