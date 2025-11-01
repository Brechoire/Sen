from django import forms
from django.core.mail import send_mail
from django.conf import settings
from django.core.validators import URLValidator
from .models import SocialMediaSettings


class SocialMediaSettingsForm(forms.ModelForm):
    """Formulaire pour la gestion des réseaux sociaux"""
    
    class Meta:
        model = SocialMediaSettings
        fields = ['facebook_url', 'tiktok_url', 'linkedin_url', 'instagram_url']
        widgets = {
            'facebook_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'https://www.facebook.com/votre-page'
            }),
            'tiktok_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'https://www.tiktok.com/@votre-compte'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'https://www.linkedin.com/company/votre-entreprise'
            }),
            'instagram_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'https://www.instagram.com/votre-compte'
            }),
        }
        labels = {
            'facebook_url': 'URL Facebook',
            'tiktok_url': 'URL TikTok',
            'linkedin_url': 'URL LinkedIn',
            'instagram_url': 'URL Instagram',
        }
        help_texts = {
            'facebook_url': 'Laissez vide pour ne pas afficher l\'icône Facebook',
            'tiktok_url': 'Laissez vide pour ne pas afficher l\'icône TikTok',
            'linkedin_url': 'Laissez vide pour ne pas afficher l\'icône LinkedIn',
            'instagram_url': 'Laissez vide pour ne pas afficher l\'icône Instagram',
        }
    
    def clean_facebook_url(self):
        url = self.cleaned_data.get('facebook_url')
        if url:
            validator = URLValidator()
            validator(url)
        return url
    
    def clean_tiktok_url(self):
        url = self.cleaned_data.get('tiktok_url')
        if url:
            validator = URLValidator()
            validator(url)
        return url
    
    def clean_linkedin_url(self):
        url = self.cleaned_data.get('linkedin_url')
        if url:
            validator = URLValidator()
            validator(url)
        return url
    
    def clean_instagram_url(self):
        url = self.cleaned_data.get('instagram_url')
        if url:
            validator = URLValidator()
            validator(url)
        return url


class ContactForm(forms.Form):
    """Formulaire de contact pour les Éditions Sen"""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
            'placeholder': 'Votre nom complet'
        }),
        label='Nom complet'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
            'placeholder': 'votre@email.com'
        }),
        label='Adresse email'
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
            'placeholder': 'Sujet de votre message'
        }),
        label='Sujet'
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-none',
            'placeholder': 'Votre message...',
            'rows': 6
        }),
        label='Message'
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
            'placeholder': 'Votre numéro de téléphone (optionnel)'
        }),
        label='Téléphone (optionnel)'
    )
    
    def send_email(self):
        """Envoie l'email de contact"""
        name = self.cleaned_data['name']
        email = self.cleaned_data['email']
        subject = self.cleaned_data['subject']
        message = self.cleaned_data['message']
        phone = self.cleaned_data.get('phone', 'Non renseigné')
        
        # Contenu de l'email
        email_content = f"""
Nouveau message de contact reçu sur le site Éditions Sen

De: {name} <{email}>
Téléphone: {phone}
Sujet: {subject}

Message:
{message}

---
Ce message a été envoyé depuis le formulaire de contact du site web.
        """
        
        # Envoyer l'email
        send_mail(
            subject=f'[Éditions Sen] {subject}',
            message=email_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=False,
        )
