# Skill : SOLID Principles

## Objectif

Ce skill présente en profondeur les 5 principes SOLID pour concevoir des architectures logicielles robustes, maintenables et évolutives. Chaque principe est illustré avec des exemples concrets en Python.

## Quand utiliser ce skill

- Conception d'architectures logicielles
- Refactoring d'un code difficile à maintenir
- Revue de code orientée architecture
- Formation sur les principes de conception orientée objet
- Écriture de code testable et découplé

## Vue d'ensemble

```
S - Single Responsibility Principle (SRP)
O - Open/Closed Principle (OCP)
L - Liskov Substitution Principle (LSP)
I - Interface Segregation Principle (ISP)
D - Dependency Inversion Principle (DIP)
```

Ces principes, popularisés par Robert C. Martin (Uncle Bob), visent à créer du code :
- **Compréhensible** : facile à lire et comprendre
- **Flexible** : facile à modifier sans casse-tête
- **Maintenable** : facile à maintenir sur le long terme
- **Testable** : facile à tester unitairement

---

## S - Single Responsibility Principle

### Définition

> **"Une classe devrait avoir une seule raison de changer."**

Une classe ne doit avoir qu'une seule responsabilité, qu'un seul job, qu'un seul objectif.

### Problème

```python
# ❌ Mauvais - trop de responsabilités
class UserManager:
    """Gère les utilisateurs, envoie des emails, génère des rapports, sauvegarde en base..."""
    
    def create_user(self, data):
        # Validation
        if not self._validate_email(data['email']):
            raise ValueError("Email invalide")
        
        # Création en base
        user = User.objects.create(**data)
        
        # Envoi d'email
        self._send_welcome_email(user)
        
        # Log
        self._log_activity(f"User {user.id} created")
        
        # Notification admin
        self._notify_admin(user)
        
        return user
    
    def generate_report(self):
        # Récupération des données
        users = User.objects.all()
        
        # Calcul des statistiques
        stats = self._calculate_stats(users)
        
        # Génération PDF
        pdf = self._generate_pdf(stats)
        
        # Envoi par email
        self._send_report_email(pdf)
    
    def backup_database(self):
        # Logique de backup
        pass
```

**Problèmes identifiés :**
- 6 raisons de changer cette classe (création, email, log, notification, reporting, backup)
- Difficile à tester (besoin de mocks pour email, log, notification...)
- Couplage fort entre les responsabilités
- Impossible de réutiliser une partie sans l'autre

### Solution

```python
# ✅ Bon - séparation des responsabilités

class UserValidator:
    """Responsabilité : valider les données utilisateur."""
    
    def validate(self, data: dict) -> ValidationResult:
        errors = []
        if not self._is_valid_email(data.get('email')):
            errors.append("Email invalide")
        if not self._is_valid_password(data.get('password')):
            errors.append("Mot de passe trop faible")
        return ValidationResult(valid=len(errors) == 0, errors=errors)


class UserRepository:
    """Responsabilité : persistance des utilisateurs."""
    
    def create(self, data: dict) -> User:
        return User.objects.create(**data)
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return User.objects.filter(id=user_id).first()


class EmailService:
    """Responsabilité : envoi d'emails."""
    
    def send_welcome_email(self, user: User) -> None:
        # Envoi d'email de bienvenue
        pass
    
    def send_notification(self, to: str, message: str) -> None:
        # Envoi de notification
        pass


class ActivityLogger:
    """Responsabilité : journalisation des activités."""
    
    def log(self, message: str) -> None:
        logger.info(message)


class UserService:
    """Responsabilité : orchestrer la création d'utilisateur."""
    
    def __init__(
        self,
        validator: UserValidator,
        repository: UserRepository,
        email_service: EmailService,
        logger: ActivityLogger
    ):
        self.validator = validator
        self.repository = repository
        self.email_service = email_service
        self.logger = logger
    
    def create_user(self, data: dict) -> User:
        # Validation
        validation = self.validator.validate(data)
        if not validation.valid:
            raise ValueError(validation.errors)
        
        # Création
        user = self.repository.create(data)
        
        # Actions post-création
        self.email_service.send_welcome_email(user)
        self.logger.log(f"User {user.id} created")
        
        return user
```

### Exemple réel : Gestionnaire de commandes

```python
# ❌ Avant - responsabilités mélangées
class OrderProcessor:
    def process_order(self, order_data):
        # Validation
        if not order_data.get('items'):
            raise ValueError("No items")
        
        # Calcul du prix
        total = sum(item['price'] * item['qty'] for item in order_data['items'])
        
        # Application des taxes
        tax_rate = self._get_tax_rate(order_data['country'])
        total_with_tax = total * (1 + tax_rate)
        
        # Sauvegarde en base
        order = Order.objects.create(
            items=order_data['items'],
            total=total_with_tax,
            customer_id=order_data['customer_id']
        )
        
        # Paiement
        payment_result = self._process_payment(order, order_data['payment_info'])
        if not payment_result.success:
            order.status = 'failed'
            order.save()
            raise PaymentError("Payment failed")
        
        # Envoi d'email de confirmation
        self._send_confirmation_email(order)
        
        # Mise à jour de l'inventaire
        self._update_inventory(order_data['items'])
        
        # Notification à l'expédition
        self._notify_shipping(order)
        
        return order


# ✅ Après - séparation claire
class OrderValidator:
    def validate(self, order_data: dict) -> None:
        if not order_data.get('items'):
            raise ValueError("Order must have items")
        if not order_data.get('customer_id'):
            raise ValueError("Customer ID required")


class PriceCalculator:
    def calculate_total(self, items: list, country: str) -> Decimal:
        subtotal = sum(item['price'] * item['qty'] for item in items)
        tax_rate = self._get_tax_rate(country)
        return subtotal * (1 + tax_rate)


class PaymentProcessor:
    def process(self, amount: Decimal, payment_info: dict) -> PaymentResult:
        # Logique de paiement
        pass


class OrderRepository:
    def save(self, order_data: dict) -> Order:
        return Order.objects.create(**order_data)
    
    def update_status(self, order_id: int, status: str) -> None:
        Order.objects.filter(id=order_id).update(status=status)


class EmailNotifier:
    def send_order_confirmation(self, order: Order) -> None:
        # Envoi d'email
        pass


class InventoryManager:
    def reserve_items(self, items: list) -> None:
        # Mise à jour de l'inventaire
        pass


class ShippingService:
    def schedule_delivery(self, order: Order) -> None:
        # Planification de la livraison
        pass


class OrderService:
    """Orchestre le processus de commande."""
    
    def __init__(
        self,
        validator: OrderValidator,
        calculator: PriceCalculator,
        payment_processor: PaymentProcessor,
        repository: OrderRepository,
        email_notifier: EmailNotifier,
        inventory_manager: InventoryManager,
        shipping_service: ShippingService
    ):
        self.validator = validator
        self.calculator = calculator
        self.payment_processor = payment_processor
        self.repository = repository
        self.email_notifier = email_notifier
        self.inventory_manager = inventory_manager
        self.shipping_service = shipping_service
    
    def process_order(self, order_data: dict) -> Order:
        # Validation
        self.validator.validate(order_data)
        
        # Calcul du prix
        total = self.calculator.calculate_total(
            order_data['items'],
            order_data['country']
        )
        
        # Création de la commande
        order = self.repository.save({
            'items': order_data['items'],
            'total': total,
            'customer_id': order_data['customer_id'],
            'status': 'pending'
        })
        
        try:
            # Paiement
            payment = self.payment_processor.process(
                total,
                order_data['payment_info']
            )
            
            if not payment.success:
                self.repository.update_status(order.id, 'payment_failed')
                raise PaymentError("Payment failed")
            
            # Actions post-paiement
            self.repository.update_status(order.id, 'paid')
            self.inventory_manager.reserve_items(order_data['items'])
            self.email_notifier.send_order_confirmation(order)
            self.shipping_service.schedule_delivery(order)
            
        except Exception as e:
            self.repository.update_status(order.id, 'error')
            raise
        
        return order
```

### Indicateurs de violation du SRP

1. **Nom de classe contenant "Manager", "Processor", "Handler"** : souvent signe de trop de responsabilités
2. **Trop de méthodes publiques** (> 7-10 méthodes)
3. **Classe dépend de trop d'autres classes** (> 5 dépendances)
4. **Difficile à nommer** : si vous ne trouvez pas un nom clair, la classe fait trop de choses

---

## O - Open/Closed Principle

### Définition

> **"Les entités logicielles (classes, modules, fonctions) devraient être ouvertes à l'extension, mais fermées à la modification."**

On devrait pouvoir ajouter de nouvelles fonctionnalités sans modifier le code existant.

### Problème

```python
# ❌ Mauvais - modifié à chaque nouveau type
class PaymentProcessor:
    def process(self, payment_type: str, amount: float):
        if payment_type == "credit_card":
            self._process_credit_card(amount)
        elif payment_type == "paypal":
            self._process_paypal(amount)
        elif payment_type == "bank_transfer":
            self._process_bank_transfer(amount)
        elif payment_type == "crypto":  # Ajouté plus tard
            self._process_crypto(amount)
        # Nouveau type ? On modifie cette méthode !


class ReportGenerator:
    def generate(self, format: str, data: dict):
        if format == "pdf":
            return self._generate_pdf(data)
        elif format == "excel":
            return self._generate_excel(data)
        elif format == "csv":
            return self._generate_csv(data)
        # Nouveau format ? On modifie cette méthode !
```

**Problèmes identifiés :**
- Modification à chaque nouveau type (risque de régression)
- Classe qui grandit indéfiniment
- Testing difficile (tous les cas à tester ensemble)
- Violation du SRP également

### Solution avec polymorphisme

```python
from abc import ABC, abstractmethod
from typing import Protocol

# ✅ Solution avec Protocol (Python 3.8+)
class PaymentMethod(Protocol):
    """Interface pour les méthodes de paiement."""
    
    def process(self, amount: float) -> PaymentResult:
        ...


class CreditCardPayment:
    """Extension : paiement par carte."""
    
    def __init__(self, card_number: str, cvv: str):
        self.card_number = card_number
        self.cvv = cvv
    
    def process(self, amount: float) -> PaymentResult:
        # Logique spécifique carte
        return PaymentResult(success=True, transaction_id="CC123")


class PayPalPayment:
    """Extension : paiement PayPal."""
    
    def __init__(self, email: str, token: str):
        self.email = email
        self.token = token
    
    def process(self, amount: float) -> PaymentResult:
        # Logique spécifique PayPal
        return PaymentResult(success=True, transaction_id="PP456")


class CryptoPayment:
    """Extension : paiement crypto (ajouté sans modifier le code existant)."""
    
    def __init__(self, wallet_address: str):
        self.wallet_address = wallet_address
    
    def process(self, amount: float) -> PaymentResult:
        # Logique spécifique crypto
        return PaymentResult(success=True, transaction_id="CRYPTO789")


class PaymentProcessor:
    """Fermé à la modification, ouvert à l'extension."""
    
    def process_payment(self, payment_method: PaymentMethod, amount: float) -> PaymentResult:
        """Fonctionne avec n'importe quelle méthode de paiement."""
        return payment_method.process(amount)


# Utilisation
processor = PaymentProcessor()

# Carte
cc_payment = CreditCardPayment("1234-5678", "123")
processor.process_payment(cc_payment, 100.0)

# PayPal
paypal_payment = PayPalPayment("user@example.com", "token123")
processor.process_payment(paypal_payment, 100.0)

# Crypto (nouveau, sans modifier PaymentProcessor)
crypto_payment = CryptoPayment("0x123...")
processor.process_payment(crypto_payment, 100.0)
```

### Exemple réel : Stratégies de réduction

```python
from abc import ABC, abstractmethod
from decimal import Decimal


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


class FixedAmountDiscount(DiscountStrategy):
    """Réduction en montant fixe."""
    
    def __init__(self, amount: Decimal):
        self.discount_amount = amount
    
    def calculate_discount(self, amount: Decimal) -> Decimal:
        return min(self.discount_amount, amount)
    
    def is_applicable(self, context: DiscountContext) -> bool:
        return amount >= self.minimum_purchase


class MemberDiscount(DiscountStrategy):
    """Réduction pour membres (nouveau type, extension)."""
    
    def calculate_discount(self, amount: Decimal) -> Decimal:
        return amount * Decimal('0.15')  # 15% pour membres
    
    def is_applicable(self, context: DiscountContext) -> bool:
        return context.user.is_member and context.user.member_since < datetime.now() - timedelta(days=365)


class SeasonalDiscount(DiscountStrategy):
    """Réduction saisonnière (nouveau type, extension)."""
    
    def __init__(self, season: str, discount_rate: Decimal):
        self.season = season
        self.discount_rate = discount_rate
    
    def calculate_discount(self, amount: Decimal) -> Decimal:
        return amount * self.discount_rate
    
    def is_applicable(self, context: DiscountContext) -> bool:
        return self._is_current_season(self.season)


class DiscountCalculator:
    """Calculateur de réductions - fermé à la modification."""
    
    def __init__(self):
        self._strategies: list[DiscountStrategy] = []
    
    def register_strategy(self, strategy: DiscountStrategy) -> None:
        """Ajoute une nouvelle stratégie (extension)."""
        self._strategies.append(strategy)
    
    def calculate_best_discount(self, amount: Decimal, context: DiscountContext) -> Decimal:
        """Calcule la meilleure réduction applicable."""
        applicable_discounts = [
            strategy.calculate_discount(amount)
            for strategy in self._strategies
            if strategy.is_applicable(context)
        ]
        
        return max(applicable_discounts, default=Decimal('0'))


# Utilisation
calculator = DiscountCalculator()

# Enregistrer les stratégies
calculator.register_strategy(NoDiscount())
calculator.register_strategy(PercentageDiscount(Decimal('10')))
calculator.register_strategy(MemberDiscount())  # Extension
calculator.register_strategy(SeasonalDiscount('summer', Decimal('0.20')))  # Extension

# Calculer
context = DiscountContext(user=current_user, date=datetime.now())
discount = calculator.calculate_best_discount(Decimal('100'), context)
```

### Pattern Strategy avec fonctions

```python
from typing import Callable

# Version plus simple avec fonctions
def calculate_percentage_discount(amount: float, percentage: float) -> float:
    return amount * (percentage / 100)

def calculate_fixed_discount(amount: float, fixed_amount: float) -> float:
    return min(fixed_amount, amount)

def calculate_buy_one_get_one(items: list) -> float:
    # Logique BOGO
    pass

DiscountFunction = Callable[[float], float]

class DiscountCalculator:
    def __init__(self):
        self._rules: list[tuple[Callable[[], bool], DiscountFunction]] = []
    
    def add_rule(self, condition: Callable[[], bool], discount_fn: DiscountFunction):
        self._rules.append((condition, discount_fn))
    
    def calculate(self, amount: float) -> float:
        for condition, discount_fn in self._rules:
            if condition():
                return discount_fn(amount)
        return 0

# Utilisation
calc = DiscountCalculator()
calc.add_rule(lambda: user.is_vip, lambda amount: calculate_percentage_discount(amount, 20))
calc.add_rule(lambda: amount > 100, lambda amount: calculate_fixed_discount(amount, 10))
```

---

## L - Liskov Substitution Principle

### Définition

> **"Les objets d'une classe fille doivent pouvoir substituer les objets de la classe parent sans altérer le fonctionnement du programme."**

Si B hérite de A, alors on devrait pouvoir utiliser B partout où A est attendu.

### Problème classique : Rectangle vs Carré

```python
# ❌ Mauvais - violation de LSP
class Rectangle:
    def __init__(self, width: float, height: float):
        self._width = width
        self._height = height
    
    @property
    def width(self) -> float:
        return self._width
    
    @width.setter
    def width(self, value: float):
        self._width = value
    
    @property
    def height(self) -> float:
        return self._height
    
    @height.setter
    def height(self, value: float):
        self._height = value
    
    def area(self) -> float:
        return self._width * self._height


class Square(Rectangle):
    """❌ Violation : un carré n'est PAS un rectangle modifiable."""
    
    def __init__(self, side: float):
        super().__init__(side, side)
    
    @Rectangle.width.setter
    def width(self, value: float):
        """❌ Effet de bord inattendu : modifie aussi la hauteur !"""
        self._width = value
        self._height = value  # Surprise !
    
    @Rectangle.height.setter
    def height(self, value: float):
        """❌ Effet de bord inattendu : modifie aussi la largeur !"""
        self._width = value
        self._height = value  # Surprise !


# ❌ Problème
def resize_rectangle(rect: Rectangle, new_width: float) -> None:
    """Fonction qui suppose que width et height sont indépendants."""
    original_height = rect.height
    rect.width = new_width
    # Attend : area = new_width * original_height
    # Avec Square : area = new_width * new_width (height a aussi changé !)
    assert rect.height == original_height, "Height shouldn't change!"  # Échoue avec Square


# Test
rect = Rectangle(4, 5)
resize_rectangle(rect, 6)  # ✓ Fonctionne

square = Square(5)
resize_rectangle(square, 6)  # ✗ AssertionError !
```

### Solution correcte

```python
from abc import ABC, abstractmethod

# ✅ Bon - utiliser la composition ou une interface commune
class Shape(ABC):
    """Interface commune pour toutes les formes."""
    
    @abstractmethod
    def area(self) -> float:
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        pass


class Rectangle(Shape):
    """Rectangle immuable (pas de setters)."""
    
    def __init__(self, width: float, height: float):
        self._width = width
        self._height = height
    
    @property
    def width(self) -> float:
        return self._width
    
    @property
    def height(self) -> float:
        return self._height
    
    def area(self) -> float:
        return self._width * self._height
    
    def perimeter(self) -> float:
        return 2 * (self._width + self._height)
    
    def with_width(self, new_width: float) -> 'Rectangle':
        """Retourne un nouveau rectangle (immutabilité)."""
        return Rectangle(new_width, self._height)


class Square(Shape):
    """Carré - pas d'héritage problématique."""
    
    def __init__(self, side: float):
        self._side = side
    
    @property
    def side(self) -> float:
        return self._side
    
    def area(self) -> float:
        return self._side ** 2
    
    def perimeter(self) -> float:
        return 4 * self._side
    
    def with_side(self, new_side: float) -> 'Square':
        """Retourne un nouveau carré (immutabilité)."""
        return Square(new_side)


# ✅ Utilisation polymorphe
def print_shape_info(shape: Shape) -> None:
    """Fonctionne avec n'importe quelle Shape."""
    print(f"Area: {shape.area()}")
    print(f"Perimeter: {shape.perimeter()}")


# Test
print_shape_info(Rectangle(4, 5))  # ✓ Fonctionne
print_shape_info(Square(5))        # ✓ Fonctionne aussi
```

### Exemple réel : Repository Pattern

```python
from abc import ABC, abstractmethod
from typing import Optional, Protocol


class UserRepository(Protocol):
    """Interface pour tous les repositories utilisateur."""
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        ...
    
    def save(self, user: User) -> User:
        ...
    
    def delete(self, user_id: int) -> None:
        ...


class PostgresUserRepository:
    """Implémentation PostgreSQL."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        row = self.db.execute(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        ).fetchone()
        return User(**row) if row else None
    
    def save(self, user: User) -> User:
        if user.id:
            self.db.execute(
                "UPDATE users SET name = %s WHERE id = %s",
                (user.name, user.id)
            )
        else:
            result = self.db.execute(
                "INSERT INTO users (name) VALUES (%s) RETURNING id",
                (user.name,)
            )
            user.id = result.fetchone()[0]
        return user


class MongoUserRepository:
    """Implémentation MongoDB - substituable à PostgresUserRepository."""
    
    def __init__(self, mongo_client):
        self.collection = mongo_client.db.users
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        doc = self.collection.find_one({"_id": user_id})
        return User(**doc) if doc else None
    
    def save(self, user: User) -> User:
        if user.id:
            self.collection.update_one(
                {"_id": user.id},
                {"$set": {"name": user.name}}
            )
        else:
            result = self.collection.insert_one({"name": user.name})
            user.id = result.inserted_id
        return user


class InMemoryUserRepository:
    """Implémentation en mémoire pour les tests - aussi substituable."""
    
    def __init__(self):
        self._users: dict[int, User] = {}
        self._next_id = 1
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)
    
    def save(self, user: User) -> User:
        if not user.id:
            user.id = self._next_id
            self._next_id += 1
        self._users[user.id] = user
        return user


class UserService:
    """Fonctionne avec n'importe quelle implémentation de UserRepository."""
    
    def __init__(self, repository: UserRepository):
        self.repo = repository
    
    def get_user(self, user_id: int) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user


# Utilisation interchangeable
service = UserService(PostgresUserRepository(db))
service = UserService(MongoUserRepository(mongo_client))
service = UserService(InMemoryUserRepository())  # Pour les tests
```

### Règles pour respecter LSP

1. **Préconditions pas renforcées** : La classe fille ne doit pas exiger plus que la classe parent
2. **Postconditions pas affaiblies** : La classe fille ne doit pas garantir moins que la classe parent
3. **Pas de nouveau type d'exception** : La classe fille ne doit pas lever des exceptions inattendues
4. **Invariant conservés** : Les invariants de la classe parent doivent être respectés

---

## I - Interface Segregation Principle

### Définition

> **"Les clients ne devraient pas être forcés de dépendre d'interfaces qu'ils n'utilisent pas."**

Préférer plusieurs interfaces petites et spécialisées plutôt qu'une grosse interface générale.

### Problème

```python
# ❌ Mauvais - interface trop grosse
class Worker:
    """Interface trop large avec trop de méthodes."""
    
    def work(self) -> None:
        pass
    
    def eat(self) -> None:
        pass
    
    def sleep(self) -> None:
        pass
    
    def take_break(self) -> None:
        pass
    
    def attend_meeting(self) -> None:
        pass
    
    def submit_timesheet(self) -> None:
        pass


class HumanWorker(Worker):
    """Un humain fait tout."""
    
    def work(self) -> None:
        print("Working...")
    
    def eat(self) -> None:
        print("Eating...")
    
    def sleep(self) -> None:
        print("Sleeping...")
    
    def take_break(self) -> None:
        print("Taking break...")
    
    def attend_meeting(self) -> None:
        print("Attending meeting...")
    
    def submit_timesheet(self) -> None:
        print("Submitting timesheet...")


class RobotWorker(Worker):
    """❌ Problème : le robot doit implémenter eat(), sleep(), etc. !"""
    
    def work(self) -> None:
        print("Robot working...")
    
    def eat(self) -> None:
        raise NotImplementedError("Robots don't eat!")  # ❌ Violation
    
    def sleep(self) -> None:
        raise NotImplementedError("Robots don't sleep!")  # ❌ Violation
    
    def take_break(self) -> None:
        raise NotImplementedError("Robots don't take breaks!")  # ❌ Violation
    
    def attend_meeting(self) -> None:
        print("Robot attending meeting...")
    
    def submit_timesheet(self) -> None:
        raise NotImplementedError("Robots don't submit timesheets!")  # ❌ Violation
```

### Solution avec interfaces spécialisées

```python
from typing import Protocol


class Workable(Protocol):
    """Interface pour tout ce qui peut travailler."""
    
    def work(self) -> None:
        ...


class Eatable(Protocol):
    """Interface pour tout ce qui peut manger."""
    
    def eat(self) -> None:
        ...


class Sleepable(Protocol):
    """Interface pour tout ce qui peut dormir."""
    
    def sleep(self) -> None:
        ...


class MeetingAttendee(Protocol):
    """Interface pour les participants aux réunions."""
    
    def attend_meeting(self) -> None:
        ...


class Human:
    """Humain : implémente plusieurs interfaces."""
    
    def work(self) -> None:
        print("Human working...")
    
    def eat(self) -> None:
        print("Human eating...")
    
    def sleep(self) -> None:
        print("Human sleeping...")
    
    def attend_meeting(self) -> None:
        print("Human in meeting...")


class Robot:
    """Robot : implémente uniquement ce qui est pertinent."""
    
    def work(self) -> None:
        print("Robot working...")
    
    def attend_meeting(self) -> None:
        print("Robot in meeting...")


class Printer:
    """Imprimante : seulement Workable."""
    
    def work(self) -> None:
        print("Printing...")


# Fonctions qui utilisent les interfaces spécialisées
def assign_task(worker: Workable, task: str) -> None:
    """Accepte tout ce qui est Workable."""
    print(f"Assigning {task} to worker")
    worker.work()


def schedule_lunch(person: Eatable) -> None:
    """Accepte seulement ce qui est Eatable."""
    print("Lunch time!")
    person.eat()


def organize_meeting(attendees: list[MeetingAttendee]) -> None:
    """Accepte seulement les MeetingAttendee."""
    print("Meeting starting...")
    for attendee in attendees:
        attendee.attend_meeting()


# Utilisation
human = Human()
robot = Robot()
printer = Printer()

assign_task(human, "coding")      # ✓
assign_task(robot, "welding")     # ✓
assign_task(printer, "printing")  # ✓

schedule_lunch(human)  # ✓
# schedule_lunch(robot)  # ✗ Erreur de type !

organize_meeting([human, robot])  # ✓
# organize_meeting([printer])  # ✗ Erreur de type !
```

### Exemple réel : Interfaces de stockage

```python
from typing import Protocol, BinaryIO


class Readable(Protocol):
    """Interface pour lecture seule."""
    
    def read(self, path: str) -> bytes:
        ...
    
    def exists(self, path: str) -> bool:
        ...


class Writable(Protocol):
    """Interface pour écriture seule."""
    
    def write(self, path: str, data: bytes) -> None:
        ...
    
    def delete(self, path: str) -> None:
        ...


class Listable(Protocol):
    """Interface pour lister le contenu."""
    
    def list_files(self, directory: str) -> list[str]:
        ...


# Implémentation complète
class LocalFileStorage:
    """Stockage local : implémente tout."""
    
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
    
    def list_files(self, directory: str) -> list[str]:
        import os
        return os.listdir(directory)


# Implémentation lecture seule
class ReadOnlyS3Storage:
    """S3 lecture seule : implémente uniquement Readable."""
    
    def __init__(self, bucket: str):
        self.bucket = bucket
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


# Fonctions utilisant les interfaces
def load_configuration(storage: Readable, config_path: str) -> dict:
    """Charge la config depuis n'importe quel Readable."""
    import json
    data = storage.read(config_path)
    return json.loads(data)


def backup_files(source: Readable, destination: Writable, files: list[str]) -> None:
    """Backup : source Readable, destination Writable."""
    for file in files:
        if source.exists(file):
            data = source.read(file)
            destination.write(f"backup/{file}", data)


def generate_report(storage: Listable, directory: str) -> str:
    """Génère un rapport des fichiers."""
    files = storage.list_files(directory)
    return f"Directory contains {len(files)} files"


# Utilisation flexible
local = LocalFileStorage()
s3_readonly = ReadOnlyS3Storage("my-bucket")

# Fonctionne avec les deux
config = load_configuration(local, "/etc/app/config.json")
config = load_configuration(s3_readonly, "configs/app.json")

# Lecture seule protégée par le type system
# s3_readonly.write("test.txt", b"data")  # ✗ Erreur !
```

---

## D - Dependency Inversion Principle

### Définition

> **1. Les modules de haut niveau ne devraient pas dépendre des modules de bas niveau. Les deux devraient dépendre d'abstractions.**
> 
> **2. Les abstractions ne devraient pas dépendre des détails. Les détails devraient dépendre des abstractions.**

Dépendre d'interfaces, pas d'implémentations concrètes.

### Problème

```python
# ❌ Mauvais - dépendance concrète directe
class MySQLUserRepository:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="secret"
        )
    
    def get_user(self, user_id: int) -> User:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return User(*cursor.fetchone())


class UserService:
    """❌ Dépend directement de MySQLUserRepository (concret)"""
    
    def __init__(self):
        self.repository = MySQLUserRepository()  # ❌ Couplage fort
    
    def get_user(self, user_id: int) -> User:
        return self.repository.get_user(user_id)


# Problèmes :
# 1. Impossible de tester sans base MySQL réelle
# 2. Impossible de changer pour PostgreSQL sans modifier UserService
# 3. Configuration codée en dur
# 4. Difficile à mocker
```

### Solution avec injection de dépendances

```python
from typing import Protocol, Optional
from abc import ABC, abstractmethod


# ✅ Abstraction (interface)
class UserRepository(Protocol):
    """Interface/abstraction pour tous les repositories."""
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        ...
    
    def save(self, user: User) -> User:
        ...
    
    def delete(self, user_id: int) -> None:
        ...


# ✅ Implémentations concrètes (dépendent de l'abstraction)
class MySQLUserRepository:
    """Implémentation MySQL."""
    
    def __init__(self, connection_pool):
        self.pool = connection_pool
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            return User(**row) if row else None
    
    def save(self, user: User) -> User:
        # Implémentation
        pass
    
    def delete(self, user_id: int) -> None:
        # Implémentation
        pass


class PostgreSQLUserRepository:
    """Implémentation PostgreSQL."""
    
    def __init__(self, connection_pool):
        self.pool = connection_pool
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            return User(**row) if row else None
    
    def save(self, user: User) -> User:
        # Implémentation PostgreSQL
        pass
    
    def delete(self, user_id: int) -> None:
        pass


class InMemoryUserRepository:
    """Implémentation en mémoire pour les tests."""
    
    def __init__(self):
        self._users: dict[int, User] = {}
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)
    
    def save(self, user: User) -> User:
        if not user.id:
            user.id = len(self._users) + 1
        self._users[user.id] = user
        return user
    
    def delete(self, user_id: int) -> None:
        self._users.pop(user_id, None)


# ✅ Module de haut niveau dépend de l'abstraction
class UserService:
    """Dépend de UserRepository (abstraction), pas d'une implémentation concrète."""
    
    def __init__(self, repository: UserRepository):
        self._repository = repository  # ✅ Injection de dépendance
    
    def get_user(self, user_id: int) -> User:
        user = self._repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user
    
    def create_user(self, user_data: dict) -> User:
        user = User(**user_data)
        return self._repository.save(user)
    
    def deactivate_user(self, user_id: int) -> None:
        user = self.get_user(user_id)
        user.is_active = False
        self._repository.save(user)


# ✅ Utilisation avec injection
def create_production_service():
    """Crée le service pour la production."""
    from mysql.connector import pooling
    pool = pooling.MySQLConnectionPool(
        host="localhost",
        user="app",
        password="secret",
        database="myapp"
    )
    repository = MySQLUserRepository(pool)
    return UserService(repository)


def create_test_service():
    """Crée le service pour les tests."""
    repository = InMemoryUserRepository()
    return UserService(repository)


def create_development_service():
    """Crée le service pour le développement."""
    from psycopg2 import pool
    pg_pool = pool.ThreadedConnectionPool(
        1, 10,
        host="localhost",
        database="devdb",
        user="dev",
        password="devpass"
    )
    repository = PostgreSQLUserRepository(pg_pool)
    return UserService(repository)


# Usage
if os.getenv("ENV") == "test":
    service = create_test_service()
elif os.getenv("ENV") == "dev":
    service = create_development_service()
else:
    service = create_production_service()
```

### Injection de dépendances avec un container

```python
from typing import TypeVar, Type

T = TypeVar('T')

class DIContainer:
    """Container d'injection de dépendances simple."""
    
    def __init__(self):
        self._registrations: dict[Type, any] = {}
        self._singletons: dict[Type, any] = {}
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Enregistre une instance singleton."""
        self._singletons[interface] = instance
    
    def register_factory(self, interface: Type[T], factory: callable) -> None:
        """Enregistre une factory pour créer des instances."""
        self._registrations[interface] = factory
    
    def resolve(self, interface: Type[T]) -> T:
        """Résout une dépendance."""
        if interface in self._singletons:
            return self._singletons[interface]
        
        if interface in self._registrations:
            return self._registrations[interface](self)
        
        raise KeyError(f"No registration for {interface}")


# Configuration du container
container = DIContainer()

# Enregistrement des dépendances
container.register_factory(
    UserRepository,
    lambda c: MySQLUserRepository(c.resolve(ConnectionPool))
)

container.register_factory(
    ConnectionPool,
    lambda c: MySQLConnectionPool(host="localhost", user="app", password="secret")
)

container.register_factory(
    UserService,
    lambda c: UserService(c.resolve(UserRepository))
)

# Résolution
user_service = container.resolve(UserService)
```

### Exemple réel : Notification Service

```python
from typing import Protocol
from abc import ABC, abstractmethod


# ✅ Abstractions
class Notifier(Protocol):
    """Interface pour tous les canaux de notification."""
    
    def send(self, recipient: str, message: str) -> bool:
        ...


class Logger(Protocol):
    """Interface pour le logging."""
    
    def log(self, message: str) -> None:
        ...


# ✅ Détails (implémentations concrètes)
class EmailNotifier:
    """Notification par email."""
    
    def __init__(self, smtp_server: str, api_key: str):
        self.smtp = smtp_server
        self.api_key = api_key
    
    def send(self, recipient: str, message: str) -> bool:
        # Envoi d'email via SMTP
        print(f"Sending email to {recipient}: {message}")
        return True


class SMSNotifier:
    """Notification par SMS."""
    
    def __init__(self, twilio_client):
        self.twilio = twilio_client
    
    def send(self, recipient: str, message: str) -> bool:
        # Envoi SMS via Twilio
        print(f"Sending SMS to {recipient}: {message}")
        return True


class PushNotifier:
    """Notification push."""
    
    def __init__(self, firebase_client):
        self.firebase = firebase_client
    
    def send(self, recipient: str, message: str) -> bool:
        # Envoi push via Firebase
        print(f"Sending push to {recipient}: {message}")
        return True


class ConsoleLogger:
    """Logger vers la console."""
    
    def log(self, message: str) -> None:
        print(f"[LOG] {message}")


class FileLogger:
    """Logger vers fichier."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    def log(self, message: str) -> None:
        with open(self.file_path, 'a') as f:
            f.write(f"{message}\n")


# ✅ Module de haut niveau
class NotificationService:
    """
    Service de notification qui dépend d'abstractions.
    
    Peut notifier via plusieurs canaux et logger les actions.
    """
    
    def __init__(
        self,
        notifiers: list[Notifier],
        logger: Logger,
        fallback_notifier: Notifier | None = None
    ):
        self.notifiers = notifiers
        self.logger = logger
        self.fallback = fallback_notifier
    
    def notify_user(self, user: User, message: str) -> NotificationResult:
        """Notifie un utilisateur via tous les canaux configurés."""
        success_count = 0
        failed_channels = []
        
        for notifier in self.notifiers:
            try:
                # Déterminer le bon identifiant selon le type de notifier
                recipient = self._get_recipient_for_notifier(user, notifier)
                
                if notifier.send(recipient, message):
                    success_count += 1
                    self.logger.log(f"Notification sent to {user.id} via {type(notifier).__name__}")
                else:
                    failed_channels.append(type(notifier).__name__)
                    
            except Exception as e:
                self.logger.log(f"Failed to notify {user.id}: {str(e)}")
                failed_channels.append(type(notifier).__name__)
        
        # Fallback si tout a échoué
        if success_count == 0 and self.fallback:
            try:
                if self.fallback.send(user.email, message):
                    success_count = 1
                    self.logger.log(f"Fallback notification sent to {user.id}")
            except Exception as e:
                self.logger.log(f"Fallback also failed: {str(e)}")
        
        return NotificationResult(
            success=success_count > 0,
            channels_attempted=len(self.notifiers),
            channels_succeeded=success_count,
            failed_channels=failed_channels
        )
    
    def _get_recipient_for_notifier(self, user: User, notifier: Notifier) -> str:
        """Détermine le destinataire selon le type de notifier."""
        if isinstance(notifier, EmailNotifier):
            return user.email
        elif isinstance(notifier, SMSNotifier):
            return user.phone
        elif isinstance(notifier, PushNotifier):
            return user.device_token
        return user.email  # Default


# ✅ Utilisation flexible
# Production : email + SMS
email = EmailNotifier("smtp.gmail.com", "api-key")
sms = SMSNotifier(twilio_client)
logger = FileLogger("/var/log/notifications.log")

service = NotificationService(
    notifiers=[email, sms],
    logger=logger
)

# Test : console uniquement
console_logger = ConsoleLogger()
test_service = NotificationService(
    notifiers=[],  # Pas de vraie notification en test
    logger=console_logger,
    fallback=ConsoleNotifier()  # Fallback vers console
)

# Développement : tout vers console
dev_service = NotificationService(
    notifiers=[ConsoleNotifier(), ConsoleNotifier()],  # Simule email et SMS
    logger=ConsoleLogger()
)
```

## Synthèse et checklist

### Application pratique

Pour chaque nouvelle classe/module, vérifiez :

**SRP - Single Responsibility**
- [ ] La classe a-t-elle une seule raison de changer ?
- [ ] Peut-on décrire sa responsabilité en une phrase ?
- [ ] A-t-elle moins de 7-10 méthodes publiques ?

**OCP - Open/Closed**
- [ ] Peut-on ajouter une fonctionnalité sans modifier le code ?
- [ ] Utilise-t-on des stratégies/polymorphisme ?
- [ ] Les `if/elif` sur les types sont-ils évités ?

**LSP - Liskov Substitution**
- [ ] Les classes filles peuvent-elles remplacer les parents ?
- [ ] Pas d'effets de bord inattendus ?
- [ ] Les mêmes préconditions/postconditions ?

**ISP - Interface Segregation**
- [ ] Les interfaces sont-elles petites et cohésives ?
- [ ] Pas de méthodes "vides" ou "NotImplemented" ?
- [ ] Chaque client utilise toutes les méthodes de l'interface ?

**DIP - Dependency Inversion**
- [ ] Dépendances vers des abstractions, pas des concrets ?
- [ ] Injection de dépendances utilisée ?
- [ ] Facile à tester avec des mocks ?

### Ressources

- [Clean Architecture - Robert C. Martin](https://www.amazon.com/Clean-Architecture-Craftsmans-Software-Structure/dp/0134494164)
- [SOLID Principles in Python](https://realpython.com/solid-principles-python/)
- [Refactoring Guru - SOLID](https://refactoring.guru/design-patterns)
