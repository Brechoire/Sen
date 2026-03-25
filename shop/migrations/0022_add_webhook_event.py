# Generated manually for WebhookEvent model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("shop", "0021_alter_book_isbn"),
    ]

    operations = [
        migrations.CreateModel(
            name="WebhookEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "event_id",
                    models.CharField(
                        max_length=255, unique=True, verbose_name="ID Événement PayPal"
                    ),
                ),
                (
                    "event_type",
                    models.CharField(max_length=100, verbose_name="Type d'événement"),
                ),
                (
                    "resource_type",
                    models.CharField(max_length=50, verbose_name="Type de ressource"),
                ),
                ("payload", models.JSONField(verbose_name="Données complètes")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("processed", "Traité"),
                            ("failed", "Échec"),
                            ("ignored", "Ignoré"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="Statut",
                    ),
                ),
                (
                    "processed_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Date de traitement"
                    ),
                ),
                (
                    "error_message",
                    models.TextField(blank=True, verbose_name="Message d'erreur"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Date de réception"
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="webhook_events",
                        to="shop.order",
                        verbose_name="Commande associée",
                    ),
                ),
            ],
            options={
                "verbose_name": "Événement Webhook",
                "verbose_name_plural": "Événements Webhook",
                "ordering": ["-created_at"],
            },
        ),
    ]
