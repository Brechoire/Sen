from django.contrib import admin
from .models import SocialMediaSettings


@admin.register(SocialMediaSettings)
class SocialMediaSettingsAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour les paramètres des réseaux sociaux"""

    list_display = [
        "__str__",
        "facebook_url",
        "instagram_url",
        "tiktok_url",
        "linkedin_url",
        "updated_at",
    ]

    fieldsets = (
        (
            "Réseaux sociaux",
            {"fields": ("facebook_url", "instagram_url", "tiktok_url", "linkedin_url")},
        ),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ["created_at", "updated_at"]

    def has_add_permission(self, request):
        """Empêcher l'ajout de plusieurs instances - singleton pattern"""
        return not SocialMediaSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Empêcher la suppression de l'instance unique"""
        return False
