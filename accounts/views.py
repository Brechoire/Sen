from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from .models import User
from shop.models import Cart


class SignUpView(CreateView):
    """Vue d'inscription"""
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Connecter automatiquement l'utilisateur après l'inscription
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1']
        )
        if user:
            login(self.request, user)
            # Transférer le panier de session vers l'utilisateur
            self.transfer_cart_to_user(user)
            messages.success(self.request, f"Bienvenue {user.full_name} ! Votre compte a été créé avec succès.")
        return response
    
    def transfer_cart_to_user(self, user):
        """Transfère le panier de session vers l'utilisateur"""
        session_key = self.request.session.session_key
        
        if session_key:
            # Récupérer le panier de session
            session_cart = Cart.objects.filter(session_key=session_key).first()
            
            if session_cart:
                # Vérifier si l'utilisateur a déjà un panier
                user_cart = Cart.objects.filter(user=user).first()
                
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
                else:
                    # Transférer le panier de session vers l'utilisateur
                    session_cart.user = user
                    session_cart.session_key = None
                    session_cart.save()


class CustomLoginView(LoginView):
    """Vue de connexion personnalisée"""
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'

    def get_success_url(self):
        return reverse_lazy('accounts:profile')

    def form_valid(self, form):
        user = form.get_user()
        # Transférer le panier de session vers l'utilisateur
        self.transfer_cart_to_user(user)
        messages.success(self.request, f"Bonjour {user.full_name} !")
        return super().form_valid(form)
    
    def transfer_cart_to_user(self, user):
        """Transfère le panier de session vers l'utilisateur"""
        session_key = self.request.session.session_key
        
        if session_key:
            # Récupérer le panier de session
            session_cart = Cart.objects.filter(session_key=session_key).first()
            
            if session_cart:
                # Vérifier si l'utilisateur a déjà un panier
                user_cart = Cart.objects.filter(user=user).first()
                
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
                else:
                    # Transférer le panier de session vers l'utilisateur
                    session_cart.user = user
                    session_cart.session_key = None
                    session_cart.save()


class CustomLogoutView(LogoutView):
    """Vue de déconnexion personnalisée"""
    next_page = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Vous avez été déconnecté avec succès.")
        return super().dispatch(request, *args, **kwargs)


@login_required
def profile_view(request):
    """Vue du profil utilisateur"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def dashboard_view(request):
    """Tableau de bord utilisateur"""
    user = request.user
    context = {
        'user': user,
        'has_complete_profile': user.has_complete_profile(),
    }
    return render(request, 'accounts/dashboard.html', context)
