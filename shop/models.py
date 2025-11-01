from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum
from ckeditor.fields import RichTextField
from author.models import Author
from app.utils import get_upload_path


class Category(models.Model):
    """Modèle pour les catégories de livres"""
    name = models.CharField(max_length=100, verbose_name="Nom")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('shop:category_detail', kwargs={'slug': self.slug})


class Book(models.Model):
    """Modèle pour les livres de la boutique"""
    
    # Informations de base
    title = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    subtitle = models.CharField(max_length=300, blank=True, verbose_name="Sous-titre")
    
    # Relation avec l'auteur
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books', verbose_name="Auteur")
    
    # Description et contenu
    description = RichTextField(verbose_name="Description")
    short_description = models.TextField(max_length=500, blank=True, verbose_name="Description courte")
    excerpt = models.TextField(blank=True, verbose_name="Extrait")
    
    # Informations éditoriales
    isbn = models.CharField(max_length=20, unique=True, verbose_name="ISBN")
    publication_date = models.DateField(verbose_name="Date de publication")
    pages = models.PositiveIntegerField(verbose_name="Nombre de pages")
    language = models.CharField(max_length=50, default="Français", verbose_name="Langue")
    format_choices = [
        ('poche', 'Poche'),
        ('broche', 'Broché'),
        ('relié', 'Relié'),
        ('ebook', 'E-book'),
        ('audio', 'Livre audio'),
    ]
    format = models.CharField(max_length=20, choices=format_choices, default='broche', verbose_name="Format")
    
    # Images
    cover_image = models.ImageField(
        upload_to=lambda instance, filename: get_upload_path(instance, filename, 'books/covers/'),
        verbose_name="Image de couverture"
    )
    back_cover_image = models.ImageField(
        upload_to=lambda instance, filename: get_upload_path(instance, filename, 'books/backs/'),
        blank=True, null=True,
        verbose_name="Image de quatrième de couverture"
    )
    
    # Prix et disponibilité
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Prix")
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Prix de promotion")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Quantité en stock")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")
    is_featured = models.BooleanField(default=False, verbose_name="Mis en avant")
    is_bestseller = models.BooleanField(default=False, verbose_name="Best-seller")
    
    # Catégorie
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='books', verbose_name="Catégorie")
    
    # Mots-clés pour le SEO
    meta_title = models.CharField(max_length=200, blank=True, verbose_name="Titre SEO")
    meta_description = models.TextField(max_length=300, blank=True, verbose_name="Description SEO")
    keywords = models.TextField(blank=True, verbose_name="Mots-clés")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Livre"
        verbose_name_plural = "Livres"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_available', 'is_featured']),
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['author', 'is_available']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.author.display_name}"
    
    def get_absolute_url(self):
        return reverse('shop:book_detail', kwargs={'slug': self.slug})
    
    @property
    def display_price(self):
        """Retourne le prix d'affichage (prix de promotion si disponible)"""
        return self.discount_price if self.discount_price else self.price
    
    @property
    def discount_percentage(self):
        """Calcule le pourcentage de réduction"""
        if self.discount_price and self.price:
            return round((1 - self.discount_price / self.price) * 100)
        return 0
    
    @property
    def is_on_sale(self):
        """Vérifie si le livre est en promotion"""
        return self.discount_price is not None and self.discount_price < self.price
    
    @property
    def in_stock(self):
        """Vérifie si le livre est en stock"""
        return self.stock_quantity > 0 and self.is_available
    
    def get_meta_title(self):
        """Retourne le titre SEO ou le titre par défaut"""
        return self.meta_title or f"{self.title} - {self.author.display_name} | Éditions Sen"
    
    def get_meta_description(self):
        """Retourne la description SEO ou la description courte"""
        return self.meta_description or self.short_description or self.description[:200] + "..."


class BookImage(models.Model):
    """Modèle pour les images supplémentaires des livres"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='images', verbose_name="Livre")
    image = models.ImageField(
        upload_to=lambda instance, filename: get_upload_path(instance, filename, 'books/gallery/'),
        verbose_name="Image"
    )
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="Texte alternatif")
    is_main = models.BooleanField(default=False, verbose_name="Image principale")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    
    class Meta:
        verbose_name = "Image de livre"
        verbose_name_plural = "Images de livres"
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"Image de {self.book.title}"


class Review(models.Model):
    """Modèle pour les avis clients"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews', verbose_name="Livre")
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name="Utilisateur")
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name="Note")
    title = models.CharField(max_length=200, verbose_name="Titre de l'avis")
    comment = models.TextField(verbose_name="Commentaire")
    is_approved = models.BooleanField(default=False, verbose_name="Approuvé")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ['-created_at']
        unique_together = ['book', 'user']
    
    def __str__(self):
        return f"Avis de {self.user.username} sur {self.book.title}"


class Cart(models.Model):
    """Modèle pour le panier d'achat"""
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='carts', null=True, blank=True, verbose_name="Utilisateur")
    session_key = models.CharField(max_length=40, blank=True, null=True, verbose_name="Clé de session")
    session_data = models.JSONField(default=dict, blank=True, verbose_name="Données de session")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"
        ordering = ['-created_at']
    
    def __str__(self):
        if self.user:
            return f"Panier de {self.user.username}"
        return f"Panier session {self.session_key}"
    
    @property
    def total_items(self):
        """Retourne le nombre total d'articles dans le panier"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        """Retourne le prix total du panier"""
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_discount(self):
        """Retourne le total des réductions"""
        return sum(item.discount_amount for item in self.items.all())
    
    @property
    def final_price(self):
        """Retourne le prix final après réductions"""
        return self.total_price - self.total_discount
    
    def clear(self):
        """Vide le panier"""
        self.items.all().delete()


class CartItem(models.Model):
    """Modèle pour les articles du panier"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Panier")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Livre")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    
    class Meta:
        verbose_name = "Article du panier"
        verbose_name_plural = "Articles du panier"
        ordering = ['-added_at']
        unique_together = ['cart', 'book']
    
    def __str__(self):
        return f"{self.quantity}x {self.book.title}"
    
    @property
    def unit_price(self):
        """Retourne le prix unitaire (avec promotion si applicable)"""
        return self.book.display_price
    
    @property
    def total_price(self):
        """Retourne le prix total pour cette quantité"""
        return self.unit_price * self.quantity
    
    @property
    def discount_amount(self):
        """Retourne le montant de la réduction"""
        if self.book.is_on_sale:
            return (self.book.price - self.book.discount_price) * self.quantity
        return 0
    
    @property
    def savings(self):
        """Retourne les économies réalisées"""
        return self.discount_amount


class Order(models.Model):
    """Modèle pour les commandes"""
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours de traitement'),
        ('shipped', 'Expédiée'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
        ('refunded', 'Remboursée'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payée'),
        ('failed', 'Échouée'),
        ('refunded', 'Remboursée'),
    ]
    
    # Informations de base
    order_number = models.CharField(max_length=20, unique=True, verbose_name="Numéro de commande")
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='orders', verbose_name="Utilisateur")
    
    # Statuts
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="Statut du paiement")
    
    # Informations de livraison
    shipping_first_name = models.CharField(max_length=50, verbose_name="Prénom")
    shipping_last_name = models.CharField(max_length=50, verbose_name="Nom")
    shipping_address = models.TextField(verbose_name="Adresse")
    shipping_city = models.CharField(max_length=100, verbose_name="Ville")
    shipping_postal_code = models.CharField(max_length=20, verbose_name="Code postal")
    shipping_country = models.CharField(max_length=100, default="France", verbose_name="Pays")
    shipping_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    
    # Informations de facturation (optionnel, peut être différent de la livraison)
    billing_first_name = models.CharField(max_length=50, blank=True, verbose_name="Prénom facturation")
    billing_last_name = models.CharField(max_length=50, blank=True, verbose_name="Nom facturation")
    billing_address = models.TextField(blank=True, verbose_name="Adresse facturation")
    billing_city = models.CharField(max_length=100, blank=True, verbose_name="Ville facturation")
    billing_postal_code = models.CharField(max_length=20, blank=True, verbose_name="Code postal facturation")
    billing_country = models.CharField(max_length=100, default="France", verbose_name="Pays facturation")
    
    # Prix
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sous-total")
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="Frais de port")
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="Montant des taxes")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant total")
    
    # Suivi de livraison
    tracking_number = models.CharField(max_length=100, blank=True, verbose_name="Numéro de suivi")
    carrier = models.CharField(max_length=100, blank=True, verbose_name="Transporteur")
    estimated_delivery = models.DateField(null=True, blank=True, verbose_name="Date de livraison estimée")
    actual_delivery = models.DateField(null=True, blank=True, verbose_name="Date de livraison effective")
    
    # Dates de changement de statut
    processing_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de traitement")
    shipped_date = models.DateTimeField(null=True, blank=True, verbose_name="Date d'expédition")
    delivered_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de livraison")
    cancelled_date = models.DateTimeField(null=True, blank=True, verbose_name="Date d'annulation")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    notes = models.TextField(blank=True, verbose_name="Notes")
    admin_notes = models.TextField(blank=True, verbose_name="Notes administrateur")
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Commande {self.order_number} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Génère un numéro de commande unique"""
        import uuid
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    @property
    def full_name(self):
        """Retourne le nom complet du client"""
        return f"{self.shipping_first_name} {self.shipping_last_name}"
    
    @property
    def is_paid(self):
        """Vérifie si la commande est payée"""
        return self.payment_status == 'paid'
    
    @property
    def can_be_cancelled(self):
        """Vérifie si la commande peut être annulée"""
        return self.status in ['pending', 'processing']
    
    def update_status(self, new_status, admin_notes=None, changed_by=None):
        """Met à jour le statut de la commande et enregistre la date"""
        from django.utils import timezone
        
        old_status = self.status
        self.status = new_status
        
        # Enregistrer la date de changement de statut
        now = timezone.now()
        if new_status == 'processing' and not self.processing_date:
            self.processing_date = now
        elif new_status == 'shipped' and not self.shipped_date:
            self.shipped_date = now
        elif new_status == 'delivered' and not self.delivered_date:
            self.delivered_date = now
            self.actual_delivery = now.date()
        elif new_status == 'cancelled' and not self.cancelled_date:
            self.cancelled_date = now
        
        # Ajouter des notes administrateur si fournies
        if admin_notes:
            if self.admin_notes:
                self.admin_notes += f"\n[{now.strftime('%d/%m/%Y %H:%M')}] {admin_notes}"
            else:
                self.admin_notes = f"[{now.strftime('%d/%m/%Y %H:%M')}] {admin_notes}"
        
        self.save()
        
        # Enregistrer dans l'historique
        OrderStatusHistory.objects.create(
            order=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            notes=admin_notes or ""
        )
        
        return old_status, new_status
    
    def get_status_display_with_date(self):
        """Retourne le statut avec la date de changement"""
        status_display = self.get_status_display()
        
        if self.status == 'processing' and self.processing_date:
            return f"{status_display} (depuis le {self.processing_date.strftime('%d/%m/%Y')})"
        elif self.status == 'shipped' and self.shipped_date:
            return f"{status_display} (depuis le {self.shipped_date.strftime('%d/%m/%Y')})"
        elif self.status == 'delivered' and self.delivered_date:
            return f"{status_display} (le {self.delivered_date.strftime('%d/%m/%Y')})"
        elif self.status == 'cancelled' and self.cancelled_date:
            return f"{status_display} (le {self.cancelled_date.strftime('%d/%m/%Y')})"
        
        return status_display
    
    def get_tracking_info(self):
        """Retourne les informations de suivi"""
        info = {}
        if self.tracking_number:
            info['tracking_number'] = self.tracking_number
        if self.carrier:
            info['carrier'] = self.carrier
        if self.estimated_delivery:
            info['estimated_delivery'] = self.estimated_delivery
        if self.actual_delivery:
            info['actual_delivery'] = self.actual_delivery
        return info


class OrderStatusHistory(models.Model):
    """Modèle pour l'historique des changements de statut des commandes"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history', verbose_name="Commande")
    old_status = models.CharField(max_length=20, verbose_name="Ancien statut")
    new_status = models.CharField(max_length=20, verbose_name="Nouveau statut")
    changed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Modifié par")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de changement")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Historique de statut"
        verbose_name_plural = "Historique des statuts"
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} → {self.new_status}"


class OrderItem(models.Model):
    """Modèle pour les articles d'une commande"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Commande")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Livre")
    quantity = models.PositiveIntegerField(verbose_name="Quantité")
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Prix unitaire")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix total")
    
    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"
        unique_together = ['order', 'book']
    
    def __str__(self):
        return f"{self.quantity}x {self.book.title} - {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Modèle pour les paiements"""
    
    PAYMENT_METHOD_CHOICES = [
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('bank_transfer', 'Virement bancaire'),
        ('check', 'Chèque'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
        ('refunded', 'Remboursé'),
    ]
    
    # Relations
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment', verbose_name="Commande")
    
    # Informations de paiement
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name="Méthode de paiement")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    currency = models.CharField(max_length=3, default='EUR', verbose_name="Devise")
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    
    # Informations PayPal
    paypal_payment_id = models.CharField(max_length=100, blank=True, verbose_name="ID de paiement PayPal")
    paypal_payer_id = models.CharField(max_length=100, blank=True, verbose_name="ID du payeur PayPal")
    paypal_token = models.CharField(max_length=100, blank=True, verbose_name="Token PayPal")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de finalisation")
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Paiement {self.payment_method} - {self.order.order_number}"
    
    @property
    def is_completed(self):
        """Vérifie si le paiement est terminé"""
        return self.status == 'completed'
    
    def mark_as_completed(self):
        """Marque le paiement comme terminé"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Mettre à jour le statut de la commande
        self.order.payment_status = 'paid'
        self.order.save()


class Refund(models.Model):
    """Modèle pour les remboursements"""
    
    REFUND_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('processed', 'Traité'),
        ('completed', 'Terminé'),
    ]
    
    REFUND_REASON_CHOICES = [
        ('customer_request', 'Demande du client'),
        ('defective_product', 'Produit défectueux'),
        ('wrong_item', 'Mauvais article'),
        ('not_delivered', 'Non livré'),
        ('duplicate_payment', 'Paiement en double'),
        ('other', 'Autre'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds', verbose_name="Commande")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant du remboursement")
    reason = models.CharField(max_length=50, choices=REFUND_REASON_CHOICES, verbose_name="Raison du remboursement")
    description = models.TextField(blank=True, verbose_name="Description détaillée")
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='pending', verbose_name="Statut")
    
    # Informations PayPal
    paypal_refund_id = models.CharField(max_length=100, blank=True, verbose_name="ID remboursement PayPal")
    paypal_status = models.CharField(max_length=50, blank=True, verbose_name="Statut PayPal")
    
    # Métadonnées
    requested_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name="Demandé par")
    processed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_refunds', verbose_name="Traité par")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de traitement")
    
    class Meta:
        verbose_name = "Remboursement"
        verbose_name_plural = "Remboursements"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Remboursement #{self.id} - {self.order.order_number} - {self.amount}€"
    
    @property
    def can_be_processed(self):
        """Vérifie si le remboursement peut être traité"""
        return self.status in ['pending', 'approved']
    
    @property
    def can_be_approved(self):
        """Vérifie si le remboursement peut être approuvé"""
        return self.status == 'pending'


class LoyaltyProgram(models.Model):
    """Modèle pour le programme de fidélité"""
    
    name = models.CharField(max_length=100, verbose_name="Nom du programme")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    # Conditions pour obtenir la réduction
    min_purchases = models.PositiveIntegerField(
        default=10, 
        verbose_name="Nombre minimum d'achats"
    )
    min_amount = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Montant minimum d'achat (€)"
    )
    
    # Réduction accordée
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Pourcentage'),
        ('fixed', 'Montant fixe'),
    ]
    discount_type = models.CharField(
        max_length=20, 
        choices=DISCOUNT_TYPE_CHOICES, 
        default='percentage',
        verbose_name="Type de réduction"
    )
    discount_value = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        verbose_name="Valeur de la réduction"
    )
    
    # Limites
    max_discount_amount = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Montant maximum de réduction (€)"
    )
    min_cart_amount = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Montant minimum du panier (€)"
    )
    
    # Période de validité
    valid_from = models.DateTimeField(
        default=timezone.now,
        verbose_name="Valide à partir de"
    )
    valid_until = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Valide jusqu'à"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Programme de fidélité"
        verbose_name_plural = "Programmes de fidélité"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def is_valid(self):
        """Vérifie si le programme est valide"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from > now:
            return False
        if self.valid_until and self.valid_until < now:
            return False
        return True
    
    def calculate_discount(self, cart_total):
        """Calcule la réduction pour un montant de panier donné"""
        if not self.is_valid or cart_total < self.min_cart_amount:
            return 0
        
        if self.discount_type == 'percentage':
            discount = (cart_total * self.discount_value) / 100
        else:  # fixed
            discount = self.discount_value
        
        # Appliquer la limite maximale si définie
        if self.max_discount_amount:
            discount = min(discount, self.max_discount_amount)
        
        return discount


class PromoCode(models.Model):
    """Modèle pour les codes promo"""
    
    # Informations de base
    code = models.CharField(max_length=50, unique=True, verbose_name="Code promo")
    name = models.CharField(max_length=100, verbose_name="Nom du code")
    description = models.TextField(blank=True, verbose_name="Description")
    
    # Type de réduction
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Pourcentage'),
        ('fixed', 'Montant fixe'),
        ('free_shipping', 'Livraison gratuite'),
    ]
    discount_type = models.CharField(
        max_length=20, 
        choices=DISCOUNT_TYPE_CHOICES, 
        default='percentage',
        verbose_name="Type de réduction"
    )
    discount_value = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valeur de la réduction"
    )
    
    # Limites
    max_discount_amount = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Montant maximum de réduction (€)"
    )
    min_cart_amount = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Montant minimum du panier (€)"
    )
    
    # Limites d'utilisation
    max_uses = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name="Nombre maximum d'utilisations"
    )
    max_uses_per_user = models.PositiveIntegerField(
        default=1,
        verbose_name="Utilisations maximum par utilisateur"
    )
    
    # Période de validité
    valid_from = models.DateTimeField(
        default=timezone.now,
        verbose_name="Valide à partir de"
    )
    valid_until = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Valide jusqu'à"
    )
    
    # Statut
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Code promo"
        verbose_name_plural = "Codes promo"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_valid(self):
        """Vérifie si le code promo est valide"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from > now:
            return False
        if self.valid_until and self.valid_until < now:
            return False
        if self.max_uses and self.usage_count >= self.max_uses:
            return False
        return True
    
    @property
    def usage_count(self):
        """Retourne le nombre d'utilisations du code"""
        return self.uses.count()
    
    def can_be_used_by_user(self, user):
        """Vérifie si un utilisateur peut utiliser ce code"""
        if not self.is_valid:
            return False
        
        if self.max_uses_per_user:
            user_uses = self.uses.filter(user=user).count()
            if user_uses >= self.max_uses_per_user:
                return False
        
        return True
    
    def calculate_discount(self, cart_total):
        """Calcule la réduction pour un montant de panier donné"""
        if not self.is_valid or cart_total < self.min_cart_amount:
            return 0
        
        if self.discount_type == 'free_shipping':
            return 0  # La logique de livraison gratuite sera gérée ailleurs
        
        if self.discount_type == 'percentage':
            discount = (cart_total * self.discount_value) / 100
        else:  # fixed
            discount = self.discount_value
        
        # Appliquer la limite maximale si définie
        if self.max_discount_amount:
            discount = min(discount, self.max_discount_amount)
        
        return discount


class PromoCodeUse(models.Model):
    """Modèle pour tracer l'utilisation des codes promo"""
    
    promo_code = models.ForeignKey(
        PromoCode, 
        on_delete=models.CASCADE, 
        related_name='uses',
        verbose_name="Code promo"
    )
    user = models.ForeignKey(
        'accounts.User', 
        on_delete=models.CASCADE,
        verbose_name="Utilisateur"
    )
    order = models.ForeignKey(
        'Order', 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Commande"
    )
    discount_amount = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        verbose_name="Montant de la réduction"
    )
    used_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'utilisation"
    )
    
    class Meta:
        verbose_name = "Utilisation de code promo"
        verbose_name_plural = "Utilisations de codes promo"
        ordering = ['-used_at']
        unique_together = ['promo_code', 'order']  # Un code par commande
    
    def __str__(self):
        return f"{self.promo_code.code} utilisé par {self.user.username}"


class UserLoyaltyStatus(models.Model):
    """Modèle pour suivre le statut de fidélité des utilisateurs"""
    
    user = models.OneToOneField(
        'accounts.User', 
        on_delete=models.CASCADE,
        related_name='loyalty_status',
        verbose_name="Utilisateur"
    )
    total_purchases = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre total d'achats"
    )
    total_spent = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00,
        verbose_name="Montant total dépensé (€)"
    )
    loyalty_points = models.PositiveIntegerField(
        default=0,
        verbose_name="Points de fidélité"
    )
    last_purchase_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date du dernier achat"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Statut de fidélité"
        verbose_name_plural = "Statuts de fidélité"
    
    def __str__(self):
        return f"Fidélité de {self.user.username}"
    
    def update_loyalty_status(self, order_amount):
        """Met à jour le statut de fidélité après un achat"""
        self.total_purchases += 1
        self.total_spent += order_amount
        self.last_purchase_date = timezone.now()
        
        # Calculer les points de fidélité (1 point par euro dépensé)
        self.loyalty_points += int(order_amount)
        
        self.save()
    
    def get_available_loyalty_discount(self):
        """Retourne la réduction de fidélité disponible"""
        # Calculer les statistiques réelles à partir des commandes confirmées
        confirmed_orders = Order.objects.filter(user=self.user, status='confirmed')
        real_purchases = confirmed_orders.count()
        real_spent = confirmed_orders.aggregate(total=models.Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Trouver le programme de fidélité applicable
        loyalty_program = LoyaltyProgram.objects.filter(
            is_active=True,
            min_purchases__lte=real_purchases,
            min_amount__lte=real_spent
        ).order_by('-min_purchases', '-min_amount').first()
        
        if loyalty_program:
            return loyalty_program
        return None
    
    def get_real_statistics(self):
        """Retourne les statistiques réelles basées sur les commandes confirmées"""
        confirmed_orders = Order.objects.filter(user=self.user, status='confirmed')
        
        stats = {
            'total_purchases': confirmed_orders.count(),
            'total_spent': confirmed_orders.aggregate(total=models.Sum('total_amount'))['total'] or Decimal('0.00'),
            'last_purchase_date': confirmed_orders.order_by('-created_at').first().created_at if confirmed_orders.exists() else None,
            'loyalty_points': 0
        }
        
        # Calculer les points de fidélité (1 point par euro dépensé)
        stats['loyalty_points'] = int(stats['total_spent'])
        
        return stats


class Invoice(models.Model):
    """Modèle pour les factures"""
    
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='invoice',
        verbose_name="Commande"
    )
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro de facture"
    )
    invoice_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de facturation"
    )
    due_date = models.DateField(
        verbose_name="Date d'échéance"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Brouillon'),
            ('sent', 'Envoyée'),
            ('paid', 'Payée'),
            ('overdue', 'En retard'),
            ('cancelled', 'Annulée'),
        ],
        default='sent',  # Par défaut, les factures sont envoyées
        verbose_name="Statut"
    )
    
    # Informations de facturation
    billing_name = models.CharField(
        max_length=200,
        verbose_name="Nom de facturation"
    )
    billing_address = models.TextField(
        verbose_name="Adresse de facturation"
    )
    billing_city = models.CharField(
        max_length=100,
        verbose_name="Ville"
    )
    billing_postal_code = models.CharField(
        max_length=20,
        verbose_name="Code postal"
    )
    billing_country = models.CharField(
        max_length=100,
        verbose_name="Pays"
    )
    
    # Totaux
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Sous-total"
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Frais de port"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant total"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-invoice_date']
    
    def __str__(self):
        return f"Facture {self.invoice_number}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Générer un numéro de facture unique
            year = timezone.now().year
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=f"FAC{year}"
            ).order_by('-invoice_number').first()
            
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.invoice_number = f"FAC{year}-{new_number:04d}"
        
        if not self.due_date:
            # Date d'échéance par défaut : 30 jours
            self.due_date = timezone.now().date() + timezone.timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Vérifie si la facture est en retard"""
        return self.status != 'paid' and self.due_date < timezone.now().date()
    
    def mark_as_sent(self):
        """Marque la facture comme envoyée"""
        self.status = 'sent'
        self.save()
    
    def mark_as_paid(self):
        """Marque la facture comme payée"""
        self.status = 'paid'
        self.save()


class ShopSettings(models.Model):
    """Modèle pour les paramètres de la boutique"""
    
    # Paramètres de livraison
    free_shipping_threshold = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=50.00,
        verbose_name="Seuil de livraison gratuite (€)"
    )
    standard_shipping_cost = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=5.90,
        verbose_name="Coût de livraison standard (€)"
    )
    
    # Paramètres de TVA
    tax_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.5,
        verbose_name="Taux de TVA (%)"
    )
    
    # Paramètres généraux
    shop_name = models.CharField(
        max_length=200, 
        default="Éditions Sen",
        verbose_name="Nom de la boutique"
    )
    shop_email = models.EmailField(
        default="contact@editions-sen.com",
        verbose_name="Email de la boutique"
    )
    shop_phone = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name="Téléphone de la boutique"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Paramètres de la boutique"
        verbose_name_plural = "Paramètres de la boutique"
    
    def __str__(self):
        return f"Paramètres de {self.shop_name}"
    
    @classmethod
    def get_settings(cls):
        """Récupère les paramètres de la boutique (singleton)"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
