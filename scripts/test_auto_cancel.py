#!/usr/bin/env python
"""
Script de test pour l'annulation automatique des commandes expirées
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Configuration Django
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from shop.models import Order, OrderStatusHistory
from django.contrib.auth import get_user_model

User = get_user_model()


def create_test_expired_order():
    """Crée une commande de test expirée pour tester l'annulation automatique"""
    
    # Créer un utilisateur de test s'il n'existe pas
    user, created = User.objects.get_or_create(
        username='test_user_auto_cancel',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    # Créer une commande expirée (créée il y a 25 heures)
    expired_time = timezone.now() - timedelta(hours=25)
    
    order = Order.objects.create(
        user=user,
        order_number=f'TEST-EXPIRED-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        status='pending',
        payment_status='pending',
        shipping_first_name='Test',
        shipping_last_name='User',
        shipping_address='123 Test Street',
        shipping_city='Test City',
        shipping_postal_code='12345',
        shipping_country='Test Country',
        subtotal=50.00,
        shipping_cost=5.00,
        total_amount=55.00
    )
    
    # Forcer la date de création après la création
    Order.objects.filter(id=order.id).update(created_at=expired_time)
    order.refresh_from_db()
    
    print(f"[OK] Commande de test creee: {order.order_number}")
    print(f"  - Statut: {order.status}")
    print(f"  - Paiement: {order.payment_status}")
    print(f"  - Creee le: {order.created_at}")
    print(f"  - Age: {timezone.now() - order.created_at}")
    
    return order


def test_auto_cancel():
    """Teste l'annulation automatique des commandes expirées"""
    
    print("=== Test de l'annulation automatique des commandes expirées ===\n")
    
    # 1. Créer une commande expirée
    print("1. Création d'une commande expirée...")
    order = create_test_expired_order()
    
    # 2. Compter les commandes en attente avant
    pending_before = Order.objects.filter(status='pending', payment_status='pending').count()
    print(f"\n2. Commandes en attente avant: {pending_before}")
    
    # 3. Exécuter la commande d'annulation
    print("\n3. Exécution de la commande d'annulation...")
    from django.core.management import call_command
    
    try:
        call_command('cancel_expired_orders', verbosity=2)
        print("[OK] Commande d'annulation executee avec succes")
    except Exception as e:
        print(f"[ERREUR] Erreur lors de l'execution: {e}")
        return False
    
    # 4. Vérifier le résultat
    print("\n4. Vérification du résultat...")
    
    # Recharger la commande depuis la base de données
    order.refresh_from_db()
    
    print(f"  - Statut après: {order.status}")
    print(f"  - Paiement après: {order.payment_status}")
    
    # Compter les commandes en attente après
    pending_after = Order.objects.filter(status='pending', payment_status='pending').count()
    print(f"  - Commandes en attente après: {pending_after}")
    
    # Vérifier l'historique
    history = OrderStatusHistory.objects.filter(order=order).order_by('-changed_at')
    if history.exists():
        print(f"  - Historique des changements: {history.count()} entrée(s)")
        for entry in history[:3]:  # Afficher les 3 dernières entrées
            print(f"    - {entry.old_status} -> {entry.new_status} ({entry.changed_at})")
    
    # 5. Résultat du test
    if order.status == 'cancelled' and order.payment_status == 'failed':
        print("\n[SUCCES] Test reussi ! La commande a ete annulee automatiquement.")
        return True
    else:
        print("\n[ECHEC] Test echoue ! La commande n'a pas ete annulee correctement.")
        return False


def cleanup_test_data():
    """Nettoie les données de test"""
    print("\n=== Nettoyage des données de test ===")
    
    # Supprimer les commandes de test
    test_orders = Order.objects.filter(order_number__startswith='TEST-EXPIRED-')
    count = test_orders.count()
    
    if count > 0:
        test_orders.delete()
        print(f"[OK] {count} commande(s) de test supprimee(s)")
    else:
        print("[OK] Aucune donnee de test a nettoyer")
    
    # Supprimer l'utilisateur de test s'il n'a plus de commandes
    try:
        user = User.objects.get(username='test_user_auto_cancel')
        if not Order.objects.filter(user=user).exists():
            user.delete()
            print("[OK] Utilisateur de test supprime")
    except User.DoesNotExist:
        pass


if __name__ == '__main__':
    try:
        success = test_auto_cancel()
        
        if success:
            print("\n[SUCCES] Tous les tests sont passes avec succes !")
        else:
            print("\n[ECHEC] Certains tests ont echoue.")
            
    except Exception as e:
        print(f"\n[ERREUR] Erreur lors du test: {e}")
        
    finally:
        cleanup_test_data()
        print("\n[OK] Nettoyage termine.")
