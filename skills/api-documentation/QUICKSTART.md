# API Documentation - Démarrage Rapide

## Installation (2 minutes)

```bash
pip install drf-spectacular
```

## Configuration rapide

```python
# settings.py
INSTALLED_APPS += ['drf_spectacular']

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Mon API',
    'DESCRIPTION': 'Description de mon API',
    'VERSION': '1.0.0',
}
```

```python
# urls.py
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    ...
]
```

## Améliorer la documentation

```python
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    @extend_schema(
        summary="Liste des articles",
        description="Récupère tous les articles",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

## Commandes utiles

```bash
# Générer le schéma
python manage.py spectacular --file schema.yml

# Voir le schéma
python manage.py spectacular --color
```

## Checklist rapide

- [ ] DRF Spectacular installé
- [ ] DEFAULT_SCHEMA_CLASS configuré
- [ ] URLs ajoutées
- [ ] Swagger UI accessible à /api/docs/
- [ ] Schéma JSON à /api/schema/
