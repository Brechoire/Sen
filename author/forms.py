from django import forms
from .models import Author


class AuthorForm(forms.ModelForm):
    """Formulaire pour créer et modifier un auteur"""
    
    class Meta:
        model = Author
        fields = [
            'first_name', 'last_name', 'pen_name', 'birth_date', 'death_date',
            'biography', 'short_bio', 'photo', 'email', 
            'website', 'social_media', 'is_featured', 'is_active'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
                'placeholder': 'Prénom de l\'auteur'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
                'placeholder': 'Nom de l\'auteur'
            }),
            'pen_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
                'placeholder': 'Nom de plume (optionnel)'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
                'type': 'date'
            }),
            'death_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
                'type': 'date'
            }),
            'short_bio': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-y',
                'rows': 3,
                'placeholder': 'Biographie courte (500 caractères max)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
                'placeholder': 'Email de contact'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
                'placeholder': 'Site web personnel'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-secondary file:cursor-pointer',
                'accept': 'image/*'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre certains champs optionnels
        self.fields['pen_name'].required = False
        self.fields['birth_date'].required = False
        self.fields['death_date'].required = False
        self.fields['short_bio'].required = False
        self.fields['email'].required = False
        self.fields['website'].required = False
        self.fields['photo'].required = False
        self.fields['social_media'].required = False
        
        # Ajouter des classes CSS pour les champs de biographie
        self.fields['biography'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-y'
        })

class AuthorSearchForm(forms.Form):
    """Formulaire de recherche d'auteurs"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un auteur...',
            'name': 'search'
        })
    )
    
    
    featured_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'name': 'featured_only'
        })
    )
