from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from news.views import get_latest_articles
from author.models import Author
from shop.models import Book
from .forms import ContactForm


def home(request):
    # Récupérer les 3 derniers articles publiés
    latest_articles = get_latest_articles(3)

    # Récupérer les auteurs mis en avant
    featured_authors = Author.objects.filter(
        is_featured=True, is_active=True
    )[:3]

    # Récupérer les livres récents (nombre configurable via query string)
    try:
        count = int(request.GET.get('count', 4))
    except (TypeError, ValueError):
        count = 4
    # bornes de sécurité
    count = max(1, min(count, 12))
    new_books = Book.objects.filter(is_available=True).order_by('-created_at')[:count]

    context = {
        'latest_articles': latest_articles,
        'featured_authors': featured_authors,
        'new_books': new_books,
        'new_books_count': count,
    }
    return render(request, 'home/index.html', context)


def a_propos(request):
    """Vue pour la page À propos des Éditions Sen"""
    return render(request, 'home/a-propos.html')


def contact(request):
    """Vue pour la page de contact des Éditions Sen"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                form.send_email()
                messages.success(request, 'Votre message a été envoyé avec succès ! Nous vous répondrons dans les plus brefs délais.', extra_tags='contact_success')
                return redirect('home:contact')
            except Exception as e:
                messages.error(request, 'Une erreur est survenue lors de l\'envoi du message. Veuillez réessayer ou nous contacter directement.', extra_tags='contact_error')
    else:
        form = ContactForm()
    
    context = {
        'form': form,
    }
    return render(request, 'home/contact.html', context)


def mentions_legales(request):
    """Vue pour la page des mentions légales des Éditions Sen"""
    return render(request, 'home/mentions-legales.html')


def politique_confidentialite(request):
    """Vue pour la page de politique de confidentialité des Éditions Sen"""
    return render(request, 'home/politique-confidentialite.html')


def conditions_generales_vente(request):
    """Vue pour la page des conditions générales de vente des Éditions Sen"""
    return render(request, 'home/conditions-generales-vente.html')
