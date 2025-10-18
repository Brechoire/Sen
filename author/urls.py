from django.urls import path
from . import views

app_name = 'author'

urlpatterns = [
    # Vues publiques
    path('', views.AuthorListView.as_view(), name='author_list'),
    path('<int:pk>/', views.AuthorDetailView.as_view(), name='author_detail'),
    
    # Vues CRUD (nécessitent une authentification)
    path('ajouter/', views.AuthorCreateView.as_view(), name='author_create'),
    path('<int:pk>/modifier/', views.AuthorUpdateView.as_view(), name='author_update'),
    path('<int:pk>/supprimer/', views.AuthorDeleteView.as_view(), name='author_delete'),
]
