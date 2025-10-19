from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.conf import settings
import os

from news.models import Article
from author.models import Author
from shop.models import Book, Category, Cart, Review, ShopSettings, Refund, LoyaltyProgram, PromoCode, UserLoyaltyStatus, PromoCodeUse
from shop.forms import ShopSettingsForm, BookForm
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
        'total_orders': Cart.objects.filter(items__isnull=False).distinct().count(),
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


@staff_member_required
def manage_loyalty_programs(request):
    """Gestion des programmes de fidélité"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', 'all')
    
    programs = LoyaltyProgram.objects.order_by('-created_at')
    
    if search:
        programs = programs.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if status == 'active':
        programs = programs.filter(is_active=True)
    elif status == 'inactive':
        programs = programs.filter(is_active=False)
    
    paginator = Paginator(programs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
    }
    
    return render(request, 'admin_panel/loyalty_programs.html', context)


@staff_member_required
def manage_promo_codes(request):
    """Gestion des codes promo"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', 'all')
    
    codes = PromoCode.objects.order_by('-created_at')
    
    if search:
        codes = codes.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if status == 'active':
        codes = codes.filter(is_active=True)
    elif status == 'inactive':
        codes = codes.filter(is_active=False)
    elif status == 'expired':
        codes = codes.filter(valid_until__lt=timezone.now())
    
    paginator = Paginator(codes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
    }
    
    return render(request, 'admin_panel/promo_codes.html', context)


@staff_member_required
def manage_loyalty_status(request):
    """Gestion des statuts de fidélité des utilisateurs"""
    search = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'total_spent')
    
    statuses = UserLoyaltyStatus.objects.select_related('user').order_by(f'-{sort_by}')
    
    if search:
        statuses = statuses.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )
    
    paginator = Paginator(statuses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'sort_by': sort_by,
    }
    
    return render(request, 'admin_panel/loyalty_status.html', context)


@staff_member_required
def create_loyalty_program(request):
    """Créer un nouveau programme de fidélité"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        min_purchases = int(request.POST.get('min_purchases', 0))
        min_amount = float(request.POST.get('min_amount', 0))
        discount_type = request.POST.get('discount_type')
        discount_value = float(request.POST.get('discount_value', 0))
        max_discount_amount = request.POST.get('max_discount_amount')
        min_cart_amount = float(request.POST.get('min_cart_amount', 0))
        valid_from = request.POST.get('valid_from')
        valid_until = request.POST.get('valid_until')
        
        if max_discount_amount:
            max_discount_amount = float(max_discount_amount)
        else:
            max_discount_amount = None
            
        if valid_until:
            valid_until = datetime.strptime(valid_until, '%Y-%m-%dT%H:%M')
            valid_until = timezone.make_aware(valid_until)
        else:
            valid_until = None
            
        if valid_from:
            valid_from = datetime.strptime(valid_from, '%Y-%m-%dT%H:%M')
            valid_from = timezone.make_aware(valid_from)
        else:
            valid_from = timezone.now()
        
        program = LoyaltyProgram.objects.create(
            name=name,
            description=description,
            min_purchases=min_purchases,
            min_amount=min_amount,
            discount_type=discount_type,
            discount_value=discount_value,
            max_discount_amount=max_discount_amount,
            min_cart_amount=min_cart_amount,
            valid_from=valid_from,
            valid_until=valid_until
        )
        
        messages.success(request, f'Programme de fidélité "{name}" créé avec succès.')
        return redirect('admin_panel:loyalty_programs')
    
    return render(request, 'admin_panel/create_loyalty_program.html')


@staff_member_required
def create_promo_code(request):
    """Créer un nouveau code promo"""
    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        discount_type = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        max_discount_amount = request.POST.get('max_discount_amount')
        min_cart_amount = float(request.POST.get('min_cart_amount', 0))
        max_uses = request.POST.get('max_uses')
        max_uses_per_user = int(request.POST.get('max_uses_per_user', 1))
        valid_from = request.POST.get('valid_from')
        valid_until = request.POST.get('valid_until')
        
        if discount_value:
            discount_value = float(discount_value)
        else:
            discount_value = None
            
        if max_discount_amount:
            max_discount_amount = float(max_discount_amount)
        else:
            max_discount_amount = None
            
        if max_uses:
            max_uses = int(max_uses)
        else:
            max_uses = None
            
        if valid_until:
            valid_until = datetime.strptime(valid_until, '%Y-%m-%dT%H:%M')
            valid_until = timezone.make_aware(valid_until)
        else:
            valid_until = None
            
        if valid_from:
            valid_from = datetime.strptime(valid_from, '%Y-%m-%dT%H:%M')
            valid_from = timezone.make_aware(valid_from)
        else:
            valid_from = timezone.now()
        
        promo_code = PromoCode.objects.create(
            code=code,
            name=name,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            max_discount_amount=max_discount_amount,
            min_cart_amount=min_cart_amount,
            max_uses=max_uses,
            max_uses_per_user=max_uses_per_user,
            valid_from=valid_from,
            valid_until=valid_until
        )
        
        messages.success(request, f'Code promo "{code}" créé avec succès.')
        return redirect('admin_panel:promo_codes')
    
    return render(request, 'admin_panel/create_promo_code.html')


@staff_member_required
def toggle_loyalty_program(request, program_id):
    """Activer/désactiver un programme de fidélité"""
    program = get_object_or_404(LoyaltyProgram, id=program_id)
    program.is_active = not program.is_active
    program.save()
    
    status = "activé" if program.is_active else "désactivé"
    messages.success(request, f'Programme de fidélité "{program.name}" {status}.')
    return redirect('admin_panel:loyalty_programs')


@staff_member_required
def toggle_promo_code(request, code_id):
    """Activer/désactiver un code promo"""
    code = get_object_or_404(PromoCode, id=code_id)
    code.is_active = not code.is_active
    code.save()
    
    status = "activé" if code.is_active else "désactivé"
    messages.success(request, f'Code promo "{code.code}" {status}.')
    return redirect('admin_panel:promo_codes')


@staff_member_required
def delete_loyalty_program(request, program_id):
    """Supprimer un programme de fidélité"""
    program = get_object_or_404(LoyaltyProgram, id=program_id)
    program_name = program.name
    program.delete()
    
    messages.success(request, f'Programme de fidélité "{program_name}" supprimé.')
    return redirect('admin_panel:loyalty_programs')


@staff_member_required
def delete_promo_code(request, code_id):
    """Supprimer un code promo"""
    code = get_object_or_404(PromoCode, id=code_id)
    code_name = code.code
    code.delete()
    
    messages.success(request, f'Code promo "{code_name}" supprimé.')
    return redirect('admin_panel:promo_codes')


# ===== GESTION DES CATÉGORIES =====

@staff_member_required
def manage_categories(request):
    """Gestion des catégories"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', 'all')
    
    categories = Category.objects.annotate(
        book_count=Count('books')
    ).order_by('name')
    
    if search:
        categories = categories.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if status == 'active':
        categories = categories.filter(is_active=True)
    elif status == 'inactive':
        categories = categories.filter(is_active=False)
    
    paginator = Paginator(categories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
    }
    
    return render(request, 'admin_panel/categories.html', context)


@staff_member_required
def create_category(request):
    """Créer une nouvelle catégorie"""
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        
        if not name or not slug:
            messages.error(request, 'Le nom et le slug sont obligatoires.')
            return render(request, 'admin_panel/create_category.html')
        
        # Vérifier si le slug existe déjà
        if Category.objects.filter(slug=slug).exists():
            messages.error(request, 'Une catégorie avec ce slug existe déjà.')
            return render(request, 'admin_panel/create_category.html')
        
        category = Category.objects.create(
            name=name,
            slug=slug,
            description=description,
            is_active=is_active
        )
        
        messages.success(request, f'Catégorie "{name}" créée avec succès.')
        return redirect('admin_panel:categories')
    
    return render(request, 'admin_panel/create_category.html')


@staff_member_required
def edit_category(request, category_id):
    """Modifier une catégorie"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        
        if not name or not slug:
            messages.error(request, 'Le nom et le slug sont obligatoires.')
            return render(request, 'admin_panel/edit_category.html', {'category': category})
        
        # Vérifier si le slug existe déjà (sauf pour la catégorie actuelle)
        if Category.objects.filter(slug=slug).exclude(id=category_id).exists():
            messages.error(request, 'Une catégorie avec ce slug existe déjà.')
            return render(request, 'admin_panel/edit_category.html', {'category': category})
        
        category.name = name
        category.slug = slug
        category.description = description
        category.is_active = is_active
        category.save()
        
        messages.success(request, f'Catégorie "{name}" modifiée avec succès.')
        return redirect('admin_panel:categories')
    
    return render(request, 'admin_panel/edit_category.html', {'category': category})


@staff_member_required
def toggle_category(request, category_id):
    """Activer/désactiver une catégorie"""
    category = get_object_or_404(Category, id=category_id)
    category.is_active = not category.is_active
    category.save()
    
    status = "activée" if category.is_active else "désactivée"
    messages.success(request, f'Catégorie "{category.name}" {status}.')
    return redirect('admin_panel:categories')


@staff_member_required
def delete_category(request, category_id):
    """Supprimer une catégorie"""
    category = get_object_or_404(Category, id=category_id)
    
    # Vérifier s'il y a des livres dans cette catégorie
    if category.book_set.exists():
        messages.error(request, f'Impossible de supprimer la catégorie "{category.name}" car elle contient des livres.')
        return redirect('admin_panel:categories')
    
    category_name = category.name
    category.delete()
    
    messages.success(request, f'Catégorie "{category_name}" supprimée.')
    return redirect('admin_panel:categories')


# ===== GESTION DES LIVRES =====

@staff_member_required
def manage_books(request):
    """Gestion des livres"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', 'all')
    category = request.GET.get('category', 'all')
    
    books = Book.objects.select_related('author', 'category').annotate(
        review_count=Count('reviews')
    ).order_by('-created_at')
    
    if search:
        books = books.filter(
            Q(title__icontains=search) |
            Q(author__name__icontains=search) |
            Q(isbn__icontains=search)
        )
    
    if status == 'available':
        books = books.filter(is_available=True)
    elif status == 'unavailable':
        books = books.filter(is_available=False)
    elif status == 'featured':
        books = books.filter(is_featured=True)
    elif status == 'bestseller':
        books = books.filter(is_bestseller=True)
    
    if category != 'all':
        books = books.filter(category_id=category)
    
    # Statistiques
    stats = {
        'total': books.count(),
        'available': Book.objects.filter(is_available=True).count(),
        'unavailable': Book.objects.filter(is_available=False).count(),
        'featured': Book.objects.filter(is_featured=True).count(),
        'bestseller': Book.objects.filter(is_bestseller=True).count(),
    }
    
    # Catégories pour le filtre
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'category': category,
        'stats': stats,
        'categories': categories,
    }
    
    return render(request, 'admin_panel/books.html', context)


@staff_member_required
def create_book(request):
    """Créer un nouveau livre"""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Livre "{book.title}" créé avec succès.')
            return redirect('admin_panel:books')
    else:
        form = BookForm()
    
    return render(request, 'admin_panel/create_book.html', {'form': form})


@staff_member_required
def edit_book(request, book_id):
    """Modifier un livre"""
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Livre "{book.title}" modifié avec succès.')
            return redirect('admin_panel:books')
    else:
        form = BookForm(instance=book)
    
    return render(request, 'admin_panel/edit_book.html', {'form': form, 'object': book})


@staff_member_required
def toggle_book(request, book_id):
    """Activer/désactiver un livre"""
    book = get_object_or_404(Book, id=book_id)
    book.is_available = not book.is_available
    book.save()
    
    status = "activé" if book.is_available else "désactivé"
    messages.success(request, f'Livre "{book.title}" {status}.')
    return redirect('admin_panel:books')


@staff_member_required
def delete_book(request, book_id):
    """Supprimer un livre"""
    book = get_object_or_404(Book, id=book_id)
    title = book.title
    book.delete()
    
    messages.success(request, f'Livre "{title}" supprimé avec succès.')
    return redirect('admin_panel:books')


@staff_member_required
def paypal_config(request):
    """Configuration PayPal"""
    context = {
        'paypal_client_id': settings.PAYPAL_CLIENT_ID,
        'paypal_client_secret': settings.PAYPAL_CLIENT_SECRET,
        'paypal_mode': settings.PAYPAL_MODE,
    }
    return render(request, 'admin_panel/paypal_config.html', context)