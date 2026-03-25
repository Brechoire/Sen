"""Handlers pour les événements webhook PayPal"""

import logging
from django.utils import timezone

from .models import Order, Payment, Refund
from .services import CartService
from .services.email_service import OrderEmailService

logger = logging.getLogger(__name__)


def extract_order_id_from_paypal_payload(payload):
    """
    Extrait l'ID de commande interne à partir du payload PayPal.

    PayPal ne connait pas notre order_id, donc on l'a passé dans
    l'invoice_id ou purchase_units[0].invoice_id
    """
    try:
        resource = payload.get("resource", {})

        # Essayer de récupérer depuis invoice_id
        invoice_id = resource.get("invoice_id")
        if invoice_id:
            # L'invoice_id est au format "ORDER-12345" ou juste "12345"
            if invoice_id.startswith("ORDER-"):
                return int(invoice_id.replace("ORDER-", ""))
            try:
                return int(invoice_id)
            except ValueError:
                pass

        # Essayer depuis purchase_units
        purchase_units = resource.get("purchase_units", [])
        if purchase_units:
            invoice_id = purchase_units[0].get("invoice_id")
            if invoice_id:
                if invoice_id.startswith("ORDER-"):
                    return int(invoice_id.replace("ORDER-", ""))
                try:
                    return int(invoice_id)
                except ValueError:
                    pass

        # Essayer depuis custom_id
        custom_id = resource.get("custom_id")
        if custom_id:
            try:
                return int(custom_id)
            except ValueError:
                pass

        # Chercher dans purchase_units custom_id
        if purchase_units:
            custom_id = purchase_units[0].get("custom_id")
            if custom_id:
                try:
                    return int(custom_id)
                except ValueError:
                    pass

        return None

    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de l'order_id: {e}")
        return None


def handle_checkout_order_completed(payload):
    """
    Gère l'événement CHECKOUT.ORDER.COMPLETED

    Args:
        payload: Données de l'événement PayPal

    Returns:
        Order: La commande mise à jour, ou None si erreur
    """
    try:
        resource = payload.get("resource", {})
        paypal_order_id = resource.get("id")

        # Extraire notre order_id
        order_id = extract_order_id_from_paypal_payload(payload)

        if not order_id:
            logger.error(
                f"Impossible d'extraire l'order_id du payload PayPal: {paypal_order_id}"
            )
            return None

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            logger.error(f"Commande {order_id} non trouvée")
            return None

        # Vérifier si la commande est déjà confirmée
        if order.status == "confirmed":
            logger.info(f"Commande {order_id} déjà confirmée, ignorée")
            return order

        # Vérifier si la commande est annulée
        if order.status == "cancelled":
            logger.warning(
                f"Commande {order_id} est annulée, paiement reçu mais ignoré"
            )
            return None

        # Mettre à jour le statut de la commande
        order.status = "confirmed"
        order.payment_status = "paid"
        order.save(update_fields=["status", "payment_status", "updated_at"])

        # Mettre à jour ou créer le paiement
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                "payment_method": "paypal",
                "amount": order.total_amount,
                "currency": "EUR",
                "status": "completed",
                "paypal_payment_id": paypal_order_id,
                "paypal_payer_id": resource.get("payer", {}).get("payer_id", ""),
                "completed_at": timezone.now(),
            },
        )

        if not created:
            payment.status = "completed"
            payment.paypal_payment_id = paypal_order_id
            payment.paypal_payer_id = resource.get("payer", {}).get("payer_id", "")
            payment.completed_at = timezone.now()
            payment.save(
                update_fields=[
                    "status",
                    "paypal_payment_id",
                    "paypal_payer_id",
                    "completed_at",
                ]
            )

        # Vider le panier de l'utilisateur si connecté
        if order.user:
            try:
                CartService.clear_cart(order.user)
                logger.info(f"Panier vidé pour l'utilisateur {order.user.id}")
            except Exception as e:
                logger.error(f"Erreur lors du vidage du panier: {e}")

        # Envoyer l'email de confirmation
        try:
            OrderEmailService.send_payment_confirmed_email(order)
            logger.info(f"Email de confirmation envoyé pour la commande {order.id}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {e}")

        logger.info(
            f"Commande {order.id} confirmée avec succès via webhook (PayPal: {paypal_order_id})"
        )
        return order

    except Exception as e:
        logger.error(f"Erreur lors du traitement de CHECKOUT.ORDER.COMPLETED: {e}")
        return None


def handle_payment_capture_refunded(payload):
    """
    Gère l'événement PAYMENT.CAPTURE.REFUNDED

    Args:
        payload: Données de l'événement PayPal

    Returns:
        bool: True si traité avec succès
    """
    try:
        resource = payload.get("resource", {})
        paypal_refund_id = resource.get("id")
        amount = resource.get("amount", {})
        currency = amount.get("currency_code", "EUR")
        value = amount.get("value", "0")

        # Récupérer le refund_id depuis les liens
        links = resource.get("links", [])
        parent_payment_id = None
        for link in links:
            if link.get("rel") == "up":
                # Extraction de l'ID de capture depuis l'URL
                href = link.get("href", "")
                if "/captures/" in href:
                    parent_payment_id = href.split("/captures/")[-1].split("/")[0]
                    break

        if not parent_payment_id:
            logger.error(
                "Impossible de trouver l'ID de capture parent dans le webhook de remboursement"
            )
            return False

        # Chercher le paiement correspondant
        try:
            payment = Payment.objects.get(paypal_payment_id=parent_payment_id)
            order = payment.order
        except Payment.DoesNotExist:
            logger.error(f"Paiement PayPal {parent_payment_id} non trouvé")
            return False

        # Mettre à jour ou créer le remboursement
        refund, created = Refund.objects.get_or_create(
            order=order,
            paypal_refund_id=paypal_refund_id,
            defaults={
                "amount": value,
                "status": "completed",
                "reason": "customer_request",  # Par défaut
                "paypal_status": resource.get("status", "COMPLETED"),
            },
        )

        if not created:
            refund.status = "completed"
            refund.paypal_status = resource.get("status", "COMPLETED")
            refund.save(update_fields=["status", "paypal_status"])

        # Mettre à jour le statut du paiement
        payment.status = "refunded"
        payment.save(update_fields=["status"])

        # Mettre à jour le statut de la commande
        order.payment_status = "refunded"
        order.save(update_fields=["payment_status"])

        logger.info(
            f"Remboursement {paypal_refund_id} traité pour la commande {order.id}"
        )
        return True

    except Exception as e:
        logger.error(f"Erreur lors du traitement de PAYMENT.CAPTURE.REFUNDED: {e}")
        return False
