# CI/CD Pipeline - Démarrage Rapide

## Installation (10 minutes)

```bash
# 1. Créer le dossier workflows
mkdir -p .github/workflows

# 2. Workflow CI (tests et lint)
cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Cache pip
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
      
      - name: Install deps
        run: |
          pip install black flake8 isort mypy
          pip install -r requirements.txt
      
      - name: Black
        run: black --check --diff .
      
      - name: Flake8
        run: flake8 . --count --show-source --statistics
      
      - name: MyPy
        run: mypy . --ignore-missing-imports

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    env:
      DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
      SECRET_KEY: test-secret-key
      DEBUG: False
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Cache pip
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
      
      - name: Install deps
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-django pytest-cov
      
      - name: Tests
        run: pytest --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
EOF

# 3. Workflow Docker
cat > .github/workflows/docker.yml << 'EOF'
name: Docker Build

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: docker/setup-buildx-action@v3
      
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
      
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
EOF
```

## Configuration GitHub

### Secrets à configurer

```
Settings → Secrets and variables → Actions

# Application
SECRET_KEY: votre-secret-key
DATABASE_URL: postgres://...

# Déploiement (optionnel)
SSH_KEY: -----BEGIN OPENSSH PRIVATE KEY-----
HOST: votre-serveur.com
USER: deploy

# Notifications (optionnel)
SLACK_WEBHOOK_URL: https://hooks.slack.com/...
```

### Protection des branches

```
Settings → Branches → Add rule

Branch name pattern: main
✅ Require a pull request before merging
✅ Require status checks to pass
   - Status checks: ci/lint, ci/test
✅ Include administrators
```

## Commandes GitHub CLI

```bash
# Vérifier le statut des workflows
gh run list

# Voir les logs d'un run
gh run view RUN_ID --log

# Relancer un workflow échoué
gh run rerun RUN_ID

# Voir les secrets configurés
gh secret list

# Ajouter un secret
gh secret set NOM_SECRET --body "valeur"

# Ajouter un secret depuis un fichier
gh secret set SSH_KEY < ~/.ssh/id_rsa
```

## Tests en local

```bash
# Simuler GitHub Actions localement
# Installer act: https://github.com/nektos/act

act                               # Run default workflow
act -j test                       # Run specific job
act -P ubuntu-latest=nektos/act-environments-ubuntu:18.04  # Full env

# Alternative: pre-commit hooks
pre-commit install
pre-commit run --all-files
```

## Checklist rapide

### Setup
- [ ] Dossier `.github/workflows/` créé
- [ ] Workflow CI (tests + lint)
- [ ] Workflow Docker (build + push)
- [ ] Protection branches configurée
- [ ] Secrets ajoutés dans GitHub

### Qualité
- [ ] Tests passent sur PR
- [ ] Lint valide le code
- [ ] Coverage > 80%
- [ ] Security scan activé

### Déploiement (optionnel)
- [ ] Environnement staging configuré
- [ ] Environnement production configuré
- [ ] Reviewers pour production
- [ ] Health checks post-déploiement

## Workflows prêts à l'emploi

### Test minimal
```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt pytest
      - run: pytest
```

### Lint + Test + Coverage
```yaml
name: CI
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install black flake8
      - run: black --check .
      - run: flake8 .
  
  test:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest --cov=. --cov-report=term-missing
```

## Troubleshooting

```bash
# Workflow ne se déclenche pas
# → Vérifier la syntaxe YAML
# → Vérifier les branches dans 'on:'

# Tests échouent uniquement sur CI
# → Vérifier variables d'environnement
# → Vérifier services (DB, Redis)

# Cache ne fonctionne pas
# → Vérifier les chemins dans cache@v3
# → Vérifier hashFiles patterns

# Docker push échoue
# → Vérifier permissions packages: write
# → Vérifier secrets.GITHUB_TOKEN
```
