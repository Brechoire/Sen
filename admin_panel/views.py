from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
import os

from news.models import Article
from author.models import Author
from shop.models import Book, Category, Cart, Review, ShopSettings, Refund
from shop.forms import ShopSettingsForm
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
    
    # Remboursements en attente (pour le menu)
    pending_refunds = Refund.objects.filter(status='pending').count()
    
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
        'pending_refunds': pending_refunds,
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
def manage_shop_settings(request):
    """Gestion des paramètres de la boutique"""
    
    # Récupérer ou créer les paramètres
    settings = ShopSettings.get_settings()
    
    if request.method == 'POST':
        form = ShopSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paramètres de la boutique mis à jour avec succès.')
            return redirect('admin_panel:shop_settings')
    else:
        form = ShopSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'settings': settings,
    }
    
    return render(request, 'admin_panel/shop_settings.html', context)


@staff_member_required
def manage_refunds(request):
    """Gestion des remboursements"""
    # Statistiques des remboursements
    total_refunds = Refund.objects.count()
    pending_refunds = Refund.objects.filter(status='pending').count()
    approved_refunds = Refund.objects.filter(status='approved').count()
    processed_refunds = Refund.objects.filter(status='processed').count()
    
    # Remboursements récents
    recent_refunds = Refund.objects.select_related(
        'order', 'requested_by', 'processed_by'
    ).order_by('-created_at')[:10]
    
    # Remboursements en attente
    pending_refunds_list = Refund.objects.filter(
        status='pending'
    ).select_related('order', 'requested_by').order_by('created_at')
    
    context = {
        'total_refunds': total_refunds,
        'pending_refunds': pending_refunds,
        'approved_refunds': approved_refunds,
        'processed_refunds': processed_refunds,
        'recent_refunds': recent_refunds,
        'pending_refunds_list': pending_refunds_list,
    }
    
    return render(request, 'admin_panel/refunds.html', context)


@staff_member_required
def process_refund(request, refund_id):
    """Traiter un remboursement"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        refund = get_object_or_404(Refund, id=refund_id)
        action = request.POST.get('action')
        
        if action == 'approve':
            if refund.can_be_approved:
                refund.status = 'approved'
                refund.processed_by = request.user
                refund.processed_at = timezone.now()
                refund.save()
                
                messages.success(request, f'Remboursement #{refund.id} approuvé.')
                return JsonResponse({
                    'success': True,
                    'message': 'Remboursement approuvé',
                    'new_status': 'approved'
                })
            else:
                return JsonResponse({'error': 'Ce remboursement ne peut pas être approuvé'}, status=400)
                
        elif action == 'reject':
            if refund.status == 'pending':
                refund.status = 'rejected'
                refund.processed_by = request.user
                refund.processed_at = timezone.now()
                refund.save()
                
                messages.success(request, f'Remboursement #{refund.id} rejeté.')
                return JsonResponse({
                    'success': True,
                    'message': 'Remboursement rejeté',
                    'new_status': 'rejected'
                })
            else:
                return JsonResponse({'error': 'Ce remboursement ne peut pas être rejeté'}, status=400)
                
        elif action == 'process':
            if refund.can_be_processed:
                # Ici, vous pouvez intégrer l'API PayPal pour traiter le remboursement
                # Pour l'instant, on simule le traitement
                refund.status = 'processed'
                refund.processed_by = request.user
                refund.processed_at = timezone.now()
                refund.save()
                
                messages.success(request, f'Remboursement #{refund.id} traité.')
                return JsonResponse({
                    'success': True,
                    'message': 'Remboursement traité',
                    'new_status': 'processed'
                })
            else:
                return JsonResponse({'error': 'Ce remboursement ne peut pas être traité'}, status=400)
        
        else:
            return JsonResponse({'error': 'Action non valide'}, status=400)
            
    except Refund.DoesNotExist:
        return JsonResponse({'error': 'Remboursement non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Erreur: {str(e)}'}, status=500)


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


@staff_member_required
def environment_variables(request):
    """Affichage des variables d'environnement actives"""
    from django.conf import settings
    
    # Variables importantes à afficher (valeurs masquées pour la sécurité)
    env_vars = {
        'Django': {
            'DEBUG': '***' if os.environ.get('DEBUG') else 'Non défini',
            'SECRET_KEY': '***' if os.environ.get('SECRET_KEY') else 'Non défini',
            'ALLOWED_HOSTS': '***' if os.environ.get('ALLOWED_HOSTS') else 'Non défini',
            'LANGUAGE_CODE': '***' if os.environ.get('LANGUAGE_CODE') else 'Non défini',
            'TIME_ZONE': '***' if os.environ.get('TIME_ZONE') else 'Non défini',
        },
        'Base de données': {
            'DATABASE_ENGINE': '***' if os.environ.get('DATABASE_ENGINE') else 'Non défini',
            'DATABASE_NAME': '***' if os.environ.get('DATABASE_NAME') else 'Non défini',
        },
        'PayPal': {
            'PAYPAL_CLIENT_ID': '***' if os.environ.get('PAYPAL_CLIENT_ID') else 'Non défini',
            'PAYPAL_CLIENT_SECRET': '***' if os.environ.get('PAYPAL_CLIENT_SECRET') else 'Non défini',
            'PAYPAL_MODE': '***' if os.environ.get('PAYPAL_MODE') else 'Non défini',
        },
        'Email': {
            'EMAIL_HOST': '***' if os.environ.get('EMAIL_HOST') else 'Non défini',
            'EMAIL_PORT': '***' if os.environ.get('EMAIL_PORT') else 'Non défini',
            'EMAIL_USE_TLS': '***' if os.environ.get('EMAIL_USE_TLS') else 'Non défini',
            'EMAIL_HOST_USER': '***' if os.environ.get('EMAIL_HOST_USER') else 'Non défini',
        },
        'Boutique': {
            'SHOP_NAME': '***' if os.environ.get('SHOP_NAME') else 'Non défini',
            'SHOP_EMAIL': '***' if os.environ.get('SHOP_EMAIL') else 'Non défini',
            'SHOP_PHONE': '***' if os.environ.get('SHOP_PHONE') else 'Non défini',
        },
        'Livraison': {
            'FREE_SHIPPING_THRESHOLD': '***' if os.environ.get('FREE_SHIPPING_THRESHOLD') else 'Non défini',
            'STANDARD_SHIPPING_COST': '***' if os.environ.get('STANDARD_SHIPPING_COST') else 'Non défini',
            'TAX_RATE': '***' if os.environ.get('TAX_RATE') else 'Non défini',
        }
    }
    
    # Variables actuelles de Django (valeurs masquées pour la sécurité)
    django_settings = {
        'DEBUG': '***' if hasattr(settings, 'DEBUG') else 'Non défini',
        'ALLOWED_HOSTS': '***' if hasattr(settings, 'ALLOWED_HOSTS') else 'Non défini',
        'LANGUAGE_CODE': '***' if hasattr(settings, 'LANGUAGE_CODE') else 'Non défini',
        'TIME_ZONE': '***' if hasattr(settings, 'TIME_ZONE') else 'Non défini',
        'PAYPAL_MODE': '***' if hasattr(settings, 'PAYPAL_MODE') else 'Non défini',
        'SHOP_NAME': '***' if hasattr(settings, 'SHOP_NAME') else 'Non défini',
    }
    
    context = {
        'env_vars': env_vars,
        'django_settings': django_settings,
        'total_vars': sum(
            len(category) for category in env_vars.values()
        ),
    }
    
    return render(request, 'admin_panel/environment_variables.html', context)