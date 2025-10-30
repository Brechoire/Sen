from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.core.management import call_command
from shop.models import Order
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def check_expired_orders_on_order_creation(sender, instance, created, **kwargs):
    """
    Vérifie les commandes expirées lorsqu'une nouvelle commande est créée.
    Ceci permet de nettoyer les commandes expirées de manière périodique.
    """
    if created:
        # Vérifier les commandes expirées en arrière-plan
        try:
            # Exécuter la commande d'annulation des commandes expirées
            call_command('cancel_expired_orders', verbosity=0)
        except Exception as e:
            logger.error(f'Erreur lors de la vérification des commandes expirées: {e}')


def check_expired_orders_manually():
    """
    Fonction utilitaire pour vérifier manuellement les commandes expirées.
    Peut être appelée depuis une vue ou un autre signal.
    """
    try:
        call_command('cancel_expired_orders', verbosity=0)
        logger.info('Vérification des commandes expirées effectuée')
    except Exception as e:
        logger.error(f'Erreur lors de la vérification manuelle des commandes expirées: {e}')






