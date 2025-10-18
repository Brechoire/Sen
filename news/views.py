from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Article
from .forms import ArticleForm


def is_superuser(user):
    """Vérifie si l'utilisateur est un superutilisateur"""
    return user.is_authenticated and user.is_superuser


def article_list(request):
    """Liste tous les articles publiés"""
    articles = Article.objects.filter(
        status='published'
    ).order_by('-published_at')

    # Recherche
    search_query = request.GET.get('search')
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(author__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(articles, 6)  # 6 articles par page
    page_number = request.GET.get('page')
    articles = paginator.get_page(page_number)

    context = {
        'articles': articles,
        'search_query': search_query,
    }
    return render(request, 'news/article_list.html', context)


def article_detail(request, slug):
    """Détail d'un article"""
    article = get_object_or_404(Article, slug=slug, status='published')

    # Articles similaires (même auteur)
    similar_articles = Article.objects.filter(
        author=article.author,
        status='published'
    ).exclude(id=article.id)[:3]

    context = {
        'article': article,
        'similar_articles': similar_articles,
    }
    return render(request, 'news/article_detail.html', context)


@login_required
@user_passes_test(is_superuser)
def article_create(request):
    """Créer un nouvel article"""
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save()
            messages.success(
                request,
                f"L'article '{article.title}' a été créé avec succès."
            )
            return redirect('news:article_detail', slug=article.slug)
    else:
        form = ArticleForm()

    context = {'form': form}
    return render(request, 'news/article_form.html', context)


@login_required
@user_passes_test(is_superuser)
def article_update(request, slug):
    """Modifier un article existant"""
    article = get_object_or_404(Article, slug=slug)

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            article = form.save()
            messages.success(
                request,
                f"L'article '{article.title}' a été modifié avec succès."
            )
            return redirect('news:article_detail', slug=article.slug)
    else:
        form = ArticleForm(instance=article)

    context = {
        'form': form,
        'article': article,
    }
    return render(request, 'news/article_form.html', context)


@login_required
@user_passes_test(is_superuser)
def article_delete(request, slug):
    """Supprimer un article"""
    article = get_object_or_404(Article, slug=slug)

    if request.method == 'POST':
        article_title = article.title
        article.delete()
        messages.success(
            request,
            f"L'article '{article_title}' a été supprimé avec succès."
        )
        return redirect('news:article_list')

    context = {'article': article}
    return render(request, 'news/article_confirm_delete.html', context)


def get_latest_articles(count=3):
    """Fonction utilitaire pour récupérer les derniers articles"""
    return Article.objects.filter(
        status='published'
    ).order_by('-published_at')[:count]
