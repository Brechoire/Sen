from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

# Exemple de signal - vous pouvez ajouter vos propres signaux ici
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         # Créer un profil utilisateur si nécessaire
#         pass










