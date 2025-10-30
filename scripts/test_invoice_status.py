#!/usr/bin/env python
"""
Script de test pour vérifier que les factures sont créées avec le bon statut
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from shop.models import Order, Invoice
from django.contrib.auth import get_user_model

User = get_user_model()


def create_test_data():
    """Crée des données de test pour tester les factures"""
    
    # Nettoyer d'abord les données existantes
    Order.objects.filter(order_number__startswith='TEST-INVOICE-').delete()
    User.objects.filter(username__in=['client_test_invoice']).delete()
    
    # Créer un utilisateur client
    client_user = User.objects.create_user(
        username='client_test_invoice',
        email='client@test.com',
        first_name='Client',
        last_name='Test',
        password='testpass123'
    )
    
    # Créer une commande confirmée
    order = Order.objects.create(
        user=client_user,
        order_number=f'TEST-INVOICE-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        status='confirmed',
        payment_status='paid',
        shipping_first_name='Client',
        shipping_last_name='Test',
        shipping_address='123 Test Street',
        shipping_city='Test City',
        shipping_postal_code='12345',
        shipping_country='Test Country',
        subtotal=50.00,
        shipping_cost=5.00,
        total_amount=55.00
    )
    
    return client_user, order


def test_invoice_creation_status():
    """Teste que les factures sont créées avec le statut 'sent'"""
    print("=== Test de création de facture avec le bon statut ===")
    
    client_user, order = create_test_data()
    
    # Créer une facture
    invoice = Invoice.objects.create(
        order=order,
        billing_name=f"{order.shipping_first_name} {order.shipping_last_name}",
        billing_address=order.shipping_address,
        billing_city=order.shipping_city,
        billing_postal_code=order.shipping_postal_code,
        billing_country=order.shipping_country,
        subtotal=order.subtotal,
        shipping_cost=order.shipping_cost,
        total_amount=order.total_amount,
    )
    
    print(f"Facture créée: {invoice.invoice_number}")
    print(f"Statut: {invoice.status} ({invoice.get_status_display()})")
    
    if invoice.status == 'sent':
        print("[OK] Facture créée avec le statut 'Envoyée'")
        return True
    else:
        print(f"[ERREUR] Facture créée avec le statut '{invoice.status}' au lieu de 'sent'")
        return False


def test_invoice_default_status():
    """Teste que le statut par défaut est bien 'sent'"""
    print("\n=== Test du statut par défaut des factures ===")
    
    client_user, order = create_test_data()
    
    # Créer une facture sans spécifier le statut
    invoice = Invoice.objects.create(
        order=order,
        billing_name=f"{order.shipping_first_name} {order.shipping_last_name}",
        billing_address=order.shipping_address,
        billing_city=order.shipping_city,
        billing_postal_code=order.shipping_postal_code,
        billing_country=order.shipping_country,
        subtotal=order.subtotal,
        shipping_cost=order.shipping_cost,
        total_amount=order.total_amount,
    )
    
    print(f"Facture créée: {invoice.invoice_number}")
    print(f"Statut par défaut: {invoice.status} ({invoice.get_status_display()})")
    
    if invoice.status == 'sent':
        print("[OK] Statut par défaut correct: 'Envoyée'")
        return True
    else:
        print(f"[ERREUR] Statut par défaut incorrect: '{invoice.status}' au lieu de 'sent'")
        return False


def cleanup_test_data():
    """Nettoie les données de test"""
    print("\n=== Nettoyage des données de test ===")
    
    # Supprimer les factures de test
    test_invoices = Invoice.objects.filter(order__order_number__startswith='TEST-INVOICE-')
    invoice_count = test_invoices.count()
    
    if invoice_count > 0:
        test_invoices.delete()
        print(f"[OK] {invoice_count} facture(s) de test supprimee(s)")
    
    # Supprimer les commandes de test
    test_orders = Order.objects.filter(order_number__startswith='TEST-INVOICE-')
    order_count = test_orders.count()
    
    if order_count > 0:
        test_orders.delete()
        print(f"[OK] {order_count} commande(s) de test supprimee(s)")
    
    # Supprimer l'utilisateur de test
    try:
        user = User.objects.get(username='client_test_invoice')
        user.delete()
        print("[OK] Utilisateur de test supprime")
    except User.DoesNotExist:
        pass


def main():
    """Fonction principale de test"""
    print("=== Test du statut des factures ===")
    
    try:
        # Tests
        test1 = test_invoice_creation_status()
        test2 = test_invoice_default_status()
        
        # Résultats
        print("\n=== Résultats des tests ===")
        print(f"Test 1 (Création avec statut 'sent'): {'[SUCCES]' if test1 else '[ECHEC]'}")
        print(f"Test 2 (Statut par défaut 'sent'): {'[SUCCES]' if test2 else '[ECHEC]'}")
        
        if all([test1, test2]):
            print("\n[SUCCES] Tous les tests sont passes avec succes !")
            return True
        else:
            print("\n[ECHEC] Certains tests ont echoue.")
            return False
            
    except Exception as e:
        print(f"\n[ERREUR] Erreur lors du test: {e}")
        return False
        
    finally:
        cleanup_test_data()
        print("\n[OK] Nettoyage termine.")


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)






