from django.shortcuts import render
from news.views import get_latest_articles
from author.models import Author


def home(request):
    # Récupérer les 3 derniers articles publiés
    latest_articles = get_latest_articles(3)

    # Récupérer les auteurs mis en avant
    featured_authors = Author.objects.filter(
        is_featured=True, is_active=True
    )[:3]

    context = {
        'latest_articles': latest_articles,
        'featured_authors': featured_authors,
    }
    return render(request, 'home/index.html', context)


def a_propos(request):
    """Vue pour la page À propos des Éditions Sen"""
    return render(request, 'home/a-propos.html')
