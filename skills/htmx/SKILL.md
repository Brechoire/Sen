# Skill : HTMX

## Objectif

Ce skill présente les bonnes pratiques pour utiliser HTMX avec Django pour créer des interfaces utilisateur dynamiques sans JavaScript complexe.

## Quand utiliser ce skill

- Création d'interfaces interactives
- Remplacement de pages entières par des mises à jour partielles
- Formulaires avec validation en temps réel
- Chargement dynamique de contenu
- Recherche et filtres instantanés

## Qu'est-ce que HTMX ?

HTMX permet d'accéder à AJAX, CSS Transitions, WebSockets et Server-Sent Events directement depuis le HTML, via des attributs.

### Concepts clés

```html
<!-- hx-get : Effectue une requête GET -->
<button hx-get="/api/data" hx-target="#result">
  Charger des données
</button>
<div id="result"></div>

<!-- hx-post : Effectue une requête POST -->
<form hx-post="/api/submit" hx-target="#response">
  {% csrf_token %}
  <input type="text" name="data">
  <button type="submit">Envoyer</button>
</form>
<div id="response"></div>
```

## Installation

### 1. Via CDN (développement)

```html
<!-- base.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
    <script src="https://unpkg.com/htmx.org@1.9.12"></script>
    <!-- Extensions utiles -->
    <script src="https://unpkg.com/htmx.org/dist/ext/loading-states.js"></script>
</head>
<body hx-ext="loading-states">
    {% block content %}{% endblock %}
</body>
</html>
```

### 2. Via npm (production)

```bash
npm install htmx.org
```

```javascript
// main.js
import 'htmx.org';
window.htmx = require('htmx.org');
```

## Attributs principaux

### hx-get, hx-post, hx-put, hx-patch, hx-delete

```html
<!-- Charger du contenu -->
<button hx-get="{% url 'load-more' %}" hx-target="#items">
    Charger plus
</button>

<!-- Soumettre un formulaire -->
<form hx-post="{% url 'create-item' %}" hx-swap="outerHTML">
    {% csrf_token %}
    <input type="text" name="name" required>
    <button type="submit">Créer</button>
</form>

<!-- Supprimer avec confirmation -->
<button 
    hx-delete="{% url 'delete-item' item.id %}"
    hx-confirm="Êtes-vous sûr ?"
    hx-target="closest .item-card"
    hx-swap="outerHTML swap:1s"
>
    Supprimer
</button>
```

### hx-target

```html
<!-- Cibler un élément spécifique par ID -->
<button hx-get="/data" hx-target="#result">Charger</button>
<div id="result"></div>

<!-- Cibler l'élément lui-même (défaut) -->
<div hx-get="/data">Cliquez pour charger</div>

<!-- Cibler l'élément parent -->
<div class="card">
    <button hx-delete="/item/1" hx-target="closest .card">
        Supprimer cette carte
    </button>
</div>

<!-- Cibler l'élément précédent/suivant -->
<button hx-get="/data" hx-target="previous .content">Charger</button>
<div class="content"></div>
```

### hx-swap

```html
<!-- innerHTML (défaut) - remplace le contenu intérieur -->
<div hx-get="/data" hx-swap="innerHTML">
    Contenu actuel sera remplacé
</div>

<!-- outerHTML - remplace l'élément entier -->
<button hx-post="/submit" hx-swap="outerHTML">
    Ce bouton sera remplacé par la réponse
</button>

<!-- beforebegin / afterbegin / beforeend / afterend -->
<!-- Insère avant/après l'élément ou au début/à la fin du contenu -->
<div id="list" hx-swap="beforeend">
    <!-- Les nouveaux éléments seront ajoutés à la fin -->
</div>

<!-- Transition animée -->
<div hx-delete="/item/1" hx-swap="outerHTML swap:1s">
    Élément avec animation de sortie de 1 seconde
</div>
```

### hx-trigger

```html
<!-- Déclencheurs courants -->

<!-- Au clic (défaut pour les boutons) -->
<button hx-get="/data" hx-trigger="click">Cliquez</button>

<!-- Au changement (input, select) -->
<select hx-get="/filter" hx-trigger="change" hx-target="#results">
    <option>Option 1</option>
    <option>Option 2</option>
</select>

<!-- Au chargement de la page -->
<div hx-get="/load" hx-trigger="load">Chargement...</div>

<!-- Recherche en temps réel avec debounce -->
<input 
    type="search"
    name="q"
    hx-get="{% url 'search' %}"
    hx-trigger="keyup changed delay:500ms"
    hx-target="#search-results"
    placeholder="Rechercher..."
>

<!-- Intersection Observer (lazy loading) -->
<div 
    hx-get="{% url 'load-more' %}"
    hx-trigger="revealed"
    hx-swap="afterend"
>
    Chargement...
</div>

<!-- Polling (rafraîchissement automatique) -->
<div hx-get="/status" hx-trigger="every 5s">
    Statut mis à jour toutes les 5 secondes
</div>

<!-- Conditionnel -->
<input 
    hx-get="/validate"
    hx-trigger="blur, keyup[key=='Enter']"
>
```

### hx-indicator

```html
<!-- Affiche un indicateur de chargement -->
<button hx-get="/data" hx-indicator="#spinner">
    Charger
    <span id="spinner" class="htmx-indicator">
        🔄
    </span>
</button>

<!-- Styles pour l'indicateur -->
<style>
.htmx-indicator {
    display: none;
}
.htmx-request .htmx-indicator {
    display: inline;
}
.htmx-request.htmx-indicator {
    display: inline;
}
</style>

<!-- Indicateur global -->
<div class="htmx-indicator fixed top-0 left-0 right-0 h-1 bg-blue-500">
    <div class="h-full bg-blue-700 animate-pulse"></div>
</div>
```

### hx-vals et hx-headers

```html
<!-- Valeurs supplémentaires -->
<button 
    hx-post="/action"
    hx-vals='{"action": "delete", "confirmed": true}'
>
    Action spéciale
</button>

<!-- En-têtes personnalisés -->
<button 
    hx-get="/api/data"
    hx-headers='{"X-Custom-Header": "value"}'
>
    Charger avec headers
</button>

<!-- Valeurs dynamiques avec JavaScript -->
<button 
    hx-post="/vote"
    hx-vals="js:{score: calculateScore()}"
>
    Voter
</button>
```

## Intégration Django

### Views Django

```python
# views.py
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Item


def item_list(request):
    """Vue pour la liste des items (HTMX ou normale)."""
    items = Item.objects.all()
    
    # Si requête HTMX, retourner uniquement le fragment
    if request.headers.get('HX-Request'):
        return render(request, 'items/_item_list.html', {'items': items})
    
    # Sinon, retourner la page complète
    return render(request, 'items/item_list.html', {'items': items})


@require_http_methods(['POST'])
@login_required
def item_create(request):
    """Création d'un item via HTMX."""
    name = request.POST.get('name', '').strip()
    
    if not name:
        return HttpResponse(
            '<span class="text-red-600">Le nom est requis</span>',
            status=400
        )
    
    item = Item.objects.create(name=name, user=request.user)
    
    # Retourner le nouvel item pour l'ajouter à la liste
    return render(request, 'items/_item_row.html', {'item': item})


@require_http_methods(['DELETE'])
@login_required
def item_delete(request, pk):
    """Suppression d'un item."""
    item = get_object_or_404(Item, pk=pk, user=request.user)
    item.delete()
    
    # Retourner une réponse vide (l'élément sera supprimé côté client)
    return HttpResponse('')


@require_http_methods(['GET'])
def item_search(request):
    """Recherche d'items avec HTMX."""
    query = request.GET.get('q', '')
    items = Item.objects.filter(name__icontains=query)[:10]
    
    return render(request, 'items/_search_results.html', {
        'items': items,
        'query': query
    })


def item_edit_form(request, pk):
    """Retourne le formulaire d'édition inline."""
    item = get_object_or_404(Item, pk=pk)
    return render(request, 'items/_edit_form.html', {'item': item})


@require_http_methods(['POST'])
@login_required
def item_update(request, pk):
    """Mise à jour d'un item."""
    item = get_object_or_404(Item, pk=pk, user=request.user)
    item.name = request.POST.get('name', '').strip()
    item.save()
    
    return render(request, 'items/_item_row.html', {'item': item})


@require_http_methods(['POST'])
@login_required
def item_toggle(request, pk):
    """Bascule le statut d'un item."""
    item = get_object_or_404(Item, pk=pk, user=request.user)
    item.completed = not item.completed
    item.save()
    
    return render(request, 'items/_item_row.html', {'item': item})
```

### URLs

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.item_list, name='item-list'),
    path('create/', views.item_create, name='item-create'),
    path('search/', views.item_search, name='item-search'),
    path('<int:pk>/delete/', views.item_delete, name='item-delete'),
    path('<int:pk>/edit/', views.item_edit_form, name='item-edit-form'),
    path('<int:pk>/update/', views.item_update, name='item-update'),
    path('<int:pk>/toggle/', views.item_toggle, name='item-toggle'),
]
```

### Templates

```html
<!-- items/item_list.html (page complète) -->
{% extends 'base.html' %}

{% block content %}
<div class="max-w-4xl mx-auto p-6">
    <h1 class="text-3xl font-bold mb-6">Ma Liste</h1>
    
    <!-- Formulaire de création -->
    <form 
        hx-post="{% url 'item-create' %}"
        hx-target="#item-list"
        hx-swap="afterbegin"
        class="mb-6 flex gap-2"
    >
        {% csrf_token %}
        <input 
            type="text"
            name="name"
            placeholder="Nouvel item..."
            required
            class="flex-1 px-4 py-2 border rounded"
        >
        <button type="submit" class="px-4 py-2 bg-blue-500 text-white rounded">
            Ajouter
        </button>
    </form>
    
    <!-- Barre de recherche -->
    <input
        type="search"
        name="q"
        hx-get="{% url 'item-search' %}"
        hx-trigger="keyup changed delay:300ms"
        hx-target="#item-list"
        placeholder="Rechercher..."
        class="w-full px-4 py-2 border rounded mb-4"
    >
    
    <!-- Liste des items -->
    <div id="item-list">
        {% include 'items/_item_list.html' %}
    </div>
</div>
{% endblock %}
```

```html
<!-- items/_item_list.html (partiel HTMX) -->
{% for item in items %}
    {% include 'items/_item_row.html' %}
{% empty %}
    <p class="text-gray-500 text-center py-8">Aucun item trouvé.</p>
{% endfor %}
```

```html
<!-- items/_item_row.html (ligne d'item) -->
<div class="item-row flex items-center justify-between p-4 bg-white border rounded mb-2">
    <div class="flex items-center gap-3">
        <input
            type="checkbox"
            {% if item.completed %}checked{% endif %}
            hx-post="{% url 'item-toggle' item.id %}"
            hx-target="closest .item-row"
            hx-swap="outerHTML"
        >
        
        <span class="{% if item.completed %}line-through text-gray-400{% endif %}">
            {{ item.name }}
        </span>
    </div>
    
    <div class="flex gap-2">
        <button
            hx-get="{% url 'item-edit-form' item.id %}"
            hx-target="closest .item-row"
            hx-swap="outerHTML"
            class="text-blue-500 hover:text-blue-700"
        >
            Modifier
        </button>
        
        <button
            hx-delete="{% url 'item-delete' item.id %}"
            hx-confirm="Supprimer cet item ?"
            hx-target="closest .item-row"
            hx-swap="outerHTML swap:0.5s"
            class="text-red-500 hover:text-red-700"
        >
            Supprimer
        </button>
    </div>
</div>
```

```html
<!-- items/_edit_form.html (formulaire d'édition inline) -->
<form
    hx-post="{% url 'item-update' item.id %}"
    hx-target="this"
    hx-swap="outerHTML"
    class="item-row flex items-center gap-2 p-4 bg-white border rounded mb-2"
>
    {% csrf_token %}
    
    <input
        type="text"
        name="name"
        value="{{ item.name }}"
        required
        class="flex-1 px-2 py-1 border rounded"
    >
    
    <button type="submit" class="text-green-500">✓</button>
    
    <button
        type="button"
        hx-get="{% url 'item-list' %}"
        hx-target="#item-list"
        class="text-gray-500"
    >
        ✕
    </button>
</form>
```

```html
<!-- items/_search_results.html (résultats de recherche) -->
{% if query %}
    <p class="text-sm text-gray-600 mb-2">
        {{ items|length }} résultat(s) pour "{{ query }}"
    </p>
{% endif %}

{% for item in items %}
    {% include 'items/_item_row.html' %}
{% empty %}
    <p class="text-gray-500 text-center py-4">Aucun résultat.</p>
{% endfor %}
```

## Patterns courants

### Infinite Scroll

```html
<!-- Liste avec scroll infini -->
<div id="items-container">
    {% include 'items/_items_page.html' %}
</div>

<!-- _items_page.html -->
{% for item in items %}
    {% include 'items/_item_card.html' %}
{% endfor %}

{% if items.has_next %}
    <div
        hx-get="{% url 'item-list' %}?page={{ items.next_page_number }}"
        hx-trigger="revealed"
        hx-target="this"
        hx-swap="outerHTML"
        class="text-center py-4"
    >
        Chargement...
    </div>
{% endif %}
```

### Toasts/Notifications

```html
<!-- Toast container (dans base.html) -->
<div id="toast-container" class="fixed top-4 right-4 z-50"></div>

<!-- Dans la vue Django, retourner un toast -->
HttpResponse(
    '<div class="toast bg-green-500 text-white p-4 rounded shadow-lg" '
    'hx-trigger="load delay:3s" hx-get="/empty" hx-swap="delete">'
    '<span>✓ Opération réussie</span>'
    '</div>'
)
```

### Modals

```html
<!-- Bouton pour ouvrir le modal -->
<button
    hx-get="{% url 'item-create-form' %}"
    hx-target="#modal-content"
    onclick="document.getElementById('modal').classList.remove('hidden')"
>
    Nouvel Item
</button>

<!-- Modal -->
<div id="modal" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
    <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div id="modal-content">
            <!-- Contenu chargé dynamiquement -->
        </div>
        
        <button
            onclick="document.getElementById('modal').classList.add('hidden')"
            class="mt-4 w-full px-4 py-2 bg-gray-200 rounded"
        >
            Fermer
        </button>
    </div>
</div>
```

### Tabs dynamiques

```html
<div class="tabs">
    <button
        hx-get="{% url 'tab-content' 'active' %}"
        hx-target="#tab-content"
        class="tab active"
    >
        Actifs
    </button>
    
    <button
        hx-get="{% url 'tab-content' 'completed' %}"
        hx-target="#tab-content"
        class="tab"
    >
        Complétés
    </button>
</div>

<div id="tab-content">
    {% include 'items/_tab_active.html' %}
</div>
```

### Bulk Actions

```html
<form id="bulk-form">
    {% csrf_token %}
    
    <div class="mb-4 flex gap-2">
        <button
            type="button"
            hx-post="{% url 'bulk-complete' %}"
            hx-target="#item-list"
            hx-include="[name='selected_items']"
        >
            Marquer comme complété
        </button>
        
        <button
            type="button"
            hx-post="{% url 'bulk-delete' %}"
            hx-target="#item-list"
            hx-confirm="Supprimer les éléments sélectionnés ?"
            hx-include="[name='selected_items']"
        >
            Supprimer
        </button>
    </div>
    
    <div id="item-list">
        {% for item in items %}
            <div class="flex items-center gap-2 p-2">
                <input type="checkbox" name="selected_items" value="{{ item.id }}">
                <span>{{ item.name }}</span>
            </div>
        {% endfor %}
    </div>
</form>
```

## Extensions utiles

### Loading States

```html
<!-- Extension loading-states -->
<body hx-ext="loading-states">
    <!-- Bouton avec état de chargement -->
    <button
        hx-get="/data"
        data-loading-disable
        data-loading-text="Chargement..."
    >
        Charger
    </button>
    
    <!-- Élément qui s'affiche pendant le chargement -->
    <div data-loading-class="opacity-50">
        Contenu à griser pendant le chargement
    </div>
</body>
```

### View Transitions

```html
<!-- Transition entre pages -->
<div hx-boost="true" hx-target="#content">
    <a href="/page1">Page 1</a>
    <a href="/page2">Page 2</a>
</div>

<div id="content">
    {&percnt; block content &percnt;}{&percnt; endblock &percnt;}
</div>
```

## Checklist

### Performance
- [ ] Utiliser `hx-trigger` avec debounce pour les recherches
- [ ] Retourner uniquement le HTML nécessaire
- [ ] Utiliser `select_related` et `prefetch_related`
- [ ] Mettre en cache les réponses si approprié

### UX
- [ ] Indicateurs de chargement (`hx-indicator`)
- [ ] Messages de confirmation (`hx-confirm`)
- [ ] Feedback visuel (toasts, animations)
- [ ] Gestion des erreurs

### Sécurité
- [ ] CSRF tokens dans tous les formulaires
- [ ] Vérification des permissions côté serveur
- [ ] Validation des données
- [ ] Rate limiting si nécessaire

### Accessibilité
- [ ] Attributs ARIA appropriés
- [ ] Navigation au clavier
- [ ] Messages d'erreur clairs
- [ ] Focus management

## Ressources

- [Documentation HTMX](https://htmx.org/docs/)
- [HTMX Examples](https://htmx.org/examples/)
- [Django-HTMX](https://github.com/adamchainz/django-htmx) - Utilitaires Django
- [HTMX + Django Tutorial](https://htmx.org/essays/django/)
