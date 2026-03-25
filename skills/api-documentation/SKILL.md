# Skill : API Documentation

## Objectif

Générer et maintenir une documentation API automatique, interactive et à jour pour les APIs Django REST Framework.

## Quand utiliser ce skill

- API REST publique ou interne
- Équipe de développement multiple
- Intégration avec des clients externes
- Tests et exploration de l'API

## Solutions recommandées

### 1. DRF Spectacular (OpenAPI 3)

```bash
pip install drf-spectacular
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    'drf_spectacular',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Mon API',
    'DESCRIPTION': 'Documentation de l\'API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}
```

```python
# urls.py
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # API schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Redoc
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ...
]
```

### 2. Documentation enrichie avec decorators

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework import viewsets

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    @extend_schema(
        summary="Liste des articles",
        description="Récupère la liste de tous les articles publiés",
        parameters=[
            OpenApiParameter(
                name='search',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Recherche dans le titre',
            ),
            OpenApiParameter(
                name='category',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Filtrer par catégorie',
            ),
        ],
        responses={
            200: ArticleSerializer(many=True),
            401: OpenApiResponse(description='Non authentifié'),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Créer un article",
        description="Crée un nouvel article (admin uniquement)",
        request=ArticleCreateSerializer,
        responses={
            201: ArticleSerializer,
            400: OpenApiResponse(description='Données invalides'),
            403: OpenApiResponse(description='Non autorisé'),
        },
        examples=[
            OpenApiExample(
                'Exemple valide',
                value={
                    'title': 'Mon article',
                    'content': 'Contenu de l\'article...',
                    'category': 'tech',
                },
                request_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
```

### 3. Sérializers documentés

```python
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

class ArticleSerializer(serializers.ModelSerializer):
    """Sérializer pour les articles."""
    
    author_name = serializers.CharField(
        source='author.username',
        read_only=True,
        help_text="Nom de l'auteur"
    )
    
    status_display = serializers.SerializerMethodField(
        help_text="Statut lisible"
    )
    
    @extend_schema_field(serializers.CharField())
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'content',
            'author_name',
            'status',
            'status_display',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'author_name']
```

## Configuration avancée

### Types personnalisés

```python
# schema.py
from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.plumbing import build_basics

def get_schema():
    return {
        'ArticleStatus': {
            'type': 'string',
            'enum': ['draft', 'published', 'archived'],
            'description': 'Statut de publication',
        }
    }

# Dans settings.py
SPECTACULAR_SETTINGS = {
    'ENUM_NAME_OVERRIDES': {
        'ArticleStatusEnum': 'myapp.models.ArticleStatus',
    },
    'POSTPROCESSING_HOOKS': [
        'myapp.schema.custom_postprocessing',
    ],
}
```

### Authentification dans la doc

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SPECTACULAR_SETTINGS = {
    'SECURITY': [
        {
            'Bearer': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        },
        {
            'Session': {
                'type': 'apiKey',
                'in': 'cookie',
                'name': 'sessionid',
            }
        },
    ],
}
```

## Documentation alternative : CoreAPI

```bash
pip install coreapi coreapi-cli
```

```python
# urls.py
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    path('api/docs/', include_docs_urls(title='API Documentation')),
    ...
]
```

## Tests de l'API

```python
# tests/test_api_schema.py
from django.test import TestCase
from django.urls import reverse

class APISchemaTests(TestCase):
    def test_schema_generation(self):
        """Vérifier que le schéma se génère sans erreur."""
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.oai.openapi+json;version=3.0.3')
    
    def test_swagger_ui_accessible(self):
        """Vérifier que Swagger UI est accessible."""
        response = self.client.get('/api/docs/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'swagger')
```

## CI/CD - Validation du schéma

```yaml
# .github/workflows/api-docs.yml
name: API Documentation

on: [push, pull_request]

jobs:
  validate-schema:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Generate schema
        run: |
          python manage.py spectacular --color --file schema.yml
      
      - name: Validate schema
        run: |
          pip install openapi-spec-validator
          openapi-spec-validator schema.yml
      
      - name: Check for breaking changes
        if: github.event_name == 'pull_request'
        run: |
          # Comparer avec le schéma de main
          git show main:schema.yml > schema-main.yml || true
          # Utiliser outil de comparaison si nécessaire
```

## Checklist Documentation API

- [ ] DRF Spectacular installé et configuré
- [ ] Endpoints documentés avec @extend_schema
- [ ] Sérializers avec help_text
- [ ] Exemples de requêtes/réponses
- [ ] Authentification documentée
- [ ] Swagger UI accessible
- [ ] Tests de génération du schéma
- [ ] CI/CD validation du schéma

## Ressources

- [DRF Spectacular](https://drf-spectacular.readthedocs.io/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [Redoc](https://github.com/Redocly/redoc)
