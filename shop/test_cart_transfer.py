from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import Cart, CartItem
from .views import get_or_create_cart

User = get_user_model()

def test_cart_transfer(request):
    """Vue de test pour vérifier le transfert de panier"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Utilisateur non connecté'})
    
    # Récupérer le panier actuel
    current_cart = get_or_create_cart(request)
    
    # Récupérer tous les paniers de l'utilisateur
    user_carts = Cart.objects.filter(user=request.user)
    
    # Récupérer tous les paniers de session
    session_carts = Cart.objects.filter(session_key__isnull=False, user__isnull=True)
    
    data = {
        'user': request.user.username,
        'session_key': request.session.session_key,
        'current_cart_id': current_cart.id,
        'current_cart_items': current_cart.total_items,
        'user_carts_count': user_carts.count(),
        'session_carts_count': session_carts.count(),
        'user_carts': [
            {
                'id': cart.id,
                'items': cart.total_items,
                'created': cart.created_at.isoformat()
            } for cart in user_carts
        ],
        'session_carts': [
            {
                'id': cart.id,
                'session_key': cart.session_key,
                'items': cart.total_items,
                'created': cart.created_at.isoformat()
            } for cart in session_carts
        ]
    }
    
    return JsonResponse(data)






