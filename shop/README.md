# Système de Boutique - Éditions Sen

Ce module gère la boutique en ligne des Éditions Sen, permettant la vente de livres avec un système CRUD complet.

## Fonctionnalités

### Modèles

- **Book** : Modèle principal pour les livres
  - Informations de base (titre, auteur, description)
  - Prix et promotions
  - Images (couverture, quatrième de couverture)
  - Métadonnées SEO
  - Gestion du stock

- **Category** : Catégories de livres
  - Organisation des livres par genre
  - Descriptions et slugs SEO

- **BookImage** : Images supplémentaires des livres
  - Galerie d'images
  - Gestion de l'ordre d'affichage

- **Review** : Avis clients
  - Système de notation (1-5 étoiles)
  - Modération des avis
  - Association utilisateur-livre

### Vues

#### Vues publiques
- `shop_home` : Page d'accueil de la boutique
- `BookListView` : Liste des livres avec filtres et recherche
- `BookDetailView` : Détail d'un livre
- `CategoryDetailView` : Livres d'une catégorie
- `add_review` : Ajout d'un avis

#### Vues d'administration (authentifiées)
- `BookCreateView` / `BookUpdateView` / `BookDeleteView`
- `CategoryCreateView` / `CategoryUpdateView` / `CategoryDeleteView`

#### Vues AJAX
- `get_books_ajax` : API pour l'autocomplétion
- `book_search_suggestions` : Suggestions de recherche

### Fonctionnalités avancées

#### Recherche et filtres
- Recherche textuelle (titre, auteur, description)
- Filtres par catégorie, auteur, prix, format
- Tri par différents critères
- Pagination

#### SEO et accessibilité
- Métadonnées personnalisables
- URLs SEO-friendly
- Structure sémantique HTML
- Images avec texte alternatif
- Navigation au clavier

#### Design responsive
- Mobile-first
- Grilles adaptatives
- Images optimisées
- Interface utilisateur intuitive

## Installation

1. Ajouter `shop` aux `INSTALLED_APPS` dans `settings.py`
2. Inclure les URLs dans `app/urls.py`
3. Créer et appliquer les migrations :
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## Données de test

Créer des données de démonstration :
```bash
python manage.py create_sample_books
```

## Utilisation

### Gestion des livres

1. **Créer un livre** : `/boutique/admin/livre/ajouter/`
2. **Modifier un livre** : `/boutique/admin/livre/<slug>/modifier/`
3. **Supprimer un livre** : `/boutique/admin/livre/<slug>/supprimer/`

### Gestion des catégories

1. **Créer une catégorie** : `/boutique/admin/categorie/ajouter/`
2. **Modifier une catégorie** : `/boutique/admin/categorie/<slug>/modifier/`
3. **Supprimer une catégorie** : `/boutique/admin/categorie/<slug>/supprimer/`

### Interface publique

1. **Page d'accueil** : `/boutique/`
2. **Liste des livres** : `/boutique/livres/`
3. **Détail d'un livre** : `/boutique/livre/<slug>/`
4. **Catégorie** : `/boutique/categorie/<slug>/`

## Personnalisation

### Styles
Les templates utilisent Tailwind CSS avec les couleurs définies dans `base.html` :
- Primary : `#2A5C4A`
- Secondary : `#45A88B`
- Accent : `#781C3B`

### Formulaires
Les formulaires sont personnalisables dans `forms.py` avec validation avancée.

### Admin
Interface d'administration optimisée dans `admin.py` avec :
- Aperçus des images
- Filtres avancés
- Recherche
- Inlines pour les relations

## Sécurité

- Protection CSRF sur tous les formulaires
- Validation des données côté serveur
- Authentification requise pour l'administration
- Sanitisation des entrées utilisateur

## Performance

- Requêtes optimisées avec `select_related` et `prefetch_related`
- Pagination pour les grandes listes
- Index de base de données pour les recherches fréquentes
- Images optimisées et lazy loading

## Tests

Pour tester le système :
1. Créer des données de test
2. Tester les vues publiques
3. Tester l'administration
4. Vérifier la responsivité
5. Tester l'accessibilité
