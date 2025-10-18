from django.contrib import admin
from .models import Author

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour le modèle Author"""
    
    list_display = ['display_name', 'pen_name', 'is_featured', 'is_active', 'created_at']
    list_filter = ['is_featured', 'is_active', 'created_at']
    search_fields = ['first_name', 'last_name', 'pen_name', 'email']
    list_editable = ['is_featured', 'is_active']
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'pen_name', 'birth_date', 'death_date')
        }),
        ('Biographie', {
            'fields': ('biography', 'short_bio')
        }),
        ('Photo et contact', {
            'fields': ('photo', 'email', 'website', 'social_media'),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('is_featured', 'is_active')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def display_name(self, obj):
        return obj.display_name
    display_name.short_description = "Nom d'affichage"