# Standard library imports
import logging
import time

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
    
    @staticmethod
    def send_preorder_confirmation_email(order):
        """Envoie un email de confirmation de précommande"""
        subject = f"[{settings.SHOP_NAME}] Précommande confirmée - {order.order_number}"
        # Trouver la date de disponibilité prévue depuis les articles de la commande
        preorder_date = None
        for item in order.items.all():
            if item.book.is_preorder and item.book.preorder_available_date:
                preorder_date = item.book.preorder_available_date
                break
        
        return OrderEmailService._send_email(
            order,
            'preorder_confirmation',
            subject,
            {
                'preorder_date': preorder_date,
            }
        )
    
    @staticmethod
    def send_preorder_available_email(order):
        """Envoie un email lorsque la précommande est disponible"""
        subject = f"[{settings.SHOP_NAME}] Votre précommande est disponible - {order.order_number}"
        return OrderEmailService._send_email(
            order,
            'preorder_available',
            subject
        )
    
    @staticmethod
    def send_preorder_date_changed_email(order, old_date, new_date, reason=None):
        """Envoie un email lorsque la date de précommande change"""
        subject = f"[{settings.SHOP_NAME}] Modification de date de précommande - {order.order_number}"
        return OrderEmailService._send_email(
            order,
            'preorder_date_changed',
            subject,
            {
                'old_date': old_date,
                'new_date': new_date,
                'reason': reason or 'Non spécifiée',
            }
        )
    
    @staticmethod
    def send_preorder_delay_notification_email(order, new_date=None, refund_option=False):
        """Envoie un email pour informer d'un retard avec options"""
        subject = f"[{settings.SHOP_NAME}] Retard sur votre précommande - {order.order_number}"
        return OrderEmailService._send_email(
            order,
            'preorder_delay_notification',
            subject,
            {
                'new_date': new_date,
                'refund_option': refund_option,
            }
        )
    
    @staticmethod
    def send_bulk_preorder_available_emails(
            book, batch_size=None, delay_between_batches=None):
        """
        Envoie des emails groupés pour notifier que la précommande est disponible.
        Gère les lots et délais pour respecter les limites Gmail.

        Args:
            book: Instance de Book
            batch_size: Nombre d'emails par lot (défaut: depuis settings)
            delay_between_batches: Délai en secondes entre les lots
                (défaut: depuis settings)

        Returns:
            dict avec total_orders, emails_sent, emails_failed, errors
        """
        from shop.models import Order
        
        if batch_size is None:
            batch_size = getattr(settings, 'PREORDER_EMAIL_BATCH_SIZE', 10)
        if delay_between_batches is None:
            delay = getattr(
                settings, 'PREORDER_EMAIL_DELAY_BETWEEN_BATCHES', 10)
            delay_between_batches = delay

        # Récupérer toutes les précommandes pour ce livre
        preorder_orders = Order.objects.filter(
            is_preorder=True,
            items__book=book
        ).distinct().order_by('created_at')

        total_orders = preorder_orders.count()
        emails_sent = 0
        emails_failed = 0
        errors = []

        logger.info(
            f"Début de l'envoi groupé pour le livre {book.title}: "
            f"{total_orders} précommandes à notifier"
        )
        
        # Traiter par lots
        for i in range(0, total_orders, batch_size):
            batch = preorder_orders[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_orders + batch_size - 1) // batch_size

            logger.info(
                f"Traitement du lot {batch_num}/{total_batches} "
                f"({len(batch)} commandes)"
            )
            
            # Envoyer les emails du lot
            for order in batch:
                try:
                    OrderEmailService.send_preorder_available_email(order)
                    emails_sent += 1
                except Exception as e:
                    emails_failed += 1
                    error_msg = f"Erreur pour la commande {order.order_number}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg, exc_info=True)
            
            # Attendre entre les lots (sauf pour le dernier)
            if i + batch_size < total_orders:
                logger.info(
                    f"Pause de {delay_between_batches} secondes "
                    f"avant le prochain lot..."
                )
                time.sleep(delay_between_batches)

        logger.info(
            f"Envoi groupé terminé pour {book.title}: "
            f"{emails_sent} envoyés, {emails_failed} échecs "
            f"sur {total_orders} total"
        )
        
        return {
            'total_orders': total_orders,
            'emails_sent': emails_sent,
            'emails_failed': emails_failed,
            'errors': errors,
        }

