from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Pages principales
    path('', views.shop_home, name='shop_home'),
    path('livres/', views.BookListView.as_view(), name='book_list'),
    path('livre/<slug:slug>/', views.BookDetailView.as_view(), name='book_detail'),
    path('categorie/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Gestion des livres (admin)
    path('admin/livre/ajouter/', views.BookCreateView.as_view(), name='book_create'),
    path('admin/livre/<slug:slug>/modifier/', views.BookUpdateView.as_view(), name='book_update'),
    path('admin/livre/<slug:slug>/supprimer/', views.BookDeleteView.as_view(), name='book_delete'),
    
    # Gestion des catégories (admin)
    path('admin/categorie/ajouter/', views.CategoryCreateView.as_view(), name='category_create'),
    path('admin/categorie/<slug:slug>/modifier/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('admin/categorie/<slug:slug>/supprimer/', views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # Avis
    path('livre/<slug:slug>/avis/ajouter/', views.add_review, name='add_review'),
    
    # Panier
    path('panier/', views.cart_detail, name='cart_detail'),
    path('panier/ajouter/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('panier/supprimer/<int:book_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('panier/modifier/<int:book_id>/', views.update_cart_item, name='update_cart_item'),
    path('panier/diminuer/<int:book_id>/', views.decrease_cart_item, name='decrease_cart_item'),
    path('panier/vider/', views.clear_cart, name='clear_cart'),
    
    # API AJAX
    path('api/livres/', views.get_books_ajax, name='books_ajax'),
    path('api/recherche/', views.book_search_suggestions, name='search_suggestions'),
    path('api/panier/', views.cart_summary, name='cart_summary'),
    
    # Test
    path('test-cart-transfer/', views.test_cart_transfer, name='test_cart_transfer'),
    path('force-cart-transfer/', views.force_cart_transfer, name='force_cart_transfer'),
]
