from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from shop.models import Order, Book
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Détecte les précommandes en retard et envoie des alertes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Nombre de jours de retard avant alerte (défaut: 7)',
        )
        parser.add_argument(
            '--notify-customers',
            action='store_true',
            help='Envoie également des emails aux clients concernés',
        )

    def handle(self, *args, **options):
        days = options['days']
        notify_customers = options['notify_customers']
        today = timezone.now().date()
        cutoff_date = today - timedelta(days=days)
        
        # Trouver les précommandes avec date dépassée
        delayed_orders = Order.objects.filter(
            is_preorder=True,
            items__book__is_preorder=True,
            items__book__preorder_available_date__lt=cutoff_date
        ).distinct()
        
        count = delayed_orders.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Aucune précommande en retard trouvée.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(
                f'⚠ Trouvé {count} précommande(s) en retard de plus de {days} jour(s)'
            )
        )
        
        # Grouper par livre
        delayed_books = {}
        for order in delayed_orders:
            for item in order.items.filter(book__is_preorder=True):
                book = item.book
                if book.id not in delayed_books:
                    delayed_books[book.id] = {
                        'book': book,
                        'orders': []
                    }
                if order not in delayed_books[book.id]['orders']:
                    delayed_books[book.id]['orders'].append(order)
        
        # Afficher les détails
        for book_id, data in delayed_books.items():
            book = data['book']
            orders = data['orders']
            delay_days = (today - book.preorder_available_date).days if book.preorder_available_date else 0
            
            self.stdout.write(
                f'\n📚 {book.title}:'
            )
            self.stdout.write(
                f'   Date prévue: {book.preorder_available_date.strftime("%d/%m/%Y") if book.preorder_available_date else "Non définie"}'
            )
            self.stdout.write(
                f'   Retard: {delay_days} jour(s)'
            )
            self.stdout.write(
                f'   Précommandes affectées: {len(orders)}'
            )
        
        # Envoyer une alerte à l'administrateur
        try:
            admin_email = settings.CONTACT_EMAIL or settings.SHOP_EMAIL
            subject = f'[Alerte] {count} précommande(s) en retard'
            message = f"""
Bonjour,

{count} précommande(s) sont en retard de plus de {days} jour(s).

Livres concernés:
"""
            for book_id, data in delayed_books.items():
                book = data['book']
                delay_days = (today - book.preorder_available_date).days if book.preorder_available_date else 0
                message += f"- {book.title}: {len(data['orders'])} précommande(s), retard de {delay_days} jour(s)\n"
            
            message += "\nVeuillez prendre les mesures nécessaires (nouvelle date ou remboursement)."
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [admin_email],
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Alerte envoyée à {admin_email}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Erreur envoi alerte admin: {e}')
            )
            logger.error(f'Erreur envoi alerte précommandes en retard: {e}')
        
        # Optionnellement, notifier les clients
        if notify_customers:
            from shop.services.email_service import OrderEmailService
            
            notified = 0
            for order in delayed_orders:
                try:
                    # Trouver la nouvelle date proposée (ou None)
                    new_date = None
                    for item in order.items.filter(book__is_preorder=True):
                        if item.book.preorder_available_date:
                            # Utiliser la date la plus récente
                            if new_date is None or item.book.preorder_available_date > new_date:
                                new_date = item.book.preorder_available_date
                    
                    OrderEmailService.send_preorder_delay_notification_email(
                        order,
                        new_date=new_date,
                        refund_option=True
                    )
                    notified += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Erreur notification client {order.order_number}: {e}'
                        )
                    )
                    logger.error(f'Erreur notification retard {order.order_number}: {e}')
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ {notified} client(s) notifié(s)')
            )



