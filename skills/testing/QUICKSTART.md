# Testing - Démarrage Rapide

## Installation

```bash
pip install pytest pytest-cov pytest-django factory-boy freezegun
```

## Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*"]
```

## Commandes essentielles

```bash
# Lancer tous les tests
pytest

# Avec couverture
pytest --cov=src --cov-report=html

# Tests spécifiques
pytest tests/test_models.py
pytest tests/test_models.py::TestUser::test_creation

# Mode verbeux
pytest -v

# Arrêter au premier échec
pytest -x

# Tests marqués
pytest -m "slow"
pytest -m "not slow"
```

## Structure d'un test

```python
import pytest
from unittest.mock import Mock, patch


class TestUserService:
    """Tests du service utilisateur."""
    
    @pytest.fixture
    def repository(self):
        return Mock()
    
    def test_create_user_success(self, repository):
        """Test la création réussie d'un utilisateur."""
        # Arrange
        service = UserService(repository)
        repository.save.return_value = User(id=1, email="test@test.com")
        
        # Act
        result = service.create_user({"email": "test@test.com"})
        
        # Assert
        assert result.id == 1
        repository.save.assert_called_once()
```

## Fixtures et Factories

```python
import factory

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    id = factory.Sequence(lambda n: n)
    email = factory.LazyAttribute(lambda o: f"user{o.id}@test.com")
    name = factory.Faker("name")


# Utilisation
@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def ten_users():
    return UserFactory.create_batch(10)
```

## Mocking

```python
from unittest.mock import Mock, patch

# Mock simple
def test_with_mock():
    mock_service = Mock()
    mock_service.process.return_value = {"status": "success"}
    
    result = mock_service.process()
    assert result["status"] == "success"

# Patch
@patch("module.email_service.send")
def test_sends_email(mock_send):
    process_order()
    mock_send.assert_called_once()

# Patch avec context manager
def test_with_context_manager():
    with patch("module.get_data") as mock_get:
        mock_get.return_value = [1, 2, 3]
        result = process_data()
        assert len(result) == 3
```

## Paramétrage

```python
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_addition(a, b, expected):
    assert add(a, b) == expected
```

## Marqueurs

```python
@pytest.mark.slow  # Test lent
@pytest.mark.integration  # Test d'intégration
@pytest.mark.django_db  # Test avec base de données Django

def test_slow_operation():
    pass
```

## Checklist

- [ ] Nom descriptif : `test_<unit>_<scenario>_<expected>`
- [ ] Pattern AAA (Arrange-Act-Assert)
- [ ] Un seul concept par test
- [ ] Pas de logique conditionnelle
- [ ] Tests indépendants
- [ ] Couverture > 80%

## Anti-patterns

```python
# ❌ Test qui dépend d'autres tests
# ❌ Test qui touche la base de production
# ❌ Test non déterministe (aléatoire)
# ❌ Test trop lent (> 1 seconde pour unit test)
```

## Ressources

- [pytest Documentation](https://docs.pytest.org/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
