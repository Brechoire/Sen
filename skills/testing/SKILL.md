# Skill : Tests Fonctionnels et Unitaires

## Objectif

Ce skill présente les bonnes pratiques pour écrire des tests unitaires et fonctionnels efficaces, maintenables et rapides. Couvre pytest, unittest, et les tests d'intégration.

## Quand utiliser ce skill

- Écriture de nouveaux tests
- Refactoring de tests legacy
- Configuration de CI/CD
- Revue de code
- Amélioration de la couverture de tests

## Types de tests

### Pyramide des tests

```
        /\
       /  \     E2E Tests (peu nombreux, lents)
      /----\
     /      \   Integration Tests (moyen)
    /--------\ 
   /          \ Unit Tests (nombreux, rapides)
  /____________\
```

- **Unit Tests** : Testent une unité isolée (fonction, classe)
- **Integration Tests** : Testent l'interaction entre composants
- **E2E Tests** : Testent l'application complète (end-to-end)

## Configuration

### Installation

```bash
pip install pytest pytest-cov pytest-django pytest-asyncio
pip install factory-boy freezegun responses
pip install coverage
```

### Configuration pytest (pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--disable-warnings"
]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "e2e: marks tests as end-to-end tests",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/venv/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
fail_under = 80
```

## Tests Unitaires

### Principes FIRST

```python
# Tests doivent être :
# F - Fast (rapides)
# I - Independent (indépendants)
# R - Repeatable (reproductibles)
# S - Self-validating (auto-validants)
# T - Timely (écrits au bon moment)

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestUserService:
    """Tests unitaires du service utilisateur."""
    
    @pytest.fixture
    def user_repository(self):
        """Fixture pour le repository mocké."""
        return Mock()
    
    @pytest.fixture
    def email_service(self):
        """Fixture pour le service email mocké."""
        return Mock()
    
    @pytest.fixture
    def user_service(self, user_repository, email_service):
        """Fixture pour le service à tester."""
        return UserService(user_repository, email_service)
    
    def test_create_user_success(self, user_service, user_repository, email_service):
        """Test la création réussie d'un utilisateur."""
        # Arrange (Given)
        user_data = {"email": "test@example.com", "name": "John"}
        user_repository.save.return_value = User(id=1, **user_data)
        
        # Act (When)
        result = user_service.create_user(user_data)
        
        # Assert (Then)
        assert result.id == 1
        assert result.email == "test@example.com"
        user_repository.save.assert_called_once()
        email_service.send_welcome_email.assert_called_once_with("test@example.com")
    
    def test_create_user_invalid_email(self, user_service):
        """Test la création avec un email invalide."""
        # Arrange
        user_data = {"email": "invalid-email", "name": "John"}
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email format"):
            user_service.create_user(user_data)
    
    def test_get_user_not_found(self, user_service, user_repository):
        """Test la récupération d'un utilisateur inexistant."""
        # Arrange
        user_repository.find_by_id.return_value = None
        
        # Act
        result = user_service.get_user(999)
        
        # Assert
        assert result is None
```

### Pattern AAA (Arrange-Act-Assert)

```python
def test_calculate_total():
    """Test le calcul du total avec réduction."""
    # Arrange
    items = [
        Item(price=10.0, quantity=2),
        Item(price=5.0, quantity=3)
    ]
    calculator = OrderCalculator(discount_rate=0.1)
    
    # Act
    total = calculator.calculate_total(items)
    
    # Assert
    expected = (20.0 + 15.0) * 0.9  # 35.0 * 0.9 = 31.5
    assert total == pytest.approx(31.5)


# Alternative avec parametrize pour plusieurs cas
import pytest

@pytest.mark.parametrize("items,discount,expected", [
    ([Item(10, 1)], 0.0, 10.0),
    ([Item(10, 2)], 0.1, 18.0),
    ([Item(10, 1), Item(5, 2)], 0.2, 16.0),
    ([], 0.0, 0.0),
])
def test_calculate_total_parametrized(items, discount, expected):
    """Test le calcul du total avec différents cas."""
    calculator = OrderCalculator(discount_rate=discount)
    
    total = calculator.calculate_total(items)
    
    assert total == pytest.approx(expected)
```

### Mocking

```python
from unittest.mock import Mock, patch, MagicMock, call
import pytest


class TestPaymentService:
    """Tests avec mocking."""
    
    def test_process_payment_calls_gateway(self):
        """Test que le service appelle la gateway de paiement."""
        # Mock manuel
        mock_gateway = Mock()
        mock_gateway.charge.return_value = {"status": "success", "id": "txn_123"}
        
        service = PaymentService(gateway=mock_gateway)
        service.process_payment(amount=100.0, card_token="tok_visa")
        
        # Vérifier l'appel
        mock_gateway.charge.assert_called_once_with(
            amount=100.0,
            currency="EUR",
            source="tok_visa"
        )
    
    @patch("services.email.EmailService.send")
    def test_payment_sends_confirmation_email(self, mock_send):
        """Test l'envoi d'email de confirmation."""
        service = PaymentService()
        service.process_payment(amount=50.0, card_token="tok_visa")
        
        mock_send.assert_called_once()
        args = mock_send.call_args
        assert "Payment confirmed" in args[1]["subject"]
    
    @patch.object(Logger, "info")
    def test_payment_logs_transaction(self, mock_log):
        """Test le logging des transactions."""
        service = PaymentService()
        service.process_payment(amount=100.0, card_token="tok_visa")
        
        mock_log.assert_any_call("Processing payment: 100.0 EUR")
    
    def test_multiple_calls(self):
        """Test plusieurs appels avec assertions sur l'ordre."""
        mock_service = Mock()
        
        mock_service.step1()
        mock_service.step2()
        mock_service.step1()
        
        # Vérifier l'ordre exact
        expected_calls = [call.step1(), call.step2(), call.step1()]
        mock_service.assert_has_calls(expected_calls)
        
        # Vérifier le nombre d'appels
        assert mock_service.step1.call_count == 2


# Mocking avec context manager
class TestFileOperations:
    """Tests avec patching de fonctions built-in."""
    
    @patch("builtins.open")
    def test_read_config_file(self, mock_open):
        """Test la lecture d'un fichier de configuration."""
        mock_file = MagicMock()
        mock_file.read.return_value = '{"key": "value"}'
        mock_open.return_value.__enter__.return_value = mock_file
        
        config = read_config("config.json")
        
        assert config == {"key": "value"}
        mock_open.assert_called_once_with("config.json", "r")
    
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_file_validation(self, mock_getsize, mock_exists):
        """Test la validation de fichier avec plusieurs mocks."""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        
        validator = FileValidator(max_size=2048)
        is_valid = validator.validate("file.txt")
        
        assert is_valid is True
```

## Tests Fonctionnels (Intégration)

### Tests de base de données

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def engine():
    """Fixture pour le moteur de base de données."""
    return create_engine("postgresql://user:pass@localhost/test_db")


@pytest.fixture(scope="function")
def db_session(engine):
    """Fixture pour la session de base de données."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.mark.integration
class TestUserRepository:
    """Tests d'intégration du repository utilisateur."""
    
    def test_save_user(self, db_session):
        """Test la sauvegarde d'un utilisateur en base."""
        # Arrange
        repo = UserRepository(db_session)
        user = User(email="test@example.com", name="John")
        
        # Act
        saved_user = repo.save(user)
        db_session.commit()
        
        # Assert
        assert saved_user.id is not None
        
        # Vérifier en base
        retrieved = repo.find_by_id(saved_user.id)
        assert retrieved.email == "test@example.com"
    
    def test_find_users_by_status(self, db_session):
        """Test la recherche d'utilisateurs par statut."""
        # Arrange
        repo = UserRepository(db_session)
        repo.save(User(email="active1@test.com", status="active"))
        repo.save(User(email="active2@test.com", status="active"))
        repo.save(User(email="inactive@test.com", status="inactive"))
        db_session.commit()
        
        # Act
        active_users = repo.find_by_status("active")
        
        # Assert
        assert len(active_users) == 2
        assert all(u.status == "active" for u in active_users)
```

### Tests d'API

```python
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Fixture pour le client de test."""
    return TestClient(app)


@pytest.mark.integration
class TestUsersAPI:
    """Tests d'intégration de l'API utilisateurs."""
    
    def test_create_user(self, client):
        """Test la création d'un utilisateur via l'API."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "name": "John Doe",
            "password": "securepassword123"
        }
        
        # Act
        response = client.post("/api/users", json=user_data)
        
        # Assert
        assert response.status_code == 201
        assert response.json()["email"] == "test@example.com"
        assert "password" not in response.json()  # Ne pas retourner le mot de passe
    
    def test_create_user_duplicate_email(self, client):
        """Test la création avec un email déjà utilisé."""
        # Arrange
        user_data = {"email": "duplicate@test.com", "name": "John"}
        client.post("/api/users", json=user_data)
        
        # Act
        response = client.post("/api/users", json=user_data)
        
        # Assert
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_get_user_not_found(self, client):
        """Test la récupération d'un utilisateur inexistant."""
        response = client.get("/api/users/99999")
        
        assert response.status_code == 404
    
    def test_update_user(self, client):
        """Test la mise à jour d'un utilisateur."""
        # Create user first
        user_data = {"email": "update@test.com", "name": "Original"}
        create_response = client.post("/api/users", json=user_data)
        user_id = create_response.json()["id"]
        
        # Update
        update_data = {"name": "Updated Name"}
        response = client.patch(f"/api/users/{user_id}", json=update_data)
        
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
        assert response.json()["email"] == "update@test.com"  # Non modifié
```

### Tests Django

```python
import pytest
from django.urls import reverse
from django.test import Client


@pytest.mark.django_db
class TestUserViews:
    """Tests des vues Django."""
    
    @pytest.fixture
    def client(self):
        return Client()
    
    def test_user_list_view(self, client):
        """Test la liste des utilisateurs."""
        # Arrange
        User.objects.create(username="user1", email="user1@test.com")
        User.objects.create(username="user2", email="user2@test.com")
        
        # Act
        response = client.get(reverse("user-list"))
        
        # Assert
        assert response.status_code == 200
        assert len(response.context["users"]) == 2
    
    def test_user_detail_view(self, client):
        """Test le détail d'un utilisateur."""
        user = User.objects.create(username="testuser", email="test@test.com")
        
        response = client.get(reverse("user-detail", kwargs={"pk": user.pk}))
        
        assert response.status_code == 200
        assert response.context["user"].username == "testuser"
    
    def test_create_user_view(self, client):
        """Test la création d'utilisateur via formulaire."""
        data = {
            "username": "newuser",
            "email": "new@test.com",
            "password1": "testpass123",
            "password2": "testpass123"
        }
        
        response = client.post(reverse("user-create"), data)
        
        assert response.status_code == 302  # Redirect after success
        assert User.objects.filter(username="newuser").exists()
```

## Tests E2E (End-to-End)

```python
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestUserJourney:
    """Tests end-to-end avec Playwright."""
    
    def test_complete_signup_flow(self, page: Page):
        """Test le flux complet d'inscription."""
        # Navigate to signup page
        page.goto("http://localhost:8000/signup")
        
        # Fill form
        page.fill("[name='email']", "newuser@example.com")
        page.fill("[name='password']", "SecurePass123!")
        page.fill("[name='confirm_password']", "SecurePass123!")
        
        # Submit
        page.click("button[type='submit']")
        
        # Verify redirect to dashboard
        expect(page).to_have_url("http://localhost:8000/dashboard")
        expect(page.locator("h1")).to_contain_text("Welcome")
        
        # Verify welcome email sent (check logs or mock service)
    
    def test_login_and_purchase(self, page: Page):
        """Test le flux de connexion et d'achat."""
        # Login
        page.goto("http://localhost:8000/login")
        page.fill("[name='email']", "user@example.com")
        page.fill("[name='password']", "password")
        page.click("button[type='submit']")
        
        # Navigate to product
        page.goto("http://localhost:8000/products/1")
        
        # Add to cart
        page.click("button:has-text('Add to Cart')")
        
        # Go to checkout
        page.click("a:has-text('Checkout')")
        
        # Fill payment info
        page.fill("[name='card_number']", "4242424242424242")
        page.fill("[name='expiry']", "12/25")
        page.fill("[name='cvc']", "123")
        
        # Complete purchase
        page.click("button:has-text('Pay')")
        
        # Verify success
        expect(page.locator(".success-message")).to_be_visible()
```

## Fixtures et Factories

```python
import pytest
import factory
from factory import Faker
from datetime import datetime, timedelta


# Factory Boy pour créer des objets de test
class UserFactory(factory.Factory):
    """Factory pour créer des utilisateurs de test."""
    class Meta:
        model = User
    
    id = factory.Sequence(lambda n: n)
    email = factory.LazyAttribute(lambda obj: f"user{obj.id}@example.com")
    name = Faker("name")
    created_at = factory.LazyFunction(datetime.now)
    is_active = True


class OrderFactory(factory.Factory):
    """Factory pour créer des commandes de test."""
    class Meta:
        model = Order
    
    id = factory.Sequence(lambda n: n)
    user = factory.SubFactory(UserFactory)
    total = factory.LazyAttribute(lambda o: sum(item.price for item in o.items))
    status = "pending"
    created_at = factory.LazyFunction(datetime.now)
    
    @factory.post_generation
    def items(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            for item in extracted:
                self.items.add(item)
        else:
            # Create default items
            OrderItemFactory.create_batch(2, order=self)


# Fixtures pytest
@pytest.fixture
def user():
    """Fixture pour un utilisateur de base."""
    return UserFactory()


@pytest.fixture
def active_user():
    """Fixture pour un utilisateur actif."""
    return UserFactory(is_active=True)


@pytest.fixture
def inactive_user():
    """Fixture pour un utilisateur inactif."""
    return UserFactory(is_active=False)


@pytest.fixture
def order(user):
    """Fixture pour une commande avec utilisateur."""
    return OrderFactory(user=user)


@pytest.fixture
def ten_orders(user):
    """Fixture pour 10 commandes."""
    return OrderFactory.create_batch(10, user=user)


# Fixture avec paramétrage
@pytest.fixture(params=["pending", "paid", "shipped", "delivered"])
def order_status(request):
    """Fixture paramétrée pour les statuts de commande."""
    return request.param


# Utilisation des fixtures
class TestOrderProcessing:
    """Tests utilisant les fixtures."""
    
    def test_can_cancel_pending_order(self, user):
        """Test qu'une commande en attente peut être annulée."""
        order = OrderFactory(user=user, status="pending")
        
        result = order.cancel()
        
        assert result is True
        assert order.status == "cancelled"
    
    def test_cannot_cancel_delivered_order(self, user):
        """Test qu'une commande livrée ne peut pas être annulée."""
        order = OrderFactory(user=user, status="delivered")
        
        with pytest.raises(ValueError, match="Cannot cancel delivered order"):
            order.cancel()
    
    def test_process_order_sends_notification(self, ten_orders, mocker):
        """Test le traitement de plusieurs commandes."""
        mock_notification = mocker.patch("services.notification.send")
        
        for order in ten_orders:
            order.process()
        
        assert mock_notification.call_count == 10
```

## Bonnes pratiques

### Organisation des tests

```
tests/
├── conftest.py              # Configuration et fixtures globales
├── unit/                    # Tests unitaires
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/             # Tests d'intégration
│   ├── test_repositories.py
│   ├── test_api.py
│   └── test_database.py
├── e2e/                     # Tests end-to-end
│   ├── test_user_journey.py
│   └── test_checkout_flow.py
└── fixtures/                # Données de test
    ├── users.json
    └── products.json
```

### Nommage des tests

```python
# ❌ Mauvais
class TestUser:
    def test1(self): pass
    def test_user(self): pass

# ✅ Bon - nom descriptif : test_<unit>_<scenario>_<expected_result>
class TestUserService:
    def test_create_user_with_valid_data_returns_user(self):
        """Création avec données valides retourne l'utilisateur."""
        pass
    
    def test_create_user_with_duplicate_email_raises_error(self):
        """Création avec email dupliqué lève une erreur."""
        pass
    
    def test_get_user_by_id_returns_none_when_not_found(self):
        """Récupération par ID retourne None si non trouvé."""
        pass
    
    def test_update_user_status_to_inactive_sends_notification(self):
        """Mise à jour du statut envoie une notification."""
        pass
```

### Tests paramétrés

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("World", "WORLD"),
    ("", ""),
    ("123", "123"),
])
def test_to_uppercase(input, expected):
    """Test la conversion en majuscules."""
    assert input.upper() == expected


@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_addition(a, b, expected):
    """Test l'addition."""
    assert add(a, b) == expected


# Paramétrage avec ids descriptifs
@pytest.mark.parametrize(
    "status,can_cancel",
    [
        pytest.param("pending", True, id="pending_can_cancel"),
        pytest.param("paid", False, id="paid_cannot_cancel"),
        pytest.param("shipped", False, id="shipped_cannot_cancel"),
        pytest.param("delivered", False, id="delivered_cannot_cancel"),
    ]
)
def test_order_cancellation(status, can_cancel):
    """Test les règles d'annulation de commande."""
    order = Order(status=status)
    assert order.can_cancel() is can_cancel
```

### Gestion du temps

```python
from freezegun import freeze_time
from datetime import datetime


class TestTimeDependent:
    """Tests dépendant du temps."""
    
    @freeze_time("2024-01-15 12:00:00")
    def test_token_expiration(self):
        """Test l'expiration d'un token."""
        token = generate_token()
        
        # Avancer le temps de 25 heures
        with freeze_time("2024-01-16 13:00:00"):
            assert is_token_valid(token) is False
    
    def test_daily_report_generation(self):
        """Test la génération du rapport quotidien."""
        with freeze_time("2024-01-15 23:59:59"):
            # Juste avant minuit - pas de rapport
            assert get_daily_report() is None
        
        with freeze_time("2024-01-16 00:00:01"):
            # Après minuit - rapport généré
            report = get_daily_report()
            assert report is not None
            assert report.date == date(2024, 1, 15)
```

## Couverture de tests

```bash
# Lancer les tests avec couverture
pytest --cov=src --cov-report=term-missing

# Générer un rapport HTML
coverage html

# Voir les lignes non couvertes
coverage report --show-missing

# Vérifier un minimum de couverture
pytest --cov=src --cov-fail-under=80
```

## Checklist tests

### Structure
- [ ] Tests organisés par type (unit/integration/e2e)
- [ ] Fixtures réutilisables
- [ ] Factories pour la génération de données
- [ ] Configuration séparée pour chaque environnement

### Qualité
- [ ] Nom descriptif pour chaque test
- [ ] Pattern AAA (Arrange-Act-Assert)
- [ ] Un seul concept testé par test
- [ ] Pas de logique conditionnelle dans les tests
- [ ] Tests indépendants (pas d'ordre de dépendance)

### Couverture
- [ ] Tests pour les cas nominaux
- [ ] Tests pour les cas limites
- [ ] Tests pour les erreurs
- [ ] Couverture > 80% pour le code métier
- [ ] Tests d'intégration pour les points critiques

### Performance
- [ ] Tests unitaires rapides (< 10ms)
- [ ] Mock des dépendances externes
- [ ] Base de données en mémoire ou rollback
- [ ] Parallélisation des tests

## Ressources

- [pytest Documentation](https://docs.pytest.org/)
- [Python Testing 101](https://realpython.com/python-testing/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
- [Playwright](https://playwright.dev/python/)
- [Test Driven Development - Kent Beck](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)
