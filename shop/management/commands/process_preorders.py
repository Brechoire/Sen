from django.core.management.base import BaseCommand
from django.utils import timezone
from shop.models import Book, Order, OrderItem
from shop.services.email_service import OrderEmailService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Convertit automatiquement les précommandes en commandes normales quand les livres deviennent disponibles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les précommandes qui seraient converties sans les convertir réellement',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today = timezone.now().date()
        
        # Trouver tous les livres en précommande dont la date est arrivée
        available_books = Book.objects.filter(
            is_preorder=True,
            preorder_available_date__lte=today
        )
        
        if not available_books.exists():
            self.stdout.write(
                self.style.SUCCESS('Aucun livre en précommande à convertir.')
            )
            return
        
        total_books = available_books.count()
        self.stdout.write(
            f'{"[DRY RUN] " if dry_run else ""}Trouvé {total_books} livre(s) à convertir'
        )
        
        total_orders_converted = 0
        total_emails_sent = 0
        
        for book in available_books:
            self.stdout.write(
                f'\n{"[DRY RUN] " if dry_run else ""}Traitement du livre: {book.title}'
            )
            
            # Trouver toutes les précommandes pour ce livre, triées par date de commande
            preorder_orders = Order.objects.filter(
                is_preorder=True,
                items__book=book
            ).distinct().order_by('created_at')
            
            order_count = preorder_orders.count()
            self.stdout.write(
                f'  → {order_count} précommande(s) trouvée(s)'
            )
            
            if order_count == 0:
                continue
            
            if not dry_run:
                # Convertir les précommandes en commandes normales
                converted = 0
                for order in preorder_orders:
                    try:
                        # Marquer comme non-précommande
                        order.is_preorder = False
                        order.preorder_ready_date = today
                        
                        # Si la commande est encore en attente, la passer en confirmée
                        if order.status == 'pending':
                            order.status = 'confirmed'
                        
                        order.save()
                        converted += 1
                        
                        # Envoyer l'email de notification
                        try:
                            OrderEmailService.send_preorder_available_email(order)
                            total_emails_sent += 1
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  ⚠ Erreur envoi email pour {order.order_number}: {e}'
                                )
                            )
                            logger.error(f'Erreur envoi email précommande {order.order_number}: {e}')
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ✗ Erreur conversion commande {order.order_number}: {e}'
                            )
                        )
                        logger.error(f'Erreur conversion précommande {order.order_number}: {e}')
                
                # Mettre à jour le livre
                book.is_preorder = False
                # Si le stock n'est pas défini, le mettre à jour avec les précommandes
                if book.stock_quantity == 0:
                    book.stock_quantity = book.preorder_current_quantity
                book.save()
                
                total_orders_converted += converted
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ {converted} commande(s) convertie(s) pour {book.title}'
                    )
                )
            else:
                # Dry run : juste afficher
                for order in preorder_orders[:5]:  # Afficher les 5 premières
                    self.stdout.write(
                        f'  → Commande {order.order_number} (créée le {order.created_at.strftime("%d/%m/%Y")})'
                    )
                if order_count > 5:
                    self.stdout.write(f'  → ... et {order_count - 5} autre(s)')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] {total_books} livre(s) et leurs précommandes seraient convertis'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Conversion terminée: {total_orders_converted} commande(s) convertie(s), '
                    f'{total_emails_sent} email(s) envoyé(s)'
                )
            )

