from django.db import models
from django.utils import timezone
from django.urls import reverse
from ckeditor.fields import RichTextField

class Author(models.Model):
    """Modèle pour les auteurs des Éditions Sen"""
    
    # Informations personnelles
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    pen_name = models.CharField(max_length=100, blank=True, verbose_name="Nom de plume")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    death_date = models.DateField(null=True, blank=True, verbose_name="Date de décès")
    
    # Biographie
    biography = RichTextField(verbose_name="Biographie")
    short_bio = models.TextField(max_length=500, blank=True, verbose_name="Biographie courte")
    
    # Photo et informations visuelles
    photo = models.ImageField(upload_to='authors/', blank=True, null=True, verbose_name="Photo")
    
    # Informations de contact (optionnelles)
    email = models.EmailField(blank=True, verbose_name="Email")
    website = models.URLField(blank=True, verbose_name="Site web")
    social_media = models.JSONField(default=dict, blank=True, verbose_name="Réseaux sociaux")
    
    # Informations éditoriales
    is_featured = models.BooleanField(default=False, verbose_name="Auteur mis en avant")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Auteur"
        verbose_name_plural = "Auteurs"
        ordering = ['last_name', 'first_name']
        unique_together = ['first_name', 'last_name']
    
    def __str__(self):
        if self.pen_name:
            return f"{self.pen_name} ({self.first_name} {self.last_name})"
        return f"{self.first_name} {self.last_name}"
    
    def get_absolute_url(self):
        return reverse('author:author_detail', kwargs={'pk': self.pk})
    
    @property
    def full_name(self):
        """Retourne le nom complet de l'auteur"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self):
        """Retourne le nom d'affichage (nom de plume ou nom complet)"""
        return self.pen_name or self.full_name
    
    @property
    def is_alive(self):
        """Vérifie si l'auteur est vivant"""
        return self.death_date is None
    
    def get_age(self):
        """Calcule l'âge de l'auteur"""
        if not self.birth_date:
            return None
        
        reference_date = self.death_date or timezone.now().date()
        return (reference_date - self.birth_date).days // 365