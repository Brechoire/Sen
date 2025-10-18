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
                'class': 'form-control',
                'placeholder': 'Prénom de l\'auteur'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'auteur'
            }),
            'pen_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de plume (optionnel)'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'death_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'short_bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Biographie courte (500 caractères max)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email de contact'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Site web personnel'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
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
            'class': 'form-control'
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
