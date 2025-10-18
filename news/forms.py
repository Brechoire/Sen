from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import Article

class ArticleForm(forms.ModelForm):
    """Formulaire pour créer et modifier des articles"""
    
    class Meta:
        model = Article
        fields = ['title', 'slug', 'content', 'excerpt', 'image', 'author', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Titre de l\'article'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'slug-de-l-article'
            }),
            'content': CKEditorWidget(attrs={
                'class': 'w-full',
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'rows': 4,
                'placeholder': 'Extrait de l\'article (optionnel)'
            }),
            'author': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Nom de l\'auteur'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre le slug optionnel pour la création
        if not self.instance.pk:
            self.fields['slug'].required = False
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug and self.instance.pk is None:
            # Générer automatiquement le slug à partir du titre
            title = self.cleaned_data.get('title', '')
            slug = title.lower().replace(' ', '-').replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('à', 'a').replace('ç', 'c')
            # Nettoyer le slug
            import re
            slug = re.sub(r'[^a-z0-9\-]', '', slug)
            slug = re.sub(r'-+', '-', slug).strip('-')
        return slug
