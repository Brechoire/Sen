from django.db import models
from django.core.validators import URLValidator


class SocialMediaSettings(models.Model):
    """Modèle pour les paramètres des réseaux sociaux (singleton)"""
    
    facebook_url = models.CharField(
        max_length=200,
        blank=True,
        validators=[URLValidator()],
        verbose_name="URL Facebook"
    )
    
    tiktok_url = models.CharField(
        max_length=200,
        blank=True,
        validators=[URLValidator()],
        verbose_name="URL TikTok"
    )
    
    linkedin_url = models.CharField(
        max_length=200,
        blank=True,
        validators=[URLValidator()],
        verbose_name="URL LinkedIn"
    )
    
    instagram_url = models.CharField(
        max_length=200,
        blank=True,
        validators=[URLValidator()],
        verbose_name="URL Instagram"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Paramètres des réseaux sociaux"
        verbose_name_plural = "Paramètres des réseaux sociaux"
    
    def __str__(self):
        return "Paramètres des réseaux sociaux"
    
    @classmethod
    def get_settings(cls):
        """Récupère les paramètres des réseaux sociaux (singleton)"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
