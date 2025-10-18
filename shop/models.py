from django.db import models
from django.urls import reverse
from django.utils import timezone
from ckeditor.fields import RichTextField
from author.models import Author


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
    cover_image = models.ImageField(upload_to='books/covers/', verbose_name="Image de couverture")
    back_cover_image = models.ImageField(upload_to='books/backs/', blank=True, null=True, verbose_name="Image de quatrième de couverture")
    
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
    image = models.ImageField(upload_to='books/gallery/', verbose_name="Image")
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
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='carts', verbose_name="Utilisateur")
    session_key = models.CharField(max_length=40, blank=True, null=True, verbose_name="Clé de session")
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
