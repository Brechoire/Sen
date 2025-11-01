"""
Utilitaires pour le panneau d'administration
"""
from shop.models import Order


def get_unread_confirmed_orders_count():
    """
    Retourne le nombre de commandes confirmées non consultées par l'admin.
    
    Returns:
        int: Nombre de commandes avec status='confirmed' et admin_viewed_at=None
    """
    return Order.objects.filter(
        status='confirmed',
        admin_viewed_at__isnull=True
    ).count()

