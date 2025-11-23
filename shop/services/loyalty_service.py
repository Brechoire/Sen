from decimal import Decimal
from ..models import UserLoyaltyStatus


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

