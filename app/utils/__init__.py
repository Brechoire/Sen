"""
Utilitaires pour l'application Django Éditions Sen
"""
import os
import re
from datetime import datetime


def clean_filename(filename):
    """
    Nettoie le nom de fichier en enlevant les caractères spéciaux et les accents.
    
    Args:
        filename: Le nom de fichier original
        
    Returns:
        Un nom de fichier nettoyé et sécurisé
    """
    # Correspondance des accents (principaux caractères français et internationaux)
    accent_map = {
        'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
        'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
        'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n',
        'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A',
        'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
        'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
        'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
        'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
        'Ç': 'C', 'Ñ': 'N',
        'ý': 'y', 'ÿ': 'y', 'Ý': 'Y', 'Ÿ': 'Y',
        'æ': 'ae', 'Æ': 'AE',
        'œ': 'oe', 'Œ': 'OE',
    }
    
    # Séparer le nom et l'extension
    name, ext = os.path.splitext(filename)
    
    # Remplacer les accents
    cleaned_name = ''.join(accent_map.get(char, char) for char in name)
    
    # Remplacer les caractères spéciaux par des tirets
    # (garder seulement alphanumériques, tirets et underscores)
    cleaned_name = re.sub(r'[^\w\-_\.]', '-', cleaned_name)
    
    # Supprimer les tirets multiples consécutifs
    cleaned_name = re.sub(r'-+', '-', cleaned_name)
    
    # Supprimer les tirets et underscores en début et fin
    cleaned_name = cleaned_name.strip('-').strip('_')
    
    # Si le nom est vide après nettoyage, utiliser un timestamp
    if not cleaned_name:
        cleaned_name = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Limiter la longueur du nom (max 100 caractères pour éviter les problèmes)
    if len(cleaned_name) > 100:
        cleaned_name = cleaned_name[:100]
    
    # Retourner le nom nettoyé avec l'extension en minuscules
    return f"{cleaned_name}{ext.lower()}"


def get_upload_path(instance, filename, folder):
    """
    Génère un chemin d'upload avec un nom de fichier nettoyé et unique.
    
    Args:
        instance: L'instance du modèle Django
        filename: Le nom de fichier original
        folder: Le dossier de destination (ex: 'authors', 'books/covers')
        
    Returns:
        Le chemin complet avec un nom de fichier nettoyé et unique
    """
    cleaned_filename = clean_filename(filename)
    
    # Ajouter un timestamp pour éviter les collisions
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(cleaned_filename)
    
    # Générer un nom unique avec timestamp
    unique_filename = f"{name}_{timestamp}{ext}"
    
    return os.path.join(folder, unique_filename)

