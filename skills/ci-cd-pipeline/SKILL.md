# Skill : CI/CD Pipeline

## Objectif

Automatiser les tests, la vérification de qualité et le déploiement à chaque modification du code.

## Quand utiliser ce skill

- Mise en place d'un nouveau projet
- Configuration des workflows GitHub Actions
- Automatisation des tests
- Déploiement continu
- Amélioration de la qualité du code

## Architecture CI/CD

```
Push/PR
    │
    ▼
┌─────────────┐
│    Lint     │ ← Black, Flake8, MyPy
│   & Test    │
└──────┬──────┘
       │
       ├─ ❌ Échec → Arrêt
       │
       ▼
┌─────────────┐
│   Security  │ ← Bandit, Safety
│    Scan     │
└──────┬──────┘
       │
       ├─ ❌ Échec → Arrêt
       │
       ▼
┌─────────────┐
│    Build    │ ← Docker image
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Deploy    │ ← Staging / Production
└─────────────┘
```

## GitHub Actions - Workflows complets

### 1. Tests et Qualité

```yaml
# .github/workflows/ci.yml
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
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Cache pip packages
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install black flake8 isort mypy
          pip install -r requirements.txt
      
      - name: Check Black formatting
        run: black --check --diff .
      
      - name: Check import sorting
        run: isort --check-only --diff .
      
      - name: Lint with Flake8
        run: flake8 . --count --show-source --statistics
      
      - name: Type check with MyPy
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
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    env:
      DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
      REDIS_URL: redis://localhost:6379/0
      SECRET_KEY: test-secret-key-not-for-production
      DEBUG: False
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Cache pip packages
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-django pytest-cov
      
      - name: Run migrations
        run: python manage.py migrate
      
      - name: Run tests with coverage
        run: pytest --cov=. --cov-report=xml --cov-report=term
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

  security:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install bandit safety
          pip install -r requirements.txt
      
      - name: Run Bandit security scan
        run: bandit -r . -f json -o bandit-report.json || true
      
      - name: Check dependencies vulnerabilities
        run: safety check
      
      - name: Upload Bandit report
        uses: actions/upload-artifact@v3
        with:
          name: bandit-report
          path: bandit-report.json
```

### 2. Build et Push Docker

```yaml
# .github/workflows/docker.yml
name: Docker Build and Push

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

### 3. Déploiement Staging

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging

on:
  push:
    branches: [develop]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Staging
        run: |
          echo "Déploiement sur le serveur de staging..."
          # Exemple avec SSH
          # ssh ${{ secrets.STAGING_SSH_USER }}@${{ secrets.STAGING_HOST }} '
          #   cd /app && 
          #   git pull origin develop && 
          #   docker-compose -f docker-compose.prod.yml pull && 
          #   docker-compose -f docker-compose.prod.yml up -d
          # '
      
      - name: Run smoke tests
        run: |
          sleep 10
          curl -f https://staging.example.com/health/ || exit 1
      
      - name: Notify Slack
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#deployments'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### 4. Déploiement Production

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy'
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.inputs.version || github.ref }}
      
      - name: Deploy to Production
        run: |
          echo "Déploiement en production..."
          # ssh ${{ secrets.PROD_SSH_USER }}@${{ secrets.PROD_HOST }} '
          #   cd /app && 
          #   git fetch --tags && 
          #   git checkout ${{ github.event.inputs.version || github.ref_name }} && 
          #   docker-compose -f docker-compose.prod.yml pull && 
          #   docker-compose -f docker-compose.prod.yml up -d && 
          #   docker system prune -f
          # '
      
      - name: Run health checks
        run: |
          sleep 15
          curl -f https://example.com/health/ || exit 1
      
      - name: Create Sentry release
        uses: getsentry/action-release@v1
        env:
          SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
          SENTRY_ORG: ${{ secrets.SENTRY_ORG }}
          SENTRY_PROJECT: ${{ secrets.SENTRY_PROJECT }}
        with:
          environment: production
          version: ${{ github.event.inputs.version || github.ref_name }}
      
      - name: Notify Slack
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#deployments'
          fields: repo,message,commit,author,action,eventName,ref,workflow
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## Configuration des environnements GitHub

### Secrets requis

```yaml
# Settings → Secrets and variables → Actions

# Application Secrets
SECRET_KEY: votre-secret-key
DATABASE_URL: postgres://...
REDIS_URL: redis://...

# API Keys
STRIPE_SECRET_KEY: sk_live_...
SENDGRID_API_KEY: SG.xxx

# Monitoring
SENTRY_DSN: https://...@sentry.io/...
SENTRY_AUTH_TOKEN: xxx

# Deployment
STAGING_SSH_USER: deploy
STAGING_HOST: staging.example.com
STAGING_SSH_KEY: -----BEGIN OPENSSH PRIVATE KEY-----

PROD_SSH_USER: deploy
PROD_HOST: example.com
PROD_SSH_KEY: -----BEGIN OPENSSH PRIVATE KEY-----

# Notifications
SLACK_WEBHOOK_URL: https://hooks.slack.com/...

# Container Registry
GITHUB_TOKEN: (fourni automatiquement)
```

### Protection des environnements

```
Settings → Environments → New environment

Environment: production
  ├─ Required reviewers: 1+ personnes
  ├─ Wait timer: 0 minutes
  ├─ Deployment branches:
  │   └─ Protected branches only (main)
  └─ Secrets spécifiques à l'environnement

Environment: staging
  ├─ Required reviewers: 0
  ├─ Deployment branches: develop
  └─ Secrets spécifiques
```

## Stratégies de déploiement

### 1. Rolling Deployment

```yaml
# Déploiement progressif sans interruption
deployment:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

### 2. Blue-Green Deployment

```yaml
# Deux environnements identiques
# Switch instantané par changement DNS/LB

steps:
  - name: Deploy Blue
    run: |
      docker-compose -f docker-compose.blue.yml up -d
      # Tests sur Blue
      curl -f http://blue.example.com/health/
  
  - name: Switch to Blue
    run: |
      # Changer le load balancer vers Blue
      update-lb blue
      # Ou changer DNS
      # update-dns blue.example.com
  
  - name: Keep Green as rollback
    run: |
      # Garder Green actif pendant X minutes
      sleep 300
      docker-compose -f docker-compose.green.yml down
```

### 3. Canary Deployment

```yaml
# Déploiement progressif sur % d'utilisateurs

steps:
  - name: Deploy Canary (10%)
    run: |
      # Route 10% du trafic vers la nouvelle version
      set-canary-percentage 10
      sleep 300  # Observer 5 minutes
  
  - name: Check metrics
    run: |
      # Vérifier erreurs, latence, etc.
      check-metrics --threshold-error-rate 1%
  
  - name: Promote or Rollback
    run: |
      if [ "${{ steps.check-metrics.outcome }}" == "success" ]; then
        set-canary-percentage 100
      else
        rollback
      fi
```

## Tests de déploiement

### Smoke Tests

```yaml
- name: Smoke Tests
  run: |
    # Test basiques après déploiement
    curl -f https://example.com/health/ || exit 1
    curl -f https://example.com/api/ || exit 1
    curl -f https://example.com/admin/login/ || exit 1
```

### Integration Tests

```yaml
- name: Integration Tests
  run: |
    pytest tests/integration/ \
      --base-url=https://staging.example.com \
      --headed=false
```

### Performance Tests

```yaml
- name: Performance Tests
  uses: grafana/k6-action@v0.3.1
  with:
    filename: tests/performance/load-test.js
    flags: --env ENV=staging
```

## Notifications et Monitoring

### Slack

```yaml
- name: Notify Slack
  uses: 8398a7/action-slack@v3
  if: always()
  with:
    status: ${{ job.status }}
    fields: repo,message,commit,author,action,eventName,ref,workflow
    mention: here
    if_mention: failure,cancelled
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Discord

```yaml
- name: Notify Discord
  uses: Ilshidur/action-discord@master
  if: always()
  env:
    DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK }}
  with:
    args: 'Déploiement ${{ job.status }}'
```

## Bonnes pratiques

### 1. Sécurité

```yaml
# ✅ Toujours utiliser des secrets
- name: Deploy
  env:
    SSH_KEY: ${{ secrets.SSH_KEY }}  # ✅
  run: |
    # ❌ Ne jamais hardcoder
    # ssh -i "hardcoded-key" user@host
    
    # ✅ Utiliser les secrets
    echo "$SSH_KEY" | ssh-add -

# ✅ Permissions minimales
permissions:
  contents: read
  packages: write

# ✅ Vérifier les signatures
checkout:
  - uses: actions/checkout@v4
    with:
      token: ${{ secrets.GITHUB_TOKEN }}
```

### 2. Performance

```yaml
# ✅ Cacher les dépendances
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}

# ✅ Cacher Docker layers
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max

# ✅ Matrices pour tests parallèles
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11']
```

### 3. Fiabilité

```yaml
# ✅ Timeout pour éviter les jobs bloqués
timeout-minutes: 30

# ✅ Retry sur échec
- name: Deploy with retry
  uses: nick-fields/retry@v2
  with:
    timeout_minutes: 10
    max_attempts: 3
    command: |
      ssh user@host 'deploy-script'

# ✅ Health checks
- name: Verify deployment
  run: |
    for i in {1..10}; do
      curl -f https://example.com/health/ && exit 0
      sleep 10
    done
    exit 1
```

## Checklist CI/CD

### Configuration initiale
- [ ] Workflow CI pour tests et lint
- [ ] Workflow Docker build et push
- [ ] Workflow déploiement staging
- [ ] Workflow déploiement production
- [ ] Protection des branches main/develop
- [ ] Environnements configurés avec reviewers

### Sécurité
- [ ] Secrets stockés dans GitHub
- [ ] Pas de secrets dans le code
- [ ] Scan de vulnérabilités (Trivy, Bandit)
- [ ] Permissions minimales sur workflows
- [ ] Branches protégées

### Qualité
- [ ] Tests automatiques sur PR
- [ ] Coverage minimum défini (ex: 80%)
- [ ] Linting automatique
- [ ] Type checking
- [ ] Security scanning

### Déploiement
- [ ] Déploiement automatique staging
- [ ] Déploiement manuel production (avec approval)
- [ ] Health checks post-déploiement
- [ ] Rollback automatisé possible
- [ ] Notifications Slack/Discord

### Monitoring
- [ ] Sentry release tracking
- [ ] Logs centralisés
- [ ] Alertes sur échec de déploiement
- [ ] Métriques de déploiement

## Ressources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Codecov](https://about.codecov.io/)
- [Sentry Release Tracking](https://docs.sentry.io/product/releases/)
