from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Tableau de bord
    path('', views.admin_dashboard, name='dashboard'),
    
    # Gestion des modules
    path('articles/', views.manage_articles, name='articles'),
    path('auteurs/', views.manage_authors, name='authors'),
    path('livres/', views.manage_books, name='books'),
    path('commandes/', views.manage_orders, name='orders'),
    path('avis/', views.manage_reviews, name='reviews'),
    path('utilisateurs/', views.manage_users, name='users'),
    path('boutique/parametres/', views.manage_shop_settings, name='shop_settings'),
    path('boutique/remboursements/', views.manage_refunds, name='refunds'),
    path('boutique/remboursements/<int:refund_id>/traiter/', views.process_refund, name='process_refund'),
    path('variables-environnement/', views.environment_variables, name='environment_variables'),
    
    # Actions sur les articles
    path('articles/<int:article_id>/toggle/', views.toggle_article_status, name='toggle_article'),
    
    # Actions sur les livres
    path('livres/<int:book_id>/toggle/', views.toggle_book_status, name='toggle_book'),
    
    # Actions sur les auteurs
    path('auteurs/<int:author_id>/toggle/', views.toggle_author_status, name='toggle_author'),
    
    # Actions sur les avis
    path('avis/<int:review_id>/approuver/', views.approve_review, name='approve_review'),
    path('avis/<int:review_id>/rejeter/', views.reject_review, name='reject_review'),
]
