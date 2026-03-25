# Django Best Practices - Démarrage Rapide

## Installation rapide

```bash
# 1. Installer les dépendances
pip install -r requirements/local.txt

# 2. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# 3. Appliquer les migrations
python manage.py migrate

# 4. Créer un superutilisateur
python manage.py createsuperuser

# 5. Lancer le serveur de développement
python manage.py runserver
```

## Checklist quotidienne

### Avant de coder

- [ ] Lire le skill `django-best-practices/SKILL.md` pour la tâche
- [ ] Vérifier que l'environnement est activé
- [ ] Créer une branche git pour la fonctionnalité

### Pendant le développement

```bash
# Créer une nouvelle app
python manage.py startapp ma_app apps/ma_app
mkdir -p apps/ma_app/{migrations,templates/ma_app,static/ma_app/{css,js}}

# Créer un modèle
# Éditer apps/ma_app/models.py
python manage.py makemigrations
python manage.py migrate

# Créer les vues
# Éditer apps/ma_app/views.py

# Créer les templates
# Éditer apps/ma_app/templates/ma_app/*.html

# Créer les URLs
# Éditer apps/ma_app/urls.py
```

### Avant de committer

```bash
# 1. Vérifier les migrations
python manage.py makemigrations --check

# 2. Vérifier les erreurs Django
python manage.py check

# 3. Lancer les tests
pytest

# 4. Vérifier la couverture
pytest --cov=apps --cov-report=term-missing

# 5. Vérifier la sécurité
bandit -r apps/
detect-secrets scan --baseline .secrets.baseline

# 6. Vérifier le linting
ruff check apps/
black --check apps/
```

## Commandes essentielles

### Gestion des modèles

```bash
# Créer les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Voir le SQL d'une migration
python manage.py sqlmigrate mon_app 0001

# Réinitialiser les migrations (attention)
python manage.py migrate mon_app zero
rm apps/mon_app/migrations/000*.py
python manage.py makemigrations
python manage.py migrate
```

### Tests

```bash
# Tous les tests
pytest

# Tests avec couverture
pytest --cov=apps --cov-report=html

# Tests spécifiques
pytest apps/blog/tests/test_models.py::TestPostModel::test_post_creation

# Tests rapides uniquement
pytest -m "not slow"

# Mode verbeux
pytest -v

# Arrêter au premier échec
pytest -x

# Réexécuter les tests échoués
pytest --lf
```

### Shell et debug

```bash
# Shell Django avec auto-import
python manage.py shell_plus --print-sql

# Lancer avec le debug toolbar
python manage.py runserver

# Vérifier les erreurs de déploiement
python manage.py check --deploy
```

### Static et media files

```bash
# Collecter les static files
python manage.py collectstatic --noinput

# Effacer les fichiers compilés
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

## Structure de fichier type

### Modèle

```python
# apps/mon_app/models.py
from django.db import models


class MonModele(models.Model):
    """Description du modèle."""
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
    ]
    
    nom = models.CharField(max_length=100, verbose_name="Nom")
    slug = models.SlugField(unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Mon Modèle"
        verbose_name_plural = "Mes Modèles"
    
    def __str__(self):
        return self.nom
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('mon_app:detail', kwargs={'slug': self.slug})
```

### Vue (Class-Based)

```python
# apps/mon_app/views.py
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import MonModele


class ModeleListView(ListView):
    """Liste des objets."""
    model = MonModele
    template_name = 'mon_app/modele_list.html'
    context_object_name = 'objets'
    paginate_by = 10
    queryset = MonModele.objects.filter(status='active')


class ModeleDetailView(DetailView):
    """Détail d'un objet."""
    model = MonModele
    template_name = 'mon_app/modele_detail.html'
    slug_url_kwarg = 'slug'


class ModeleCreateView(LoginRequiredMixin, CreateView):
    """Création d'un objet."""
    model = MonModele
    fields = ['nom', 'status']
    template_name = 'mon_app/modele_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, "Objet créé avec succès !")
        return super().form_valid(form)
```

### URL

```python
# apps/mon_app/urls.py
from django.urls import path
from . import views

app_name = 'mon_app'

urlpatterns = [
    path('', views.ModeleListView.as_view(), name='list'),
    path('<slug:slug>/', views.ModeleDetailView.as_view(), name='detail'),
    path('create/', views.ModeleCreateView.as_view(), name='create'),
]
```

### Template

```html
<!-- templates/mon_app/modele_list.html -->
{% extends 'base.html' %}

{% block title %}Liste - {{ block.super }}{% endblock %}

{% block content %}
<h1>Liste des objets</h1>

{% if objets %}
    <ul>
        {% for objet in objets %}
            <li><a href="{{ objet.get_absolute_url }}">{{ objet.nom }}</a></li>
        {% endfor %}
    </ul>
    
    {% include 'includes/pagination.html' with page_obj=page_obj %}
{% else %}
    <p>Aucun objet trouvé.</p>
{% endif %}

<a href="{% url 'mon_app:create' %}">Créer un objet</a>
{% endblock %}
```

### Test

```python
# apps/mon_app/tests/test_models.py
import pytest
from apps.mon_app.models import MonModele


@pytest.mark.django_db
class TestMonModele:
    """Tests du modèle MonModele."""
    
    def test_creation(self):
        """Test la création d'un objet."""
        obj = MonModele.objects.create(nom='Test', slug='test')
        assert obj.nom == 'Test'
        assert obj.slug == 'test'
    
    def test_get_absolute_url(self):
        """Test l'URL absolue."""
        obj = MonModele.objects.create(nom='Test', slug='test')
        assert obj.get_absolute_url() == '/mon-app/test/'
```

## Configuration pyproject.toml minimale

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.local"
python_files = ["tests.py", "test_*.py", "*_tests.py"]

[tool.coverage.run]
source = ["apps"]
omit = ["*/migrations/*", "*/tests/*"]

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
target-version = "py311"
line-length = 88
select = ["E", "W", "F", "I", "N", "UP", "B"]
```

## Variables d'environnement (.env)

```bash
# Django
DJANGO_SECRET_KEY=votre-cle-super-secrete-ici
DJANGO_SETTINGS_MODULE=config.settings.local
DJANGO_DEBUG=True

# Database
DB_NAME=mon_projet
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Email (dev)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## Anti-patterns à éviter

### Modèles

```python
# ❌ Mauvais : pas de related_name
author = models.ForeignKey(User, on_delete=models.CASCADE)

# ✅ Bon
author = models.ForeignKey(
    User, 
    on_delete=models.CASCADE,
    related_name='posts'
)
```

### Vues

```python
# ❌ Mauvais : pas de protection
class CreateView(CreateView):
    pass

# ✅ Bon
class CreateView(LoginRequiredMixin, CreateView):
    pass
```

### Templates

```html
<!-- ❌ Mauvais : pas de csrf_token -->
<form method="post">
    <input type="text" name="nom">
</form>

<!-- ✅ Bon -->
<form method="post">
    {% csrf_token %}
    <input type="text" name="nom">
</form>
```

## Ressources rapides

- **Documentation Django** : https://docs.djangoproject.com/
- **Django Packages** : https://djangopackages.org/
- **Django Debug Toolbar** : http://localhost:8000/__debug__/
- **Admin** : http://localhost:8000/admin/

## Support

Voir le fichier `SKILL.md` complet pour :
- Architecture détaillée
- Bonnes pratiques par composant
- Sécurité avancée
- Optimisation des performances
- Configuration complète
