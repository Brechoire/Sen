from django.db import transaction
from decimal import Decimal
from ..models import PromoCode
from .loyalty_service import LoyaltyService
from .promo_code_service import PromoCodeService


class DiscountService:
    """Service pour gérer les calculs de réductions"""
    
    @staticmethod
    def calculate_cart_discounts(user, cart):
        """Calcule toutes les réductions applicables à un panier"""
        discounts = {
            'loyalty_discount': Decimal('0.00'),
            'promo_discount': Decimal('0.00'),
            'total_discount': Decimal('0.00'),
            'loyalty_program': None,
            'promo_code': None
        }
        
        # Réduction de fidélité
        loyalty_discount = LoyaltyService.get_available_loyalty_discount(user, cart.total_price)
        discounts['loyalty_discount'] = loyalty_discount
        
        if loyalty_discount > 0:
            discounts['loyalty_program'] = LoyaltyService.get_loyalty_program_for_user(user)
        
        # Réduction de code promo
        if hasattr(cart, 'session_data') and cart.session_data:
            promo_code_id = cart.session_data.get('promo_code')
            if promo_code_id:
                try:
                    promo_code = PromoCode.objects.get(id=promo_code_id)
                    if promo_code.is_valid and promo_code.can_be_used_by_user(user):
                        discounts['promo_discount'] = Decimal(str(cart.session_data.get('promo_discount', 0)))
                        discounts['promo_code'] = promo_code
                except PromoCode.DoesNotExist:
                    pass
        
        # Total des réductions
        discounts['total_discount'] = discounts['loyalty_discount'] + discounts['promo_discount']
        
        return discounts
    
    @staticmethod
    def apply_discounts_to_order(user, order):
        """Applique les réductions à une commande"""
        with transaction.atomic():
            # Mettre à jour le statut de fidélité
            LoyaltyService.update_loyalty_status(user, order.total_amount)
            
            # Enregistrer l'utilisation du code promo si applicable
            if hasattr(order, 'cart') and order.cart.session_data:
                promo_code_id = order.cart.session_data.get('promo_code')
                if promo_code_id:
                    try:
                        promo_code = PromoCode.objects.get(id=promo_code_id)
                        PromoCodeService.record_promo_code_use(
                            promo_code, 
                            user, 
                            order, 
                            order.cart.session_data.get('promo_discount', 0)
                        )
                    except PromoCode.DoesNotExist:
                        pass

