"""
Context processors pour l'application home
"""
from .models import SocialMediaSettings


def social_media_settings(request):
    """
    Context processor qui ajoute les paramètres des réseaux sociaux
    au contexte pour toutes les pages.
    
    Returns:
        dict: Dictionnaire contenant 'social_settings'
    """
    return {
        'social_settings': SocialMediaSettings.get_settings()
    }

