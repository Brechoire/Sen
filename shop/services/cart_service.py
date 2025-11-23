import logging
from ..models import Cart

logger = logging.getLogger(__name__)


class CartService:
    """Service pour gérer les opérations sur le panier"""
    
    @staticmethod
    def get_or_create_cart(user, session_key):
        """Récupère ou crée un panier pour un utilisateur ou une session"""
        if user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=user)
        else:
            cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart
    
    @staticmethod
    def transfer_cart_to_user(session_cart, user):
        """Transfère un panier de session vers un utilisateur connecté"""
        if not user.is_authenticated:
            return False
        
        try:
            user_cart = Cart.objects.get(user=user)
            # Transférer les articles du panier de session vers le panier utilisateur
            for item in session_cart.items.all():
                user_item, created = user_cart.items.get_or_create(
                    book=item.book,
                    defaults={'quantity': item.quantity}
                )
                if not created:
                    user_item.quantity += item.quantity
                    user_item.save()
            
            # Supprimer le panier de session
            session_cart.delete()
            return True
        except Cart.DoesNotExist:
            # Si l'utilisateur n'a pas de panier, renommer le panier de session
            session_cart.user = user
            session_cart.session_key = None
            session_cart.save()
            return True
    
    @staticmethod
    def clear_cart(user):
        """Vide le panier d'un utilisateur après une commande réussie"""
        try:
            user_cart = Cart.objects.get(user=user)
            if user_cart.items.exists():
                user_cart.items.all().delete()
                user_cart.save()
                logger.info(f"Panier vidé pour l'utilisateur {user.id}")
                return True
        except Cart.DoesNotExist:
            logger.warning(f"Aucun panier trouvé pour l'utilisateur {user.id}")
        except Exception as e:
            logger.error(f"Erreur lors du vidage du panier pour l'utilisateur {user.id}: {e}")
        
        return False

