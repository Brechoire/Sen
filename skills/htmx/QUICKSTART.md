# HTMX - Démarrage Rapide

## Installation

```html
<!-- CDN (développement) -->
<script src="https://unpkg.com/htmx.org@1.9.12"></script>

<!-- Ou npm -->
npm install htmx.org
```

## Attributs essentiels

```html
<!-- hx-get - Requête GET -->
<button hx-get="/api/data" hx-target="#result">Charger</button>

<!-- hx-post - Requête POST -->
<form hx-post="/api/submit" hx-target="#response">
  {% csrf_token %}
  <input name="data">
  <button type="submit">Envoyer</button>
</form>

<!-- hx-target - Cible de la réponse -->
<div hx-get="/data" hx-target="this">Cliquez</div>

<!-- hx-swap - Comment insérer -->
<!-- innerHTML (défaut), outerHTML, beforeend, afterend -->
<div hx-get="/data" hx-swap="innerHTML"></div>

<!-- hx-trigger - Quand déclencher -->
<input hx-get="/search" hx-trigger="keyup delay:500ms">

<!-- hx-confirm - Confirmation -->
<button hx-delete="/item/1" hx-confirm="Supprimer ?">Supprimer</button>
```

## Django + HTMX

### View

```python
from django.http import HttpResponse
from django.shortcuts import render

def item_list(request):
    items = Item.objects.all()
    
    # Si HTMX, retourner le fragment
    if request.headers.get('HX-Request'):
        return render(request, 'items/_list.html', {'items': items})
    
    # Sinon, page complète
    return render(request, 'items/list.html', {'items': items})
```

### Template

```html
<!-- Formulaire -->
<form hx-post="{% url 'item-create' %}"
      hx-target="#item-list"
      hx-swap="afterbegin">
  {% csrf_token %}
  <input name="name" required>
  <button type="submit">Ajouter</button>
</form>

<!-- Liste -->
<div id="item-list">
  {% include 'items/_list.html' %}
</div>
```

## Patterns courants

### Recherche en temps réel

```html
<input
  type="search"
  name="q"
  hx-get="{% url 'search' %}"
  hx-trigger="keyup changed delay:300ms"
  hx-target="#results"
  placeholder="Rechercher..."
>
<div id="results"></div>
```

### Suppression avec confirmation

```html
<button
  hx-delete="{% url 'item-delete' item.id %}"
  hx-confirm="Êtes-vous sûr ?"
  hx-target="closest .item-card"
  hx-swap="outerHTML swap:0.5s"
>
  Supprimer
</button>
```

### Chargement infini

```html
{% for item in items %}
  <div>{{ item.name }}</div>
{% endfor %}

{% if items.has_next %}
  <div
    hx-get="?page={{ items.next_page_number }}"
    hx-trigger="revealed"
    hx-target="this"
    hx-swap="outerHTML"
  >
    Chargement...
  </div>
{% endif %}
```

## Checklist

- [ ] CSRF token dans les formulaires
- [ ] hx-target défini
- [ ] Indicateur de chargement
- [ ] Gestion des erreurs
- [ ] Tests des endpoints

## Ressources

- [HTMX Docs](https://htmx.org/docs/)
- [HTMX Examples](https://htmx.org/examples/)
- [Django-HTMX](https://github.com/adamchainz/django-htmx)
