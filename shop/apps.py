from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shop"
    
    def ready(self):
        # Importer les signaux pour l'annulation automatique des commandes expirées
        import shop.signals