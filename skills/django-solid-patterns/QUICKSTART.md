# Quick Start - Django SOLID Patterns

Guide rapide pour appliquer les principes SOLID dans Django.

## Les 5 principes en 5 minutes

```
S - Single Responsibility : Une classe = un job
O - Open/Closed          : Ouvert à l'extension, fermé à la modification
L - Liskov Substitution  : Les filles peuvent remplacer les parents
I - Interface Segregation: Petites interfaces spécialisées
D - Dependency Inversion : Dépendre d'abstractions, pas de concrets
```

## Anti-patterns courants → Solutions

### 1. Fat Model → Services (SRP)

```python
# ❌ AVANT : Modèle avec trop de responsabilités
class Article(models.Model):
    title = models.CharField(max_length=200)
    
    def send_email(self): pass       # Email
    def generate_pdf(self): pass     # PDF
    def post_twitter(self): pass     # API externe
    def validate_seo(self): pass     # Validation complexe
    def calculate_stats(self): pass  # Stats


# ✅ APRÈS : Séparation des responsabilités
class Article(models.Model):
    """Responsabilité : données et logique métier de base."""
    title = models.CharField(max_length=200)
    
    def publish(self):
        self.status = 'published'
        self.save()

class ArticleNotifier:
    """Responsabilité : envoyer des notifications."""
    def send_email(self, article): pass

class ArticleExporter:
    """Responsabilité : exporter dans différents formats."""
    def to_pdf(self, article): pass
    def to_word(self, article): pass

class ArticleValidator:
    """Responsabilité : valider les articles."""
    def validate(self, data): pass
```

### 2. If/Elif chaîne → Strategy Pattern (OCP)

```python
# ❌ AVANT : Modifié à chaque nouveau type
class PaymentProcessor:
    def process(self, payment_type, amount):
        if payment_type == 'stripe':
            return self._process_stripe(amount)
        elif payment_type == 'paypal':
            return self._process_paypal(amount)
        elif payment_type == 'crypto':  # Ajouté plus tard
            return self._process_crypto(amount)


# ✅ APRÈS : Extension sans modification
from typing import Protocol

class PaymentGateway(Protocol):
    def charge(self, amount: float) -> PaymentResult: ...

class StripeGateway:
    def charge(self, amount: float) -> PaymentResult:
        # Logique Stripe
        pass

class CryptoGateway:  # Nouveau, sans modifier le code existant
    def charge(self, amount: float) -> PaymentResult:
        # Logique Crypto
        pass

class PaymentProcessor:
    def process(self, gateway: PaymentGateway, amount: float):
        return gateway.charge(amount)  # Fonctionne avec tous les gateways
```

### 3. Tests difficiles → Injection de dépendances (DIP)

```python
# ❌ AVANT : Difficile à tester (dépendance concrète)
class OrderService:
    def __init__(self):
        self.payment = StripeGateway(API_KEY)  # Couplage fort
        self.email = SendGridService()         # Couplage fort
    
    def process_order(self, order):
        self.payment.charge(order.total)
        self.email.send(order.customer_email)


# ✅ APRÈS : Facile à tester (dépendance abstraite)
from typing import Protocol

class PaymentGateway(Protocol):
    def charge(self, amount: float) -> bool: ...

class EmailService(Protocol):
    def send(self, to: str, subject: str) -> None: ...

class OrderService:
    def __init__(
        self,
        payment: PaymentGateway,  # Abstraction
        email: EmailService,      # Abstraction
    ):
        self.payment = payment
        self.email = email

# Tests avec mocks
service = OrderService(
    payment=MockPaymentGateway(),
    email=MockEmailService(),
)
```

### 4. Interfaces trop larges → Interfaces spécialisées (ISP)

```python
# ❌ AVANT : Interface trop large
class Storage:
    def read(self, path): pass
    def write(self, path, data): pass
    def delete(self, path): pass
    def list(self, path): pass
    def copy(self, src, dst): pass
    def move(self, src, dst): pass


# ✅ APRÈS : Petites interfaces spécialisées
class Readable(Protocol):
    def read(self, path) -> bytes: ...
    def exists(self, path) -> bool: ...

class Writable(Protocol):
    def write(self, path, data) -> None: ...
    def delete(self, path) -> None: ...

class Listable(Protocol):
    def list_files(self, path) -> list: ...

# Lecture seule - implémente uniquement Readable
class S3ReadOnlyStorage:
    def read(self, path): ...
    def exists(self, path): ...

# Fonction utilisant seulement Readable
def load_config(storage: Readable, path):
    return json.loads(storage.read(path))
```

### 5. Héritage fragile → Composition (LSP)

```python
# ❌ AVANT : Violation de LSP
class Rectangle:
    def __init__(self, width, height):
        self._width = width
        self._height = height
    
    def set_width(self, value):
        self._width = value
    
    def set_height(self, value):
        self._height = value

class Square(Rectangle):  # ❌ Violation!
    def set_width(self, value):
        self._width = value
        self._height = value  # Effet de bord!


# ✅ APRÈS : Interface commune
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: pass
    
    @abstractmethod
    def perimeter(self) -> float: pass

class Rectangle(Shape):
    def __init__(self, width, height):
        self._width = width
        self._height = height
    
    def area(self) -> float:
        return self._width * self._height

class Square(Shape):  # ✅ Pas d'héritage problématique
    def __init__(self, side):
        self._side = side
    
    def area(self) -> float:
        return self._side ** 2
```

## Patterns essentiels

### Repository Pattern

```python
from typing import TypeVar, Generic, Optional
from django.db.models import Model

T = TypeVar('T', bound=Model)

class Repository(Generic[T]):
    """Repository générique."""
    
    def __init__(self, model_class: type[T]):
        self.model_class = model_class
    
    def get_by_id(self, id: int) -> Optional[T]:
        try:
            return self.model_class.objects.get(pk=id)
        except self.model_class.DoesNotExist:
            return None
    
    def create(self, **kwargs) -> T:
        return self.model_class.objects.create(**kwargs)

# Utilisation
class ArticleRepository(Repository[Article]):
    def get_published(self):
        return self.model_class.objects.filter(status='published')

repo = ArticleRepository()
article = repo.get_by_id(1)
```

### Service Pattern

```python
class ArticleCreationService:
    """Orchestre la création d'article."""
    
    def __init__(
        self,
        repository: ArticleRepository,
        validator: ArticleValidator,
        notifier: ArticleNotifier,
    ):
        self.repository = repository
        self.validator = validator
        self.notifier = notifier
    
    def create(self, data: dict, author: User) -> Article:
        # Validation
        validation = self.validator.validate(data)
        if not validation.is_valid:
            raise ValidationError(validation.errors)
        
        # Création
        article = self.repository.create(
            title=data['title'],
            content=data['content'],
            author=author,
        )
        
        # Notification
        self.notifier.notify_new_article(article)
        
        return article
```

### Factory Pattern

```python
def create_article_service() -> ArticleCreationService:
    """Factory qui crée le service avec ses dépendances."""
    return ArticleCreationService(
        repository=ArticleRepository(),
        validator=ArticleValidator(),
        notifier=ArticleNotifier(EmailService()),
    )

# Utilisation
service = create_article_service()
article = service.create(data, request.user)
```

## Checklist quotidienne

### Avant de committer

**Single Responsibility**
- [ ] Chaque classe a une responsabilité claire
- [ ] Nom de classe décrit ce qu'elle fait
- [ ] Pas de méthodes qui font des choses non liées

**Open/Closed**
- [ ] Nouvelle fonctionnalité = nouvelle classe/méthode
- [ ] Pas de modification de code existant fonctionnel
- [ ] Utilisation de polymorphisme/stratégies

**Liskov Substitution**
- [ ] Implémentations substituables
- [ ] Tests passent avec n'importe quelle implémentation

**Interface Segregation**
- [ ] Pas de méthodes "raise NotImplementedError"
- [ ] Interfaces petites et cohérentes

**Dependency Inversion**
- [ ] Pas de `new ClasseConcrete()` dans le code métier
- [ ] Dépendances injectées via constructeur
- [ ] Facile à mocker dans les tests

## Anti-patterns à détecter

```python
# 🚨 SIGNES D'ALERTE

# 1. Nom de classe contenant "Manager", "Handler", "Processor"
#    = souvent trop de responsabilités
class ArticleManager:  # ❌ SRP violation probable

# 2. Méthodes avec beaucoup de if/elif sur des types
if type == 'A':        # ❌ OCP violation
    do_a()
elif type == 'B':
    do_b()

# 3. Instanciation concrète dans les classes
self.db = MySQL()      # ❌ DIP violation

# 4. Héritage juste pour réutiliser du code
class Utils:           # ❌ Mauvaise utilisation héritage
    def method(self): pass

# 5. Interfaces avec méthodes non utilisées
def method(self):      # ❌ ISP violation
    raise NotImplementedError
```

## Exemple complet : Refactoring pas à pas

### Étape 1 : Code initial (problématique)

```python
class ArticleView(View):
    def post(self, request):
        # Validation
        if not request.POST.get('title'):
            return JsonResponse({'error': 'Titre requis'})
        
        # Création
        article = Article.objects.create(
            title=request.POST['title'],
            content=request.POST['content'],
            author=request.user,
        )
        
        # Envoi d'email
        send_mail(
            subject='Article créé',
            message=f'Votre article {article.title} est créé',
            from_email='noreply@example.com',
            recipient_list=[request.user.email],
        )
        
        # Indexation Elasticsearch
        es.index(index='articles', body={
            'id': article.id,
            'title': article.title,
        })
        
        return JsonResponse({'id': article.id})
```

### Étape 2 : Séparation SRP

```python
class ArticleValidator:
    def validate(self, data):
        if not data.get('title'):
            raise ValidationError('Titre requis')

class ArticleRepository:
    def create(self, data, author):
        return Article.objects.create(**data, author=author)

class ArticleNotifier:
    def notify_created(self, article):
        send_mail(...)

class ArticleIndexer:
    def index(self, article):
        es.index(...)

class ArticleService:
    def __init__(self):
        self.validator = ArticleValidator()
        self.repository = ArticleRepository()
        self.notifier = ArticleNotifier()
        self.indexer = ArticleIndexer()
    
    def create(self, data, author):
        self.validator.validate(data)
        article = self.repository.create(data, author)
        self.notifier.notify_created(article)
        self.indexer.index(article)
        return article
```

### Étape 3 : Injection DIP

```python
class ArticleService:
    def __init__(
        self,
        validator: ArticleValidator,      # Interface
        repository: ArticleRepository,    # Interface
        notifier: ArticleNotifier,        # Interface
        indexer: ArticleIndexer,          # Interface
    ):
        self.validator = validator
        self.repository = repository
        self.notifier = notifier
        self.indexer = indexer

def create_article_service():
    """Factory avec injection."""
    return ArticleService(
        validator=ArticleValidator(),
        repository=ArticleRepository(),
        notifier=ArticleNotifier(),
        indexer=ArticleIndexer(),
    )
```

## Commandes de vérification

```bash
# Compter les méthodes par classe (SRP)
find apps -name "*.py" -exec grep -c "def " {} \; | sort -n | tail

# Détecter les classes suspectes (noms génériques)
grep -r "class.*Manager\|class.*Handler\|class.*Processor" apps/

# Vérifier les imports concrets (DIP)
grep -r "from.*import.*Repository\|from.*import.*Service" apps/
```

## Ressources

- [Documentation complète](./SKILL.md)
- [Architecture Hexagonale](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID en Python](https://realpython.com/solid-principles-python/)

---

**Règle d'or** : Si une classe est difficile à nommer, elle fait trop de choses.
