from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Configuration de l'administration pour le modèle User personnalisé"""

    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "phone",
        "is_staff",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_staff", "is_active", "newsletter", "marketing", "created_at"]
    search_fields = ["username", "email", "first_name", "last_name", "phone"]
    ordering = ["-created_at"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Informations personnelles",
            {"fields": ("first_name", "last_name", "email", "phone", "birth_date")},
        ),
        (
            "Adresse de facturation",
            {
                "fields": (
                    "billing_address",
                    "billing_city",
                    "billing_postal_code",
                    "billing_country",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Adresse de livraison",
            {
                "fields": (
                    "shipping_address",
                    "shipping_city",
                    "shipping_postal_code",
                    "shipping_country",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Préférences",
            {"fields": ("newsletter", "marketing"), "classes": ("collapse",)},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Dates importantes",
            {
                "fields": ("last_login", "date_joined", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )

    readonly_fields = ["created_at", "updated_at", "last_login", "date_joined"]
