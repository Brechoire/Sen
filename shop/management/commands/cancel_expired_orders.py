from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from shop.models import Order, OrderStatusHistory
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Annule automatiquement les commandes en attente de paiement depuis plus de 24h'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les commandes qui seraient annulées sans les annuler réellement',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Nombre d\'heures après lesquelles annuler les commandes (défaut: 24)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        hours = options['hours']
        
        # Calculer la date limite
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Trouver les commandes en attente depuis plus de X heures
        expired_orders = Order.objects.filter(
            status='pending',
            payment_status='pending',
            created_at__lt=cutoff_time
        )
        
        count = expired_orders.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Aucune commande expirée trouvée.')
            )
            return
        
        self.stdout.write(
            f'{"[DRY RUN] " if dry_run else ""}Trouvé {count} commande(s) expirée(s) depuis plus de {hours}h'
        )
        
        cancelled_count = 0
        
        for order in expired_orders:
            self.stdout.write(
                f'{"[DRY RUN] " if dry_run else ""}Annulation de la commande {order.order_number} '
                f'(créée le {order.created_at.strftime("%d/%m/%Y %H:%M")})'
            )
            
            if not dry_run:
                try:
                    # Annuler la commande
                    order.update_status(
                        new_status='cancelled',
                        admin_notes=f'Annulation automatique - Paiement en attente depuis plus de {hours}h',
                        changed_by=None  # Système automatique
                    )
                    
                    # Marquer le paiement comme échoué
                    order.payment_status = 'failed'
                    order.save()
                    
                    cancelled_count += 1
                    
                    logger.info(f'Commande {order.order_number} annulée automatiquement (expirée)')
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Erreur lors de l\'annulation de la commande {order.order_number}: {e}'
                        )
                    )
                    logger.error(f'Erreur annulation commande {order.order_number}: {e}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] {count} commande(s) seraient annulée(s)'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'{cancelled_count} commande(s) annulée(s) avec succès'
                )
            )






