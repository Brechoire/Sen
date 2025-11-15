from django.db import models
from django.utils import timezone
from django.urls import reverse
from ckeditor.fields import RichTextField
from app.utils import get_upload_path


def article_image_upload_path(instance, filename):
    """Chemin d'upload pour les images d'articles"""
    return get_upload_path(instance, filename, 'articles/')


class Article(models.Model):
    """Modèle pour les articles d'actualités littéraires"""
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('archived', 'Archivé'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug")
    content = RichTextField(verbose_name="Contenu")
    excerpt = models.TextField(max_length=500, blank=True, verbose_name="Extrait")
    image = models.ImageField(
        upload_to=article_image_upload_path,
        blank=True, null=True,
        verbose_name="Image"
    )
    author = models.CharField(max_length=100, verbose_name="Auteur")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name="Statut")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    published_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de publication")
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-published_at', '-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('news:article_detail', kwargs={'slug': self.slug})
    
    @property
    def is_published(self):
        return self.status == 'published' and self.published_at is not None
