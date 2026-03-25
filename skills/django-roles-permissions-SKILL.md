# Django Rôles & Permissions - Bonnes Pratiques CMS

## Vue d'ensemble
Ce skill fournit les bonnes pratiques pour implémenter un système de contrôle d'accès basé sur les rôles, inspiré de WordPress, dans des projets Django, permettant des permissions granulaires pour les fonctionnalités CMS.

## Quand utiliser ce Skill
- Construire une plateforme CMS ou blog avec Django
- Implémenter des accès multi-niveaux (administrateurs, éditeurs, auteurs, contributeurs)
- Besoin de permissions granulaires pour la gestion de contenu
- Créer un workflow de publication avec processus d'approbation
- Gérer des équipes avec différentes capacités d'édition de contenu

## Concepts Fondamentaux

### Système de Permissions de Django
Django dispose d'un système de permissions intégré avec :
- **Permissions au niveau modèle** : add, change, delete, view (automatiques)
- **Permissions au niveau objet** : contrôle fin par instance
- **Groupes** : collections de permissions
- **Permissions utilisateur** : attribution directe aux utilisateurs

## Bonnes Pratiques

### 1. Définir des Rôles Clairs comme Groupes

Créer des groupes qui reflètent les rôles CMS :

```python
# core/management/commands/setup_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from articles.models import Article, Category

class Command(BaseCommand):
    help = 'Configuration des rôles et permissions CMS'

    def handle(self, *args, **kwargs):
        # Supprimer les groupes existants (optionnel, pour le développement)
        Group.objects.all().delete()
        
        # Définir les rôles
        roles = {
            'Administrateur': self.get_admin_permissions(),
            'Éditeur': self.get_editor_permissions(),
            'Auteur': self.get_author_permissions(),
            'Contributeur': self.get_contributor_permissions(),
            'Abonné': self.get_subscriber_permissions(),
        }
        
        for role_name, permissions in roles.items():
            group, created = Group.objects.get_or_create(name=role_name)
            group.permissions.set(permissions)
            self.stdout.write(
                self.style.SUCCESS(f'{"Créé" if created else "Mis à jour"} rôle : {role_name}')
            )
    
    def get_admin_permissions(self):
        """Accès complet à tout"""
        return Permission.objects.all()
    
    def get_editor_permissions(self):
        """Peut publier/modifier tout le contenu"""
        article_ct = ContentType.objects.get_for_model(Article)
        category_ct = ContentType.objects.get_for_model(Category)
        
        return Permission.objects.filter(
            content_type__in=[article_ct, category_ct]
        )
    
    def get_author_permissions(self):
        """Peut publier ses propres articles"""
        article_ct = ContentType.objects.get_for_model(Article)
        
        return Permission.objects.filter(
            content_type=article_ct,
            codename__in=['add_article', 'change_article', 'view_article']
        )
    
    def get_contributor_permissions(self):
        """Peut créer des brouillons, ne peut pas publier"""
        article_ct = ContentType.objects.get_for_model(Article)
        
        return Permission.objects.filter(
            content_type=article_ct,
            codename__in=['add_article', 'view_article']
        )
    
    def get_subscriber_permissions(self):
        """Accès en lecture seule"""
        article_ct = ContentType.objects.get_for_model(Article)
        
        return Permission.objects.filter(
            content_type=article_ct,
            codename='view_article'
        )
```

### 2. Ajouter des Permissions Personnalisées aux Modèles

Définir des permissions spécifiques dans vos modèles :

```python
# articles/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('pending', 'En attente de révision'),
        ('published', 'Publié'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        permissions = [
            ('publish_article', 'Peut publier des articles'),
            ('edit_others_article', 'Peut modifier les articles d\'autres auteurs'),
            ('delete_others_article', 'Peut supprimer les articles d\'autres auteurs'),
            ('view_all_articles', 'Peut voir tous les articles incluant les brouillons'),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
```

### 3. Implémenter les Permissions au Niveau Objet

Utiliser django-guardian pour les permissions par objet :

```bash
pip install django-guardian
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'guardian',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]
```

```python
# articles/permissions.py
from guardian.shortcuts import assign_perm, remove_perm

def assign_article_ownership(article, user):
    """Accorder à l'auteur un contrôle total sur son article"""
    assign_perm('change_article', user, article)
    assign_perm('delete_article', user, article)
    assign_perm('view_article', user, article)

def can_edit_article(user, article):
    """Vérifier si l'utilisateur peut modifier cet article spécifique"""
    # Les admins et éditeurs peuvent tout modifier
    if user.groups.filter(name__in=['Administrateur', 'Éditeur']).exists():
        return True
    
    # Les auteurs peuvent modifier leurs propres articles
    if article.author == user:
        return True
    
    # Vérifier la permission au niveau objet
    return user.has_perm('change_article', article)
```

### 4. Créer des Décorateurs et Mixins de Permission

```python
# articles/decorators.py
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from functools import wraps
from .models import Article

def role_required(*role_names):
    """Décorateur pour vérifier si l'utilisateur a le rôle requis"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Vous devez être connecté")
            
            if not request.user.groups.filter(name__in=role_names).exists():
                raise PermissionDenied(
                    f"Cette action nécessite l'un de ces rôles : {', '.join(role_names)}"
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def can_edit_article_required(view_func):
    """Décorateur pour vérifier si l'utilisateur peut modifier un article spécifique"""
    @wraps(view_func)
    def wrapper(request, article_id, *args, **kwargs):
        article = get_object_or_404(Article, id=article_id)
        
        if not can_edit_article(request.user, article):
            raise PermissionDenied("Vous n'avez pas la permission de modifier cet article")
        
        return view_func(request, article_id, *args, **kwargs)
    return wrapper
```

```python
# articles/mixins.py
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from .models import Article

class RoleRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès à des rôles spécifiques"""
    required_roles = []
    
    def test_func(self):
        return self.request.user.groups.filter(
            name__in=self.required_roles
        ).exists()
    
    def handle_no_permission(self):
        raise PermissionDenied(
            f"Cette page nécessite l'un de ces rôles : {', '.join(self.required_roles)}"
        )

class ArticleOwnerOrEditorMixin(UserPassesTestMixin):
    """Mixin pour autoriser uniquement le propriétaire de l'article ou les éditeurs"""
    
    def test_func(self):
        article = self.get_object()
        user = self.request.user
        
        # Vérifier si l'utilisateur est éditeur ou admin
        if user.groups.filter(name__in=['Administrateur', 'Éditeur']).exists():
            return True
        
        # Vérifier si l'utilisateur est l'auteur
        return article.author == user
```

### 5. Appliquer les Permissions dans les Vues

**Vues basées sur des fonctions :**

```python
# articles/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from .models import Article
from .forms import ArticleForm
from .decorators import role_required, can_edit_article_required

@login_required
@permission_required('articles.add_article', raise_exception=True)
def create_article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            
            # Assigner les permissions au niveau objet
            assign_article_ownership(article, request.user)
            
            return redirect('article_detail', article.id)
    else:
        form = ArticleForm()
    
    return render(request, 'articles/create.html', {'form': form})

@login_required
@can_edit_article_required
def edit_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            return redirect('article_detail', article.id)
    else:
        form = ArticleForm(instance=article)
    
    return render(request, 'articles/edit.html', {'form': form, 'article': article})

@login_required
@role_required('Éditeur', 'Administrateur')
@permission_required('articles.publish_article', raise_exception=True)
def publish_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    article.status = 'published'
    article.published_at = timezone.now()
    article.save()
    return redirect('article_detail', article.id)
```

**Vues basées sur des classes :**

```python
# articles/views.py
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .mixins import RoleRequiredMixin, ArticleOwnerOrEditorMixin
from .models import Article

class ArticleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Article
    fields = ['title', 'content', 'status']
    permission_required = 'articles.add_article'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        
        # Assigner les permissions au niveau objet
        assign_article_ownership(self.object, self.request.user)
        
        return response

class ArticleUpdateView(LoginRequiredMixin, ArticleOwnerOrEditorMixin, UpdateView):
    model = Article
    fields = ['title', 'content', 'status']

class ArticleDeleteView(LoginRequiredMixin, ArticleOwnerOrEditorMixin, DeleteView):
    model = Article
    success_url = '/articles/'

class ArticleListView(ListView):
    model = Article
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Montrer tous les articles aux éditeurs/admins
        if user.is_authenticated and user.groups.filter(
            name__in=['Administrateur', 'Éditeur']
        ).exists():
            return qs
        
        # Montrer uniquement les articles publiés aux autres
        if user.is_authenticated:
            return qs.filter(
                models.Q(status='published') | models.Q(author=user)
            )
        
        return qs.filter(status='published')
```

### 6. Permissions au Niveau des Templates

Contrôler ce que les utilisateurs voient dans les templates :

```django
{# articles/article_detail.html #}
{% load guardian_tags %}

<h1>{{ article.title }}</h1>
<p>par {{ article.author.username }}</p>

{# Vérifier la permission au niveau modèle #}
{% if perms.articles.change_article %}
    <a href="{% url 'edit_article' article.id %}">Modifier</a>
{% endif %}

{# Vérifier la permission au niveau objet #}
{% get_obj_perms user for article as "article_perms" %}
{% if "change_article" in article_perms %}
    <a href="{% url 'edit_article' article.id %}">Modifier cet article</a>
{% endif %}

{# Vérifier le rôle #}
{% if user.groups.all|join:", "|search:"Éditeur|Administrateur" %}
    <a href="{% url 'publish_article' article.id %}">Publier</a>
{% endif %}

{# Template tag personnalisé pour des vérifications de rôle plus propres #}
{% if user|has_role:"Éditeur,Administrateur" %}
    <a href="{% url 'admin_panel' %}">Panneau d'administration</a>
{% endif %}
```

**Template tags personnalisés :**

```python
# articles/templatetags/role_tags.py
from django import template

register = template.Library()

@register.filter(name='has_role')
def has_role(user, roles):
    """Vérifier si l'utilisateur a l'un des rôles spécifiés (séparés par des virgules)"""
    if not user.is_authenticated:
        return False
    
    role_list = [r.strip() for r in roles.split(',')]
    return user.groups.filter(name__in=role_list).exists()

@register.filter(name='has_permission')
def has_permission(user, perm):
    """Vérifier si l'utilisateur a la permission"""
    return user.has_perm(perm)
```

### 7. Configuration de l'Interface d'Administration

```python
# articles/admin.py
from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from .models import Article

@admin.register(Article)
class ArticleAdmin(GuardedModelAdmin):
    list_display = ['title', 'author', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'content']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # Les admins voient tout
        if request.user.groups.filter(name='Administrateur').exists():
            return qs
        
        # Les éditeurs voient tous les articles
        if request.user.groups.filter(name='Éditeur').exists():
            return qs
        
        # Les auteurs voient uniquement les leurs
        return qs.filter(author=request.user)
    
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        
        # Les éditeurs peuvent tout modifier
        if request.user.groups.filter(name='Éditeur').exists():
            return True
        
        # Les auteurs peuvent uniquement modifier les leurs
        return obj.author == request.user
```

### 8. Permissions API REST (Django REST Framework)

```python
# articles/permissions.py
from rest_framework import permissions

class IsAuthorOrEditor(permissions.BasePermission):
    """
    Permission au niveau objet pour permettre uniquement aux auteurs ou éditeurs de modifier
    """
    
    def has_object_permission(self, request, view, obj):
        # Les permissions de lecture sont autorisées pour toute requête
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Les éditeurs peuvent tout faire
        if request.user.groups.filter(name__in=['Administrateur', 'Éditeur']).exists():
            return True
        
        # Les auteurs peuvent uniquement modifier leurs propres articles
        return obj.author == request.user

class CanPublish(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur peut publier des articles
    """
    
    def has_permission(self, request, view):
        return request.user.has_perm('articles.publish_article')
```

```python
# articles/api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Article
from .serializers import ArticleSerializer
from ..permissions import IsAuthorOrEditor, CanPublish

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrEditor]
    
    def get_queryset(self):
        user = self.request.user
        
        # Les éditeurs voient tout
        if user.groups.filter(name__in=['Administrateur', 'Éditeur']).exists():
            return Article.objects.all()
        
        # Les autres voient les publiés + les leurs
        return Article.objects.filter(
            models.Q(status='published') | models.Q(author=user)
        )
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[CanPublish])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.status = 'published'
        article.save()
        return Response({'status': 'article publié'})
```

## Tester les Permissions

```python
# articles/tests.py
from django.test import TestCase
from django.contrib.auth.models import User, Group
from .models import Article

class ArticlePermissionsTest(TestCase):
    
    def setUp(self):
        # Créer les utilisateurs
        self.admin = User.objects.create_user('admin', password='test')
        self.editor = User.objects.create_user('editor', password='test')
        self.author = User.objects.create_user('author', password='test')
        self.contributor = User.objects.create_user('contributor', password='test')
        
        # Assigner les rôles
        admin_group = Group.objects.get(name='Administrateur')
        editor_group = Group.objects.get(name='Éditeur')
        author_group = Group.objects.get(name='Auteur')
        
        self.admin.groups.add(admin_group)
        self.editor.groups.add(editor_group)
        self.author.groups.add(author_group)
        
        # Créer des articles
        self.article = Article.objects.create(
            title='Article de test',
            content='Contenu',
            author=self.author
        )
    
    def test_author_can_edit_own_article(self):
        self.assertTrue(can_edit_article(self.author, self.article))
    
    def test_contributor_cannot_edit_others_article(self):
        self.assertFalse(can_edit_article(self.contributor, self.article))
    
    def test_editor_can_edit_any_article(self):
        self.assertTrue(can_edit_article(self.editor, self.article))
```

## Stratégie de Migration

```python
# Exécuter ceci après avoir créé votre commande
python manage.py setup_roles

# Assigner les utilisateurs aux rôles
from django.contrib.auth.models import User, Group

user = User.objects.get(username='john')
editor_group = Group.objects.get(name='Éditeur')
user.groups.add(editor_group)
```

## Modèles Courants

### Modèle 1 : Workflow avec Approbation
```python
class Article(models.Model):
    # ... champs ...
    
    def submit_for_review(self):
        """Les contributeurs soumettent pour révision"""
        if self.status == 'draft':
            self.status = 'pending'
            self.save()
    
    def approve(self, user):
        """Les éditeurs approuvent les articles"""
        if user.has_perm('articles.publish_article'):
            self.status = 'published'
            self.save()
```

### Modèle 2 : Types de Contenu Multi-niveaux
```python
# Différents ensembles de permissions pour différents types de contenu
class Page(models.Model):
    # Pages statiques - seuls les admins peuvent modifier
    class Meta:
        permissions = [
            ('manage_pages', 'Peut gérer les pages'),
        ]

class BlogPost(models.Model):
    # Articles de blog - les auteurs peuvent créer
    class Meta:
        permissions = [
            ('publish_blogpost', 'Peut publier des articles de blog'),
        ]
```

## Checklist de Sécurité

- [ ] Ne jamais faire confiance uniquement aux vérifications de permissions côté client
- [ ] Toujours valider les permissions côté serveur
- [ ] Utiliser à la fois les permissions au niveau modèle et objet quand nécessaire
- [ ] Tester minutieusement les limites de permissions
- [ ] Logger les actions liées aux permissions pour l'audit
- [ ] Utiliser les permissions intégrées de Django avant d'en créer de personnalisées
- [ ] Garder les définitions de rôles sous contrôle de version
- [ ] Documenter les exigences de permissions pour chaque vue/endpoint

## Ressources Supplémentaires

- Django Authentication : https://docs.djangoproject.com/en/stable/topics/auth/
- Django Guardian : https://django-guardian.readthedocs.io/
- DRF Permissions : https://www.django-rest-framework.org/api-guide/permissions/
