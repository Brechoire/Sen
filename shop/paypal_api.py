# Standard library imports
import base64
import json
import logging

# Third-party imports
import requests

# Django imports
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

# Project imports
from .models import Order, Payment
from .services import CartService

logger = logging.getLogger(__name__)


def get_paypal_access_token():
    """Récupère un token d'accès PayPal"""
    client_id = settings.PAYPAL_CLIENT_ID
    client_secret = settings.PAYPAL_CLIENT_SECRET
    
    # URL selon le mode (sandbox ou production)
    if settings.PAYPAL_MODE == "sandbox":
        token_url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    else:
        token_url = "https://api.paypal.com/v1/oauth2/token"
    
    # Encoder les identifiants
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {"grant_type": "client_credentials"}
    
    try:
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()['access_token']
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur lors de la récupération du token PayPal: {e}")
        return None


@login_required
@require_http_methods(["POST"])
def create_paypal_order(request):
    """
    Crée une commande PayPal.
    
    Requiert une authentification utilisateur et protection CSRF standard.
    Cette fonction est appelée depuis le client JavaScript avec un token CSRF.
    """
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        amount = data.get('amount')
        
        if not order_id or not amount:
            return JsonResponse(
                {'error': 'order_id et amount requis'}, status=400
            )
        
        # Validation du montant
        try:
            amount = float(amount)
            if amount <= 0:
                return JsonResponse(
                    {'error': 'Le montant doit être positif'}, status=400
                )
        except (ValueError, TypeError):
            return JsonResponse(
                {'error': 'Montant invalide'}, status=400
            )
        
        # Récupérer la commande et vérifier qu'elle appartient à l'utilisateur
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return JsonResponse(
                {'error': 'Commande non trouvée ou non autorisée'}, 
                status=404
            )
        
        # Récupérer le token d'accès
        access_token = get_paypal_access_token()
        if not access_token:
            return JsonResponse({'error': 'Impossible de récupérer le token PayPal'}, status=500)
        
        # URL selon le mode
        if settings.PAYPAL_MODE == "sandbox":
            orders_url = "https://api.sandbox.paypal.com/v2/checkout/orders"
        else:
            orders_url = "https://api.paypal.com/v2/checkout/orders"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": str(order.id),
                "amount": {
                    "currency_code": "EUR",
                    "value": str(amount)
                },
                "description": f"Commande #{order.order_number}",
                "custom_id": str(order.id)
            }],
            "application_context": {
                "return_url": request.build_absolute_uri('/boutique/paiement/paypal/success/'),
                "cancel_url": request.build_absolute_uri('/boutique/paiement/paypal/cancel/'),
                "brand_name": "Éditions Sen",
                "landing_page": "NO_PREFERENCE",
                "user_action": "PAY_NOW"
            }
        }
        
        response = requests.post(orders_url, json=payload, headers=headers)
        response.raise_for_status()
        
        order_data = response.json()
        
        # Sauvegarder l'ID de commande PayPal
        payment = order.payment
        payment.paypal_payment_id = order_data['id']
        payment.save()
        
        # Ajouter les URLs d'approbation pour la redirection directe
        if 'links' in order_data:
            approval_link = next((link for link in order_data['links'] if link['rel'] == 'approve'), None)
            if approval_link:
                order_data['approval_url'] = approval_link['href']
        
        return JsonResponse(order_data)
        
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Données JSON invalides'}, status=400)
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur API PayPal: {e}")
        return JsonResponse({'error': 'Erreur lors de la création de la commande PayPal'}, status=500)
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return JsonResponse({'error': 'Erreur interne du serveur'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def capture_paypal_order(request):
    """
    Capture un paiement PayPal.
    
    Cette fonction est appelée par PayPal via webhook ou depuis le client
    après approbation du paiement. CSRF est désactivé car PayPal n'envoie pas
    de token CSRF, mais on valide quand même l'intégrité des données.
    
    TODO: Ajouter validation de signature PayPal pour production.
    """
    try:
        data = json.loads(request.body)
        order_id = data.get('paypal_order_id')
        
        if not order_id:
            return JsonResponse(
                {'error': 'paypal_order_id requis'}, status=400
            )
        
        # Validation basique de l'ID PayPal (format attendu)
        if not isinstance(order_id, str) or len(order_id) < 10:
            return JsonResponse(
                {'error': 'Format paypal_order_id invalide'}, status=400
            )
        
        # Récupérer le token d'accès
        access_token = get_paypal_access_token()
        if not access_token:
            return JsonResponse({'error': 'Impossible de récupérer le token PayPal'}, status=500)
        
        # URL selon le mode
        if settings.PAYPAL_MODE == "sandbox":
            capture_url = f"https://api.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
        else:
            capture_url = f"https://api.paypal.com/v2/checkout/orders/{order_id}/capture"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.post(capture_url, headers=headers)
        response.raise_for_status()
        
        capture_data = response.json()
        
        # Mettre à jour la commande si le paiement est réussi
        if capture_data['status'] == 'COMPLETED':
            # Trouver la commande par l'ID PayPal
            payment = Payment.objects.get(paypal_payment_id=order_id)
            order = payment.order
            
            # Mettre à jour le statut
            order.payment_status = 'paid'
            order.status = 'confirmed'
            order.save()
            
            payment.status = 'completed'
            payment.save()
            
            # Vider le panier de l'utilisateur après paiement réussi
            CartService.clear_cart(order.user)
            
            # Logger le paiement PayPal réussi
            security_logger = logging.getLogger('security')
            security_logger.info(
                f"Paiement PayPal capturé: order_id={order.id}, "
                f"order_number={order.order_number}, "
                f"paypal_order_id={order_id}, "
                f"user_id={order.user.id}, "
                f"user_email={order.user.email}, "
                f"amount={order.total_amount}"
            )
            
            logger.info(
                f"Paiement PayPal capturé avec succès pour la commande {order.id}"
            )
        
        return JsonResponse(capture_data)
        
    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Paiement non trouvé'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Données JSON invalides'}, status=400)
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur API PayPal: {e}")
        return JsonResponse({'error': 'Erreur lors de la capture du paiement'}, status=500)
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return JsonResponse({'error': 'Erreur interne du serveur'}, status=500)


def process_paypal_refund(refund):
    """Traite un remboursement PayPal"""
    try:
        # Récupérer le token d'accès
        access_token = get_paypal_access_token()
        if not access_token:
            return False, "Impossible de récupérer le token PayPal"
        
        # URL selon le mode
        if settings.PAYPAL_MODE == "sandbox":
            refund_url = "https://api.sandbox.paypal.com/v2/payments/captures/{capture_id}/refund"
        else:
            refund_url = "https://api.paypal.com/v2/payments/captures/{capture_id}/refund"
        
        # Récupérer l'ID de capture PayPal
        payment = refund.order.payment
        if not payment.paypal_payment_id:
            return False, "ID de paiement PayPal manquant"
        
        # Pour simplifier, on utilise l'ID de paiement comme ID de capture
        # En réalité, il faudrait récupérer l'ID de capture depuis PayPal
        capture_id = payment.paypal_payment_id
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        payload = {
            "amount": {
                "value": str(refund.amount),
                "currency_code": "EUR"
            },
            "note_to_payer": f"Remboursement pour la commande {refund.order.order_number}"
        }
        
        response = requests.post(
            refund_url.format(capture_id=capture_id),
            json=payload,
            headers=headers
        )
        
        if response.status_code == 201:
            refund_data = response.json()
            refund.paypal_refund_id = refund_data['id']
            refund.paypal_status = refund_data['status']
            refund.status = 'processed'
            refund.save()
            
            logger.info(f"Remboursement PayPal traité: {refund_data['id']}")
            return True, "Remboursement traité avec succès"
        else:
            error_data = response.json()
            error_msg = error_data.get('details', [{}])[0].get('description', 'Erreur inconnue')
            logger.error(f"Erreur remboursement PayPal: {error_msg}")
            return False, f"Erreur PayPal: {error_msg}"
            
    except Exception as e:
        logger.error(f"Erreur lors du remboursement PayPal: {e}")
        return False, f"Erreur interne: {str(e)}"
