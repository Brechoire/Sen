# Skill : Django SOLID Patterns

## Objectif

Appliquer concrètement les principes SOLID dans les projets Django pour créer des architectures maintenables, testables et évolutives. Patterns pratiques et anti-patterns courants à éviter.

## Quand utiliser ce skill

- Refactoring d'un code legacy difficile à maintenir
- Création de nouvelles fonctionnalités avec une architecture propre
- Revues de code orientées architecture
- Mise en place de tests unitaires faciles à écrire
- Formation sur les bonnes pratiques Django

---

## Table des matières

1. [Single Responsibility Principle (SRP)](#1-single-responsibility-principle-srp)
2. [Open/Closed Principle (OCP)](#2-openclosed-principle-ocp)
3. [Liskov Substitution Principle (LSP)](#3-liskov-substitution-principle-lsp)
4. [Interface Segregation Principle (ISP)](#4-interface-segregation-principle-isp)
5. [Dependency Inversion Principle (DIP)](#5-dependency-inversion-principle-dip)
6. [Architecture hexagonale dans Django](#6-architecture-hexagonale-dans-django)

---

## 1. Single Responsibility Principle (SRP)

### Principe

> **"Une classe ne devrait avoir qu'une seule raison de changer."**

### Anti-pattern : Fat Model

```python
# ❌ ANTI-PATTERN : Fat Model avec trop de responsabilités
class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Logique métier mélangée
    def publish(self):
        self.status = 'published'
        self.save()
    
    # Envoi d'email
    def send_notification_email(self):
        send_mail(
            subject=f"Nouvel article: {self.title}",
            message=...,  # Logique d'email
            from_email=...,
            recipient_list=...,
        )
    
    # Génération de PDF
    def generate_pdf(self):
        from reportlab.pdfgen import canvas
        # Logique de génération PDF
        pass
    
    # API externe
    def post_to_twitter(self):
        import tweepy
        # Logique Twitter
        pass
    
    # Génération de RSS
    def to_rss_item(self):
        # Logique RSS
        pass
    
    # Validation complexe
    def validate_seo_score(self):
        # Logique SEO
        pass
    
    # Calculs statistiques
    def calculate_reading_time(self):
        # Logique de calcul
        pass
    
    # Export
    def export_to_word(self):
        # Logique Word
        pass
```

**Problèmes** :
- 8 raisons de changer cette classe
- Difficile à tester (besoin de mocks pour email, Twitter, PDF...)
- Couplage fort
- Impossible de réutiliser une fonctionnalité sans tout embarquer

### Solution : Services et Repositories

```python
# ✅ SRP - Modèle minimal
class Article(models.Model):
    """Responsabilité : représenter un article (données + logique métier de base)."""
    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=20, default='draft')
    
    class Meta:
        indexes = [models.Index(fields=['status', 'created_at'])]
    
    def publish(self) -> None:
        """Change le statut en publié (logique métier de base)."""
        self.status = 'published'
        self.published_at = timezone.now()
        self.save()
    
    def is_published(self) -> bool:
        return self.status == 'published'


# ✅ SRP - Repository pour la persistance
class ArticleRepository:
    """Responsabilité : accès aux données articles."""
    
    def get_by_slug(self, slug: str) -> Optional[Article]:
        return Article.objects.filter(slug=slug).first()
    
    def get_published(self) -> QuerySet[Article]:
        return Article.objects.filter(status='published')
    
    def get_by_author(self, author: User) -> QuerySet[Article]:
        return Article.objects.filter(author=author)
    
    def create(self, data: dict, author: User) -> Article:
        return Article.objects.create(
            title=data['title'],
            content=data['content'],
            author=author,
            slug=self._generate_slug(data['title'])
        )
    
    def _generate_slug(self, title: str) -> str:
        from django.utils.text import slugify
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        while Article.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug


# ✅ SRP - Service pour les notifications
class ArticleNotifier:
    """Responsabilité : notifier lors de la création/publication d'articles."""
    
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
    
    def notify_new_article(self, article: Article) -> None:
        subscribers = Subscriber.objects.filter(is_active=True)
        
        for subscriber in subscribers:
            self.email_service.send(
                to=subscriber.email,
                subject=f"Nouvel article : {article.title}",
                template='emails/new_article.html',
                context={'article': article}
            )
    
    def notify_author_published(self, article: Article) -> None:
        self.email_service.send(
            to=article.author.email,
            subject="Votre article est publié !",
            template='emails/article_published.html',
            context={'article': article}
        )


# ✅ SRP - Service pour les exports
class ArticleExporter:
    """Responsabilité : exporter des articles dans différents formats."""
    
    def __init__(self):
        self._exporters = {}
    
    def register(self, format: str, exporter):
        self._exporters[format] = exporter
    
    def export(self, article: Article, format: str) -> str:
        exporter = self._exporters.get(format)
        if not exporter:
            raise ValueError(f"Format '{format}' non supporté")
        return exporter.export(article)


class PDFExporter:
    """Responsabilité : export PDF."""
    def export(self, article: Article) -> str:
        # Logique PDF
        return f"{article.slug}.pdf"


class WordExporter:
    """Responsabilité : export Word."""
    def export(self, article: Article) -> str:
        # Logique Word
        return f"{article.slug}.docx"


# ✅ SRP - Service métier orchestrateur
class ArticleCreationService:
    """
    Responsabilité : orchestrer le processus de création d'un article.
    Coordonne les autres services sans faire le travail lui-même.
    """
    
    def __init__(
        self,
        repository: ArticleRepository,
        validator: ArticleValidator,
        notifier: ArticleNotifier,
        search_indexer: SearchIndexer,
    ):
        self.repository = repository
        self.validator = validator
        self.notifier = notifier
        self.search_indexer = search_indexer
    
    def create(self, data: dict, author: User) -> Article:
        # Validation
        validation = self.validator.validate(data)
        if not validation.is_valid:
            raise ValidationError(validation.errors)
        
        # Création
        article = self.repository.create(data, author)
        
        # Actions post-création
        self._on_article_created(article)
        
        return article
    
    def _on_article_created(self, article: Article) -> None:
        """Actions déclenchées après création."""
        # Ces actions peuvent être asynchrones (Celery)
        self.search_indexer.index_article(article)
        self.notifier.notify_new_article(article)


# ✅ SRP - Validation
class ArticleValidator:
    """Responsabilité : valider les données d'article."""
    
    def validate(self, data: dict) -> ValidationResult:
        errors = []
        
        if not data.get('title') or len(data['title']) < 5:
            errors.append("Le titre doit faire au moins 5 caractères")
        
        if not data.get('content'):
            errors.append("Le contenu est requis")
        
        if Article.objects.filter(slug=slugify(data.get('title', ''))).exists():
            errors.append("Un article avec ce titre existe déjà")
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
```

### Pattern : Repository Pattern

```python
# ✅ Repository Pattern générique
from typing import TypeVar, Generic, Optional, List
from django.db.models import Model, QuerySet

T = TypeVar('T', bound=Model)


class Repository(Generic[T]):
    """Repository générique de base."""
    
    def __init__(self, model_class: type[T]):
        self.model_class = model_class
    
    def get_by_id(self, id: int) -> Optional[T]:
        try:
            return self.model_class.objects.get(pk=id)
        except self.model_class.DoesNotExist:
            return None
    
    def get_all(self) -> QuerySet[T]:
        return self.model_class.objects.all()
    
    def create(self, **kwargs) -> T:
        return self.model_class.objects.create(**kwargs)
    
    def update(self, instance: T, **kwargs) -> T:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance
    
    def delete(self, instance: T) -> None:
        instance.delete()


# Implémentation spécifique
class ArticleRepository(Repository[Article]):
    """Repository spécifique pour Article avec méthodes métier."""
    
    def __init__(self):
        super().__init__(Article)
    
    def get_published(self) -> QuerySet[Article]:
        return self.model_class.objects.filter(status='published')
    
    def get_by_author(self, author: User) -> QuerySet[Article]:
        return self.model_class.objects.filter(author=author)
    
    def search(self, query: str) -> QuerySet[Article]:
        return self.model_class.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )
```

---

## 2. Open/Closed Principle (OCP)

### Principe

> **"Ouvert à l'extension, fermé à la modification."**

### Anti-pattern : Modification à chaque nouveau type

```python
# ❌ ANTI-PATTERN : Modifié à chaque nouveau format
class ReportGenerator:
    def generate(self, data: dict, format: str) -> str:
        if format == 'pdf':
            return self._generate_pdf(data)
        elif format == 'excel':
            return self._generate_excel(data)
        elif format == 'csv':
            return self._generate_csv(data)
        elif format == 'json':  # Ajouté plus tard
            return self._generate_json(data)
        elif format == 'xml':   # Ajouté encore plus tard
            return self._generate_xml(data)
        else:
            raise ValueError(f"Format {format} non supporté")
```

**Problèmes** :
- Modifié à chaque nouveau format
- Risque de régression
- Tests de plus en plus lourds

### Solution : Strategy Pattern

```python
from abc import ABC, abstractmethod
from typing import Protocol


# ✅ Protocole (interface)
class ExportStrategy(Protocol):
    """Interface pour tous les exporteurs."""
    
    def export(self, data: dict) -> str:
        ...
    
    def get_extension(self) -> str:
        ...
    
    def get_content_type(self) -> str:
        ...


# ✅ Implémentations concrètes (extensions)
class PDFExportStrategy:
    """Extension : Export PDF."""
    
    def export(self, data: dict) -> str:
        from reportlab.pdfgen import canvas
        # Logique PDF
        return "contenu_pdf"
    
    def get_extension(self) -> str:
        return 'pdf'
    
    def get_content_type(self) -> str:
        return 'application/pdf'


class ExcelExportStrategy:
    """Extension : Export Excel."""
    
    def export(self, data: dict) -> str:
        import openpyxl
        # Logique Excel
        return "contenu_xlsx"
    
    def get_extension(self) -> str:
        return 'xlsx'
    
    def get_content_type(self) -> str:
        return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


class CSVExportStrategy:
    """Extension : Export CSV."""
    
    def export(self, data: dict) -> str:
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    
    def get_extension(self) -> str:
        return 'csv'
    
    def get_content_type(self) -> str:
        return 'text/csv'


class JSONExportStrategy:
    """Extension : Export JSON (ajouté sans modifier le code existant)."""
    
    def export(self, data: dict) -> str:
        import json
        return json.dumps(data, indent=2, default=str)
    
    def get_extension(self) -> str:
        return 'json'
    
    def get_content_type(self) -> str:
        return 'application/json'


# ✅ Service fermé à la modification
class ExportService:
    """
    Service d'export - fermé à la modification, ouvert à l'extension.
    """
    
    def __init__(self):
        self._strategies: dict[str, ExportStrategy] = {}
    
    def register(self, format: str, strategy: ExportStrategy) -> None:
        """Enregistre une nouvelle stratégie (extension)."""
        self._strategies[format] = strategy
    
    def export(self, data: dict, format: str) -> ExportResult:
        """Exporte dans le format demandé."""
        strategy = self._strategies.get(format)
        if not strategy:
            raise UnsupportedFormatError(format)
        
        content = strategy.export(data)
        return ExportResult(
            content=content,
            extension=strategy.get_extension(),
            content_type=strategy.get_content_type(),
        )
    
    def get_supported_formats(self) -> list[str]:
        return list(self._strategies.keys())


@dataclass
class ExportResult:
    content: str
    extension: str
    content_type: str


# Configuration
service = ExportService()
service.register('pdf', PDFExportStrategy())
service.register('excel', ExcelExportStrategy())
service.register('csv', CSVExportStrategy())

# Ajout d'un nouveau format sans modifier ExportService
service.register('json', JSONExportStrategy())
service.register('xml', XMLExportStrategy())  # Nouvelle extension

# Utilisation
result = service.export(data, 'pdf')
```

### Pattern : Stratégie de réduction

```python
from abc import ABC, abstractmethod
from decimal import Decimal


# ✅ Stratégies de réduction
class DiscountStrategy(ABC):
    """Stratégie abstraite de réduction."""
    
    @abstractmethod
    def calculate_discount(self, amount: Decimal) -> Decimal:
        pass
    
    @abstractmethod
    def is_applicable(self, context: DiscountContext) -> bool:
        pass


class NoDiscount(DiscountStrategy):
    """Aucune réduction."""
    
    def calculate_discount(self, amount: Decimal) -> Decimal:
        return Decimal('0')
    
    def is_applicable(self, context: DiscountContext) -> bool:
        return True


class PercentageDiscount(DiscountStrategy):
    """Réduction en pourcentage."""
    
    def __init__(self, percentage: Decimal):
        self.percentage = percentage
    
    def calculate_discount(self, amount: Decimal) -> Decimal:
        return amount * (self.percentage / 100)
    
    def is_applicable(self, context: DiscountContext) -> bool:
        return True


class MemberDiscount(DiscountStrategy):
    """Réduction pour membres."""
    
    def calculate_discount(self, amount: Decimal) -> Decimal:
        return amount * Decimal('0.15')  # 15%
    
    def is_applicable(self, context: DiscountContext) -> bool:
        return context.user.is_member


class SeasonalDiscount(DiscountStrategy):
    """Réduction saisonnière (nouveau type, extension)."""
    
    def __init__(self, season: str, discount_rate: Decimal):
        self.season = season
        self.discount_rate = discount_rate
    
    def calculate_discount(self, amount: Decimal) -> Decimal:
        return amount * self.discount_rate
    
    def is_applicable(self, context: DiscountContext) -> bool:
        return self._is_current_season(self.season)


# ✅ Calculateur fermé à la modification
class DiscountCalculator:
    """Calculateur de réductions."""
    
    def __init__(self):
        self._strategies: list[DiscountStrategy] = []
    
    def add_strategy(self, strategy: DiscountStrategy, priority: int = 0):
        """Ajoute une stratégie avec priorité."""
        self._strategies.append((priority, strategy))
        self._strategies.sort(key=lambda x: x[0], reverse=True)
    
    def calculate_best_discount(self, amount: Decimal, context: DiscountContext) -> Decimal:
        """Calcule la meilleure réduction applicable."""
        for priority, strategy in self._strategies:
            if strategy.is_applicable(context):
                discount = strategy.calculate_discount(amount)
                if discount > 0:
                    return discount
        return Decimal('0')


# Utilisation
calculator = DiscountCalculator()
calculator.add_strategy(NoDiscount(), priority=0)
calculator.add_strategy(PercentageDiscount(Decimal('10')), priority=5)
calculator.add_strategy(MemberDiscount(), priority=10)
calculator.add_strategy(SeasonalDiscount('summer', Decimal('0.20')), priority=8)

context = DiscountContext(user=current_user, date=timezone.now())
discount = calculator.calculate_best_discount(Decimal('100'), context)
```

---

## 3. Liskov Substitution Principle (LSP)

### Principe

> **"Les classes filles doivent pouvoir substituer leurs classes parent."**

### Exemple : Repository Pattern

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Protocol


# ✅ Interface commune
class ArticleRepositoryInterface(Protocol):
    """
    Interface pour tous les repositories d'articles.
    Toute implémentation doit pouvoir substituer une autre.
    """
    
    def get_by_id(self, article_id: int) -> Optional[Article]:
        ...
    
    def get_by_slug(self, slug: str) -> Optional[Article]:
        ...
    
    def get_published(self) -> List[Article]:
        ...
    
    def save(self, article: Article) -> Article:
        ...


# ✅ Implémentation PostgreSQL/Django ORM
class DjangoArticleRepository:
    """Implémentation avec Django ORM."""
    
    def get_by_id(self, article_id: int) -> Optional[Article]:
        try:
            return Article.objects.get(pk=article_id)
        except Article.DoesNotExist:
            return None
    
    def get_by_slug(self, slug: str) -> Optional[Article]:
        return Article.objects.filter(slug=slug).first()
    
    def get_published(self) -> List[Article]:
        return list(Article.objects.filter(status='published'))
    
    def save(self, article: Article) -> Article:
        article.save()
        return article


# ✅ Implémentation en mémoire pour les tests
class InMemoryArticleRepository:
    """
    Implémentation en mémoire - substituable à DjangoArticleRepository.
    """
    
    def __init__(self):
        self._articles: dict[int, Article] = {}
        self._slug_index: dict[str, int] = {}
        self._next_id = 1
    
    def get_by_id(self, article_id: int) -> Optional[Article]:
        return self._articles.get(article_id)
    
    def get_by_slug(self, slug: str) -> Optional[Article]:
        article_id = self._slug_index.get(slug)
        return self._articles.get(article_id) if article_id else None
    
    def get_published(self) -> List[Article]:
        return [
            a for a in self._articles.values()
            if a.status == 'published'
        ]
    
    def save(self, article: Article) -> Article:
        if not article.id:
            article.id = self._next_id
            self._next_id += 1
        
        self._articles[article.id] = article
        self._slug_index[article.slug] = article.id
        return article


# ✅ Service qui utilise l'abstraction
class ArticleService:
    """
    Fonctionne avec n'importe quelle implémentation de ArticleRepositoryInterface.
    """
    
    def __init__(self, repository: ArticleRepositoryInterface):
        self._repository = repository
    
    def get_article(self, slug: str) -> Article:
        article = self._repository.get_by_slug(slug)
        if not article:
            raise ArticleNotFoundError(slug)
        return article
    
    def get_homepage_articles(self) -> List[Article]:
        return self._repository.get_published()[:10]


# ✅ Substitution transparente
# Production
service_prod = ArticleService(DjangoArticleRepository())

# Tests (substitution transparente)
service_test = ArticleService(InMemoryArticleRepository())

# Les deux fonctionnent identiquement
article = service.get_article('mon-article')
```

---

## 4. Interface Segregation Principle (ISP)

### Principe

> **"Les clients ne devraient pas dépendre d'interfaces qu'ils n'utilisent pas."**

### Exemple : Interfaces de stockage

```python
from typing import Protocol, BinaryIO


# ✅ Petites interfaces spécialisées

class Readable(Protocol):
    """Interface pour la lecture seule."""
    
    def read(self, path: str) -> bytes:
        ...
    
    def exists(self, path: str) -> bool:
        ...
    
    def get_url(self, path: str) -> str:
        ...


class Writable(Protocol):
    """Interface pour l'écriture."""
    
    def write(self, path: str, data: bytes) -> None:
        ...
    
    def delete(self, path: str) -> None:
        ...


class Listable(Protocol):
    """Interface pour lister le contenu."""
    
    def list_files(self, directory: str) -> List[str]:
        ...


# ✅ Implémentation complète
class LocalFileStorage:
    """Stockage local : implémente toutes les interfaces."""
    
    def read(self, path: str) -> bytes:
        with open(path, 'rb') as f:
            return f.read()
    
    def write(self, path: str, data: bytes) -> None:
        with open(path, 'wb') as f:
            f.write(data)
    
    def delete(self, path: str) -> None:
        import os
        os.remove(path)
    
    def exists(self, path: str) -> bool:
        import os
        return os.path.exists(path)
    
    def list_files(self, directory: str) -> List[str]:
        import os
        return os.listdir(directory)
    
    def get_url(self, path: str) -> str:
        return f"/media/{path}"


# ✅ Implémentation lecture seule
class S3ReadOnlyStorage:
    """S3 lecture seule : implémente uniquement Readable."""
    
    def __init__(self, bucket: str):
        self.bucket = bucket
        import boto3
        self.s3 = boto3.client('s3')
    
    def read(self, path: str) -> bytes:
        response = self.s3.get_object(Bucket=self.bucket, Key=path)
        return response['Body'].read()
    
    def exists(self, path: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=path)
            return True
        except ClientError:
            return False
    
    def get_url(self, path: str) -> str:
        return f"https://{self.bucket}.s3.amazonaws.com/{path}"


# ✅ Fonctions utilisant les interfaces spécialisées

def load_configuration(storage: Readable, config_path: str) -> dict:
    """Accepte tout objet Readable."""
    import json
    data = storage.read(config_path)
    return json.loads(data)


def backup_files(source: Readable, destination: Writable, files: List[str]) -> None:
    """Source Readable, destination Writable."""
    for file in files:
        if source.exists(file):
            data = source.read(file)
            destination.write(f"backup/{file}", data)


def generate_report(storage: Listable, directory: str) -> str:
    """Accepte seulement les objets Listable."""
    files = storage.list_files(directory)
    return f"Répertoire contient {len(files)} fichiers"


# Utilisation
local = LocalFileStorage()
s3_readonly = S3ReadOnlyStorage("my-bucket")

# Fonctionne avec les deux
config = load_configuration(local, "/etc/config.json")
config = load_configuration(s3_readonly, "configs/app.json")

# Lecture seule protégée par le type system
# s3_readonly.write("test.txt", b"data")  # ❌ Erreur de type !
```

---

## 5. Dependency Inversion Principle (DIP)

### Principe

> **"Dépendre d'abstractions, pas d'implémentations concrètes."**

### Exemple : Service de commandes

```python
from typing import Protocol
from abc import ABC, abstractmethod
from decimal import Decimal


# ✅ Abstractions

class PaymentGateway(Protocol):
    """Interface pour les passerelles de paiement."""
    
    def charge(self, amount: Decimal, token: str) -> PaymentResult:
        ...


class Notifier(Protocol):
    """Interface pour les notifications."""
    
    def send_order_confirmation(self, order: Order) -> None:
        ...


class Inventory(Protocol):
    """Interface pour l'inventaire."""
    
    def reserve_items(self, items: List[OrderItem]) -> bool:
        ...


# ✅ Implémentations concrètes

class StripeGateway:
    """Passerelle Stripe."""
    
    def __init__(self, api_key: str):
        import stripe
        stripe.api_key = api_key
        self.stripe = stripe
    
    def charge(self, amount: Decimal, token: str) -> PaymentResult:
        try:
            charge = self.stripe.Charge.create(
                amount=int(amount * 100),  # cents
                currency='eur',
                source=token,
            )
            return PaymentResult(success=True, transaction_id=charge.id)
        except self.stripe.error.CardError as e:
            return PaymentResult(success=False, error=str(e))


class PayPalGateway:
    """Passerelle PayPal."""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    def charge(self, amount: Decimal, token: str) -> PaymentResult:
        # Logique PayPal
        return PaymentResult(success=True, transaction_id="PAYPAL123")


class EmailNotifier:
    """Notification par email."""
    
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
    
    def send_order_confirmation(self, order: Order) -> None:
        self.email_service.send(
            to=order.customer_email,
            subject=f"Commande #{order.id} confirmée",
            template='emails/order_confirmation.html',
            context={'order': order}
        )


class DjangoInventory:
    """Inventaire avec Django ORM."""
    
    def reserve_items(self, items: List[OrderItem]) -> bool:
        for item in items:
            product = Product.objects.select_for_update().get(id=item.product_id)
            if product.stock < item.quantity:
                return False
            product.stock -= item.quantity
            product.save()
        return True


# ✅ Module de haut niveau avec injection de dépendances

class OrderService:
    """
    Service de commande - dépend d'abstractions.
    Peut fonctionner avec n'importe quelle implémentation.
    """
    
    def __init__(
        self,
        payment_gateway: PaymentGateway,
        notifier: Notifier,
        inventory: Inventory,
        order_repository: OrderRepository,
    ):
        self.payment_gateway = payment_gateway
        self.notifier = notifier
        self.inventory = inventory
        self.order_repository = order_repository
    
    def process_order(self, order_data: OrderData) -> Order:
        """Traite une commande."""
        # Création
        order = self.order_repository.create(order_data)
        
        try:
            # Réservation d'inventaire
            if not self.inventory.reserve_items(order.items):
                raise InsufficientStockError()
            
            # Paiement
            payment_result = self.payment_gateway.charge(
                order.total,
                order_data.payment_token
            )
            
            if not payment_result.success:
                order.status = 'payment_failed'
                order.save()
                raise PaymentError(payment_result.error)
            
            # Succès
            order.status = 'confirmed'
            order.transaction_id = payment_result.transaction_id
            order.save()
            
            # Notification
            self.notifier.send_order_confirmation(order)
            
            return order
            
        except Exception as e:
            # Rollback
            order.status = 'error'
            order.save()
            raise


# ✅ Factories avec injection

def create_production_order_service():
    """Crée le service pour la production."""
    return OrderService(
        payment_gateway=StripeGateway(settings.STRIPE_API_KEY),
        notifier=EmailNotifier(SendGridService()),
        inventory=DjangoInventory(),
        order_repository=DjangoOrderRepository(),
    )


def create_test_order_service():
    """Crée le service pour les tests."""
    return OrderService(
        payment_gateway=MockPaymentGateway(),
        notifier=MockNotifier(),
        inventory=MockInventory(),
        order_repository=InMemoryOrderRepository(),
    )


# Utilisation
if settings.DEBUG:
    order_service = create_test_order_service()
else:
    order_service = create_production_order_service()
```

### Injection avec Django

```python
# middleware/dependency_injection.py

class DependencyInjectionMiddleware:
    """
    Middleware qui injecte les dépendances dans les vues.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._container = self._build_container()
    
    def _build_container(self):
        """Configure le container d'injection."""
        container = DIContainer()
        
        # Enregistrement des services
        container.register(
            ArticleRepository,
            DjangoArticleRepository()
        )
        
        container.register(
            ArticleService,
            ArticleService(container.resolve(ArticleRepository))
        )
        
        container.register(
            EmailService,
            SendGridEmailService(
                api_key=settings.SENDGRID_API_KEY
            )
        )
        
        return container
    
    def __call__(self, request):
        # Rend le container disponible sur la requête
        request.container = self._container
        return self.get_response(request)


# Utilisation dans une vue
class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    
    def form_valid(self, form):
        # Injection via la requête
        article_service = self.request.container.resolve(ArticleService)
        
        article = article_service.create(
            data=form.cleaned_data,
            author=self.request.user
        )
        
        return redirect(article.get_absolute_url())
```

---

## 6. Architecture hexagonale dans Django

### Structure du projet

```
apps/
├── mon_app/
│   ├── domain/              # Cœur métier (indépendant de Django)
│   │   ├── __init__.py
│   │   ├── models.py        # Modèles de domaine (entités pures)
│   │   ├── services.py      # Logique métier
│   │   └── interfaces.py    # Interfaces (ports)
│   ├── application/         # Couche application (use cases)
│   │   ├── __init__.py
│   │   ├── commands.py      # Commandes
│   │   ├── queries.py       # Requêtes
│   │   └── handlers.py      # Gestionnaires
│   ├── infrastructure/      # Adaptateurs techniques
│   │   ├── __init__.py
│   │   ├── django/          # Adaptateurs Django
│   │   │   ├── models.py    # Modèles Django (ORM)
│   │   │   ├── repositories.py
│   │   │   └── mappers.py
│   │   ├── external/        # Services externes
│   │   │   ├── payment.py
│   │   │   └── email.py
│   │   └── persistence/     # Repositories concrets
│   ├── interfaces/          # Interface utilisateur (vues, API)
│   │   ├── __init__.py
│   │   ├── web/             # Vues web
│   │   │   └── views.py
│   │   └── api/             # API REST
│   │       └── views.py
│   └── tests/
```

### Exemple complet

```python
# domain/models.py - Entités pures (indépendantes)
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID, uuid4


@dataclass
class Article:
    """Entité de domaine - indépendante de Django."""
    title: str
    content: str
    author_id: UUID
    id: UUID = field(default_factory=uuid4)
    status: str = field(default='draft')
    created_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    
    def publish(self) -> None:
        """Logique métier de publication."""
        if not self.title or len(self.title) < 5:
            raise ValueError("Titre invalide")
        self.status = 'published'
    
    def add_tag(self, tag: str) -> None:
        """Ajoute un tag si valide."""
        if tag and tag not in self.tags:
            self.tags.append(tag)


# domain/interfaces.py - Ports
from typing import Protocol, Optional


class ArticleRepository(Protocol):
    def get_by_id(self, article_id: UUID) -> Optional[Article]:
        ...
    
    def save(self, article: Article) -> None:
        ...
    
    def delete(self, article_id: UUID) -> None:
        ...


class EmailService(Protocol):
    def send(self, to: str, subject: str, body: str) -> None:
        ...


# domain/services.py - Logique métier
class ArticlePublishingService:
    """Service de domaine - logique métier pure."""
    
    def __init__(
        self,
        repository: ArticleRepository,
        email_service: EmailService,
    ):
        self.repository = repository
        self.email_service = email_service
    
    def publish_article(self, article_id: UUID) -> Article:
        article = self.repository.get_by_id(article_id)
        if not article:
            raise ArticleNotFoundError(article_id)
        
        article.publish()
        self.repository.save(article)
        
        self.email_service.send(
            to=str(article.author_id),  # Simplifié
            subject="Article publié",
            body=f"Votre article '{article.title}' est publié"
        )
        
        return article


# infrastructure/django/models.py - Modèle Django (ORM)
from django.db import models


class ArticleORM(models.Model):
    """Modèle Django - adaptateur de persistance."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.JSONField(default=list)
    
    class Meta:
        db_table = 'articles'


# infrastructure/django/mappers.py
class ArticleMapper:
    """Mappe entre modèle de domaine et modèle Django."""
    
    @staticmethod
    def to_domain(orm: ArticleORM) -> Article:
        return Article(
            id=orm.id,
            title=orm.title,
            content=orm.content,
            author_id=orm.author_id,
            status=orm.status,
            created_at=orm.created_at,
            tags=orm.tags,
        )
    
    @staticmethod
    def to_orm(domain: Article) -> ArticleORM:
        return ArticleORM(
            id=domain.id,
            title=domain.title,
            content=domain.content,
            author_id=domain.author_id,
            status=domain.status,
            created_at=domain.created_at,
            tags=domain.tags,
        )


# infrastructure/django/repositories.py
class DjangoArticleRepository:
    """Implémentation concrète avec Django ORM."""
    
    def __init__(self):
        self.mapper = ArticleMapper()
    
    def get_by_id(self, article_id: UUID) -> Optional[Article]:
        try:
            orm = ArticleORM.objects.get(pk=article_id)
            return self.mapper.to_domain(orm)
        except ArticleORM.DoesNotExist:
            return None
    
    def save(self, article: Article) -> None:
        orm = self.mapper.to_orm(article)
        orm.save()
    
    def delete(self, article_id: UUID) -> None:
        ArticleORM.objects.filter(pk=article_id).delete()


# interfaces/web/views.py
class PublishArticleView(LoginRequiredMixin, View):
    """Vue Django - couche interface."""
    
    def post(self, request, article_id):
        # Construction avec injection
        repository = DjangoArticleRepository()
        email_service = DjangoEmailService()
        
        service = ArticlePublishingService(
            repository=repository,
            email_service=email_service,
        )
        
        try:
            article = service.publish_article(UUID(article_id))
            messages.success(request, "Article publié !")
        except ArticleNotFoundError:
            raise Http404()
        
        return redirect('article_detail', article_id=article_id)
```

---

## Checklist SOLID

### Pour chaque nouvelle classe

**Single Responsibility**
- [ ] Une seule raison de changer
- [ ] Responsabilité claire et unique
- [ ] < 7-10 méthodes publiques

**Open/Closed**
- [ ] Nouvelles fonctionnalités via extension
- [ ] Pas de modification du code existant
- [ ] Utilisation de polymorphisme

**Liskov Substitution**
- [ ] Classes filles substituables
- [ ] Pas de comportements inattendus
- [ ] Respect des contrats de l'interface

**Interface Segregation**
- [ ] Petites interfaces spécialisées
- [ ] Pas de méthodes inutiles
- [ ] Client dépend seulement de ce qu'il utilise

**Dependency Inversion**
- [ ] Dépendances vers abstractions
- [ ] Injection de dépendances
- [ ] Facile à mocker pour les tests

---

## Ressources

- [Architecture hexagonale](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture - Robert C. Martin](https://www.amazon.com/Clean-Architecture-Craftsmans-Software-Structure/dp/0134494164)
- [SOLID Principles in Python](https://realpython.com/solid-principles-python/)
- [Django Best Practices](../django-best-practices/SKILL.md)
