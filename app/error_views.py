"""
Vues personnalisées pour la gestion des erreurs HTTP
"""

from django.shortcuts import render
from django.http import HttpResponseServerError, HttpResponseNotFound, HttpResponseForbidden, HttpResponseBadRequest


def custom_404(request, exception=None):
    """Vue personnalisée pour l'erreur 404"""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Vue personnalisée pour l'erreur 500"""
    return render(request, '500.html', status=500)


def custom_403(request, exception=None):
    """Vue personnalisée pour l'erreur 403"""
    return render(request, '403.html', status=403)


def custom_400(request, exception=None):
    """Vue personnalisée pour l'erreur 400"""
    return render(request, '400.html', status=400)
