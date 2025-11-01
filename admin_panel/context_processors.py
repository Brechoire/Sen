"""
Context processors pour le panneau d'administration
"""
from .utils import get_unread_confirmed_orders_count


def admin_notifications(request):
    """
    Context processor qui ajoute le nombre de commandes non consultées
    au contexte pour toutes les pages admin.
    
    Returns:
        dict: Dictionnaire contenant 'unread_orders_count'
    """
    if request.user.is_authenticated and request.user.is_staff:
        return {
            'unread_orders_count': get_unread_confirmed_orders_count()
        }
    return {
        'unread_orders_count': 0
    }

