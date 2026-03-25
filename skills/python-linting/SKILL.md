# Skill : Gestion des Erreurs de Linting Python

## Objectif

Ce skill permet de maintenir une qualité de code Python optimale en utilisant les meilleurs outils de linting et de formatage. Il couvre l'installation, la configuration et l'utilisation efficace de PEP8, pylint, flake8, black, mypy et ruff.

## Quand utiliser ce skill

- Lors de la création d'un nouveau projet Python
- Avant de committer du code
- Lors de la revue de code
- Pour configurer l'intégration continue (CI/CD)
- Quand du code legacy doit être modernisé

## Outils couverts

### 1. PEP8 (Style Guide)
**Rôle** : Guide de style officiel Python
**Utilisation** : Référence théorique pour écrire du code Python idiomatique

### 2. Black (Formateur de code)
**Rôle** : Formateur de code opinioné et automatique
**Avantages** :
- Zero configuration
- Sortie déterministe (même résultat partout)
- Gère automatiquement la longueur des lignes

### 3. isort (Tri des imports)
**Rôle** : Trie et organise les imports automatiquement
**Avantages** :
- Sépare les imports stdlib, tiers et locaux
- Compatible avec Black

### 4. Flake8 (Linter)
**Rôle** : Vérifie le style et détecte les erreurs logiques
**Vérifie** :
- Conformité PEP8 (via pycodestyle)
- Erreurs logiques (via pyflakes)
- Complexité cyclomatique (via mccabe)

### 5. Pylint (Analyseur statique avancé)
**Rôle** : Analyse statique complète du code
**Détecte** :
- Erreurs de programmation
- Code mort
- Duplications
- Problèmes d'architecture
- Conventions de nommage

### 6. MyPy (Vérification de types)
**Rôle** : Vérification statique des type hints
**Avantages** :
- Détecte les erreurs de type avant l'exécution
- Améliore la documentation du code
- Facilite la refactorisation

### 7. Ruff (Linter ultra-rapide)
**Rôle** : Remplace flake8, pylint et isort en Rust
**Avantages** :
- 10-100x plus rapide que les alternatives
- Compatible avec les règles de flake8
- Supporte le formatage (comme Black)

## Installation

```bash
# Installation de base
pip install black isort flake8 pylint mypy ruff

# Ou avec un gestionnaire de dépendances
pip install -r requirements-dev.txt
```

**requirements-dev.txt** :
```
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
pylint>=2.17.0
mypy>=1.0.0
ruff>=0.1.0
```

## Configuration recommandée

### Fichier pyproject.toml (recommandé)

```toml
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["mon_projet"]

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
exclude = [".git", "__pycache__", "build", "dist", ".venv"]

[tool.pylint.messages_control]
disable = [
    "C0103",  # invalid-name
    "C0114",  # missing-module-docstring
    "C0115",  # missing-class-docstring
    "C0116",  # missing-function-docstring
    "R0903",  # too-few-public-methods
    "R0913",  # too-many-arguments
]

[tool.pylint.format]
max-line-length = 88

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = false
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
show_error_codes = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.ruff]
target-version = "py38"
line-length = 88
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "W",   # pycodestyle warnings
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]
ignore = ["E501", "W503"]

[tool.ruff.pydocstyle]
convention = "google"

[tool.ruff.per-file-ignores]
"tests/*" = ["S101"]
"__init__.py" = ["F401"]
```

### Alternative : setup.cfg

Si pyproject.toml n'est pas supporté :

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist,.venv

[pylint.messages_control]
disable=C0103,C0114,C0115,C0116,R0903,R0913

[pylint.format]
max-line-length=88

[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

## Workflow recommandé

### Ordre d'exécution

1. **Formatage** (modifie le code)
   ```bash
   # Option A : Black + isort
   black .
   isort .
   
   # Option B : Ruff (format + lint)
   ruff format .
   ```

2. **Linting** (vérifie sans modifier)
   ```bash
   # Option A : Outils traditionnels
   flake8 .
   pylint src/
   mypy src/
   
   # Option B : Ruff uniquement
   ruff check .
   ```

3. **Vérification finale**
   ```bash
   # Script de vérification complet
   python -m black --check .
   python -m isort --check-only .
   python -m flake8 .
   python -m pylint src/
   python -m mypy src/
   ```

### Script d'automatisation

**lint.sh** (Linux/Mac) :
```bash
#!/bin/bash
set -e

echo "=== Formatage avec Black ==="
black .

echo "=== Organisation des imports ==="
isort .

echo "=== Vérification avec Flake8 ==="
flake8 .

echo "=== Analyse avec Pylint ==="
pylint src/

echo "=== Vérification des types ==="
mypy src/

echo "=== Linting avec Ruff ==="
ruff check .

echo "=== Toutes les vérifications sont passées ! ==="
```

**lint.ps1** (Windows) :
```powershell
Write-Host "=== Formatage avec Black ===" -ForegroundColor Green
black .

Write-Host "=== Organisation des imports ===" -ForegroundColor Green
isort .

Write-Host "=== Vérification avec Flake8 ===" -ForegroundColor Green
flake8 .

Write-Host "=== Analyse avec Pylint ===" -ForegroundColor Green
pylint src/

Write-Host "=== Vérification des types ===" -ForegroundColor Green
mypy src/

Write-Host "=== Linting avec Ruff ===" -ForegroundColor Green
ruff check .

Write-Host "=== Toutes les vérifications sont passées ! ===" -ForegroundColor Green
```

## Cas d'usage

### Cas 1 : Nouveau projet

```bash
# 1. Créer la structure
mkdir mon_projet && cd mon_projet

# 2. Initialiser le projet
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# 3. Créer le fichier de configuration
cat > pyproject.toml << 'EOF'
[tool.black]
line-length = 88

[tool.isort]
profile = "black"

[tool.mypy]
python_version = "3.8"
disallow_untyped_defs = true
EOF

# 4. Installer les dépendances
pip install black isort flake8 pylint mypy

# 5. Créer un pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
black --check .
flake8 .
EOF
chmod +x .git/hooks/pre-commit
```

### Cas 2 : Code legacy à moderniser

```bash
# 1. Sauvegarder le code original
cp -r src/ src_backup/

# 2. Formater automatiquement
black src/
isort src/

# 3. Ajouter progressivement les type hints
# Commencer par les fonctions les plus utilisées

# 4. Vérifier avec mypy
mypy src/ --ignore-missing-imports

# 5. Corriger les erreurs pylint les plus critiques
pylint src/ --errors-only
```

### Cas 3 : Intégration CI/CD (GitHub Actions)

```yaml
# .github/workflows/lint.yml
name: Lint

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install black isort flake8 pylint mypy ruff
    
    - name: Check formatting with Black
      run: black --check .
    
    - name: Check imports with isort
      run: isort --check-only .
    
    - name: Lint with flake8
      run: flake8 .
    
    - name: Lint with pylint
      run: pylint src/
    
    - name: Type check with mypy
      run: mypy src/
    
    - name: Lint with ruff
      run: ruff check .
```

### Cas 4 : Utilisation de Ruff uniquement (recommandé pour la rapidité)

```bash
# Ruff remplace flake8, pylint, isort ET black

# Configuration minimale pyproject.toml
[tool.ruff]
target-version = "py38"
line-length = 88
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "SIM"]

# Commandes
ruff format .      # Formate le code (comme Black)
ruff check .       # Lint le code (comme flake8 + pylint)
ruff check --fix . # Lint + corrige automatiquement
```

## Pièges à éviter

### 1. Conflits entre outils

**Problème** : Black utilise 88 caractères, flake8 utilise 79 par défaut
**Solution** : Configurer flake8 pour accepter 88 caractères
```toml
[tool.flake8]
max-line-length = 88
```

### 2. isort et Black en conflit

**Problème** : isort peut reformater différemment de Black
**Solution** : Utiliser le profil Black dans isort
```toml
[tool.isort]
profile = "black"
```

### 3. MyPy trop strict sur un projet legacy

**Problème** : MyPy génère des milliers d'erreurs sur du code sans type hints
**Solution** : Commencer avec une configuration souple
```toml
[tool.mypy]
python_version = "3.8"
ignore_missing_imports = true
follow_imports = "skip"
# Puis progressivement activer :
# disallow_untyped_defs = true
```

### 4. Pylint trop verbeux

**Problème** : Pylint génère trop de warnings sur des cas légitimes
**Solution** : Désactiver les règles non pertinentes
```toml
[tool.pylint.messages_control]
disable = [
    "C0114",  # missing-module-docstring (trop strict)
    "R0903",  # too-few-public-methods (classes utilitaires)
]
```

### 5. Exclusions incorrectes

**Problème** : Les outils analysent les fichiers générés (migrations, build)
**Solution** : Bien configurer les exclusions
```toml
[tool.black]
extend-exclude = '''
/(
  migrations
  | node_modules
  | \.venv
)/
'''
```

### 6. Oublier de vérifier avant de committer

**Problème** : Le code non linté arrive dans le repository
**Solution** : Utiliser pre-commit
```bash
pip install pre-commit

# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
```

## Bonnes pratiques

### 1. Commencer simple
- Commencer par Black (formatage automatique)
- Ajouter progressivement les autres outils
- Ne pas tout activer d'un coup sur un projet existant

### 2. Configurer une fois, réutiliser partout
- Créer un template pyproject.toml pour tous vos projets
- Versionner la configuration avec le code

### 3. Automatiser
- Utiliser les pre-commit hooks
- Intégrer dans la CI/CD
- Configurer son IDE pour formatter à la sauvegarde

### 4. Équilibrer strictness et productivité
- Ne pas être trop strict sur les projets legacy
- Adapter la configuration à l'équipe et au projet
- Privilégier les erreurs réelles aux warnings cosmétiques

### 5. Documenter les exceptions
```python
# noqa: E501  # URL trop longue, ignorer cette ligne
# type: ignore  # MyPy ne comprend pas ce cas particulier
# pylint: disable=invalid-name  # Nom imposé par une API externe
```

## Commandes de diagnostic

### Vérifier la configuration

```bash
# Voir la configuration effective de Black
black --config pyproject.toml --verbose --diff fichier.py

# Voir les règles activées dans flake8
flake8 --verbose --show-source fichier.py

# Voir la configuration pylint
pylint --generate-rcfile > .pylintrc

# Voir la configuration mypy
mypy --show-error-codes src/

# Voir les règles ruff
ruff linter
ruff linter --select E
```

### Ignorer temporairement une règle

```python
# Ignorer une ligne spécifique
long_line = "x" * 100  # noqa: E501

# Ignorer un fichier entier pour pylint
# pylint: skip-file

# Ignorer une erreur mypy sur une ligne
result = ambiguous_function()  # type: ignore

# Ignorer avec code d'erreur spécifique
result = ambiguous_function()  # type: ignore[return-value]
```

## Migration progressive

### Phase 1 : Formatage (Semaine 1)
```bash
# Uniquement Black et isort
black .
isort .
```

### Phase 2 : Linting basique (Semaine 2-3)
```bash
# Ajouter flake8
black .
isort .
flake8 .
```

### Phase 3 : Analyse approfondie (Semaine 4)
```bash
# Ajouter pylint (configuration souple)
black .
isort .
flake8 .
pylint src/ --errors-only
```

### Phase 4 : Types (Semaine 5+)
```bash
# Ajouter mypy progressivement
black .
isort .
flake8 .
pylint src/
mypy src/ --ignore-missing-imports
```

### Phase 5 : Optimisation (Optionnel)
```bash
# Remplacer par Ruff pour la vitesse
ruff format .
ruff check --fix .
mypy src/
```

## Ressources

- [PEP8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [Pylint Documentation](https://pylint.readthedocs.io/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [isort Documentation](https://pycqa.github.io/isort/)

## Checklist avant commit

- [ ] `black .` exécuté sans erreur
- [ ] `isort .` exécuté sans erreur
- [ ] `flake8 .` passe sans erreur
- [ ] `pylint src/` passe sans erreur critique
- [ ] `mypy src/` passe sans erreur
- [ ] Aucun `print()` de debug restant
- [ ] Les `# noqa` et `# type: ignore` sont justifiés
