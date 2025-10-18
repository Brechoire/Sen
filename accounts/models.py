from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    """Modèle utilisateur personnalisé pour les Éditions Sen"""
    
    # Informations personnelles
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    
    # Adresse de facturation
    billing_address = models.TextField(blank=True, verbose_name="Adresse de facturation")
    billing_city = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    billing_postal_code = models.CharField(max_length=10, blank=True, verbose_name="Code postal")
    billing_country = models.CharField(max_length=100, blank=True, default="France", verbose_name="Pays")
    
    # Adresse de livraison (peut être différente)
    shipping_address = models.TextField(blank=True, verbose_name="Adresse de livraison")
    shipping_city = models.CharField(max_length=100, blank=True, verbose_name="Ville de livraison")
    shipping_postal_code = models.CharField(max_length=10, blank=True, verbose_name="Code postal de livraison")
    shipping_country = models.CharField(max_length=100, blank=True, default="France", verbose_name="Pays de livraison")
    
    # Préférences
    newsletter = models.BooleanField(default=True, verbose_name="Recevoir la newsletter")
    marketing = models.BooleanField(default=False, verbose_name="Recevoir les offres marketing")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}" if self.first_name else self.username
    
    @property
    def full_name(self):
        """Retourne le nom complet de l'utilisateur"""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def has_complete_profile(self):
        """Vérifie si le profil utilisateur est complet"""
        return all([
            self.first_name,
            self.last_name,
            self.email,
            self.billing_address,
            self.billing_city,
            self.billing_postal_code,
        ])
