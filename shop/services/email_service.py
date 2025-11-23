# Standard library imports
import logging

# Django imports
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class OrderEmailService:
    """Service pour l'envoi d'emails liés aux commandes"""
    
    @staticmethod
    def _send_email(order, template_name, subject, context=None):
        """
        Méthode utilitaire pour envoyer un email HTML
        
        Args:
            order: Instance de Order
            template_name: Nom du template (sans extension)
            subject: Sujet de l'email
            context: Contexte additionnel pour le template
        """
        try:
            # Contexte de base pour tous les emails
            # Construire l'URL de la commande (sera complété dans les templates si nécessaire)
            base_context = {
                'order': order,
                'shop_name': settings.SHOP_NAME,
                'shop_email': settings.SHOP_EMAIL,
                'shop_phone': getattr(settings, 'SHOP_PHONE', ''),
            }
            
            # Fusionner avec le contexte additionnel
            if context:
                base_context.update(context)
            
            # Rendre le template HTML
            html_content = render_to_string(
                f'shop/emails/{template_name}.html',
                base_context
            )
            
            # Créer l'email avec version texte simple
            text_content = f"Votre commande {order.order_number} - {subject}"
            
            # Créer l'email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.user.email],
            )
            
            # Attacher la version HTML
            email.attach_alternative(html_content, "text/html")
            
            # Envoyer l'email
            email.send(fail_silently=False)
            
            logger.info(
                f"Email '{template_name}' envoyé avec succès pour la commande {order.order_number} "
                f"à {order.user.email}"
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"Erreur lors de l'envoi de l'email '{template_name}' pour la commande {order.order_number}: {e}",
                exc_info=True
            )
            return False
    
    @staticmethod
    def send_payment_confirmed_email(order):
        """Envoie un email de confirmation de paiement"""
        subject = f"[{settings.SHOP_NAME}] Paiement confirmé - Commande {order.order_number}"
        payment_method = 'Non spécifié'
        if hasattr(order, 'payment') and order.payment:
            payment_method = order.payment.get_payment_method_display()
        return OrderEmailService._send_email(
            order,
            'payment_confirmed',
            subject,
            {
                'payment_method': payment_method,
                'amount': order.total_amount,
            }
        )
    
    @staticmethod
    def send_order_confirmed_email(order):
        """Envoie un email de confirmation de commande"""
        subject = f"[{settings.SHOP_NAME}] Commande confirmée - {order.order_number}"
        return OrderEmailService._send_email(
            order,
            'order_confirmed',
            subject
        )
    
    @staticmethod
    def send_processing_email(order):
        """Envoie un email lorsque la commande est en cours de traitement"""
        subject = f"[{settings.SHOP_NAME}] Votre commande {order.order_number} est en cours de traitement"
        return OrderEmailService._send_email(
            order,
            'processing',
            subject
        )
    
    @staticmethod
    def send_shipped_email(order, tracking_number=None):
        """Envoie un email lorsque la commande est expédiée"""
        subject = f"[{settings.SHOP_NAME}] Votre commande {order.order_number} a été expédiée"
        return OrderEmailService._send_email(
            order,
            'shipped',
            subject,
            {
                'tracking_number': tracking_number or order.tracking_number,
                'carrier': order.carrier,
                'estimated_delivery': order.estimated_delivery,
            }
        )
    
    @staticmethod
    def send_delivered_email(order):
        """Envoie un email lorsque la commande est livrée"""
        subject = f"[{settings.SHOP_NAME}] Votre commande {order.order_number} a été livrée"
        return OrderEmailService._send_email(
            order,
            'delivered',
            subject,
            {
                'delivery_date': order.delivered_date or order.actual_delivery,
            }
        )
    
    @staticmethod
    def send_cancelled_email(order, reason=None):
        """Envoie un email lorsque la commande est annulée"""
        subject = f"[{settings.SHOP_NAME}] Commande annulée - {order.order_number}"
        return OrderEmailService._send_email(
            order,
            'cancelled',
            subject,
            {
                'reason': reason or order.admin_notes or 'Non spécifiée',
            }
        )
    
    @staticmethod
    def send_refunded_email(order):
        """Envoie un email lorsque la commande est remboursée"""
        subject = f"[{settings.SHOP_NAME}] Remboursement effectué - Commande {order.order_number}"
        return OrderEmailService._send_email(
            order,
            'refunded',
            subject,
            {
                'refund_amount': order.total_amount,
            }
        )

