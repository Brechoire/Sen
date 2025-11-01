"""
Utilitaires de sécurité pour l'application Django Éditions Sen
"""
import bleach
from bleach.css_sanitizer import CSSSanitizer


# Tags HTML autorisés pour le contenu CKEditor
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'b', 'i', 's', 'strike',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'a', 'blockquote', 'div', 'span',
    'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'hr', 'pre', 'code',
]

# Attributs autorisés par tag
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'style'],
    'div': ['class', 'style'],
    'span': ['class', 'style'],
    'p': ['class', 'style'],
    'table': ['class', 'style'],
    'th': ['class', 'style'],
    'td': ['class', 'style'],
}

# Styles CSS autorisés
ALLOWED_STYLES = [
    'color', 'background-color', 'font-size', 'font-weight',
    'text-align', 'padding', 'margin', 'border', 'border-left',
    'border-right', 'border-top', 'border-bottom',
]

css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_STYLES)


def clean_html(content):
    """
    Nettoie le contenu HTML en utilisant bleach pour prévenir les attaques XSS.
    
    Cette fonction permet les tags HTML couramment utilisés dans les éditeurs
    de texte riche (CKEditor) tout en supprimant les éléments malveillants.
    
    Args:
        content: Le contenu HTML à nettoyer
        
    Returns:
        Le contenu HTML nettoyé et sécurisé
    """
    if not content:
        return ''
    
    # Nettoyer le HTML avec bleach
    cleaned = bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        css_sanitizer=css_sanitizer,
        strip=False,  # Ne pas supprimer les tags non autorisés, les échapper
    )
    
    return cleaned


def clean_text(text):
    """
    Nettoie un texte simple en supprimant tout HTML.
    
    Args:
        text: Le texte à nettoyer
        
    Returns:
        Le texte sans HTML
    """
    if not text:
        return ''
    
    return bleach.clean(text, tags=[], strip=True)

