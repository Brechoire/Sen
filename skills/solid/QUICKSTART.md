# SOLID Principles - Démarrage Rapide

## Les 5 principes en 5 minutes

```
S - Single Responsibility : Une classe = une responsabilité
O - Open/Closed         : Ouvert à l'extension, fermé à la modification
L - Liskov Substitution : Les filles substituables aux parents
I - Interface Segregation : Petites interfaces spécialisées
D - Dependency Inversion : Dépendre d'abstractions
```

## Checklist rapide

### Avant d'écrire une classe
- [ ] Elle a-t-elle une seule raison de changer ? (SRP)
- [ ] Peut-on l'étendre sans la modifier ? (OCP)
- [ ] Dépend-elle d'interfaces, pas de concrets ? (DIP)

### Après avoir écrit
- [ ] Test unitaire facile ? (DIP)
- [ ] Pas de méthodes "pass" ou NotImplemented ? (ISP)
- [ ] Les classes filles fonctionnent comme les parents ? (LSP)

## Exemples clés

### SRP - Séparer les responsabilités

```python
# ❌ Mauvais
def process_order(order):
    validate(order)
    save_to_db(order)
    send_email(order)
    update_inventory(order)

# ✅ Bon
class OrderService:
    def __init__(self, validator, repository, email_service):
        self.validator = validator
        self.repository = repository
        self.email_service = email_service
    
    def process(self, order):
        self.validator.validate(order)
        self.repository.save(order)
        self.email_service.send_confirmation(order)
```

### OCP - Stratégies extensibles

```python
# ❌ Mauvais
def calculate_discount(amount, type):
    if type == "vip":
        return amount * 0.8
    elif type == "member":
        return amount * 0.9

# ✅ Bon
class DiscountStrategy(ABC):
    @abstractmethod
    def calculate(self, amount): pass

class VIPDiscount(DiscountStrategy):
    def calculate(self, amount):
        return amount * 0.8

class DiscountCalculator:
    def __init__(self):
        self.strategies = []
    
    def register(self, strategy):
        self.strategies.append(strategy)
```

### LSP - Substitution propre

```python
# ❌ Mauvais
class Rectangle:
    def set_width(self, w): self.width = w
    def set_height(self, h): self.height = h

class Square(Rectangle):  # Problème !
    def set_width(self, w):
        self.width = w
        self.height = w  # Effet de bord !

# ✅ Bon
class Shape(ABC):
    @abstractmethod
    def area(self): pass

class Rectangle(Shape):
    def __init__(self, w, h):
        self.width = w
        self.height = h

class Square(Shape):
    def __init__(self, side):
        self.side = side
```

### ISP - Interfaces petites

```python
# ❌ Mauvais
class Worker:
    def work(self): pass
    def eat(self): pass    # Robot doit implémenter ?!
    def sleep(self): pass  # Robot doit implémenter ?!

# ✅ Bon
class Workable(Protocol):
    def work(self): ...

class Eatable(Protocol):
    def eat(self): ...

class Human(Workable, Eatable):
    def work(self): ...
    def eat(self): ...

class Robot(Workable):
    def work(self): ...
```

### DIP - Injection de dépendances

```python
# ❌ Mauvais
class UserService:
    def __init__(self):
        self.db = MySQLDatabase()  # Couplage fort !

# ✅ Bon
class UserRepository(Protocol):
    def get(self, id): ...

class UserService:
    def __init__(self, repository: UserRepository):
        self.repo = repository  # Injection

# Utilisation
service = UserService(MySQLRepository())
service = UserService(PostgresRepository())  # Facilement interchangeable
service = UserService(MockRepository())      # Facile à tester
```

## Anti-patterns SOLID

```python
# ❌ God Object (violation SRP)
class Manager:
    def do_everything(self): pass

# ❌ Modification constante (violation OCP)
def process(item_type):
    if item_type == "A": ...
    elif item_type == "B": ...
    elif item_type == "C": ...  # Toujours modifié !

# ❌ Héritage abusif (violation LSP)
class Child(Parent):
    def method(self):
        raise NotImplementedError()  # Casse le contrat !

# ❌ Interface obese (violation ISP)
class BigInterface:
    def method1(self): pass  # Utilisé par Client A
    def method2(self): pass  # Utilisé par Client B
    def method3(self): pass  # Utilisé par Client C

# ❌ Dépendance concrète (violation DIP)
class Service:
    def __init__(self):
        self.db = ConcreteDatabase()  # Impossible à remplacer
```

## Questions à se poser

**SRP** : "Si je change X, est-ce que cette classe doit aussi changer ?"

**OCP** : "Si j'ajoute un nouveau type, dois-je modifier cette classe ?"

**LSP** : "Ma classe fille respecte-t-elle le contrat de la classe parent ?"

**ISP** : "Toutes les méthodes de cette interface sont-elles utilisées ?"

**DIP** : "Puis-je tester cette classe sans base de données/réseau ?"

## Ressources rapides

- [SOLID Principles - Real Python](https://realpython.com/solid-principles-python/)
- [Clean Architecture - Uncle Bob](https://www.amazon.com/Clean-Architecture-Craftsmans-Software-Structure/dp/0134494164)
- [Refactoring Guru](https://refactoring.guru/design-patterns)
