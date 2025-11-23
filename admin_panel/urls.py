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
    path('reseaux-sociaux/', views.manage_social_media, name='social_media'),
    path('boutique/remboursements/', views.manage_refunds, name='refunds'),
    path('boutique/remboursements/<int:refund_id>/traiter/', views.process_refund, name='process_refund'),
    path('boutique/fidelite/', views.manage_loyalty_programs, name='loyalty_programs'),
    path('boutique/fidelite/creer/', views.create_loyalty_program, name='create_loyalty_program'),
    path('boutique/fidelite/<int:program_id>/toggle/', views.toggle_loyalty_program, name='toggle_loyalty_program'),
    path('boutique/fidelite/<int:program_id>/supprimer/', views.delete_loyalty_program, name='delete_loyalty_program'),
    path('boutique/codes-promo/', views.manage_promo_codes, name='promo_codes'),
    path('boutique/codes-promo/creer/', views.create_promo_code, name='create_promo_code'),
    path('boutique/codes-promo/<int:code_id>/toggle/', views.toggle_promo_code, name='toggle_promo_code'),
    path('boutique/codes-promo/<int:code_id>/supprimer/', views.delete_promo_code, name='delete_promo_code'),
    path('boutique/statuts-fidelite/', views.manage_loyalty_status, name='loyalty_status'),
    path('categories/', views.manage_categories, name='categories'),
    path('categories/creer/', views.create_category, name='create_category'),
    path('categories/<int:category_id>/modifier/', views.edit_category, name='edit_category'),
    path('categories/<int:category_id>/toggle/', views.toggle_category, name='toggle_category'),
    path('categories/<int:category_id>/supprimer/', views.delete_category, name='delete_category'),
    path('boutique/paypal-config/', views.paypal_config, name='paypal_config'),
    path('variables-environnement/', views.environment_variables, name='environment_variables'),
    
    # Actions sur les articles
    path('articles/<int:article_id>/toggle/', views.toggle_article_status, name='toggle_article'),
    
    # Actions sur les livres
    path('livres/creer/', views.create_book, name='create_book'),
    path('livres/<int:book_id>/modifier/', views.edit_book, name='edit_book'),
    path('livres/<int:book_id>/toggle/', views.toggle_book, name='toggle_book'),
    path('livres/<int:book_id>/supprimer/', views.delete_book, name='delete_book'),
    path('livres/<int:book_id>/marquer-disponible/', views.mark_book_available, name='mark_book_available'),
    
    # Actions sur les auteurs
    path('auteurs/<int:author_id>/toggle/', views.toggle_author_status, name='toggle_author'),
    
    # Actions sur les avis
    path('avis/<int:review_id>/approuver/', views.approve_review, name='approve_review'),
    path('avis/<int:review_id>/rejeter/', views.reject_review, name='reject_review'),
    
    # Factures
    path('factures/', views.invoice_list, name='invoice_list'),
    path('facture/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('facture/creer/<int:order_id>/', views.create_invoice, name='create_invoice'),
    path('facture/<int:invoice_id>/statut/', views.update_invoice_status, name='update_invoice_status'),
    
    # Gestion avancée des commandes
    path('commande/<int:order_id>/', views.order_detail, name='order_detail'),
    path('commande/<int:order_id>/statut/', views.update_order_status, name='update_order_status'),
    path('commande/<int:order_id>/suivi/', views.update_tracking_info, name='update_tracking_info'),
    path('commande/<int:order_id>/paiement/', views.update_payment_status, name='update_payment_status'),
    path('commande/<int:order_id>/annuler/', views.cancel_order, name='cancel_order'),
]
