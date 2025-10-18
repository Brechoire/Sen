from django.contrib import admin
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'published_at', 'created_at']
    list_filter = ['status', 'created_at', 'published_at', 'author']
    search_fields = ['title', 'content', 'author']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'published_at'
    ordering = ['-published_at', '-created_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'slug', 'author', 'status')
        }),
        ('Contenu', {
            'fields': ('excerpt', 'content', 'image')
        }),
        ('Dates', {
            'fields': ('published_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
