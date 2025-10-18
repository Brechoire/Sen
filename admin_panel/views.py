from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta

from news.models import Article
from author.models import Author
from shop.models import Book, Category, Cart, CartItem, Review
from accounts.models import User


@staff_member_required
def admin_dashboard(request):
    """Tableau de bord principal de l'administration"""
    
    # Statistiques générales
    stats = {
        'total_articles': Article.objects.count(),
        'total_authors': Author.objects.count(),
        'total_books': Book.objects.count(),
        'total_categories': Category.objects.count(),
        'total_users': User.objects.count(),
        'total_carts': Cart.objects.count(),
        'total_reviews': Review.objects.count(),
    }
    
    # Articles récents
    recent_articles = Article.objects.order_by('-created_at')[:5]
    
    # Livres récents
    recent_books = Book.objects.select_related('author', 'category').order_by('-created_at')[:5]
    
    # Auteurs récents
    recent_authors = Author.objects.order_by('-created_at')[:5]
    
    # Commandes récentes (paniers avec des articles)
    recent_orders = Cart.objects.filter(items__isnull=False).distinct().order_by('-created_at')[:5]
    
    # Statistiques des ventes (approximation basée sur les paniers)
    total_sales = sum(cart.final_price for cart in Cart.objects.filter(items__isnull=False).distinct())
    
    # Livres les plus vendus (approximation)
    popular_books = Book.objects.annotate(
        total_ordered=Count('cartitem')
    ).order_by('-total_ordered')[:5]
    
    context = {
        'stats': stats,
        'recent_articles': recent_articles,
        'recent_books': recent_books,
        'recent_authors': recent_authors,
        'recent_orders': recent_orders,
        'total_sales': total_sales,
        'popular_books': popular_books,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)


@staff_member_required
def manage_articles(request):
    """Gestion des articles"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', 'all')
    
    articles = Article.objects.order_by('-created_at')
    
    if search:
        articles = articles.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(author__icontains=search)
        )
    
    if status == 'published':
        articles = articles.filter(is_published=True)
    elif status == 'draft':
        articles = articles.filter(is_published=False)
    
    paginator = Paginator(articles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
    }
    
    return render(request, 'admin_panel/articles.html', context)


@staff_member_required
def manage_authors(request):
    """Gestion des auteurs"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', 'all')
    
    authors = Author.objects.order_by('last_name', 'first_name')
    
    if search:
        authors = authors.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(pen_name__icontains=search)
        )
    
    if status == 'active':
        authors = authors.filter(is_active=True)
    elif status == 'inactive':
        authors = authors.filter(is_active=False)
    elif status == 'featured':
        authors = authors.filter(is_featured=True)
    
    paginator = Paginator(authors, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
    }
    
    return render(request, 'admin_panel/authors.html', context)


@staff_member_required
def manage_books(request):
    """Gestion des livres"""
    search = request.GET.get('search', '')
    category = request.GET.get('category', 'all')
    status = request.GET.get('status', 'all')
    
    books = Book.objects.select_related('author', 'category').order_by('-created_at')
    
    if search:
        books = books.filter(
            Q(title__icontains=search) |
            Q(author__first_name__icontains=search) |
            Q(author__last_name__icontains=search) |
            Q(author__pen_name__icontains=search)
        )
    
    if category != 'all':
        books = books.filter(category__slug=category)
    
    if status == 'available':
        books = books.filter(is_available=True)
    elif status == 'unavailable':
        books = books.filter(is_available=False)
    elif status == 'on_sale':
        books = books.filter(is_on_sale=True)
    
    categories = Category.objects.all()
    
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search': search,
        'category': category,
        'status': status,
    }
    
    return render(request, 'admin_panel/books.html', context)


@staff_member_required
def manage_orders(request):
    """Gestion des commandes (paniers)"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', 'all')
    
    orders = Cart.objects.filter(items__isnull=False).distinct().order_by('-created_at')
    
    if search:
        orders = orders.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(items__book__title__icontains=search)
        ).distinct()
    
    # Pour simplifier, on considère qu'un panier avec des articles est une commande
    # Dans un vrai système, il faudrait un modèle Order séparé
    
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
    }
    
    return render(request, 'admin_panel/orders.html', context)


@staff_member_required
def manage_reviews(request):
    """Gestion des avis"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', 'all')
    
    reviews = Review.objects.select_related('book', 'user').order_by('-created_at')
    
    if search:
        reviews = reviews.filter(
            Q(book__title__icontains=search) |
            Q(user__username__icontains=search) |
            Q(comment__icontains=search)
        )
    
    if status == 'approved':
        reviews = reviews.filter(is_approved=True)
    elif status == 'pending':
        reviews = reviews.filter(is_approved=False)
    
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
    }
    
    return render(request, 'admin_panel/reviews.html', context)


@staff_member_required
def manage_users(request):
    """Gestion des utilisateurs"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', 'all')
    
    users = User.objects.order_by('-date_joined')
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    elif status == 'staff':
        users = users.filter(is_staff=True)
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
    }
    
    return render(request, 'admin_panel/users.html', context)


@staff_member_required
def approve_review(request, review_id):
    """Approuver un avis"""
    review = get_object_or_404(Review, id=review_id)
    review.is_approved = True
    review.save()
    messages.success(request, f'Avis de {review.user.username} approuvé avec succès.')
    return redirect('admin_panel:reviews')


@staff_member_required
def reject_review(request, review_id):
    """Rejeter un avis"""
    review = get_object_or_404(Review, id=review_id)
    review.is_approved = False
    review.save()
    messages.success(request, f'Avis de {review.user.username} rejeté.')
    return redirect('admin_panel:reviews')


@staff_member_required
def toggle_article_status(request, article_id):
    """Basculer le statut de publication d'un article"""
    article = get_object_or_404(Article, id=article_id)
    article.is_published = not article.is_published
    article.save()
    
    status = "publié" if article.is_published else "dépublié"
    messages.success(request, f'Article "{article.title}" {status} avec succès.')
    return redirect('admin_panel:articles')


@staff_member_required
def toggle_book_status(request, book_id):
    """Basculer le statut de disponibilité d'un livre"""
    book = get_object_or_404(Book, id=book_id)
    book.is_available = not book.is_available
    book.save()
    
    status = "disponible" if book.is_available else "indisponible"
    messages.success(request, f'Livre "{book.title}" marqué comme {status}.')
    return redirect('admin_panel:books')


@staff_member_required
def toggle_author_status(request, author_id):
    """Basculer le statut d'un auteur"""
    author = get_object_or_404(Author, id=author_id)
    author.is_active = not author.is_active
    author.save()
    
    status = "actif" if author.is_active else "inactif"
    messages.success(request, f'Auteur "{author.display_name}" marqué comme {status}.')
    return redirect('admin_panel:authors')