# Standard library imports
import logging
from decimal import Decimal

# Django imports
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin, UserPassesTestMixin
)
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Avg, Count
from django.db import transaction
from django.core.paginator import Paginator
from django.conf import settings
from django_ratelimit.decorators import ratelimit

# Local application imports
from app.utils.validation import (
    validate_search_query, validate_slug, validate_id, validate_price
)

# Project imports
from .models import (
    Book, Category, BookImage, Review, Cart, CartItem, Order, OrderItem,
    Payment, ShopSettings, Refund, PromoCode, UserLoyaltyStatus, Invoice,
    OrderStatusHistory
)
from .forms import (
    BookForm, CategoryForm, BookImageForm, ReviewForm, BookSearchForm,
    CheckoutForm, PaymentMethodForm, RefundRequestForm, PromoCodeForm
)
from .services import (
    PromoCodeService, LoyaltyService, DiscountService, CartService
)
from .paypal_api import create_paypal_order, capture_paypal_order, capture_paypal_order_by_token
from author.models import Author

logger = logging.getLogger(__name__)


class BookListView(ListView):
    """Vue pour lister tous les livres avec filtres et recherche"""
    model = Book
    template_name = 'shop/book_list.html'
    context_object_name = 'books'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Book.objects.filter(is_available=True).prefetch_related('authors').select_related('category')
        
        # Filtres avec validation
        search_query = validate_search_query(self.request.GET.get('query'))
        category_slug = validate_slug(self.request.GET.get('category'))
        author_id = validate_id(self.request.GET.get('author'))
        price_min = validate_price(self.request.GET.get('price_min'))
        price_max = validate_price(self.request.GET.get('price_max'))
        
        # Format: validation basique (liste blanche)
        format_filter = self.request.GET.get('format')
        allowed_formats = ['paperback', 'hardcover', 'ebook', 'audiobook']
        if format_filter not in allowed_formats:
            format_filter = None
        
        # Tri: validation (liste blanche)
        sort_by = self.request.GET.get('sort_by', '-created_at')
        allowed_sort = [
            '-created_at', 'created_at', '-title', 'title',
            '-price', 'price', '-rating', 'rating'
        ]
        if sort_by not in allowed_sort:
            sort_by = '-created_at'
        
        # Recherche textuelle
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(subtitle__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(authors__first_name__icontains=search_query) |
                Q(authors__last_name__icontains=search_query) |
                Q(authors__pen_name__icontains=search_query)
            ).distinct()
        
        # Filtre par catégorie
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filtre par auteur
        if author_id:
            queryset = queryset.filter(authors__id=author_id).distinct()
        
        # Filtre par prix
        if price_min is not None:
            queryset = queryset.filter(price__gte=price_min)
        if price_max is not None:
            queryset = queryset.filter(price__lte=price_max)
        
        # Filtre par format
        if format_filter:
            queryset = queryset.filter(format=format_filter)
        
        # Tri
        queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = BookSearchForm(self.request.GET)
        context['categories'] = Category.objects.filter(is_active=True)
        context['featured_books'] = Book.objects.filter(is_available=True, is_featured=True)[:6]
        context['bestsellers'] = Book.objects.filter(is_available=True, is_bestseller=True)[:6]
        return context


class BookDetailView(DetailView):
    """Vue pour afficher les détails d'un livre"""
    model = Book
    template_name = 'shop/book_detail.html'
    context_object_name = 'book'
    slug_field = 'slug'
    
    def get_queryset(self):
        return Book.objects.filter(is_available=True).select_related('category').prefetch_related('authors', 'images', 'reviews')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        
        # Livres similaires (même catégorie ou même auteur)
        book_author_ids = book.authors.values_list('id', flat=True)
        similar_books = Book.objects.filter(
            is_available=True
        ).filter(
            Q(category=book.category) | Q(authors__in=book_author_ids)
        ).exclude(id=book.id).distinct()[:4]
        
        # Avis approuvés
        reviews = book.reviews.filter(is_approved=True).select_related('user')
        
        # Moyenne des notes
        avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        
        context.update({
            'similar_books': similar_books,
            'reviews': reviews[:5],  # 5 derniers avis
            'avg_rating': round(avg_rating, 1),
            'review_count': reviews.count(),
            'review_form': ReviewForm(),
        })
        
        return context


class CategoryDetailView(DetailView):
    """Vue pour afficher les livres d'une catégorie"""
    model = Category
    template_name = 'shop/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        
        # Livres de cette catégorie
        books = Book.objects.filter(
            category=category,
            is_available=True
        ).prefetch_related('authors').order_by('-created_at')
        
        # Pagination
        paginator = Paginator(books, 12)
        page_number = self.request.GET.get('page')
        context['books'] = paginator.get_page(page_number)
        
        return context


# Vues d'administration (nécessitent une connexion et permissions staff)
class BookCreateView(UserPassesTestMixin, LoginRequiredMixin, CreateView):
    """
    Vue pour créer un nouveau livre.
    
    Requiert que l'utilisateur soit staff (is_staff=True).
    """
    model = Book
    form_class = BookForm
    template_name = 'shop/book_form.html'
    success_url = reverse_lazy('admin_panel:books')
    
    def test_func(self):
        """Vérifie que l'utilisateur est staff"""
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, 'Le livre a été créé avec succès.')
        return super().form_valid(form)


class BookUpdateView(UserPassesTestMixin, LoginRequiredMixin, UpdateView):
    """
    Vue pour modifier un livre existant.
    
    Requiert que l'utilisateur soit staff (is_staff=True).
    """
    model = Book
    form_class = BookForm
    template_name = 'shop/book_form.html'
    slug_field = 'slug'
    
    def test_func(self):
        """Vérifie que l'utilisateur est staff"""
        return self.request.user.is_staff
    
    def get_success_url(self):
        return reverse('admin_panel:books')
    
    def form_valid(self, form):
        messages.success(self.request, 'Le livre a été modifié avec succès.')
        return super().form_valid(form)


class BookDeleteView(UserPassesTestMixin, LoginRequiredMixin, DeleteView):
    """
    Vue pour supprimer un livre.
    
    Requiert que l'utilisateur soit staff (is_staff=True).
    """
    model = Book
    template_name = 'shop/book_confirm_delete.html'
    slug_field = 'slug'
    success_url = reverse_lazy('shop:book_list')
    
    def test_func(self):
        """Vérifie que l'utilisateur est staff"""
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Le livre a été supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


class CategoryCreateView(UserPassesTestMixin, LoginRequiredMixin, CreateView):
    """
    Vue pour créer une nouvelle catégorie.
    
    Requiert que l'utilisateur soit staff (is_staff=True).
    """
    model = Category
    form_class = CategoryForm
    template_name = 'shop/category_form.html'
    success_url = reverse_lazy('shop:book_list')
    
    def test_func(self):
        """Vérifie que l'utilisateur est staff"""
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, 'La catégorie a été créée avec succès.')
        return super().form_valid(form)


class CategoryUpdateView(UserPassesTestMixin, LoginRequiredMixin, UpdateView):
    """
    Vue pour modifier une catégorie existante.
    
    Requiert que l'utilisateur soit staff (is_staff=True).
    """
    model = Category
    form_class = CategoryForm
    template_name = 'shop/category_form.html'
    slug_field = 'slug'
    success_url = reverse_lazy('shop:book_list')
    
    def test_func(self):
        """Vérifie que l'utilisateur est staff"""
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, 'La catégorie a été modifiée avec succès.')
        return super().form_valid(form)


class CategoryDeleteView(UserPassesTestMixin, LoginRequiredMixin, DeleteView):
    """
    Vue pour supprimer une catégorie.
    
    Requiert que l'utilisateur soit staff (is_staff=True).
    """
    model = Category
    template_name = 'shop/category_confirm_delete.html'
    slug_field = 'slug'
    success_url = reverse_lazy('shop:book_list')
    
    def test_func(self):
        """Vérifie que l'utilisateur est staff"""
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'La catégorie a été supprimée avec succès.')
        return super().delete(request, *args, **kwargs)


# Vues pour les avis
@login_required
def add_review(request, slug):
    """Vue pour ajouter un avis sur un livre"""
    book = get_object_or_404(Book, slug=slug, is_available=True)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Vérifier si l'utilisateur a déjà laissé un avis
            existing_review = Review.objects.filter(book=book, user=request.user).first()
            if existing_review:
                messages.error(request, 'Vous avez déjà laissé un avis sur ce livre.')
            else:
                review = form.save(commit=False)
                review.book = book
                review.user = request.user
                review.save()
                
                # Logger l'ajout d'avis
                security_logger = logging.getLogger('security')
                security_logger.info(
                    f"Avis ajouté: review_id={review.id}, "
                    f"book_id={book.id}, book_title={book.title}, "
                    f"user_id={request.user.id}, rating={review.rating}"
                )
                
                messages.success(
                    request,
                    'Votre avis a été ajouté et sera publié après validation.'
                )
            return redirect('shop:book_detail', slug=book.slug)
    else:
        form = ReviewForm()
    
    return render(request, 'shop/add_review.html', {
        'book': book,
        'form': form
    })


# Vues AJAX
def get_books_ajax(request):
    """Vue AJAX pour récupérer des livres (pour l'autocomplétion)"""
    query = request.GET.get('q', '')
    books = Book.objects.filter(
        is_available=True,
        title__icontains=query
    )[:10]
    
    data = [{
        'id': book.id,
        'title': book.title,
        'author': book.get_authors_display(),
        'price': float(book.display_price),
        'cover_url': book.cover_image.url if book.cover_image else '',
        'url': book.get_absolute_url()
    } for book in books]
    
    return JsonResponse(data, safe=False)


def book_search_suggestions(request):
    """Vue pour les suggestions de recherche"""
    query = validate_search_query(request.GET.get('q', ''), max_length=100)
    
    if not query or len(query) < 2:
        return JsonResponse([], safe=False)
    
    books = Book.objects.filter(
        is_available=True,
        title__icontains=query
    )[:5]
    
    suggestions = [book.title for book in books]
    return JsonResponse(suggestions, safe=False)


# Vue pour la page d'accueil de la boutique
def shop_home(request):
    """Page d'accueil de la boutique"""
    featured_books = Book.objects.filter(is_available=True, is_featured=True)[:8]
    bestsellers = Book.objects.filter(is_available=True, is_bestseller=True)[:8]
    new_books = Book.objects.filter(is_available=True).order_by('-created_at')[:8]
    categories = Category.objects.filter(is_active=True)[:6]
    
    context = {
        'featured_books': featured_books,
        'bestsellers': bestsellers,
        'new_books': new_books,
        'categories': categories,
    }
    
    return render(request, 'shop/shop_home.html', context)


# Vues pour le panier
def get_or_create_cart(request):
    """
    Récupère ou crée un panier pour l'utilisateur ou la session.
    
    Si l'utilisateur est authentifié, récupère/crée un panier lié à
    l'utilisateur. Sinon, utilise la clé de session pour gérer le panier.
    
    Args:
        request: La requête HTTP
        
    Returns:
        Cart: Le panier de l'utilisateur ou de la session
    """
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, defaults={'session_key': None})
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key, defaults={'user': None})
    return cart


def add_to_cart(request, book_id):
    """
    Ajoute un livre au panier via AJAX.
    
    Vérifie la disponibilité et le stock avant d'ajouter l'article.
    Retourne une réponse JSON avec le statut de l'opération.
    
    Args:
        request: La requête HTTP (POST uniquement)
        book_id: L'ID du livre à ajouter
        
    Returns:
        JsonResponse: Réponse JSON avec le statut et les infos du panier
    """
    if request.method == 'POST':
        try:
            book = get_object_or_404(Book, id=book_id, is_available=True)
            quantity = int(request.POST.get('quantity', 1))
            
            if quantity <= 0:
                return JsonResponse({'error': 'La quantité doit être positive'}, status=400)
            
            # Validation pour les précommandes
            if book.is_preorder:
                if not book.is_available_for_preorder():
                    return JsonResponse({
                        'error': 'Cette précommande n\'est plus disponible'
                    }, status=400)
                if not book.can_preorder(quantity):
                    if book.preorder_max_quantity:
                        return JsonResponse({
                            'error': f'Il ne reste que {book.preorder_max_quantity - book.preorder_current_quantity} précommande(s) disponible(s)'
                        }, status=400)
                    else:
                        return JsonResponse({
                            'error': 'Cette précommande n\'est plus disponible'
                        }, status=400)
            else:
                # Validation pour les livres normaux
                if quantity > book.stock_quantity:
                    return JsonResponse({'error': 'Stock insuffisant'}, status=400)
            
            cart = get_or_create_cart(request)
            
            # Vérifier si le livre est déjà dans le panier
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                book=book,
                defaults={'quantity': quantity}
            )
            
            if not created:
                # Si l'article existe déjà, ajouter la quantité
                new_quantity = cart_item.quantity + quantity
                # Validation pour les précommandes
                if book.is_preorder:
                    if not book.can_preorder(new_quantity):
                        if book.preorder_max_quantity:
                            return JsonResponse({
                                'error': f'Il ne reste que {book.preorder_max_quantity - book.preorder_current_quantity} précommande(s) disponible(s)'
                            }, status=400)
                        else:
                            return JsonResponse({
                                'error': 'Cette précommande n\'est plus disponible'
                            }, status=400)
                else:
                    # Validation pour les livres normaux
                    if new_quantity > book.stock_quantity:
                        return JsonResponse({'error': 'Stock insuffisant'}, status=400)
                cart_item.quantity = new_quantity
                cart_item.save()
            
            # Retourner les informations du panier
            return JsonResponse({
                'success': True,
                'message': f'{book.title} ajouté au panier',
                'cart_total_items': cart.total_items,
                'cart_total_price': float(cart.final_price),
                'item_total_price': float(cart_item.total_price)
            })
        except Exception as e:
            return JsonResponse({'error': f'Erreur serveur: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


def remove_from_cart(request, book_id):
    """
    Supprime un livre du panier via AJAX.
    
    Args:
        request: La requête HTTP (POST uniquement)
        book_id: L'ID du livre à supprimer
        
    Returns:
        JsonResponse: Réponse JSON avec le statut et les infos du panier
    """
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        cart = get_or_create_cart(request)
        
        try:
            cart_item = CartItem.objects.get(cart=cart, book=book)
            cart_item.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'{book.title} supprimé du panier',
                'cart_total_items': cart.total_items,
                'cart_total_price': float(cart.final_price)
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'error': 'Article non trouvé dans le panier'}, status=404)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


def update_cart_item(request, book_id):
    """
    Met à jour la quantité d'un article dans le panier via AJAX.
    
    Vérifie la disponibilité et le stock avant la mise à jour.
    
    Args:
        request: La requête HTTP (POST uniquement)
        book_id: L'ID du livre à mettre à jour
        
    Returns:
        JsonResponse: Réponse JSON avec le statut et les infos du panier
    """
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            return JsonResponse({'error': 'La quantité doit être positive'}, status=400)
        
        # Validation pour les précommandes
        if book.is_preorder:
            if not book.is_available_for_preorder():
                return JsonResponse({
                    'error': 'Cette précommande n\'est plus disponible'
                }, status=400)
            if not book.can_preorder(quantity):
                if book.preorder_max_quantity:
                    return JsonResponse({
                        'error': f'Il ne reste que {book.preorder_max_quantity - book.preorder_current_quantity} précommande(s) disponible(s)'
                    }, status=400)
                else:
                    return JsonResponse({
                        'error': 'Cette précommande n\'est plus disponible'
                    }, status=400)
        else:
            # Validation pour les livres normaux
            if quantity > book.stock_quantity:
                return JsonResponse({'error': 'Stock insuffisant'}, status=400)
        
        cart = get_or_create_cart(request)
        
        try:
            cart_item = CartItem.objects.get(cart=cart, book=book)
            cart_item.quantity = quantity
            cart_item.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Quantité mise à jour pour {book.title}',
                'cart_total_items': cart.total_items,
                'cart_total_price': float(cart.final_price),
                'item_total_price': float(cart_item.total_price)
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'error': 'Article non trouvé dans le panier'}, status=404)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


def decrease_cart_item(request, book_id):
    """Diminue la quantité d'un article dans le panier"""
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        cart = get_or_create_cart(request)
        
        try:
            cart_item = CartItem.objects.get(cart=cart, book=book)
            
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                message = f'Quantité diminuée pour {book.title}'
            else:
                # Si la quantité est 1, supprimer l'article
                cart_item.delete()
                message = f'{book.title} supprimé du panier'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'cart_total_items': cart.total_items,
                'cart_total_price': float(cart.final_price),
                'item_removed': cart_item.quantity == 0 if 'cart_item' in locals() else True
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'error': 'Article non trouvé dans le panier'}, status=404)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


def cart_detail(request):
    """Affiche le détail du panier"""
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('book').all()
    
    # Vérifier s'il y a au moins un article en précommande
    has_preorder = any(item.book.is_preorder for item in cart_items)
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'has_preorder': has_preorder,
    }
    
    return render(request, 'shop/cart_detail.html', context)


def cart_summary(request):
    """Retourne un résumé du panier (pour AJAX)"""
    try:
        cart = get_or_create_cart(request)
        cart_items = cart.items.select_related('book').prefetch_related('book__authors').all()[:3]  # Limiter à 3 articles pour l'aperçu
        
        items_data = []
        for item in cart_items:
            # Gérer le cas où il y a plusieurs auteurs - prendre le premier pour le slug
            first_author = item.book.authors.first()
            author_slug = getattr(first_author, 'slug', None) if first_author else None
            if not author_slug and first_author:
                author_slug = first_author.id
            
            items_data.append({
                'id': item.book.id,
                'slug': item.book.slug,
                'title': item.book.title,
                'author': item.book.get_authors_display(),
                'author_slug': author_slug,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price),
                'cover_url': item.book.cover_image.url if item.book.cover_image else '',
                'is_on_sale': item.book.is_on_sale,
                'original_price': float(item.book.price) if item.book.is_on_sale else None,
                'discount_percentage': item.book.discount_percentage if item.book.is_on_sale else 0
            })
        
        return JsonResponse({
            'total_items': cart.total_items,
            'total_price': float(cart.total_price),
            'total_discount': float(cart.total_discount),
            'final_price': float(cart.final_price),
            'items': items_data
        })
    except Exception as e:
        # En cas d'erreur, retourner un panier vide
        return JsonResponse({
            'total_items': 0,
            'total_price': 0.0,
            'total_discount': 0.0,
            'final_price': 0.0,
            'items': []
        })


def clear_cart(request):
    """Vide le panier"""
    if request.method == 'POST':
        cart = get_or_create_cart(request)
        cart.clear()
        
        return JsonResponse({
            'success': True,
            'message': 'Panier vidé',
            'cart_total_items': 0,
            'cart_total_price': 0.0
        })
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


def test_cart_transfer(request):
    """Vue de test pour vérifier le transfert de panier"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Utilisateur non connecté'})
    
    # Récupérer le panier actuel
    current_cart = get_or_create_cart(request)
    
    # Récupérer tous les paniers de l'utilisateur
    user_carts = Cart.objects.filter(user=request.user)
    
    # Récupérer tous les paniers de session
    session_carts = Cart.objects.filter(session_key__isnull=False, user__isnull=True)
    
    data = {
        'user': request.user.username,
        'session_key': request.session.session_key,
        'current_cart_id': current_cart.id,
        'current_cart_items': current_cart.total_items,
        'user_carts_count': user_carts.count(),
        'session_carts_count': session_carts.count(),
        'user_carts': [
            {
                'id': cart.id,
                'items': cart.total_items,
                'created': cart.created_at.isoformat()
            } for cart in user_carts
        ],
        'session_carts': [
            {
                'id': cart.id,
                'session_key': cart.session_key,
                'items': cart.total_items,
                'created': cart.created_at.isoformat()
            } for cart in session_carts
        ]
    }
    
    return JsonResponse(data)


def force_cart_transfer(request):
    """Force le transfert de panier pour test"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Utilisateur non connecté'})
    
    session_key = request.session.session_key
    
    if session_key:
        # Récupérer le panier de session
        session_cart = Cart.objects.filter(session_key=session_key).first()
        
        if session_cart:
            # Vérifier si l'utilisateur a déjà un panier
            user_cart = Cart.objects.filter(user=request.user).first()
            
            if user_cart:
                # Fusionner les paniers
                for item in session_cart.items.all():
                    existing_item = user_cart.items.filter(book=item.book).first()
                    if existing_item:
                        existing_item.quantity += item.quantity
                        existing_item.save()
                    else:
                        item.cart = user_cart
                        item.save()
                
                # Supprimer le panier de session
                session_cart.delete()
                message = "Paniers fusionnés"
            else:
                # Transférer le panier de session vers l'utilisateur
                session_cart.user = request.user
                session_cart.session_key = None
                session_cart.save()
                message = "Panier transféré"
            
            return JsonResponse({
                'success': True,
                'message': message,
                'session_cart_items': session_cart.total_items if 'session_cart' in locals() else 0
            })
        else:
            return JsonResponse({'error': 'Aucun panier de session trouvé'})
    else:
        return JsonResponse({'error': 'Aucune clé de session'})


# Vues pour le processus de commande et paiement
@login_required
@ratelimit(key='user', rate='10/1h', method='POST')
def checkout(request):
    """
    Vue pour le processus de commande avec rate limiting.
    
    Limite à 10 commandes par heure par utilisateur pour prévenir les abus.
    """
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('book').all()
    
    if not cart_items.exists():
        messages.warning(request, 'Votre panier est vide.')
        return redirect('shop:cart_detail')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        payment_form = PaymentMethodForm(request.POST)
        
        if form.is_valid() and payment_form.is_valid():
            try:
                with transaction.atomic():
                    # Vérifier si le panier contient des précommandes
                    has_preorder = any(item.book.is_preorder for item in cart_items)
                    
                    # Vérifier les quantités de précommande avant de créer la commande
                    if has_preorder:
                        for cart_item in cart_items:
                            if cart_item.book.is_preorder:
                                if not cart_item.book.can_preorder(cart_item.quantity):
                                    messages.error(
                                        request,
                                        f'La quantité demandée pour "{cart_item.book.title}" dépasse '
                                        f'le nombre de précommandes disponibles.'
                                    )
                                    return redirect('shop:checkout')
                    
                    # Créer la commande
                    order = form.save(commit=False)
                    order.user = request.user
                    
                    # Marquer comme précommande si nécessaire
                    if has_preorder:
                        order.is_preorder = True
                        # Enregistrer la date originale pour chaque livre en précommande
                        for cart_item in cart_items:
                            if cart_item.book.is_preorder and cart_item.book.preorder_available_date:
                                if not order.preorder_original_date:
                                    order.preorder_original_date = cart_item.book.preorder_available_date
                                # Prendre la date la plus proche
                                elif cart_item.book.preorder_available_date < order.preorder_original_date:
                                    order.preorder_original_date = cart_item.book.preorder_available_date
                    
                    # Récupérer les paramètres de la boutique
                    shop_settings = ShopSettings.get_settings()
                    
                    # Calculer les montants
                    order.subtotal = cart.final_price
                    order.shipping_cost = Decimal('0.00') if order.subtotal >= shop_settings.free_shipping_threshold else shop_settings.standard_shipping_cost
                    order.tax_amount = order.subtotal * (shop_settings.tax_rate / Decimal('100'))
                    
                    order.total_amount = order.subtotal + order.shipping_cost + order.tax_amount
                    
                    order.save()
                    
                    # Logger la création de la commande
                    security_logger = logging.getLogger('security')
                    security_logger.info(
                        f"Commande créée: order_id={order.id}, "
                        f"order_number={order.order_number}, "
                        f"user_id={request.user.id}, "
                        f"user_email={request.user.email}, "
                        f"total_amount={order.total_amount}"
                    )
                    
                    # Mettre à jour les informations de livraison de l'utilisateur
                    user = request.user
                    user.shipping_address = order.shipping_address
                    user.shipping_city = order.shipping_city
                    user.shipping_postal_code = order.shipping_postal_code
                    user.shipping_country = order.shipping_country
                    user.shipping_phone = order.shipping_phone
                    user.save()
                    
                    # Créer les articles de commande et mettre à jour les compteurs de précommande
                    for cart_item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            book=cart_item.book,
                            quantity=cart_item.quantity,
                            unit_price=cart_item.unit_price,
                            total_price=cart_item.total_price
                        )
                        
                        # Incrémenter le compteur de précommande si nécessaire
                        if cart_item.book.is_preorder:
                            cart_item.book.preorder_current_quantity += cart_item.quantity
                            cart_item.book.save(update_fields=['preorder_current_quantity'])
                    
                    # Créer le paiement
                    payment_method = payment_form.cleaned_data['payment_method']
                    payment = Payment.objects.create(
                        order=order,
                        payment_method=payment_method,
                        amount=order.total_amount,
                        currency='EUR'
                    )
                    
                    # Envoyer l'email de confirmation de précommande si nécessaire
                    if has_preorder:
                        from shop.services.email_service import OrderEmailService
                        try:
                            OrderEmailService.send_preorder_confirmation_email(order)
                        except Exception as e:
                            logger.warning(f"Erreur envoi email confirmation précommande {order.order_number}: {e}")
                    
                    # Rediriger vers le paiement approprié
                    if payment_method == 'paypal':
                        return redirect('shop:paypal_payment', order_id=order.id)
                    else:
                        messages.error(request, 'Méthode de paiement non supportée.')
                        return redirect('shop:checkout')
                        
            except Exception as e:
                # Logger l'erreur de création de commande
                security_logger = logging.getLogger('security')
                security_logger.error(
                    f"Erreur création commande: user_id={request.user.id}, "
                    f"user_email={request.user.email}, error={str(e)}"
                )
                messages.error(
                    request,
                    f'Erreur lors de la création de la commande: {str(e)}'
                )
                return redirect('shop:checkout')
    else:
        # Pré-remplir le formulaire avec les données de l'utilisateur
        user = request.user
        initial_data = {
            'shipping_first_name': user.first_name or '',
            'shipping_last_name': user.last_name or '',
            'shipping_address': user.shipping_address or '',
            'shipping_city': user.shipping_city or '',
            'shipping_postal_code': user.shipping_postal_code or '',
            'shipping_country': user.shipping_country or 'France',
            'shipping_phone': user.phone or '',
        }
        
        form = CheckoutForm(initial=initial_data)
        payment_form = PaymentMethodForm()
    
    # Récupérer les paramètres de la boutique
    shop_settings = ShopSettings.get_settings()
    
    # Calculer les montants pour l'affichage
    subtotal = cart.final_price
    shipping_cost = Decimal('0.00') if subtotal >= shop_settings.free_shipping_threshold else shop_settings.standard_shipping_cost
    tax_amount = subtotal * (shop_settings.tax_rate / Decimal('100'))
    total_amount = subtotal + shipping_cost + tax_amount
    
    # Vérifier si le panier contient des précommandes
    has_preorder = any(item.book.is_preorder for item in cart_items)
    preorder_items = [item for item in cart_items if item.book.is_preorder]
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'form': form,
        'payment_form': payment_form,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
        'has_preorder': has_preorder,
        'preorder_items': preorder_items,
    }
    
    return render(request, 'shop/checkout.html', context)


@login_required
def paypal_payment(request, order_id):
    """Vue pour traiter le paiement PayPal"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.payment_status != 'pending':
        messages.error(request, 'Cette commande a déjà été traitée.')
        return redirect('shop:order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'paypal_client_id': settings.PAYPAL_CLIENT_ID,
        'paypal_mode': settings.PAYPAL_MODE,
    }
    
    return render(request, 'shop/paypal_payment.html', context)


@login_required
def paypal_success(request):
    """Vue appelée après un paiement PayPal réussi"""
    # Récupérer le token PayPal depuis l'URL (paramètres possibles: 'token', 'PayerID', etc.)
    paypal_token = request.GET.get('token') or request.GET.get('PayerID')
    
    if paypal_token:
        # Capturer le paiement PayPal
        success, order, error_message = capture_paypal_order_by_token(paypal_token)
        
        if success and order:
            # Vérifier que la commande appartient à l'utilisateur
            if order.user != request.user:
                messages.error(request, 'Erreur : cette commande ne vous appartient pas.')
                return redirect('shop:order_list')
            
            messages.success(request, 'Paiement effectué avec succès ! Votre commande est en cours de traitement.')
        else:
            # Si la capture a échoué, vérifier si le paiement a déjà été capturé
            try:
                payment = Payment.objects.get(paypal_payment_id=paypal_token)
                if payment.status == 'completed':
                    messages.success(request, 'Paiement déjà traité avec succès !')
                else:
                    messages.warning(request, f'Erreur lors du traitement du paiement: {error_message or "Erreur inconnue"}')
            except Payment.DoesNotExist:
                # Essayer de trouver une commande en attente pour cet utilisateur
                pending_order = Order.objects.filter(
                    user=request.user,
                    payment_status='pending',
                    payment__method='paypal'
                ).order_by('-created_at').first()
                
                if pending_order and pending_order.payment.paypal_payment_id:
                    # Essayer de capturer avec l'ID PayPal de la commande en attente
                    success, order, error_message = capture_paypal_order_by_token(
                        pending_order.payment.paypal_payment_id
                    )
                    if success and order:
                        messages.success(request, 'Paiement effectué avec succès ! Votre commande est en cours de traitement.')
                    else:
                        messages.warning(request, 'Paiement non trouvé. Veuillez contacter le support si le paiement a été effectué.')
                else:
                    messages.warning(request, 'Paiement non trouvé. Veuillez contacter le support si le paiement a été effectué.')
    else:
        # Pas de token dans l'URL, essayer de trouver une commande en attente
        pending_order = Order.objects.filter(
            user=request.user,
            payment_status='pending',
            payment__method='paypal',
            payment__paypal_payment_id__isnull=False
        ).order_by('-created_at').first()
        
        if pending_order:
            # Essayer de capturer avec l'ID PayPal de la commande en attente
            success, order, error_message = capture_paypal_order_by_token(
                pending_order.payment.paypal_payment_id
            )
            if success and order:
                messages.success(request, 'Paiement effectué avec succès ! Votre commande est en cours de traitement.')
            else:
                CartService.clear_cart(request.user)
                messages.info(request, 'Retour depuis PayPal. Si le paiement a été effectué, votre commande sera mise à jour.')
        else:
            # Vider le panier par sécurité
            CartService.clear_cart(request.user)
            messages.info(request, 'Retour depuis PayPal. Si le paiement a été effectué, votre commande sera mise à jour.')
    
    return redirect('shop:order_list')


@login_required
def paypal_cancel(request):
    """Vue appelée si l'utilisateur annule le paiement PayPal"""
    messages.warning(request, 'Paiement PayPal annulé.')
    return redirect('shop:order_list')


@login_required
def manual_payment(request, order_id):
    """Vue pour le paiement manuel par virement bancaire"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.payment_status != 'pending':
        messages.error(request, 'Cette commande a déjà été traitée.')
        return redirect('shop:order_detail', order_id=order.id)
    
    # Mettre à jour le paiement pour indiquer qu'il s'agit d'un paiement manuel
    payment = order.payment
    payment.payment_method = 'bank_transfer'
    payment.status = 'pending'
    payment.save()
    
    # Vider le panier après création de la commande pour paiement manuel
    CartService.clear_cart(request.user)
    
    # Ici, vous pourriez envoyer un email avec les coordonnées bancaires
    # ou afficher une page avec les informations de paiement
    
    context = {
        'order': order,
        'payment': payment,
    }
    
    return render(request, 'shop/manual_payment.html', context)


@login_required
def order_detail(request, order_id):
    """
    Vue pour afficher les détails d'une commande.
    
    Vérifie que l'utilisateur peut voir cette commande
    (soit c'est sa commande, soit il est staff).
    """
    order = get_object_or_404(Order, id=order_id)
    
    # Vérifier que l'utilisateur peut voir cette commande
    if order.user != request.user and not request.user.is_staff:
        messages.error(
            request,
            'Vous n\'avez pas accès à cette commande.'
        )
        return redirect('shop:order_list')
    
    context = {
        'order': order,
        'order_items': order.items.select_related('book').all(),
    }
    
    return render(request, 'shop/order_detail.html', context)


@login_required
def order_list(request):
    """Vue pour lister les commandes de l'utilisateur"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'shop/order_list.html', context)


@login_required
def cancel_order(request, order_id):
    """Vue pour annuler une commande"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        if not order.can_be_cancelled:
            return JsonResponse({'error': 'Cette commande ne peut pas être annulée'}, status=400)
        
        # Annuler la commande
        order.status = 'cancelled'
        order.payment_status = 'cancelled'
        order.save()
        
        # Annuler le paiement associé
        if hasattr(order, 'payment'):
            order.payment.status = 'cancelled'
            order.payment.save()
        
        messages.success(request, f'Commande {order.order_number} annulée avec succès.')
        
        return JsonResponse({
            'success': True,
            'message': 'Commande annulée avec succès',
            'order_id': order.id
        })
        
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Erreur lors de l\'annulation: {str(e)}'}, status=500)


@login_required
def request_refund(request, order_id):
    """Vue pour demander un remboursement"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Vérifier si la commande peut être remboursée
    if order.payment_status != 'paid':
        messages.error(request, 'Cette commande ne peut pas être remboursée.')
        return redirect('shop:order_detail', order_id=order.id)
    
    if request.method == 'POST':
        form = RefundRequestForm(request.POST, order=order)
        if form.is_valid():
            refund = form.save(commit=False)
            refund.order = order
            refund.requested_by = request.user
            refund.save()
            
            messages.success(request, 'Votre demande de remboursement a été envoyée. Nous vous contacterons sous 24-48h.')
            return redirect('shop:order_detail', order_id=order.id)
    else:
        form = RefundRequestForm(order=order)
    
    context = {
        'order': order,
        'form': form,
    }
    
    return render(request, 'shop/request_refund.html', context)


@login_required
def refund_list(request):
    """Vue pour lister les remboursements de l'utilisateur"""
    refunds = Refund.objects.filter(requested_by=request.user).order_by('-created_at')
    
    context = {
        'refunds': refunds,
    }
    
    return render(request, 'shop/refund_list.html', context)


def apply_promo_code(request):
    """Vue AJAX pour appliquer un code promo"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    form = PromoCodeForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': form.errors['code'][0]}, status=400)
    
    code = form.cleaned_data['code']
    
    # Récupérer le panier
    cart = CartService.get_or_create_cart(request.user, request.session.session_key)
    
    # Appliquer le code promo
    success, message = PromoCodeService.apply_promo_code(code, request.user, cart)
    
    if success:
        # Recalculer les totaux
        discounts = DiscountService.calculate_cart_discounts(request.user, cart)
        
        return JsonResponse({
            'success': True,
            'message': message,
            'discounts': {
                'loyalty_discount': float(discounts['loyalty_discount']),
                'promo_discount': float(discounts['promo_discount']),
                'total_discount': float(discounts['total_discount']),
            },
            'cart_total': float(cart.total_price),
            'final_total': float(cart.total_price - discounts['total_discount'])
        })
    else:
        return JsonResponse({'error': message}, status=400)


def remove_promo_code(request):
    """Vue AJAX pour supprimer un code promo"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    # Récupérer le panier
    cart = CartService.get_or_create_cart(request.user, request.session.session_key)
    
    # Supprimer le code promo
    success, message = PromoCodeService.remove_promo_code(cart)
    
    if success:
        # Recalculer les totaux
        discounts = DiscountService.calculate_cart_discounts(request.user, cart)
        
        return JsonResponse({
            'success': True,
            'message': message,
            'discounts': {
                'loyalty_discount': float(discounts['loyalty_discount']),
                'promo_discount': float(discounts['promo_discount']),
                'total_discount': float(discounts['total_discount']),
            },
            'cart_total': float(cart.total_price),
            'final_total': float(cart.total_price - discounts['total_discount'])
        })
    else:
        return JsonResponse({'error': message}, status=400)


@login_required
def loyalty_status(request):
    """Vue pour afficher le statut de fidélité de l'utilisateur"""
    loyalty_status = LoyaltyService.get_or_create_loyalty_status(request.user)
    loyalty_program = loyalty_status.get_available_loyalty_discount()
    
    # Obtenir les statistiques réelles basées sur les commandes confirmées
    real_stats = loyalty_status.get_real_statistics()
    
    # Récupérer les commandes confirmées récentes
    recent_orders = Order.objects.filter(user=request.user, status='confirmed').order_by('-created_at')[:5]
    
    context = {
        'loyalty_status': loyalty_status,
        'loyalty_program': loyalty_program,
        'real_stats': real_stats,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'shop/loyalty_status.html', context)


def get_cart_discounts(request):
    """Vue AJAX pour récupérer les réductions du panier"""
    cart = CartService.get_or_create_cart(request.user, request.session.session_key)
    discounts = DiscountService.calculate_cart_discounts(request.user, cart)
    
    return JsonResponse({
        'discounts': {
            'loyalty_discount': float(discounts['loyalty_discount']),
            'promo_discount': float(discounts['promo_discount']),
            'total_discount': float(discounts['total_discount']),
        },
        'cart_total': float(cart.total_price),
        'final_total': float(cart.total_price - discounts['total_discount']),
        'loyalty_program': {
            'name': discounts['loyalty_program'].name if discounts['loyalty_program'] else None,
            'discount_value': float(discounts['loyalty_program'].discount_value) if discounts['loyalty_program'] else 0,
            'discount_type': discounts['loyalty_program'].discount_type if discounts['loyalty_program'] else None,
        } if discounts['loyalty_program'] else None,
        'promo_code': {
            'code': discounts['promo_code'].code if discounts['promo_code'] else None,
            'name': discounts['promo_code'].name if discounts['promo_code'] else None,
        } if discounts['promo_code'] else None,
    })


# Vues de redirection vers l'administration
def redirect_to_admin_create_book(request):
    """Redirige vers la création de livre dans l'administration"""
    return HttpResponseRedirect(reverse('admin_panel:create_book'))


def redirect_to_admin_books(request, slug=None):
    """Redirige vers la liste des livres dans l'administration"""
    return HttpResponseRedirect(reverse('admin_panel:books'))


# ===== GESTION DES FACTURES =====

@login_required
def create_invoice(request, order_id):
    """Créer une facture pour une commande"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Vérifier si une facture existe déjà
    if hasattr(order, 'invoice'):
        messages.info(request, 'Une facture existe déjà pour cette commande.')
        return redirect('shop:order_detail', order_id=order.id)
    
    # Créer la facture
    invoice = Invoice.objects.create(
        order=order,
        billing_name=f"{order.shipping_first_name} {order.shipping_last_name}",
        billing_address=order.shipping_address,
        billing_city=order.shipping_city,
        billing_postal_code=order.shipping_postal_code,
        billing_country=order.shipping_country,
        subtotal=order.subtotal,
        shipping_cost=order.shipping_cost,
        total_amount=order.total_amount,
        status='sent',  # Marquer comme envoyée dès la création
    )
    
    messages.success(request, f'Facture {invoice.invoice_number} créée avec succès.')
    return redirect('shop:invoice_detail', invoice_id=invoice.id)


@login_required
def invoice_detail(request, invoice_id):
    """Afficher le détail d'une facture"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Vérifier que l'utilisateur peut voir cette facture
    if not request.user.is_staff and invoice.order.user != request.user:
        messages.error(request, 'Vous n\'avez pas accès à cette facture.')
        return redirect('shop:order_list')
    
    context = {
        'invoice': invoice,
        'order': invoice.order,
        'order_items': invoice.order.items.all(),
        'shop_settings': ShopSettings.get_settings(),
    }
    
    return render(request, 'shop/invoice_detail.html', context)


@login_required
def invoice_pdf(request, invoice_id):
    """Générer le PDF d'une facture"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Vérifier que l'utilisateur peut voir cette facture
    if not request.user.is_staff and invoice.order.user != request.user:
        messages.error(request, 'Vous n\'avez pas accès à cette facture.')
        return redirect('shop:order_list')
    
    context = {
        'invoice': invoice,
        'order': invoice.order,
        'order_items': invoice.order.items.all(),
        'shop_settings': ShopSettings.get_settings(),
    }
    
    # Pour l'instant, on retourne la version HTML
    # Plus tard, on pourra ajouter la génération PDF avec weasyprint
    return render(request, 'shop/invoice_pdf.html', context)


@login_required
def invoice_list(request):
    """Liste des factures de l'utilisateur"""
    if request.user.is_staff:
        # Admin : voir toutes les factures
        invoices = Invoice.objects.all().order_by('-invoice_date')
    else:
        # Utilisateur : voir ses factures
        invoices = Invoice.objects.filter(order__user=request.user).order_by('-invoice_date')
    
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'invoices': page_obj,
    }
    
    return render(request, 'shop/invoice_list.html', context)


@login_required
def cancel_order(request, order_id):
    """Annuler une commande côté client"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Vérifier que la commande peut être annulée par le client
    if order.status not in ['pending', 'processing']:
        messages.error(request, f'Impossible d\'annuler cette commande. Statut actuel: {order.get_status_display()}')
        return redirect('shop:order_detail', order_id=order.id)
    
    # Vérifier que le paiement n'est pas déjà confirmé
    if order.payment_status == 'paid':
        messages.error(request, 'Impossible d\'annuler cette commande car le paiement a déjà été confirmé.')
        return redirect('shop:order_detail', order_id=order.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Annulation demandée par le client')
        admin_notes = request.POST.get('admin_notes', '')
        
        try:
            # Annuler la commande
            old_status, new_status = order.update_status(
                new_status='cancelled',
                admin_notes=f"{reason}. {admin_notes}" if admin_notes else reason,
                changed_by=request.user
            )
            
            # Marquer le paiement comme échoué si c'était en attente
            if order.payment_status == 'pending':
                order.payment_status = 'failed'
                order.save()
                OrderStatusHistory.objects.create(
                    order=order,
                    old_status='payment_pending',
                    new_status='payment_failed',
                    changed_by=request.user,
                    notes=f"Paiement marqué comme échoué suite à l'annulation par le client"
                )
            
            messages.success(request, f'Votre commande {order.order_number} a été annulée avec succès.', extra_tags='order_cancelled')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'annulation de la commande: {str(e)}', extra_tags='order_error')
            logger.error(f'Erreur annulation commande {order.order_number} par client {request.user.username}: {e}')
        
        return redirect('shop:order_detail', order_id=order.id)
    
    # Afficher le formulaire de confirmation
    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    return render(request, 'shop/cancel_order.html', context)
