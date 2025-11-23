from ..models import PromoCode, PromoCodeUse


class PromoCodeService:
    """Service pour gérer la logique des codes promo"""
    
    @staticmethod
    def validate_promo_code(code, user, cart_total):
        """Valide un code promo pour un utilisateur et un panier"""
        try:
            promo_code = PromoCode.objects.get(code=code.upper())
        except PromoCode.DoesNotExist:
            return False, "Code promo invalide"
        
        if not promo_code.is_valid:
            return False, "Code promo expiré ou inactif"
        
        if not promo_code.can_be_used_by_user(user):
            return False, "Vous avez déjà utilisé ce code promo"
        
        if cart_total < promo_code.min_cart_amount:
            return False, f"Montant minimum du panier requis : {promo_code.min_cart_amount}€"
        
        return True, promo_code
    
    @staticmethod
    def calculate_promo_discount(promo_code, cart_total):
        """Calcule la réduction d'un code promo"""
        return promo_code.calculate_discount(cart_total)
    
    @staticmethod
    def apply_promo_code(code, user, cart):
        """Applique un code promo à un panier"""
        is_valid, result = PromoCodeService.validate_promo_code(code, user, cart.total_price)
        
        if not is_valid:
            return False, result
        
        promo_code = result
        discount_amount = PromoCodeService.calculate_promo_discount(promo_code, cart.total_price)
        
        # Stocker le code promo dans la session pour l'utiliser lors de la commande
        cart.session_data = {
            'promo_code': promo_code.id,
            'promo_discount': float(discount_amount)
        }
        cart.save()
        
        return True, f"Code promo '{promo_code.code}' appliqué avec succès"
    
    @staticmethod
    def remove_promo_code(cart):
        """Supprime le code promo d'un panier"""
        cart.session_data = {}
        cart.save()
        return True, "Code promo supprimé"
    
    @staticmethod
    def record_promo_code_use(promo_code, user, order, discount_amount):
        """Enregistre l'utilisation d'un code promo"""
        PromoCodeUse.objects.create(
            promo_code=promo_code,
            user=user,
            order=order,
            discount_amount=discount_amount
        )

