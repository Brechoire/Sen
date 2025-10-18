from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Book, Category, BookImage, Review, Cart, CartItem, Order, OrderItem, Payment, Refund, ShopSettings


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


class BookImageInline(admin.TabularInline):
    model = BookImage
    extra = 1
    fields = ['image', 'alt_text', 'is_main', 'order']


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ['user', 'created_at']
    fields = ['user', 'rating', 'title', 'comment', 'is_approved', 'created_at']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = [
        'cover_thumbnail', 'title', 'author', 'category', 'price', 
        'display_price', 'stock_quantity', 'is_available', 'is_featured', 
        'is_bestseller', 'created_at'
    ]
    list_filter = [
        'is_available', 'is_featured', 'is_bestseller', 'format', 
        'category', 'author', 'created_at'
    ]
    search_fields = ['title', 'subtitle', 'isbn', 'author__first_name', 'author__last_name']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    inlines = [BookImageInline, ReviewInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'slug', 'subtitle', 'author', 'category')
        }),
        ('Description', {
            'fields': ('description', 'short_description', 'excerpt')
        }),
        ('Informations éditoriales', {
            'fields': ('isbn', 'publication_date', 'pages', 'language', 'format')
        }),
        ('Images', {
            'fields': ('cover_image', 'back_cover_image')
        }),
        ('Prix et disponibilité', {
            'fields': ('price', 'discount_price', 'stock_quantity', 'is_available')
        }),
        ('Mise en avant', {
            'fields': ('is_featured', 'is_bestseller')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'keywords'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def cover_thumbnail(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" width="50" height="70" style="object-fit: cover;" />',
                obj.cover_image.url
            )
        return "Pas d'image"
    cover_thumbnail.short_description = "Couverture"
    
    def display_price(self, obj):
        if obj.is_on_sale:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">{:.2f} €</span><br>'
                '<span style="color: #e74c3c; font-weight: bold;">{:.2f} €</span>',
                obj.price, obj.discount_price
            )
        return f"{obj.price:.2f} €"
    display_price.short_description = "Prix"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'category')


@admin.register(BookImage)
class BookImageAdmin(admin.ModelAdmin):
    list_display = ['book', 'image_thumbnail', 'alt_text', 'is_main', 'order']
    list_filter = ['is_main', 'book__author']
    search_fields = ['book__title', 'alt_text']
    ordering = ['book', 'order', 'id']
    
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="40" height="60" style="object-fit: cover;" />',
                obj.image.url
            )
        return "Pas d'image"
    image_thumbnail.short_description = "Image"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'rating', 'title', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'created_at', 'book__author']
    search_fields = ['book__title', 'user__username', 'title', 'comment']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Avis', {
            'fields': ('book', 'user', 'rating', 'title', 'comment')
        }),
        ('Modération', {
            'fields': ('is_approved',)
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('book', 'user')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['added_at']
    fields = ['book', 'quantity', 'added_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'user', 'session_key', 'total_items', 'final_price', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['user__username', 'session_key']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CartItemInline]
    
    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = "Articles"
    
    def final_price(self, obj):
        return f"{obj.final_price:.2f} €"
    final_price.short_description = "Total"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['book', 'cart', 'quantity', 'unit_price', 'total_price', 'added_at']
    list_filter = ['added_at', 'cart__user']
    search_fields = ['book__title', 'cart__user__username']
    readonly_fields = ['added_at']
    
    def unit_price(self, obj):
        return f"{obj.unit_price:.2f} €"
    unit_price.short_description = "Prix unitaire"
    
    def total_price(self, obj):
        return f"{obj.total_price:.2f} €"
    total_price.short_description = "Total"


# Administration des commandes et paiements
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['book', 'quantity', 'unit_price', 'total_price']
    fields = ['book', 'quantity', 'unit_price', 'total_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'payment_status', 
        'total_amount', 'created_at', 'can_be_cancelled'
    ]
    list_filter = ['status', 'payment_status', 'created_at', 'shipping_country']
    search_fields = ['order_number', 'user__username', 'user__email', 'shipping_first_name', 'shipping_last_name']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Adresse de livraison', {
            'fields': (
                'shipping_first_name', 'shipping_last_name', 'shipping_address',
                'shipping_city', 'shipping_postal_code', 'shipping_country', 'shipping_phone'
            )
        }),
        ('Adresse de facturation', {
            'fields': (
                'billing_first_name', 'billing_last_name', 'billing_address',
                'billing_city', 'billing_postal_code', 'billing_country'
            )
        }),
        ('Montants', {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'total_amount')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def can_be_cancelled(self, obj):
        return obj.can_be_cancelled
    can_be_cancelled.boolean = True
    can_be_cancelled.short_description = "Peut être annulée"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'payment_method', 'amount', 'status', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['order__order_number', 'paypal_payment_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'order', 'amount', 'reason', 'status', 
        'requested_by', 'processed_by', 'created_at'
    ]
    list_filter = ['status', 'reason', 'created_at', 'processed_at']
    search_fields = [
        'order__order_number', 'requested_by__username', 
        'processed_by__username', 'description'
    ]
    readonly_fields = ['created_at', 'processed_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('order', 'amount', 'reason', 'description', 'status')
        }),
        ('Utilisateurs', {
            'fields': ('requested_by', 'processed_by')
        }),
        ('PayPal', {
            'fields': ('paypal_refund_id', 'paypal_status'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'order', 'requested_by', 'processed_by'
        )


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ['shop_name', 'free_shipping_threshold', 'standard_shipping_cost', 'tax_rate', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Empêcher l'ajout de plusieurs instances
        return not ShopSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Empêcher la suppression de l'instance unique
        return False
