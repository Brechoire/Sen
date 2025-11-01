"""
Utilitaires de validation pour l'application Django Éditions Sen
"""
import re


# Limites maximales pour les paramètres GET
MAX_SEARCH_LENGTH = 200
MAX_SLUG_LENGTH = 100
MAX_ID_LENGTH = 20


def validate_search_query(query, max_length=MAX_SEARCH_LENGTH):
    """
    Valide et nettoie une requête de recherche.
    
    Args:
        query: La requête de recherche à valider
        max_length: Longueur maximale autorisée (défaut: 200)
        
    Returns:
        La requête nettoyée et validée, ou None si invalide
    """
    if not query:
        return None
    
    # Convertir en string et supprimer les espaces
    query = str(query).strip()
    
    # Limiter la longueur
    if len(query) > max_length:
        query = query[:max_length]
    
    # Supprimer les caractères potentiellement dangereux
    # Autoriser lettres, chiffres, espaces, tirets, apostrophes
    query = re.sub(r'[^\w\s\-\'àáâãäåèéêëìíîïòóôõöùúûüçñÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÇÑ]', '', query)
    
    # Supprimer les espaces multiples
    query = re.sub(r'\s+', ' ', query)
    
    # Retourner None si vide après nettoyage
    if not query or len(query) < 2:
        return None
    
    return query


def validate_slug(slug, max_length=MAX_SLUG_LENGTH):
    """
    Valide un slug.
    
    Args:
        slug: Le slug à valider
        max_length: Longueur maximale autorisée
        
    Returns:
        Le slug nettoyé et validé, ou None si invalide
    """
    if not slug:
        return None
    
    slug = str(slug).strip()
    
    # Limiter la longueur
    if len(slug) > max_length:
        return None
    
    # Slug doit contenir uniquement lettres, chiffres, tirets et underscores
    if not re.match(r'^[a-z0-9_-]+$', slug, re.IGNORECASE):
        return None
    
    return slug


def validate_id(id_value, max_length=MAX_ID_LENGTH):
    """
    Valide un ID numérique.
    
    Args:
        id_value: L'ID à valider
        max_length: Longueur maximale de la représentation string
        
    Returns:
        L'ID converti en int, ou None si invalide
    """
    if not id_value:
        return None
    
    try:
        # Tenter de convertir en entier
        id_int = int(str(id_value).strip())
        
        # Vérifier que c'est positif
        if id_int <= 0:
            return None
        
        # Vérifier la longueur de la représentation string
        if len(str(id_int)) > max_length:
            return None
        
        return id_int
    except (ValueError, TypeError):
        return None


def validate_price(price_str, min_value=0, max_value=10000):
    """
    Valide un prix.
    
    Args:
        price_str: Le prix en string
        min_value: Valeur minimale autorisée
        max_value: Valeur maximale autorisée
        
    Returns:
        Le prix en float, ou None si invalide
    """
    if not price_str:
        return None
    
    try:
        price = float(str(price_str).strip())
        
        if price < min_value or price > max_value:
            return None
        
        return price
    except (ValueError, TypeError):
        return None


def sanitize_string(value, max_length=100):
    """
    Nettoie une chaîne de caractères en supprimant les caractères dangereux.
    
    Args:
        value: La valeur à nettoyer
        max_length: Longueur maximale
        
    Returns:
        La chaîne nettoyée ou None si vide
    """
    if not value:
        return None
    
    value = str(value).strip()
    
    if len(value) > max_length:
        value = value[:max_length]
    
    # Supprimer les caractères de contrôle et potentiellement dangereux
    value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
    
    return value if value else None

