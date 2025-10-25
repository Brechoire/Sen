#!/usr/bin/env python
"""
Script de test pour vérifier que les messages de commande ne s'affichent plus sur la page contact
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
    """Crée des données de test pour tester les messages"""
    
    # Nettoyer d'abord les données existantes
    Order.objects.filter(order_number__startswith='TEST-MESSAGE-').delete()
    User.objects.filter(username__in=['client_test_message']).delete()
    
    # Créer un utilisateur client
    client_user = User.objects.create_user(
        username='client_test_message',
        email='client@test.com',
        first_name='Client',
        last_name='Test',
        password='testpass123'
    )
    
    # Créer une commande en attente
    order = Order.objects.create(
        user=client_user,
        order_number=f'TEST-MESSAGE-{datetime.now().strftime("%Y%m%d%H%M%S")}',
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
    
    return client_user, order


def test_messages_not_on_contact_page():
    """Teste que les messages de commande ne s'affichent pas sur la page contact"""
    print("=== Test que les messages de commande ne s'affichent pas sur la page contact ===")
    
    client_user, order = create_test_data()
    
    # Simuler la connexion client
    client = Client()
    client.force_login(client_user)
    client.defaults['HTTP_HOST'] = 'localhost'
    
    # 1. Annuler une commande pour créer un message
    print("1. Annulation d'une commande...")
    cancel_data = {
        'reason': 'Test de message',
        'admin_notes': 'Test automatique'
    }
    
    response = client.post(reverse('shop:cancel_order', args=[order.id]), cancel_data)
    
    if response.status_code == 302:
        print("[OK] Commande annulée avec succès")
    else:
        print(f"[ERREUR] Échec de l'annulation: {response.status_code}")
        return False
    
    # 2. Vérifier que la page de contact n'affiche pas le message de commande
    print("2. Vérification de la page contact...")
    response = client.get(reverse('home:contact'))
    
    if response.status_code == 200:
        print("[OK] Page contact accessible")
        
        # Vérifier que le contenu ne contient pas le message de commande
        content = response.content.decode('utf-8')
        
        # Le message de commande ne devrait pas apparaître
        if 'commande' in content.lower() and 'annulée' in content.lower():
            print("[ERREUR] Message de commande trouvé sur la page contact")
            print(f"Contenu trouvé: {[line for line in content.split('\\n') if 'commande' in line.lower() and 'annulée' in line.lower()]}")
            return False
        else:
            print("[OK] Aucun message de commande trouvé sur la page contact")
    else:
        print(f"[ERREUR] Page contact inaccessible: {response.status_code}")
        return False
    
    # 3. Vérifier que le message s'affiche bien sur la page de détail de commande
    print("3. Vérification que le message s'affiche sur la page de commande...")
    response = client.get(reverse('shop:order_detail', args=[order.id]))
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        if 'commande' in content.lower() and 'annulée' in content.lower():
            print("[OK] Message de commande trouvé sur la page de détail de commande")
        else:
            print("[ERREUR] Message de commande non trouvé sur la page de détail de commande")
            return False
    else:
        print(f"[ERREUR] Page de détail de commande inaccessible: {response.status_code}")
        return False
    
    return True


def test_contact_messages_still_work():
    """Teste que les messages de contact fonctionnent toujours"""
    print("\n=== Test que les messages de contact fonctionnent toujours ===")
    
    client_user, order = create_test_data()
    
    # Simuler la connexion client
    client = Client()
    client.force_login(client_user)
    client.defaults['HTTP_HOST'] = 'localhost'
    
    # Tester l'envoi d'un message de contact
    contact_data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'subject': 'Test de message',
        'phone': '0123456789',
        'message': 'Ceci est un test de message de contact'
    }
    
    response = client.post(reverse('home:contact'), contact_data)
    
    if response.status_code == 200:
        print("[OK] Message de contact envoyé")
        
        # Vérifier que le message de contact s'affiche
        content = response.content.decode('utf-8')
        
        # Debug: afficher le contenu pour voir ce qui se passe
        print(f"[DEBUG] Contenu de la réponse: {content[:500]}...")
        
        if 'message' in content.lower() and 'envoyé' in content.lower():
            print("[OK] Message de contact affiché correctement")
            return True
        else:
            print("[ERREUR] Message de contact non affiché")
            # Vérifier si le formulaire a des erreurs
            if 'error' in content.lower() or 'erreur' in content.lower():
                print("[DEBUG] Erreurs de formulaire détectées")
            return False
    else:
        print(f"[ERREUR] Échec de l'envoi du message de contact: {response.status_code}")
        return False


def cleanup_test_data():
    """Nettoie les données de test"""
    print("\n=== Nettoyage des données de test ===")
    
    # Supprimer les commandes de test
    test_orders = Order.objects.filter(order_number__startswith='TEST-MESSAGE-')
    count = test_orders.count()
    
    if count > 0:
        test_orders.delete()
        print(f"[OK] {count} commande(s) de test supprimee(s)")
    else:
        print("[OK] Aucune donnee de test a nettoyer")
    
    # Supprimer l'utilisateur de test
    try:
        user = User.objects.get(username='client_test_message')
        user.delete()
        print("[OK] Utilisateur de test supprime")
    except User.DoesNotExist:
        pass


def main():
    """Fonction principale de test"""
    print("=== Test de correction des messages sur la page contact ===")
    
    try:
        # Tests
        test1 = test_messages_not_on_contact_page()
        test2 = test_contact_messages_still_work()
        
        # Résultats
        print("\n=== Résultats des tests ===")
        print(f"Test 1 (Messages de commande masqués sur contact): {'[SUCCES]' if test1 else '[ECHEC]'}")
        print(f"Test 2 (Messages de contact fonctionnent): {'[SUCCES]' if test2 else '[ECHEC]'}")
        
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
