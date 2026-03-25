# Skill : Django REST Framework (DRF)

## Objectif

Ce skill présente les bonnes pratiques pour créer des API REST robustes, sécurisées et maintenables avec Django REST Framework.

## Quand utiliser ce skill

- Création d'une nouvelle API
- Refactoring d'une API existante
- Ajout d'authentification et permissions
- Optimisation des performances API

## Architecture recommandée

### Structure du projet

```
apps/
├── api/                           # App API principale
│   ├── __init__.py
│   ├── urls.py                    # URLs racine de l'API
│   ├── pagination.py              # Pagination personnalisée
│   ├── permissions.py             # Permissions personnalisées
│   ├── authentication.py          # Authentification personnalisée
│   ├── throttling.py              # Rate limiting
│   └── renderers.py               # Renderers personnalisés
├── users/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── views.py               # ViewSets utilisateurs
│   │   ├── serializers.py         # Sérialiseurs
│   │   ├── filters.py             # Filtres
│   │   └── urls.py                # URLs utilisateurs
│   └── models.py
├── products/
│   ├── api/
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   └── models.py
```

### Configuration de base

```python
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'drf_spectacular',  # Documentation OpenAPI
    'api',
    'apps.users',
    'apps.products',
]

REST_FRAMEWORK = {
    # Pagination
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    
    # Authentification
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    
    # Permissions
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    
    # Throttling
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
    
    # Filtrage
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    
    # Renderers
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    
    # Exceptions
    'EXCEPTION_HANDLER': 'api.exceptions.custom_exception_handler',
    
    # Versioning
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
    
    # Documentation
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Configuration JWT
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Configuration drf-spectacular (documentation)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Mon API',
    'DESCRIPTION': 'Description de mon API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
```

```python
# api/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """Pagination standard pour toutes les listes."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })


class LargeResultsSetPagination(PageNumberPagination):
    """Pagination pour les grandes listes."""
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000
```

```python
# api/permissions.py
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée : seul le propriétaire peut modifier.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission : seuls les admins peuvent modifier, les autres en lecture seule.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsVerifiedUser(permissions.BasePermission):
    """
    Permission : uniquement les utilisateurs vérifiés.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_verified
        )
```

```python
# api/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status


def custom_exception_handler(exc, context):
    """Gestionnaire d'exceptions personnalisé."""
    response = exception_handler(exc, context)
    
    if response is not None:
        # Formater la réponse d'erreur
        custom_response = {
            'error': {
                'code': response.status_code,
                'message': response.data.get('detail', 'Une erreur est survenue'),
                'details': response.data
            }
        }
        response.data = custom_response
    
    return response


class ServiceUnavailable(APIException):
    """Exception pour service temporairement indisponible."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporairement indisponible.'
    default_code = 'service_unavailable'
```

## Sérialiseurs

### Bonnes pratiques

```python
# apps/users/api/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.users.models import Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le profil utilisateur."""
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = ['bio', 'location', 'website', 'avatar', 'avatar_url']
        read_only_fields = ['avatar_url']
    
    def get_avatar_url(self, obj):
        """Retourne l'URL complète de l'avatar."""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None


class UserListSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la liste des utilisateurs (données limitées)."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email', 'date_joined']
        read_only_fields = ['date_joined']


class UserDetailSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le détail d'un utilisateur."""
    profile = ProfileSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    is_online = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'profile', 'is_online', 'date_joined', 'last_login'
        ]
        read_only_fields = ['date_joined', 'last_login']
        extra_kwargs = {
            'email': {'required': True},
        }


class UserCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création d'un utilisateur."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']
    
    def validate(self, data):
        """Validation personnalisée."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Les mots de passe ne correspondent pas.'
            })
        return data
    
    def create(self, validated_data):
        """Création de l'utilisateur."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la mise à jour d'un utilisateur."""
    current_password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        min_length=8
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'current_password', 'new_password']
    
    def update(self, instance, validated_data):
        """Mise à jour avec gestion du mot de passe."""
        current_password = validated_data.pop('current_password', None)
        new_password = validated_data.pop('new_password', None)
        
        if new_password:
            if not current_password:
                raise serializers.ValidationError({
                    'current_password': 'Mot de passe actuel requis pour changer le mot de passe.'
                })
            if not instance.check_password(current_password):
                raise serializers.ValidationError({
                    'current_password': 'Mot de passe actuel incorrect.'
                })
            instance.set_password(new_password)
        
        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    """Sérialiseur pour le changement de mot de passe."""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Les mots de passe ne correspondent pas.'
            })
        return data
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Mot de passe actuel incorrect.')
        return value
```

## ViewSets et Views

```python
# apps/users/api/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.users.models import Profile
from apps.users.api.serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ProfileSerializer,
    ChangePasswordSerializer,
)
from api.permissions import IsOwnerOrReadOnly

User = get_user_model()


@extend_schema(tags=['users'])
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des utilisateurs.
    
    Liste, crée, modifie et supprime des utilisateurs.
    """
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username', 'email']
    ordering = ['-date_joined']
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """Sélectionne le sérialiseur selon l'action."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
            return UserListSerializer
        return UserDetailSerializer
    
    def get_permissions(self):
        """Définit les permissions selon l'action."""
        if self.action == 'create':
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filtre le queryset selon les permissions."""
        queryset = super().get_queryset()
        
        # Ne pas montrer les utilisateurs inactifs sauf aux admins
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        return queryset.select_related('profile').prefetch_related('groups', 'user_permissions')
    
    def perform_create(self, serializer):
        """Crée l'utilisateur et son profil."""
        user = serializer.save()
        Profile.objects.create(user=user)
    
    @extend_schema(
        summary="Récupérer l'utilisateur connecté",
        responses={200: UserDetailSerializer}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Retourne l'utilisateur connecté."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Changer le mot de passe",
        request=ChangePasswordSerializer,
        responses={200: {'description': 'Mot de passe changé avec succès'}}
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Change le mot de passe de l'utilisateur connecté."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response(
            {'message': 'Mot de passe changé avec succès.'},
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        summary="Activer/désactiver un utilisateur",
        responses={200: {'description': 'Statut modifié'}}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_active(self, request, pk=None):
        """Active ou désactive un utilisateur."""
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        
        return Response({
            'message': f"Utilisateur {'activé' if user.is_active else 'désactivé'}.",
            'is_active': user.is_active
        })


@extend_schema(tags=['profiles'])
class ProfileViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des profils."""
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)
```

## Filtres avancés

```python
# apps/products/api/filters.py
import django_filters
from django.db.models import Q
from apps.products.models import Product


class ProductFilter(django_filters.FilterSet):
    """Filtres avancés pour les produits."""
    
    # Filtre par prix
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Filtre par date
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Filtre personnalisé
    search = django_filters.CharFilter(method='filter_search')
    
    # Filtre par catégories (multiple)
    categories = django_filters.CharFilter(method='filter_categories')
    
    # Filtre booléen
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    
    class Meta:
        model = Product
        fields = ['status', 'brand', 'min_price', 'max_price']
    
    def filter_search(self, queryset, name, value):
        """Recherche dans le nom et la description."""
        return queryset.filter(
            Q(name__icontains=value) | 
            Q(description__icontains=value) |
            Q(sku__iexact=value)
        )
    
    def filter_categories(self, queryset, name, value):
        """Filtre par catégories (liste d'IDs séparés par des virgules)."""
        category_ids = [int(x) for x in value.split(',')]
        return queryset.filter(categories__id__in=category_ids).distinct()
    
    def filter_in_stock(self, queryset, name, value):
        """Filtre les produits en stock."""
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset.filter(stock_quantity=0)
```

```python
# apps/products/api/views.py
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from apps.products.models import Product
from apps.products.api.serializers import ProductSerializer
from apps.products.api.filters import ProductFilter


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet pour les produits avec filtres avancés."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
```

## URLs et Routing

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    
    # Documentation API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

```python
# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.api.views import UserViewSet, ProfileViewSet
from apps.products.api.views import ProductViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('auth/token/', include('apps.users.api.urls')),  # JWT endpoints
]
```

## Authentification JWT

```python
# apps/users/api/urls.py
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from apps.users.api.views import LogoutView

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
```

```python
# apps/users/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken


class LogoutView(APIView):
    """Vue pour la déconnexion (blacklist du refresh token)."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {'message': 'Déconnexion réussie.'},
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            return Response(
                {'error': 'Token invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )
```

## Throttling et Rate Limiting

```python
# api/throttling.py
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """Rate limit pour les requêtes en rafale."""
    scope = 'burst'
    rate = '60/minute'


class SustainedRateThrottle(UserRateThrottle):
    """Rate limit pour les requêtes soutenues."""
    scope = 'sustained'
    rate = '1000/day'


class CustomAnonRateThrottle(AnonRateThrottle):
    """Rate limit pour les utilisateurs anonymes."""
    rate = '100/hour'
```

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'api.throttling.BurstRateThrottle',
        'api.throttling.SustainedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'burst': '60/minute',
        'sustained': '1000/day',
        'user': '1000/hour',
        'anon': '100/hour',
    },
}
```

## Tests

```python
# apps/users/api/tests/test_views.py
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserViewSet:
    """Tests du UserViewSet."""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def authenticated_client(self, api_client, user):
        api_client.force_authenticate(user=user)
        return api_client
    
    def test_list_users(self, authenticated_client, user):
        """Test la liste des utilisateurs."""
        url = reverse('user-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_create_user(self, api_client):
        """Test la création d'un utilisateur."""
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123'
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username='newuser').exists()
    
    def test_create_user_password_mismatch(self, api_client):
        """Test la création avec mots de passe différents."""
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'pass123',
            'password_confirm': 'pass456'
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data
    
    def test_retrieve_user(self, authenticated_client, user):
        """Test la récupération d'un utilisateur."""
        url = reverse('user-detail', kwargs={'pk': user.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'
    
    def test_update_user(self, authenticated_client, user):
        """Test la mise à jour d'un utilisateur."""
        url = reverse('user-detail', kwargs={'pk': user.pk})
        data = {'first_name': 'Updated'}
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == 'Updated'
    
    def test_delete_user(self, authenticated_client, user):
        """Test la suppression d'un utilisateur."""
        url = reverse('user-detail', kwargs={'pk': user.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(pk=user.pk).exists()
    
    def test_me_endpoint(self, authenticated_client, user):
        """Test l'endpoint /me."""
        url = reverse('user-me')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == user.username
    
    def test_change_password(self, authenticated_client, user):
        """Test le changement de mot de passe."""
        url = reverse('user-change-password')
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password('newpass123')
    
    def test_unauthenticated_access(self, api_client):
        """Test l'accès non authentifié."""
        url = reverse('user-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

## Checklist

### Configuration
- [ ] Pagination configurée
- [ ] Authentification et permissions définies
- [ ] Throttling pour rate limiting
- [ ] Documentation API (drf-spectacular)
- [ ] Gestion des exceptions personnalisée

### Sécurité
- [ ] Authentification requise par défaut
- [ ] Permissions granulaires
- [ ] Validation des entrées
- [ ] Pas de données sensibles en clair
- [ ] Rate limiting activé

### Performance
- [ ] select_related et prefetch_related
- [ ] Pagination sur toutes les listes
- [ ] Caching si nécessaire
- [ ] Throttling configuré

### Documentation
- [ ] Docstrings sur ViewSets
- [ ] @extend_schema pour OpenAPI
- [ ] Exemples de requêtes/réponses
- [ ] Documentation des permissions

## Ressources

- [Django REST Framework Docs](https://www.django-rest-framework.org/)
- [DRF Spectacular](https://drf-spectacular.readthedocs.io/)
- [Django Filter](https://django-filter.readthedocs.io/)
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
