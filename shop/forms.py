from django import forms
from django.core.exceptions import ValidationError
from .models import Book, Category, BookImage, Review, Order, ShopSettings, Payment, Refund
from author.models import Author


class BookForm(forms.ModelForm):
    """Formulaire pour créer et modifier un livre"""
    
    class Meta:
        model = Book
        fields = [
            'title', 'slug', 'subtitle', 'author', 'description', 'short_description', 
            'excerpt', 'isbn', 'publication_date', 'pages', 'language', 'format',
            'cover_image', 'back_cover_image', 'price', 'discount_price', 
            'stock_quantity', 'is_available', 'is_featured', 'is_bestseller',
            'category', 'meta_title', 'meta_description', 'keywords'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Titre du livre'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'titre-du-livre'
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Sous-titre (optionnel)'
            }),
            'author': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'rows': 6,
                'placeholder': 'Description détaillée du livre'
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'rows': 3,
                'placeholder': 'Description courte (max 500 caractères)'
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'rows': 4,
                'placeholder': 'Extrait du livre'
            }),
            'isbn': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': '978-2-123456-78-9'
            }),
            'publication_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'type': 'date'
            }),
            'pages': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'min': 1
            }),
            'language': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Français'
            }),
            'format': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
            'back_cover_image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'step': '0.01',
                'min': '0'
            }),
            'discount_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'step': '0.01',
                'min': '0'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'min': '0'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Titre SEO (optionnel)'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'rows': 3,
                'placeholder': 'Description SEO (max 300 caractères)'
            }),
            'keywords': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Mots-clés séparés par des virgules'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les auteurs actifs
        self.fields['author'].queryset = Author.objects.filter(is_active=True)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        
        # Rendre certains champs optionnels
        self.fields['subtitle'].required = False
        self.fields['short_description'].required = False
        self.fields['excerpt'].required = False
        self.fields['back_cover_image'].required = False
        self.fields['discount_price'].required = False
        self.fields['category'].required = False
        self.fields['meta_title'].required = False
        self.fields['meta_description'].required = False
        self.fields['keywords'].required = False
    
    def clean_discount_price(self):
        """Valide que le prix de promotion est inférieur au prix normal"""
        discount_price = self.cleaned_data.get('discount_price')
        price = self.cleaned_data.get('price')
        
        if discount_price and price and discount_price >= price:
            raise ValidationError("Le prix de promotion doit être inférieur au prix normal.")
        
        return discount_price
    
    def clean_short_description(self):
        """Valide la longueur de la description courte"""
        short_description = self.cleaned_data.get('short_description')
        if short_description and len(short_description) > 500:
            raise ValidationError("La description courte ne peut pas dépasser 500 caractères.")
        return short_description
    
    def clean_meta_description(self):
        """Valide la longueur de la description SEO"""
        meta_description = self.cleaned_data.get('meta_description')
        if meta_description and len(meta_description) > 300:
            raise ValidationError("La description SEO ne peut pas dépasser 300 caractères.")
        return meta_description


class CategoryForm(forms.ModelForm):
    """Formulaire pour créer et modifier une catégorie"""
    
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Nom de la catégorie'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'nom-de-la-categorie'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'rows': 4,
                'placeholder': 'Description de la catégorie'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False


class BookImageForm(forms.ModelForm):
    """Formulaire pour ajouter des images à un livre"""
    
    class Meta:
        model = BookImage
        fields = ['image', 'alt_text', 'is_main', 'order']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Description de l\'image'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'min': '0'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['alt_text'].required = False
        self.fields['is_main'].required = False
        self.fields['order'].required = False


class ReviewForm(forms.ModelForm):
    """Formulaire pour ajouter un avis sur un livre"""
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Titre de votre avis'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'rows': 4,
                'placeholder': 'Votre avis sur ce livre'
            }),
        }


class BookSearchForm(forms.Form):
    """Formulaire de recherche de livres"""
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Rechercher un livre, un auteur...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
    )
    author = forms.ModelChoiceField(
        queryset=Author.objects.filter(is_active=True),
        required=False,
        empty_label="Tous les auteurs",
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
    )
    price_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Prix min',
            'step': '0.01',
            'min': '0'
        })
    )
    price_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Prix max',
            'step': '0.01',
            'min': '0'
        })
    )
    format = forms.ChoiceField(
        choices=[('', 'Tous les formats')] + Book._meta.get_field('format').choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Plus récents'),
            ('created_at', 'Plus anciens'),
            ('title', 'Titre A-Z'),
            ('-title', 'Titre Z-A'),
            ('price', 'Prix croissant'),
            ('-price', 'Prix décroissant'),
            ('-is_featured', 'Mis en avant'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-r-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        price_min = cleaned_data.get('price_min')
        price_max = cleaned_data.get('price_max')
        
        if price_min and price_max and price_min > price_max:
            raise ValidationError("Le prix minimum ne peut pas être supérieur au prix maximum.")
        
        return cleaned_data


class CheckoutForm(forms.ModelForm):
    """Formulaire pour le processus de commande"""
    
    # Case à cocher pour utiliser les mêmes informations pour la facturation
    same_as_shipping = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded',
            'onchange': 'toggleBillingFields()'
        }),
        label="Utiliser les mêmes informations pour la facturation"
    )
    
    class Meta:
        model = Order
        fields = [
            'shipping_first_name', 'shipping_last_name', 'shipping_address',
            'shipping_city', 'shipping_postal_code', 'shipping_country', 'shipping_phone',
            'billing_first_name', 'billing_last_name', 'billing_address',
            'billing_city', 'billing_postal_code', 'billing_country'
        ]
        widgets = {
            'shipping_first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Prénom'
            }),
            'shipping_last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Nom'
            }),
            'shipping_address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'rows': 3,
                'placeholder': 'Adresse complète'
            }),
            'shipping_city': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Ville'
            }),
            'shipping_postal_code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Code postal'
            }),
            'shipping_country': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Pays'
            }),
            'shipping_phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Téléphone (optionnel)'
            }),
            'billing_first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Prénom'
            }),
            'billing_last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Nom'
            }),
            'billing_address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'rows': 3,
                'placeholder': 'Adresse complète'
            }),
            'billing_city': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Ville'
            }),
            'billing_postal_code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Code postal'
            }),
            'billing_country': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Pays'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs de facturation optionnels
        self.fields['billing_first_name'].required = False
        self.fields['billing_last_name'].required = False
        self.fields['billing_address'].required = False
        self.fields['billing_city'].required = False
        self.fields['billing_postal_code'].required = False
        self.fields['billing_country'].required = False
        self.fields['shipping_phone'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        same_as_shipping = cleaned_data.get('same_as_shipping')
        
        if same_as_shipping:
            # Copier les informations de livraison vers la facturation
            cleaned_data['billing_first_name'] = cleaned_data.get('shipping_first_name')
            cleaned_data['billing_last_name'] = cleaned_data.get('shipping_last_name')
            cleaned_data['billing_address'] = cleaned_data.get('shipping_address')
            cleaned_data['billing_city'] = cleaned_data.get('shipping_city')
            cleaned_data['billing_postal_code'] = cleaned_data.get('shipping_postal_code')
            cleaned_data['billing_country'] = cleaned_data.get('shipping_country')
        
        return cleaned_data


class PaymentMethodForm(forms.Form):
    """Formulaire pour choisir la méthode de paiement"""
    
    PAYMENT_METHOD_CHOICES = [
        ('paypal', 'PayPal'),
        # ('stripe', 'Carte bancaire (Stripe)'),
        # ('bank_transfer', 'Virement bancaire'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio h-4 w-4 text-primary focus:ring-primary border-gray-300'
        }),
        label="Méthode de paiement"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].initial = 'paypal'


class ShopSettingsForm(forms.ModelForm):
    """Formulaire pour gérer les paramètres de la boutique"""
    
    class Meta:
        model = ShopSettings
        fields = [
            'free_shipping_threshold', 'standard_shipping_cost', 'tax_rate',
            'shop_name', 'shop_email', 'shop_phone'
        ]
        widgets = {
            'free_shipping_threshold': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'step': '0.01',
                'min': '0'
            }),
            'standard_shipping_cost': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'step': '0.01',
                'min': '0'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'shop_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'shop_email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'shop_phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
        }


class RefundRequestForm(forms.ModelForm):
    """Formulaire pour demander un remboursement"""
    
    class Meta:
        model = Refund
        fields = ['reason', 'description', 'amount']
        widgets = {
            'reason': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'rows': 4,
                'placeholder': 'Décrivez la raison de votre demande de remboursement...'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                'step': '0.01',
                'min': '0'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        if self.order:
            # Limiter le montant au maximum de la commande
            self.fields['amount'].widget.attrs['max'] = str(self.order.total_amount)
            self.fields['amount'].initial = self.order.total_amount
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.order and amount > self.order.total_amount:
            raise ValidationError(f'Le montant ne peut pas dépasser {self.order.total_amount}€')
        if amount <= 0:
            raise ValidationError('Le montant doit être positif')
        return amount
