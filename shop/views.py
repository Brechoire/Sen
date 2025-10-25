from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal
import logging

from .models import Book, Category, BookImage, Review, Cart, CartItem, Order, OrderItem, Payment, ShopSettings, Refund, PromoCode, UserLoyaltyStatus, Invoice, OrderStatusHistory
from .forms import BookForm, CategoryForm, BookImageForm, ReviewForm, BookSearchForm, CheckoutForm, PaymentMethodForm, RefundRequestForm, PromoCodeForm
from .services import PromoCodeService, LoyaltyService, DiscountService, CartService
from .paypal_api import create_paypal_order, capture_paypal_order
from django.conf import settings
from author.models import Author

logger = logging.getLogger(__name__)


class BookListView(ListView):
    """Vue pour lister tous les livres avec filtres et recherche"""
    model = Book
    template_name = 'shop/book_list.html'
    context_object_name = 'books'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Book.objects.filter(is_available=True).select_related('author', 'category')
        
        # Filtres
        search_query = self.request.GET.get('query')
        category_slug = self.request.GET.get('category')
        author_id = self.request.GET.get('author')
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        format_filter = self.request.GET.get('format')
        sort_by = self.request.GET.get('sort_by', '-created_at')
        
        # Recherche textuelle
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(subtitle__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(author__first_name__icontains=search_query) |
                Q(author__last_name__icontains=search_query) |
                Q(author__pen_name__icontains=search_query)
            )
        
        # Filtre par catégorie
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filtre par auteur
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # Filtre par prix
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)
        
        # Filtre par format
        if format_filter:
            queryset = queryset.filter(format=format_filter)
        
        # Tri
        if sort_by:
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
        return Book.objects.filter(is_available=True).select_related('author', 'category').prefetch_related('images', 'reviews')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        
        # Livres similaires (même catégorie ou même auteur)
        similar_books = Book.objects.filter(
            is_available=True
        ).filter(
            Q(category=book.category) | Q(author=book.author)
        ).exclude(id=book.id)[:4]
        
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
        ).select_related('author').order_by('-created_at')
        
        # Pagination
        paginator = Paginator(books, 12)
        page_number = self.request.GET.get('page')
        context['books'] = paginator.get_page(page_number)
        
        return context


# Vues d'administration (nécessitent une connexion)
class BookCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer un nouveau livre"""
    model = Book
    form_class = BookForm
    template_name = 'shop/book_form.html'
    success_url = reverse_lazy('admin_panel:books')
    
    def form_valid(self, form):
        messages.success(self.request, 'Le livre a été créé avec succès.')
        return super().form_valid(form)


class BookUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un livre existant"""
    model = Book
    form_class = BookForm
    template_name = 'shop/book_form.html'
    slug_field = 'slug'
    
    def get_success_url(self):
        return reverse('admin_panel:books')
    
    def form_valid(self, form):
        messages.success(self.request, 'Le livre a été modifié avec succès.')
        return super().form_valid(form)


class BookDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer un livre"""
    model = Book
    template_name = 'shop/book_confirm_delete.html'
    slug_field = 'slug'
    success_url = reverse_lazy('shop:book_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Le livre a été supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle catégorie"""
    model = Category
    form_class = CategoryForm
    template_name = 'shop/category_form.html'
    success_url = reverse_lazy('shop:book_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'La catégorie a été créée avec succès.')
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier une catégorie existante"""
    model = Category
    form_class = CategoryForm
    template_name = 'shop/category_form.html'
    slug_field = 'slug'
    success_url = reverse_lazy('shop:book_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'La catégorie a été modifiée avec succès.')
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer une catégorie"""
    model = Category
    template_name = 'shop/category_confirm_delete.html'
    slug_field = 'slug'
    success_url = reverse_lazy('shop:book_list')
    
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
                messages.success(request, 'Votre avis a été ajouté et sera publié après validation.')
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
        'author': book.author.display_name,
        'price': float(book.display_price),
        'cover_url': book.cover_image.url if book.cover_image else '',
        'url': book.get_absolute_url()
    } for book in books]
    
    return JsonResponse(data, safe=False)


def book_search_suggestions(request):
    """Vue pour les suggestions de recherche"""
    query = request.GET.get('q', '')
    if len(query) < 2:
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
    """Récupère ou crée un panier pour l'utilisateur ou la session"""
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
    """Ajoute un livre au panier"""
    if request.method == 'POST':
        try:
            book = get_object_or_404(Book, id=book_id, is_available=True)
            quantity = int(request.POST.get('quantity', 1))
            
            if quantity <= 0:
                return JsonResponse({'error': 'La quantité doit être positive'}, status=400)
            
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
    """Supprime un livre du panier"""
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
    """Met à jour la quantité d'un article dans le panier"""
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            return JsonResponse({'error': 'La quantité doit être positive'}, status=400)
        
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
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    
    return render(request, 'shop/cart_detail.html', context)


def cart_summary(request):
    """Retourne un résumé du panier (pour AJAX)"""
    try:
        cart = get_or_create_cart(request)
        cart_items = cart.items.select_related('book', 'book__author').all()[:3]  # Limiter à 3 articles pour l'aperçu
        
        items_data = []
        for item in cart_items:
            # Gérer le cas où l'auteur n'a pas de slug
            author_slug = getattr(item.book.author, 'slug', None) or item.book.author.id
            
            items_data.append({
                'id': item.book.id,
                'slug': item.book.slug,
                'title': item.book.title,
                'author': item.book.author.display_name,
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
def checkout(request):
    """Vue pour le processus de commande"""
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
                    # Créer la commande
                    order = form.save(commit=False)
                    order.user = request.user
                    
                    # Récupérer les paramètres de la boutique
                    shop_settings = ShopSettings.get_settings()
                    
                    # Calculer les montants
                    order.subtotal = cart.final_price
                    order.shipping_cost = Decimal('0.00') if order.subtotal >= shop_settings.free_shipping_threshold else shop_settings.standard_shipping_cost
                    order.tax_amount = order.subtotal * (shop_settings.tax_rate / Decimal('100'))
                    
                    order.total_amount = order.subtotal + order.shipping_cost + order.tax_amount
                    
                    order.save()
                    
                    # Mettre à jour les informations de livraison de l'utilisateur
                    user = request.user
                    user.shipping_address = order.shipping_address
                    user.shipping_city = order.shipping_city
                    user.shipping_postal_code = order.shipping_postal_code
                    user.shipping_country = order.shipping_country
                    user.shipping_phone = order.shipping_phone
                    user.save()
                    
                    # Créer les articles de commande
                    for cart_item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            book=cart_item.book,
                            quantity=cart_item.quantity,
                            unit_price=cart_item.unit_price,
                            total_price=cart_item.total_price
                        )
                    
                    # Créer le paiement
                    payment_method = payment_form.cleaned_data['payment_method']
                    payment = Payment.objects.create(
                        order=order,
                        payment_method=payment_method,
                        amount=order.total_amount,
                        currency='EUR'
                    )
                    
                    # Rediriger vers le paiement approprié
                    if payment_method == 'paypal':
                        return redirect('shop:paypal_payment', order_id=order.id)
                    else:
                        messages.error(request, 'Méthode de paiement non supportée.')
                        return redirect('shop:checkout')
                        
            except Exception as e:
                messages.error(request, f'Erreur lors de la création de la commande: {str(e)}')
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
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'form': form,
        'payment_form': payment_form,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
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
    # S'assurer que le panier est vidé après un paiement réussi
    CartService.clear_cart(request.user)
    
    messages.success(request, 'Paiement effectué avec succès ! Votre commande est en cours de traitement.')
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
    """Vue pour afficher les détails d'une commande"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
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
