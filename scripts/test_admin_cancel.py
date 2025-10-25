#!/usr/bin/env python
"""
Script de test pour la fonctionnalité d'annulation de commandes par l'admin
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

from shop.models import Order, OrderStatusHistory
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


def create_test_data():
    """Crée des données de test pour tester l'annulation"""
    
    # Nettoyer d'abord les données existantes
    Order.objects.filter(order_number__startswith='TEST-').delete()
    User.objects.filter(username__in=['admin_test', 'client_test']).delete()
    
    # Créer un utilisateur admin
    admin_user = User.objects.create_user(
        username='admin_test',
        email='admin@test.com',
        first_name='Admin',
        last_name='Test',
        password='testpass123',
        is_staff=True,
        is_superuser=True
    )
    
    # Créer un utilisateur client
    client_user = User.objects.create_user(
        username='client_test',
        email='client@test.com',
        first_name='Client',
        last_name='Test',
        password='testpass123'
    )
    
    # Créer une commande en attente
    pending_order = Order.objects.create(
        user=client_user,
        order_number=f'TEST-PENDING-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        status='pending',
        payment_status='pending',
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
    
    # Créer une commande en cours de traitement
    processing_order = Order.objects.create(
        user=client_user,
        order_number=f'TEST-PROCESSING-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        status='processing',
        payment_status='paid',
        shipping_first_name='Client',
        shipping_last_name='Test',
        shipping_address='123 Test Street',
        shipping_city='Test City',
        shipping_postal_code='12345',
        shipping_country='Test Country',
        subtotal=75.00,
        shipping_cost=5.00,
        total_amount=80.00
    )
    
    # Créer une commande livrée (ne peut pas être annulée)
    delivered_order = Order.objects.create(
        user=client_user,
        order_number=f'TEST-DELIVERED-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        status='delivered',
        payment_status='paid',
        shipping_first_name='Client',
        shipping_last_name='Test',
        shipping_address='123 Test Street',
        shipping_city='Test City',
        shipping_postal_code='12345',
        shipping_country='Test Country',
        subtotal=100.00,
        shipping_cost=5.00,
        total_amount=105.00
    )
    
    return admin_user, client_user, pending_order, processing_order, delivered_order


def test_cancel_pending_order():
    """Teste l'annulation d'une commande en attente"""
    print("=== Test d'annulation d'une commande en attente ===")
    
    admin_user, client_user, pending_order, processing_order, delivered_order = create_test_data()
    
    # Simuler la connexion admin
    client = Client()
    client.force_login(admin_user)
    
    # Configurer les headers pour éviter l'erreur ALLOWED_HOSTS
    client.defaults['HTTP_HOST'] = 'localhost'
    
    # Tester l'accès à la page d'annulation
    response = client.get(reverse('admin_panel:cancel_order', args=[pending_order.id]))
    
    if response.status_code == 200:
        print("[OK] Page d'annulation accessible")
    else:
        print(f"[ERREUR] Page d'annulation inaccessible: {response.status_code}")
        return False
    
    # Tester l'annulation
    cancel_data = {
        'reason': 'Test d\'annulation',
        'admin_notes': 'Test automatique'
    }
    
    response = client.post(reverse('admin_panel:cancel_order', args=[pending_order.id]), cancel_data)
    
    if response.status_code == 302:  # Redirection après succès
        print("[OK] Annulation effectuée avec succès")
        
        # Vérifier que la commande est annulée
        pending_order.refresh_from_db()
        if pending_order.status == 'cancelled' and pending_order.payment_status == 'failed':
            print("[OK] Commande correctement annulée")
            
            # Vérifier l'historique
            history = OrderStatusHistory.objects.filter(order=pending_order)
            if history.exists():
                print(f"[OK] Historique créé: {history.count()} entrée(s)")
                for entry in history:
                    print(f"  - {entry.old_status} -> {entry.new_status} ({entry.changed_at})")
            else:
                print("[ERREUR] Aucun historique créé")
                return False
        else:
            print(f"[ERREUR] Commande non annulée correctement: status={pending_order.status}, payment={pending_order.payment_status}")
            return False
    else:
        print(f"[ERREUR] Échec de l'annulation: {response.status_code}")
        return False
    
    return True


def test_cancel_processing_order():
    """Teste l'annulation d'une commande en cours de traitement"""
    print("\n=== Test d'annulation d'une commande en cours de traitement ===")
    
    admin_user, client_user, pending_order, processing_order, delivered_order = create_test_data()
    
    # Simuler la connexion admin
    client = Client()
    client.force_login(admin_user)
    client.defaults['HTTP_HOST'] = 'localhost'
    
    # Tester l'annulation
    cancel_data = {
        'reason': 'Test d\'annulation processing',
        'admin_notes': 'Test automatique processing'
    }
    
    response = client.post(reverse('admin_panel:cancel_order', args=[processing_order.id]), cancel_data)
    
    if response.status_code == 302:  # Redirection après succès
        print("[OK] Annulation effectuée avec succès")
        
        # Vérifier que la commande est annulée
        processing_order.refresh_from_db()
        if processing_order.status == 'cancelled':
            print("[OK] Commande en cours de traitement correctement annulée")
            return True
        else:
            print(f"[ERREUR] Commande non annulée correctement: status={processing_order.status}")
            return False
    else:
        print(f"[ERREUR] Échec de l'annulation: {response.status_code}")
        return False


def test_cancel_delivered_order():
    """Teste qu'on ne peut pas annuler une commande livrée"""
    print("\n=== Test d'impossibilité d'annuler une commande livrée ===")
    
    admin_user, client_user, pending_order, processing_order, delivered_order = create_test_data()
    
    # Simuler la connexion admin
    client = Client()
    client.force_login(admin_user)
    client.defaults['HTTP_HOST'] = 'localhost'
    
    # Tester l'accès à la page d'annulation (devrait rediriger)
    response = client.get(reverse('admin_panel:cancel_order', args=[delivered_order.id]))
    
    if response.status_code == 302:  # Redirection
        print("[OK] Accès à l'annulation d'une commande livrée correctement bloqué")
        return True
    else:
        print(f"[ERREUR] L'annulation d'une commande livrée devrait être bloquée: {response.status_code}")
        return False


def cleanup_test_data():
    """Nettoie les données de test"""
    print("\n=== Nettoyage des données de test ===")
    
    # Supprimer les commandes de test
    test_orders = Order.objects.filter(order_number__startswith='TEST-')
    count = test_orders.count()
    
    if count > 0:
        test_orders.delete()
        print(f"[OK] {count} commande(s) de test supprimee(s)")
    else:
        print("[OK] Aucune donnee de test a nettoyer")
    
    # Supprimer les utilisateurs de test
    test_users = User.objects.filter(username__in=['admin_test', 'client_test'])
    for user in test_users:
        if not Order.objects.filter(user=user).exists():
            user.delete()
            print(f"[OK] Utilisateur {user.username} supprime")


def main():
    """Fonction principale de test"""
    print("=== Test de la fonctionnalite d'annulation de commandes par l'admin ===")
    
    try:
        # Tests
        test1 = test_cancel_pending_order()
        test2 = test_cancel_processing_order()
        test3 = test_cancel_delivered_order()
        
        # Résultats
        print("\n=== Résultats des tests ===")
        print(f"Test 1 (Commande en attente): {'[SUCCES]' if test1 else '[ECHEC]'}")
        print(f"Test 2 (Commande en traitement): {'[SUCCES]' if test2 else '[ECHEC]'}")
        print(f"Test 3 (Commande livrée bloquée): {'[SUCCES]' if test3 else '[ECHEC]'}")
        
        if all([test1, test2, test3]):
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
