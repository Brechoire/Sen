"""
Template filters personnalisés pour l'application shop
"""
from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def calculate_tax(amount, rate=5.5):
    """Calcule la TVA sur un montant"""
    if not amount:
        return Decimal('0.00')
    
    # Convertir en Decimal pour les calculs précis
    amount = Decimal(str(amount))
    rate = Decimal(str(rate))
    
    # Calculer la TVA : montant * (taux / 100)
    tax = amount * (rate / 100)
    return tax.quantize(Decimal('0.01'))


@register.filter
def calculate_total_with_tax(amount, rate=5.5):
    """Calcule le total avec TVA"""
    if not amount:
        return Decimal('0.00')
    
    amount = Decimal(str(amount))
    rate = Decimal(str(rate))
    
    # Total = montant + (montant * taux / 100)
    total = amount + (amount * (rate / 100))
    return total.quantize(Decimal('0.01'))


@register.filter
def calculate_shipping(subtotal, free_threshold=50):
    """Calcule les frais de port"""
    if not subtotal:
        return Decimal('5.90')
    
    subtotal = Decimal(str(subtotal))
    free_threshold = Decimal(str(free_threshold))
    
    if subtotal >= free_threshold:
        return Decimal('0.00')
    else:
        return Decimal('5.90')


@register.filter
def calculate_final_total(subtotal, rate=5.5, free_threshold=50):
    """Calcule le total final avec TVA et frais de port"""
    if not subtotal:
        return Decimal('0.00')
    
    subtotal = Decimal(str(subtotal))
    rate = Decimal(str(rate))
    free_threshold = Decimal(str(free_threshold))
    
    # Calculer la TVA
    tax = subtotal * (rate / 100)
    
    # Calculer les frais de port
    shipping = Decimal('0.00') if subtotal >= free_threshold else Decimal('5.90')
    
    # Total final
    total = subtotal + tax + shipping
    return total.quantize(Decimal('0.01'))
