from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db import transaction

from .models import Book, Category, BookImage, Review, Cart, CartItem
from .forms import BookForm, CategoryForm, BookImageForm, ReviewForm, BookSearchForm
from author.models import Author


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
    success_url = reverse_lazy('shop:book_list')
    
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
        return reverse('shop:book_detail', kwargs={'slug': self.object.slug})
    
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
