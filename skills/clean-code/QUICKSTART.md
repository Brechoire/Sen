# Clean Code - Démarrage Rapide

## Principes clés

### Nomenclature
- **Variables** : `snake_case`, descriptif, pas d'abréviations obscures
- **Fonctions** : verbe + nom, une seule chose, < 20 lignes
- **Classes** : `PascalCase`, nom commun, responsabilité unique

### Exemples

```python
# ❌ Mauvais
def calc(d, r):
    return d * r

# ✅ Bon
def calculate_rectangle_area(width: float, height: float) -> float:
    """Calcule l'aire d'un rectangle."""
    return width * height

# ❌ Mauvais
class DataManager:
    def process(self): pass
    def save(self): pass
    def send_email(self): pass

# ✅ Bon
class OrderProcessor:
    def process(self, order: Order) -> ProcessedOrder:
        pass

class EmailService:
    def send_confirmation(self, order: Order) -> None:
        pass
```

### Fonctions

```python
# ✅ Pattern AAA (Arrange-Act-Assert)
def test_addition():
    # Arrange
    a, b = 2, 3
    
    # Act
    result = add(a, b)
    
    # Assert
    assert result == 5

# ✅ Early returns
def process_payment(payment):
    if not payment.is_valid:
        return False
    if payment.amount <= 0:
        return False
    # ... traitement principal
    return True
```

### Commentaires

```python
# ❌ Mauvais - commentaire évident
# Increment counter
counter += 1

# ✅ Bon - explique le POURQUOI
# Nous utilisons un cache car cette opération est coûteuse
# et les données changent rarement (une fois par jour)
def get_expensive_data():
    return cache.get_or_compute('key', compute_data)
```

## SOLID en bref

1. **S**ingle Responsibility : Une classe = une responsabilité
2. **O**pen/Closed : Ouvert à l'extension, fermé à la modification
3. **L**iskov Substitution : Les classes filles substituables aux parents
4. **I**nterface Segregation : Petites interfaces spécialisées
5. **D**ependency Inversion : Dépendre d'abstractions, pas de concret

## Checklist avant commit

- [ ] Noms révélateurs de l'intention
- [ ] Fonctions courtes et focalisées
- [ ] Pas de duplication (DRY)
- [ ] Gestion d'erreurs appropriée
- [ ] Tests présents

## Anti-patterns

```python
# ❌ Magic numbers
def calculate_price(qty):
    if qty > 100:
        return qty * 0.9  # Qu'est-ce que 0.9 ?

# ✅ Constantes nommées
BULK_DISCOUNT_THRESHOLD = 100
BULK_DISCOUNT_RATE = 0.9

# ❌ Code mort
if False:
    old_function()  # Supprimer !

# ❌ Paramètres booléens
def create_user(name, is_admin=False):
    pass

# ✅ Deux fonctions claires
def create_user(name): pass
def create_admin_user(name): pass
```

## Ressources

- [Clean Code - Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Refactoring - Martin Fowler](https://www.amazon.com/Refactoring-Improving-Existing-Addison-Wesley-Signature/dp/0134757599)
