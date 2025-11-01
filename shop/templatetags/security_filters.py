"""
Template tags de sécurité pour nettoyer le contenu HTML
"""
from django import template
from django.utils.safestring import mark_safe
from app.utils.security import clean_html

register = template.Library()


@register.filter(name='clean_html')
def clean_html_filter(value):
    """
    Template filter pour nettoyer le HTML et prévenir les attaques XSS.
    
    Usage dans les templates:
        {{ content|clean_html }}
    
    Remplace l'utilisation de {{ content|safe }} pour un affichage sécurisé.
    """
    if not value:
        return ''
    
    return clean_html(str(value))


@register.filter(name='clean_html_safe')
def clean_html_safe_filter(value):
    """
    Template filter qui nettoie le HTML et marque comme safe.
    
    Usage dans les templates:
        {{ content|clean_html_safe }}
    
    À utiliser uniquement pour du contenu provenant de CKEditor ou
    d'autres sources de confiance qui nécessitent l'affichage HTML.
    """
    if not value:
        return ''
    
    cleaned = clean_html(str(value))
    return mark_safe(cleaned)

