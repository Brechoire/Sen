from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Pages principales
    path('', views.shop_home, name='shop_home'),
    path('livres/', views.BookListView.as_view(), name='book_list'),
    path('livre/<slug:slug>/', views.BookDetailView.as_view(), name='book_detail'),
    path('categorie/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Gestion des livres (admin) - Redirige vers l'administration
    path('admin/livre/ajouter/', views.redirect_to_admin_create_book, name='book_create'),
    path('admin/livre/<slug:slug>/modifier/', views.redirect_to_admin_books, name='book_update'),
    path('admin/livre/<slug:slug>/supprimer/', views.redirect_to_admin_books, name='book_delete'),
    
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
    path('api/code-promo/appliquer/', views.apply_promo_code, name='apply_promo_code'),
    path('api/code-promo/supprimer/', views.remove_promo_code, name='remove_promo_code'),
    path('api/reductions/', views.get_cart_discounts, name='get_cart_discounts'),
    
    # Commandes et paiements
    path('commande/', views.checkout, name='checkout'),
    path('commande/<int:order_id>/', views.order_detail, name='order_detail'),
    path('mes-commandes/', views.order_list, name='order_list'),
    path('commande/<int:order_id>/annuler/', views.cancel_order, name='cancel_order'),
    path('commande/<int:order_id>/remboursement/', views.request_refund, name='request_refund'),
    path('mes-remboursements/', views.refund_list, name='refund_list'),
    path('fidelite/', views.loyalty_status, name='loyalty_status'),
    path('paiement/paypal/<int:order_id>/', views.paypal_payment, name='paypal_payment'),
    path('paiement/paypal/success/', views.paypal_success, name='paypal_success'),
    path('paiement/paypal/cancel/', views.paypal_cancel, name='paypal_cancel'),
    path('paiement/manuel/<int:order_id>/', views.manual_payment, name='manual_payment'),
    
    # API PayPal
    path('api/paypal/create-order/', views.create_paypal_order, name='create_paypal_order'),
    path('api/paypal/capture-order/', views.capture_paypal_order, name='capture_paypal_order'),
    
    # Test
    path('test-cart-transfer/', views.test_cart_transfer, name='test_cart_transfer'),
    path('force-cart-transfer/', views.force_cart_transfer, name='force_cart_transfer'),
    
    # Factures
    path('factures/', views.invoice_list, name='invoice_list'),
    path('facture/creer/<int:order_id>/', views.create_invoice, name='create_invoice'),
    path('facture/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('facture/<int:invoice_id>/pdf/', views.invoice_pdf, name='invoice_pdf'),
]
