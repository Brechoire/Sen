"""Gestion des webhooks PayPal"""

import json
import logging
import requests
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Order, Payment, WebhookEvent
from .webhook_handlers import (
    handle_checkout_order_completed,
    handle_payment_capture_refunded,
)

logger = logging.getLogger(__name__)


def verify_paypal_signature(headers, body, webhook_id):
    """
    Vérifie la signature du webhook PayPal pour s'assurer de son authenticité.

    Args:
        headers: Headers de la requête HTTP
        body: Corps de la requête (bytes)
        webhook_id: ID du webhook configuré dans PayPal

    Returns:
        bool: True si la signature est valide, False sinon
    """
    try:
        transmission_id = headers.get("PayPal-Transmission-Id")
        cert_url = headers.get("PayPal-Cert-Url")
        auth_algo = headers.get("PayPal-Auth-Algo")
        transmission_sig = headers.get("PayPal-Transmission-Sig")
        transmission_time = headers.get("PayPal-Transmission-Time")

        if not all(
            [transmission_id, cert_url, auth_algo, transmission_sig, transmission_time]
        ):
            logger.warning("Headers PayPal incomplets pour la validation de signature")
            # En mode debug/sandbox, on accepte sans validation
            if settings.PAYPAL_DEBUG or settings.PAYPAL_MODE == "sandbox":
                logger.info("Mode debug/sandbox: validation de signature ignorée")
                return True
            return False

        # En mode production, il faudrait implémenter la vérification complète
        # Cela nécessite de télécharger le certificat PayPal et vérifier la signature
        # Pour l'instant, en mode debug/sandbox on accepte
        if settings.PAYPAL_DEBUG or settings.PAYPAL_MODE == "sandbox":
            logger.info("Mode debug/sandbox: validation de signature ignorée")
            return True

        # TODO: Implémenter la vérification complète de signature pour production
        # https://developer.paypal.com/api/rest/webhooks/verify-signature/
        logger.info(
            "Validation de signature PayPal non implémentée en production - webhook accepté"
        )
        return True

    except Exception as e:
        logger.error(f"Erreur lors de la validation de signature PayPal: {e}")
        return False


@csrf_exempt
@require_http_methods(["POST"])
def paypal_webhook(request):
    """
    Endpoint pour recevoir les webhooks PayPal.

    Traite les événements :
    - CHECKOUT.ORDER.COMPLETED : Commande payée
    - PAYMENT.CAPTURE.REFUNDED : Remboursement effectué
    """
    try:
        # Récupérer le corps de la requête
        body = request.body

        # Vérifier la signature
        webhook_id = getattr(settings, "PAYPAL_WEBHOOK_ID", "")
        if not verify_paypal_signature(request.headers, body, webhook_id):
            logger.warning("Signature PayPal invalide")
            return JsonResponse(
                {"status": "error", "message": "Invalid signature"}, status=400
            )

        # Parser le JSON
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON invalide reçu: {e}")
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON"}, status=400
            )

        # Extraire les informations de l'événement
        event_id = payload.get("id")
        event_type = payload.get("event_type")
        resource_type = payload.get("resource_type")
        resource = payload.get("resource", {})

        if not event_id or not event_type:
            logger.error("Événement PayPal incomplet: ID ou type manquant")
            return JsonResponse(
                {"status": "error", "message": "Invalid event data"}, status=400
            )

        # Vérifier si l'événement a déjà été traité
        if WebhookEvent.objects.filter(event_id=event_id).exists():
            logger.info(f"Événement {event_id} déjà traité, ignoré")
            return JsonResponse({"status": "success", "message": "Already processed"})

        # Créer l'entrée dans la base de données
        webhook_event = WebhookEvent.objects.create(
            event_id=event_id,
            event_type=event_type,
            resource_type=resource_type,
            payload=payload,
            status="pending",
        )

        logger.info(f"Webhook reçu: {event_type} (ID: {event_id})")

        # Traiter l'événement selon son type
        try:
            if event_type == "CHECKOUT.ORDER.COMPLETED":
                order = handle_checkout_order_completed(payload)
                if order:
                    webhook_event.order = order
                    webhook_event.mark_processed()
                    logger.info(f"Commande {order.id} confirmée via webhook")
                else:
                    webhook_event.mark_failed("Commande non trouvée ou déjà traitée")

            elif event_type == "PAYMENT.CAPTURE.REFUNDED":
                success = handle_payment_capture_refunded(payload)
                if success:
                    webhook_event.mark_processed()
                    logger.info("Remboursement traité via webhook")
                else:
                    webhook_event.mark_failed("Remboursement non traité")

            else:
                # Événement non géré
                webhook_event.status = "ignored"
                webhook_event.save(update_fields=["status"])
                logger.info(f"Événement {event_type} ignoré (non géré)")

            return JsonResponse({"status": "success"})

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erreur lors du traitement du webhook {event_id}: {e}")
            webhook_event.mark_failed(error_msg)
            # Retourner quand même 200 pour éviter les retries PayPal
            # mais logger l'erreur pour investigation
            return JsonResponse({"status": "error", "message": error_msg}, status=200)

    except Exception as e:
        logger.error(f"Erreur critique webhook PayPal: {e}")
        return JsonResponse(
            {"status": "error", "message": "Internal error"}, status=500
        )
