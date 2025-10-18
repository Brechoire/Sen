from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from .models import Author
from .forms import AuthorForm, AuthorSearchForm

class AuthorListView(ListView):
    """Vue pour lister tous les auteurs"""
    model = Author
    template_name = 'author/author_list.html'
    context_object_name = 'authors'
    paginate_by = 12
    
    def get_queryset(self):
        """Retourne la liste des auteurs avec filtres"""
        queryset = Author.objects.filter(is_active=True)
        
        # Filtre par recherche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(pen_name__icontains=search) |
                Q(biography__icontains=search)
            )
        
        
        # Filtre par auteurs mis en avant
        featured_only = self.request.GET.get('featured_only')
        if featured_only:
            queryset = queryset.filter(is_featured=True)
        
        return queryset.order_by('last_name', 'first_name')
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte"""
        context = super().get_context_data(**kwargs)
        context['featured_authors'] = Author.objects.filter(is_featured=True, is_active=True)[:6]
        context['search_form'] = AuthorSearchForm(self.request.GET)
        return context

class AuthorDetailView(DetailView):
    """Vue pour afficher les détails d'un auteur"""
    model = Author
    template_name = 'author/author_detail.html'
    context_object_name = 'author'
    
    def get_queryset(self):
        """Retourne seulement les auteurs actifs"""
        return Author.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte"""
        context = super().get_context_data(**kwargs)
        author = self.get_object()
        
        # Ajouter d'autres auteurs similaires (par nom de plume ou prénom)
        context['related_authors'] = Author.objects.filter(
            is_active=True
        ).exclude(pk=author.pk)[:4]
        
        return context

class AuthorCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer un nouvel auteur"""
    model = Author
    form_class = AuthorForm
    template_name = 'author/author_form.html'
    success_url = reverse_lazy('author:author_list')
    
    def form_valid(self, form):
        """Message de succès après création"""
        messages.success(self.request, f'Auteur "{form.instance.display_name}" créé avec succès !')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte"""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ajouter un nouvel auteur'
        context['submit_text'] = 'Créer l\'auteur'
        return context

class AuthorUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un auteur existant"""
    model = Author
    form_class = AuthorForm
    template_name = 'author/author_form.html'
    
    def get_success_url(self):
        """Redirection vers la page de détail après modification"""
        return reverse('author:author_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """Message de succès après modification"""
        messages.success(self.request, f'Auteur "{form.instance.display_name}" modifié avec succès !')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte"""
        context = super().get_context_data(**kwargs)
        context['title'] = f'Modifier {self.object.display_name}'
        context['submit_text'] = 'Modifier l\'auteur'
        return context

class AuthorDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer un auteur"""
    model = Author
    template_name = 'author/author_confirm_delete.html'
    success_url = reverse_lazy('author:author_list')
    
    def delete(self, request, *args, **kwargs):
        """Message de succès après suppression"""
        author = self.get_object()
        messages.success(request, f'Auteur "{author.display_name}" supprimé avec succès !')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte"""
        context = super().get_context_data(**kwargs)
        context['title'] = f'Supprimer {self.object.display_name}'
        return context