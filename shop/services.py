from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import LoyaltyProgram, PromoCode, UserLoyaltyStatus, PromoCodeUse, Cart, Order


class LoyaltyService:
    """Service pour gérer la logique de fidélité"""
    
    @staticmethod
    def get_or_create_loyalty_status(user):
        """Récupère ou crée le statut de fidélité d'un utilisateur"""
        status, created = UserLoyaltyStatus.objects.get_or_create(user=user)
        return status
    
    @staticmethod
    def update_loyalty_status(user, order_amount):
        """Met à jour le statut de fidélité après un achat"""
        status = LoyaltyService.get_or_create_loyalty_status(user)
        status.update_loyalty_status(order_amount)
        return status
    
    @staticmethod
    def get_available_loyalty_discount(user, cart_total):
        """Retourne la réduction de fidélité disponible pour un utilisateur"""
        status = LoyaltyService.get_or_create_loyalty_status(user)
        loyalty_program = status.get_available_loyalty_discount()
        
        if loyalty_program:
            return loyalty_program.calculate_discount(cart_total)
        return Decimal('0.00')
    
    @staticmethod
    def get_loyalty_program_for_user(user):
        """Retourne le programme de fidélité applicable pour un utilisateur"""
        status = LoyaltyService.get_or_create_loyalty_status(user)
        return status.get_available_loyalty_discount()


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
