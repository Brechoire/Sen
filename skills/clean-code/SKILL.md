# Skill : Clean Code

## Objectif

Ce skill présente les principes et pratiques du Clean Code pour écrire du code lisible, maintenable et évolutif. Applicable à tous les langages de programmation.

## Quand utiliser ce skill

- Écriture de nouveau code
- Refactoring de code legacy
- Revue de code
- Formation d'équipe
- Définition de standards de code

## Principes fondamentaux

### 1. Nomenclature

**Noms significatifs et descriptifs**

```python
# ❌ Mauvais - noms peu clairs
def calc(d, r):
    return d * r

# ❌ Mauvais - abréviations obscures
def get_usr_dt(usr_id):
    pass

# ✅ Bon - descriptif et clair
def calculate_rectangle_area(width: float, height: float) -> float:
    """Calcule l'aire d'un rectangle."""
    return width * height

# ✅ Bon - intention révélée
def get_user_by_id(user_id: int) -> User:
    """Récupère un utilisateur par son ID."""
    pass
```

**Conventions de nommage**

```python
# Variables : snake_case, nom significatif
user_count = 10
is_active = True
MAX_RETRY_COUNT = 3  # Constantes : SCREAMING_SNAKE_CASE

# Fonctions : verbe + nom, snake_case
def send_email(to_address: str, subject: str) -> None:
    pass

def calculate_total_price(items: list[Item]) -> Decimal:
    pass

# Classes : PascalCase, nom commun
class UserAccount:
    pass

class PaymentProcessor:
    pass

# Booléens : préfixe is_, has_, can_, should_
is_valid = True
has_permission = False
can_delete = True
should_retry = False
```

### 2. Fonctions

**Règle des 3 : petite, fait une chose, niveau d'abstraction constant**

```python
# ❌ Mauvais - trop longue, fait plusieurs choses
def process_order(order):
    # Validation
    if not order.items:
        raise ValueError("Order must have items")
    
    # Calcul du prix
    total = 0
    for item in order.items:
        total += item.price * item.quantity
    
    # Application de la remise
    if order.customer.is_vip:
        total *= 0.9
    
    # Sauvegarde
    order.total = total
    order.save()
    
    # Envoi d'email
    send_confirmation_email(order)
    
    # Log
    logger.info(f"Order {order.id} processed")
    
    return order

# ✅ Bon - fonctions focalisées
def process_order(order: Order) -> Order:
    """Traite une commande de bout en bout."""
    validate_order(order)
    order.total = calculate_order_total(order)
    save_order(order)
    notify_customer(order)
    log_order_processed(order)
    return order


def validate_order(order: Order) -> None:
    """Valide qu'une commande est correcte."""
    if not order.items:
        raise ValueError("Order must have at least one item")
    if not order.customer:
        raise ValueError("Order must have a customer")


def calculate_order_total(order: Order) -> Decimal:
    """Calcule le total d'une commande avec remises."""
    subtotal = sum(
        item.price * item.quantity 
        for item in order.items
    )
    return apply_discounts(subtotal, order.customer)


def apply_discounts(amount: Decimal, customer: Customer) -> Decimal:
    """Applique les remises applicables."""
    if customer.is_vip:
        return amount * Decimal('0.9')
    return amount
```

**Arguments de fonction**

```python
# ❌ Mauvais - trop d'arguments
def create_user(first_name, last_name, email, phone, address, city, zip_code, country):
    pass

# ✅ Bon - utiliser un objet/dataclass
from dataclasses import dataclass

@dataclass
class UserData:
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    address: Address | None = None


def create_user(user_data: UserData) -> User:
    """Crée un nouvel utilisateur."""
    pass


# ✅ Utiliser des arguments nommés pour la clarté
# Au lieu de :
send_email("test@example.com", "Hello", "Body text", True, None)

# Préférer :
send_email(
    to_address="test@example.com",
    subject="Hello",
    body="Body text",
    is_html=True
)
```

### 3. Commentaires

**Le code doit être auto-documenté**

```python
# ❌ Mauvais - commentaire redondant
# Increment i by 1
i += 1

# ✅ Bon - code clair sans commentaire
line_count += 1

# ❌ Mauvais - commentaire trompeur
# Check if user is active
if user.last_login > threshold:
    pass

# ✅ Bon - nom explicite
if user.is_recently_active:
    pass

# ✅ Bon - commentaire pour expliquer le POURQUOI, pas le QUOI
# Nous utilisons ici un algorithme naïf car les volumes
# sont faibles (< 100 éléments) et la lisibilité prime
# sur la performance dans ce cas.
def find_duplicates(items: list[str]) -> list[str]:
    return [item for item in items if items.count(item) > 1]
```

**Docstrings**

```python
from typing import Optional


def calculate_shipping_cost(
    weight_kg: float,
    destination_country: str,
    express_delivery: bool = False
) -> float:
    """
    Calcule le coût d'expédition d'un colis.
    
    Args:
        weight_kg: Poids du colis en kilogrammes (max 30kg)
        destination_country: Code ISO du pays de destination (ex: 'FR', 'US')
        express_delivery: True pour livraison express (+50%)
    
    Returns:
        Coût d'expédition en euros, arrondi à 2 décimales
    
    Raises:
        ValueError: Si le poids dépasse 30kg ou si le pays est invalide
    
    Example:
        >>> calculate_shipping_cost(2.5, 'FR')
        8.50
        >>> calculate_shipping_cost(2.5, 'FR', express_delivery=True)
        12.75
    """
    if weight_kg > 30:
        raise ValueError("Weight cannot exceed 30kg")
    # ...
```

### 4. Structures de contrôle

```python
# ❌ Mauvais - imbriquations profondes
def process_payment(payment):
    if payment.is_valid:
        if payment.amount > 0:
            if payment.customer.has_funds(payment.amount):
                # Traitement...
                return True
    return False

# ✅ Bon - early returns (guard clauses)
def process_payment(payment: Payment) -> bool:
    """Traite un paiement si valide."""
    if not payment.is_valid:
        return False
    
    if payment.amount <= 0:
        return False
    
    if not payment.customer.has_funds(payment.amount):
        return False
    
    # Traitement principal...
    return True


# ❌ Mauvais - conditions négatives complexes
if not (user.is_active and not user.is_banned):
    pass

# ✅ Bon - conditions positives simples
if user.is_inactive or user.is_banned:
    pass


# ❌ Mauvais - switch/if-else long
if status == "pending":
    process_pending()
elif status == "approved":
    process_approved()
elif status == "rejected":
    process_rejected()
# ... 10 autres cas

# ✅ Bon - utiliser un dictionnaire/mapping
STATUS_HANDLERS = {
    "pending": process_pending,
    "approved": process_approved,
    "rejected": process_rejected,
    # ...
}

def handle_status(status: str) -> None:
    handler = STATUS_HANDLERS.get(status)
    if handler:
        handler()
    else:
        raise ValueError(f"Unknown status: {status}")
```

### 5. Gestion des erreurs

```python
# ❌ Mauvais - retourner None ou codes d'erreur
def divide(a, b):
    if b == 0:
        return None  # Ou -1, ou "error"
    return a / b

result = divide(10, 0)
if result is None:  # Facile à oublier
    handle_error()

# ✅ Bon - exceptions pour les cas exceptionnels
def divide(a: float, b: float) -> float:
    """Divise a par b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

try:
    result = divide(10, 0)
except ValueError as e:
    logger.error(f"Division error: {e}")
    handle_error()


# ✅ Bon - Result/Option pattern pour les cas attendus
from typing import Optional
from dataclasses import dataclass

@dataclass
class Result:
    success: bool
    data: any = None
    error: str = None


def find_user(user_id: int) -> Result:
    """Recherche un utilisateur, retourne un Result."""
    user = database.get(user_id)
    if user:
        return Result(success=True, data=user)
    return Result(success=False, error=f"User {user_id} not found")


# Utilisation
result = find_user(123)
if result.success:
    process_user(result.data)
else:
    show_error(result.error)
```

### 6. Classes et objets

```python
# ❌ Mauvais - classe "god object"
class UserManager:
    def create_user(self): pass
    def delete_user(self): pass
    def authenticate(self): pass
    def send_email(self): pass
    def generate_report(self): pass
    def backup_database(self): pass

# ✅ Bon - responsabilité unique (SRP)
class UserService:
    """Gère le cycle de vie des utilisateurs."""
    
    def __init__(self, repository: UserRepository, email_service: EmailService):
        self.repository = repository
        self.email_service = email_service
    
    def create_user(self, data: UserData) -> User:
        user = User(**data)
        self.repository.save(user)
        self.email_service.send_welcome_email(user)
        return user


class AuthenticationService:
    """Gère l'authentification."""
    
    def authenticate(self, credentials: Credentials) -> Optional[User]:
        pass
    
    def generate_token(self, user: User) -> str:
        pass


# ❌ Mauvais - données et comportement séparés
class UserData:
    name: str
    email: str
    orders: list

class UserProcessor:
    @staticmethod
    def get_total_spent(user_data: UserData) -> float:
        return sum(order.total for order in user_data.orders)

# ✅ Bon - encapsulation
typing import List

class User:
    def __init__(self, name: str, email: str):
        self._name = name
        self._email = email
        self._orders: List[Order] = []
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def email(self) -> str:
        return self._email
    
    def add_order(self, order: Order) -> None:
        self._orders.append(order)
    
    def get_total_spent(self) -> float:
        return sum(order.total for order in self._orders)
```

### 7. DRY (Don't Repeat Yourself)

```python
# ❌ Mauvais - duplication de code
def send_welcome_email(user):
    subject = "Welcome!"
    body = f"Hello {user.name}, welcome to our platform!"
    send_email(user.email, subject, body)

def send_password_reset_email(user):
    subject = "Password Reset"
    body = f"Hello {user.name}, click here to reset your password."
    send_email(user.email, subject, body)

# ✅ Bon - abstraction
@dataclass
class EmailTemplate:
    subject: str
    body_template: str
    
    def render(self, **kwargs) -> tuple[str, str]:
        return self.subject, self.body_template.format(**kwargs)


EMAIL_TEMPLATES = {
    "welcome": EmailTemplate(
        subject="Welcome!",
        body_template="Hello {name}, welcome to our platform!"
    ),
    "password_reset": EmailTemplate(
        subject="Password Reset",
        body_template="Hello {name}, click here to reset your password."
    )
}


def send_templated_email(user: User, template_name: str, **extra_context) -> None:
    """Envoie un email en utilisant un template."""
    template = EMAIL_TEMPLATES[template_name]
    subject, body = template.render(name=user.name, **extra_context)
    send_email(user.email, subject, body)


# Utilisation
send_templated_email(user, "welcome")
send_templated_email(user, "password_reset", reset_link="https://...")
```

## SOLID Principles

### Single Responsibility Principle (SRP)

```python
# ❌ Mauvais - plusieurs responsabilités
class ReportGenerator:
    def read_data(self): pass
    def calculate_statistics(self): pass
    def format_as_pdf(self): pass
    def format_as_csv(self): pass
    def send_email(self): pass
    def save_to_disk(self): pass

# ✅ Bon - séparation des responsabilités
class DataReader:
    """Responsabilité : lire les données."""
    def read(self) -> DataFrame:
        pass

class StatisticsCalculator:
    """Responsabilité : calculer les statistiques."""
    def calculate(self, data: DataFrame) -> Statistics:
        pass

class PDFFormatter:
    """Responsabilité : formater en PDF."""
    def format(self, stats: Statistics) -> PDFDocument:
        pass

class ReportService:
    """Orchestre les différentes responsabilités."""
    def __init__(self, reader, calculator, formatter):
        self.reader = reader
        self.calculator = calculator
        self.formatter = formatter
    
    def generate_report(self) -> PDFDocument:
        data = self.reader.read()
        stats = self.calculator.calculate(data)
        return self.formatter.format(stats)
```

### Open/Closed Principle (OCP)

```python
# ❌ Mauvais - modifié pour chaque nouveau type
def calculate_shipping(product):
    if product.type == "physical":
        return 10.0
    elif product.type == "digital":
        return 0.0
    elif product.type == "subscription":
        return 5.0
    # Ajouter un nouveau elif à chaque nouveau type

# ✅ Bon - extensible sans modification
from abc import ABC, abstractmethod

class ShippingStrategy(ABC):
    @abstractmethod
    def calculate(self, product: Product) -> float:
        pass


class PhysicalShipping(ShippingStrategy):
    def calculate(self, product: Product) -> float:
        return 10.0 * product.weight


class DigitalShipping(ShippingStrategy):
    def calculate(self, product: Product) -> float:
        return 0.0


class ShippingCalculator:
    def __init__(self):
        self._strategies: dict[str, ShippingStrategy] = {}
    
    def register_strategy(self, product_type: str, strategy: ShippingStrategy):
        self._strategies[product_type] = strategy
    
    def calculate(self, product: Product) -> float:
        strategy = self._strategies.get(product.type)
        if not strategy:
            raise ValueError(f"No strategy for type: {product.type}")
        return strategy.calculate(product)


# Utilisation
calculator = ShippingCalculator()
calculator.register_strategy("physical", PhysicalShipping())
calculator.register_strategy("digital", DigitalShipping())
# Ajouter de nouveaux types sans modifier le code existant
```

### Liskov Substitution Principle (LSP)

```python
# ❌ Mauvais - violation de LSP
class Rectangle:
    def __init__(self, width, height):
        self._width = width
        self._height = height
    
    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, value):
        self._width = value
    
    @property
    def height(self):
        return self._height
    
    @height.setter
    def height(self, value):
        self._height = value
    
    def area(self):
        return self._width * self._height


class Square(Rectangle):  # ❌ Violation : un carré n'est pas un rectangle modifiable
    @Rectangle.width.setter
    def width(self, value):
        self._width = value
        self._height = value
    
    @Rectangle.height.setter
    def height(self, value):
        self._width = value
        self._height = value


# ✅ Bon - utiliser la composition
class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        pass


class Rectangle(Shape):
    def __init__(self, width: float, height: float):
        self._width = width
        self._height = height
    
    def area(self) -> float:
        return self._width * self._height


class Square(Shape):
    def __init__(self, side: float):
        self._side = side
    
    def area(self) -> float:
        return self._side ** 2


# Les deux sont substituables
def print_area(shape: Shape) -> None:
    print(f"Area: {shape.area()}")

print_area(Rectangle(4, 5))  # Area: 20
print_area(Square(4))        # Area: 16
```

### Interface Segregation Principle (ISP)

```python
# ❌ Mauvais - interface trop grosse
class Worker:
    def work(self): pass
    def eat(self): pass
    def sleep(self): pass

class Robot(Worker):  # ❌ Le robot ne mange ni ne dort
    def work(self):
        print("Working...")
    
    def eat(self):
        raise NotImplementedError("Robots don't eat")
    
    def sleep(self):
        raise NotImplementedError("Robots don't sleep")

# ✅ Bon - interfaces spécialisées
class Workable(ABC):
    @abstractmethod
    def work(self) -> None:
        pass

class Eatable(ABC):
    @abstractmethod
    def eat(self) -> None:
        pass

class Sleepable(ABC):
    @abstractmethod
    def sleep(self) -> None:
        pass


class Human(Workable, Eatable, Sleepable):
    def work(self): print("Working...")
    def eat(self): print("Eating...")
    def sleep(self): print("Sleeping...")


class Robot(Workable):
    def work(self): print("Working...")
```

### Dependency Inversion Principle (DIP)

```python
# ❌ Mauvais - dépendance concrète
class MySQLDatabase:
    def connect(self): pass
    def query(self, sql): pass

class UserRepository:
    def __init__(self):
        self.db = MySQLDatabase()  # ❌ Couplage fort
    
    def get_user(self, id):
        return self.db.query(f"SELECT * FROM users WHERE id = {id}")

# ✅ Bon - dépendance abstraite
from typing import Protocol

class Database(Protocol):
    def connect(self) -> None: ...
    def query(self, sql: str) -> list[dict]: ...


class UserRepository:
    def __init__(self, db: Database):  # ✅ Injection de dépendance
        self.db = db
    
    def get_user(self, user_id: int) -> User:
        result = self.db.query("SELECT * FROM users WHERE id = %s", (user_id,))
        return User(**result[0]) if result else None


# Implémentations concrètes
class MySQLDatabase:
    def connect(self) -> None: ...
    def query(self, sql: str, params: tuple = ()) -> list[dict]: ...

class PostgreSQLDatabase:
    def connect(self) -> None: ...
    def query(self, sql: str, params: tuple = ()) -> list[dict]: ...


# Injection
repo = UserRepository(MySQLDatabase())
repo = UserRepository(PostgreSQLDatabase())  # Facilement interchangeable
```

## Anti-patterns à éviter

### Code smells

```python
# ❌ Feature Envy - une classe utilise trop de données d'une autre
class Order:
    def __init__(self, customer):
        self.customer = customer

class OrderPrinter:
    def print_order(self, order):
        # Accède beaucoup aux données de Customer
        print(f"Customer: {order.customer.name}")
        print(f"Address: {order.customer.address.street}")
        print(f"City: {order.customer.address.city}")
        # ...

# ✅ Solution : déplacer le comportage vers la classe concernée
class Customer:
    def get_full_address(self) -> str:
        return f"{self.address.street}, {self.address.city}"


# ❌ Primitive Obsession - utiliser des types primitifs au lieu d'objets
def create_user(name: str, email: str, phone: str):
    pass

# ✅ Solution : utiliser des Value Objects
@dataclass(frozen=True)
class Email:
    value: str
    
    def __post_init__(self):
        if not self._is_valid(self.value):
            raise ValueError("Invalid email")
    
    @staticmethod
    def _is_valid(email: str) -> bool:
        return "@" in email

@dataclass(frozen=True)
class Phone:
    value: str
    
    def __post_init__(self):
        if not self._is_valid(self.value):
            raise ValueError("Invalid phone")

def create_user(name: str, email: Email, phone: Phone):
    pass


# ❌ Magic Numbers
def calculate_price(quantity):
    if quantity > 100:
        return quantity * 0.9  # Qu'est-ce que 0.9 ?
    return quantity

# ✅ Solution : constantes nommées
BULK_DISCOUNT_THRESHOLD = 100
BULK_DISCOUNT_RATE = 0.9

def calculate_price(quantity: int) -> float:
    if quantity > BULK_DISCOUNT_THRESHOLD:
        return quantity * BULK_DISCOUNT_RATE
    return quantity
```

## Tests et clean code

```python
# ❌ Mauvais - difficile à tester
def process_order(order_id):
    db = Database()
    order = db.get_order(order_id)
    email_service = EmailService()
    email_service.send_confirmation(order.customer_email)

# ✅ Bon - injectable et testable
class OrderProcessor:
    def __init__(self, repository: OrderRepository, email_service: EmailService):
        self.repository = repository
        self.email_service = email_service
    
    def process_order(self, order_id: int) -> Order:
        order = self.repository.get(order_id)
        self.email_service.send_confirmation(order.customer_email)
        return order


# Test
import pytest
from unittest.mock import Mock

def test_process_order():
    # Arrange
    mock_repo = Mock()
    mock_email = Mock()
    processor = OrderProcessor(mock_repo, mock_email)
    
    order = Order(id=1, customer_email="test@example.com")
    mock_repo.get.return_value = order
    
    # Act
    result = processor.process_order(1)
    
    # Assert
    assert result.id == 1
    mock_email.send_confirmation.assert_called_once_with("test@example.com")
```

## Checklist Clean Code

### Nomenclature
- [ ] Noms révélateurs de l'intention
- [ ] Pas d'abréviations obscures
- [ ] Noms prononçables
- [ ] Un concept = un mot

### Fonctions
- [ ] Petites (< 20 lignes idéalement)
- [ ] Fait une seule chose
- [ ] Niveau d'abstraction constant
- [ ] Pas de side effects cachés
- [ ] Maximum 3 arguments

### Classes
- [ ] Responsabilité unique
- [ ] Faible couplage
- [ ] Forte cohésion
- [ ] Ouvert à l'extension, fermé à la modification

### Code
- [ ] Pas de duplication (DRY)
- [ ] Early returns pour réduire l'imbrication
- [ ] Pas de commentaires inutiles
- [ ] Gestion d'erreurs claire
- [ ] Tests unitaires présents

## Ressources

- [Clean Code - Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Refactoring - Martin Fowler](https://www.amazon.com/Refactoring-Improving-Existing-Addison-Wesley-Signature/dp/0134757599)
- [The Pragmatic Programmer](https://pragprog.com/titles/tpp20/the-pragmatic-programmer-20th-anniversary-edition/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
