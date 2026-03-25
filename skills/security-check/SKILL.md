# Skill : Vérification de Sécurité Pré-Push

## Objectif

Ce skill permet de vérifier l'intégrité et la sécurité d'un projet Python avant de le pousser sur GitHub. Il détecte les secrets, vulnérabilités et patterns dangereux pour éviter les fuites de données et les failles de sécurité.

## Quand utiliser ce skill

- **Avant chaque push** : Vérification rapide (30 secondes)
- **Avant création de PR** : Vérification complète
- **Audit mensuel** : Scan approfondi du projet
- **Intégration CI/CD** : Vérification automatique sur chaque commit

## Outils utilisés

### 1. detect-secrets (Yelp)
**Rôle** : Détecte les secrets dans le code (clés API, tokens, passwords)
**Avantages** :
- Très simple à utiliser
- Supporte de nombreux formats de secrets
- Peut scanner l'historique git

### 2. bandit
**Rôle** : Analyse statique de sécurité Python
**Détecte** :
- Utilisation dangereuse de `eval()`, `exec()`
- Injections SQL
- Utilisation non sécurisée de `subprocess`
- Désérialisation non sécurisée
- Hardcoded passwords

### 3. pip-audit
**Rôle** : Vérifie les vulnérabilités des dépendances
**Avantages** :
- Utilise la base de données PyPA Advisory
- Plus rapide et simple que safety
- Intégré à pip

### 4. pre-commit
**Rôle** : Exécute automatiquement les vérifications avant chaque commit
**Avantages** :
- Bloque le commit si problème détecté
- Intégration transparente avec git
- Facile à configurer

## Installation rapide (1 commande)

```bash
pip install detect-secrets bandit pip-audit pre-commit
```

Ou avec un fichier requirements-dev.txt :

```
detect-secrets>=1.4.0
bandit>=1.7.0
pip-audit>=2.6.0
pre-commit>=3.0.0
```

## Configuration initiale (5 minutes)

### Étape 1 : Initialiser detect-secrets

```bash
# Créer la baseline (fichier de référence)
detect-secrets scan > .secrets.baseline

# Vérifier que tout est OK
detect-secrets audit .secrets.baseline
```

### Étape 2 : Configurer le pre-commit hook

Créer le fichier `.pre-commit-config.yaml` à la racine :

```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package.lock.json

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', '.', '-f', 'json', '-o', 'bandit-report.json']
        exclude: ^tests/

  - repo: local
    hooks:
      - id: pip-audit
        name: pip-audit
        entry: pip-audit
        language: system
        pass_filenames: false
        always_run: true
```

Installer le hook :

```bash
pre-commit install
```

### Étape 3 : Configurer .gitignore de base

Ajouter ces lignes si pas déjà présentes :

```gitignore
# Secrets et environnement
.env
.env.local
.env.*.local
*.pem
*.key
secrets.yaml
secrets.json
config.local.py

# Fichiers de rapport de sécurité
bandit-report.json
security-report.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```

## Workflow quotidien

### Option A : Script automatisé (Recommandé)

```bash
# Linux/Mac
./skills/security-check/scripts/security-check.sh

# Windows PowerShell
.\skills\security-check\scripts\security-check.ps1
```

### Option B : Commandes manuelles

```bash
# 1. Vérifier les secrets
detect-secrets scan --baseline .secrets.baseline

# 2. Analyse de sécurité du code
bandit -r . -f json -o bandit-report.json

# 3. Vérifier les dépendances vulnérables
pip-audit

# 4. Vérifier les fichiers traqués
git status
```

## Utilisation détaillée des outils

### detect-secrets

**Scanner le projet** :
```bash
detect-secrets scan > .secrets.baseline
```

**Vérifier les nouveaux secrets** :
```bash
detect-secrets scan --baseline .secrets.baseline
```

**Auditer les secrets trouvés** (marquer comme faux positifs) :
```bash
detect-secrets audit .secrets.baseline
```

**Scanner l'historique git** (important !) :
```bash
detect-secrets scan --all-files --force-use-all-plugins
```

**Exclusions courantes** (ajouter dans `.secrets.baseline`) :
```json
{
  "exclude": {
    "files": [
      "package-lock.json",
      "yarn.lock",
      "poetry.lock",
      ".secrets.baseline"
    ]
  }
}
```

### bandit

**Scan de base** :
```bash
bandit -r .
```

**Scan avec niveau de sévérité** (Low, Medium, High) :
```bash
# Ne rapporter que Medium et High
bandit -r . -ll

# Ne rapporter que High
bandit -r . -lll
```

**Scan avec rapport JSON** :
```bash
bandit -r . -f json -o bandit-report.json
```

**Exclure des répertoires** :
```bash
bandit -r . -x ./tests,./venv
```

**Configuration via pyproject.toml** :
```toml
[tool.bandit]
exclude_dirs = ["tests", "venv", ".venv"]
skips = ["B101", "B601"]  # Codes à ignorer
```

**Codes d'erreur courants** :
- `B101` : assert_used (assert dans le code de production)
- `B102` : exec_used (utilisation d'exec())
- `B105` : hardcoded_password_string
- `B307` : eval (utilisation d'eval())
- `B608` : hardcoded_sql_expressions

### pip-audit

**Vérification de base** :
```bash
pip-audit
```

**Vérification avec requirements.txt** :
```bash
pip-audit -r requirements.txt
```

**Format de sortie JSON** :
```bash
pip-audit -f json -o audit-report.json
```

**Ignorer des vulnérabilités spécifiques** :
```bash
pip-audit --ignore-vuln GHSA-xxxx-xxxx-xxxx
```

**Vérification avec PyPI** (plus complet mais plus lent) :
```bash
pip-audit --desc --vulnerability-service pypi
```

## Cas d'usage

### Cas 1 : Avant push quotidien (30 secondes)

```bash
# Vérification rapide
./scripts/security-check.sh

# Si tout est vert → git push
# Si alerte → corriger avant de push
```

### Cas 2 : Avant création de Pull Request (2 minutes)

```bash
# 1. Vérification complète
./scripts/security-check.sh

# 2. Vérifier l'historique git
detect-secrets scan --all-files

# 3. Vérifier que .secrets.baseline est à jour
git add .secrets.baseline
git commit -m "chore: update secrets baseline"

# 4. Push et créer la PR
git push origin ma-branche
```

### Cas 3 : Audit mensuel complet (5 minutes)

```bash
# 1. Scan complet de l'historique
detect-secrets scan --all-files --force-use-all-plugins > full-scan.json

# 2. Analyse approfondie
bandit -r . -lll -f json -o monthly-audit.json

# 3. Audit des dépendances avec descriptions
pip-audit --desc -f json -o dependency-audit.json

# 4. Vérifier les permissions des fichiers sensibles
ls -la .env* *.key *.pem 2>/dev/null || echo "Aucun fichier sensible trouvé"

# 5. Vérifier les gros fichiers ajoutés récemment
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '$1 == "blob" && $3 > 1048576' | sort -k3 -rn
```

### Cas 4 : Incident - Secret exposé accidentellement

```bash
# 1. NE PAS PANIQUER

# 2. Identifier le commit
git log --all --full-history --source --name-only -- '*.env' '*.key'

# 3. Révoquer immédiatement le secret (API key, token, etc.)
# Exemple : Si clé AWS → AWS Console → IAM → Révoquer
# Exemple : Si token GitHub → GitHub Settings → Developer settings → Tokens

# 4. Retirer le secret de l'historique git (ATTENTION : modifie l'historique)
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch chemin/vers/fichier' \
--prune-empty --tag-name-filter cat -- --all

# Alternative plus moderne avec git-filter-repo
# pip install git-filter-repo
# git filter-repo --path chemin/vers/fichier --invert-paths

# 5. Forcer le push (si branche non partagée)
git push origin --force --all

# 6. Mettre à jour la baseline
detect-secrets scan > .secrets.baseline

# 7. Vérifier que plus rien n'est exposé
./scripts/security-check.sh

# 8. Prévenir l'équipe si historique partagé modifié
```

### Cas 5 : Intégration CI/CD GitHub Actions

Créer `.github/workflows/security.yml` :

```yaml
name: Security Check

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    # Audit quotidien à 2h du matin
    - cron: '0 2 * * *'

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0  # Nécessaire pour detect-secrets

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install detect-secrets bandit pip-audit

    - name: Check for secrets
      run: |
        detect-secrets scan --baseline .secrets.baseline

    - name: Run bandit security scan
      run: |
        bandit -r . -f json -o bandit-report.json || true
        bandit -r .  # Affiche aussi dans la console

    - name: Check dependencies vulnerabilities
      run: |
        pip-audit --desc

    - name: Upload security reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: security-reports
        path: |
          bandit-report.json

    - name: Fail on critical vulnerabilities
      run: |
        # Vérifier s'il y a des vulnérabilités High/Critical
        if [ -f bandit-report.json ]; then
          HIGH_COUNT=$(cat bandit-report.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(len([r for r in d.get('results',[]) if r['issue_severity'] in ['HIGH','CRITICAL']]))" 2>/dev/null || echo "0")
          if [ "$HIGH_COUNT" -gt 0 ]; then
            echo "❌ $HIGH_COUNT vulnérabilité(s) HIGH/CRITICAL détectée(s)"
            exit 1
          fi
        fi
        echo "✅ Aucune vulnérabilité critique détectée"
```

## Pièges à éviter

### 1. Secrets dans l'historique git

**Problème** : Le secret a été supprimé du fichier mais existe encore dans l'historique
**Solution** :
```bash
# Scanner tout l'historique
detect-secrets scan --all-files

# Si secret trouvé → utiliser git-filter-repo ou filter-branch
```

### 2. Faux positifs avec detect-secrets

**Problème** : detect-secrets signale des faux secrets (ex: UUIDs légitimes)
**Solution** :
```bash
# Marquer comme faux positif
detect-secrets audit .secrets.baseline
# Puis choisir 'y' pour marquer comme faux positif

# Ou ajouter manuellement dans .secrets.baseline
```

### 3. .gitignore mal configuré

**Problème** : Des fichiers sensibles sont traqués par git
**Solution** :
```bash
# Vérifier les fichiers traqués
git ls-files | grep -E '\.(env|key|pem)$'

# Si trouvé, les retirer de git (mais pas du disque)
git rm --cached fichier.env
git commit -m "chore: remove sensitive file from tracking"
```

### 4. Dépendances non verrouillées

**Problème** : `pip install` sans requirements.txt ou version non fixée
**Solution** :
```bash
# Générer requirements.txt avec versions exactes
pip freeze > requirements.txt

# Ou utiliser pip-tools pour gérer les dépendances
pip install pip-tools
pip-compile requirements.in
pip-sync
```

### 5. Ignorer les alertes mineures

**Problème** : "C'est juste une alerte mineure, ça peut attendre"
**Solution** : Configurer pour bloquer dès le niveau LOW
```bash
bandit -r . -ll  # Bloque sur Medium et High
```

## Checklist pré-push

- [ ] `detect-secrets scan` passe sans nouveau secret
- [ ] `bandit -r .` ne rapporte pas d'erreur
- [ ] `pip-audit` ne montre pas de vulnérabilité non corrigée
- [ ] Pas de fichier `.env`, `*.key`, `*.pem` dans `git status`
- [ ] `.secrets.baseline` est à jour et commité
- [ ] Pas de `print()` ou `console.log()` avec données sensibles
- [ ] Pas de `eval()`, `exec()` ou `subprocess` non sécurisés
- [ ] Pas de mots de passe en dur dans le code
- [ ] Les clés API sont dans des variables d'environnement
- [ ] Le fichier `.gitignore` inclut bien les fichiers sensibles

## Commandes de diagnostic

### Vérifier si un secret est dans l'historique

```bash
# Rechercher un pattern spécifique
git log --all --full-history -p --grep="AKIA"  # Clés AWS
git log --all --full-history -p --grep="ghp_"  # Tokens GitHub
git log --all --full-history -p --grep="sk-"   # Clés OpenAI

# Rechercher dans le contenu
git log --all --full-history -S "mot_de_passe" --source --name-only
```

### Lister tous les fichiers sensibles traqués

```bash
git ls-files | grep -E '\.(env|key|pem|p12|pfx|keystore)$'
```

### Vérifier la taille des fichiers (détection de secrets binaires)

```bash
# Lister les gros fichiers
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '$1 == "blob" && $3 > 1048576' | \
  sort -k3 -rn | \
  head -20
```

### Nettoyer l'historique (dangereux !)

```bash
# Installation de git-filter-repo (outil moderne)
pip install git-filter-repo

# Supprimer un fichier de tout l'historique
git filter-repo --path fichier-secret.env --invert-paths

# Supprimer un dossier entier
git filter-repo --path dossier-secrets/ --invert-paths

# Supprimer par contenu (tous les fichiers contenant "password")
git filter-repo --replace-text <(echo 'password==>REMOVED')
```

## Bonnes pratiques

### 1. Ne jamais committer de secrets

**À faire** :
- Utiliser des variables d'environnement
- Utiliser des fichiers `.env` (non traqués)
- Utiliser des outils comme `python-dotenv`

**À ne pas faire** :
```python
# ❌ MAL
API_KEY = "sk-1234567890abcdef"

# ✅ BIEN
import os
API_KEY = os.getenv("API_KEY")
```

### 2. Utiliser des outils de gestion de secrets

```bash
# Option 1 : python-dotenv
pip install python-dotenv

# .env (dans .gitignore)
API_KEY=sk-1234567890abcdef

# code.py
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("API_KEY")
```

```bash
# Option 2 : AWS Secrets Manager / Azure Key Vault / HashiCorp Vault
# Pour les projets professionnels
```

### 3. Rotation régulière des secrets

- Changer les clés API tous les 3-6 mois
- Révoquer immédiatement en cas de doute
- Ne jamais réutiliser une clé compromise

### 4. Principe du moindre privilège

- Donner uniquement les permissions nécessaires
- Utiliser des clés API en lecture seule quand possible
- Restreindre les IP autorisées

### 5. Éducation de l'équipe

- Documenter les procédures de sécurité
- Faire des revues de code régulières
- Former aux bonnes pratiques

## Ressources

- [detect-secrets Documentation](https://github.com/Yelp/detect-secrets)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [pip-audit Documentation](https://pypi.org/project/pip-audit/)
- [pre-commit Documentation](https://pre-commit.com/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)

## Migration progressive

### Phase 1 : Installation (Jour 1)
```bash
pip install detect-secrets bandit pip-audit pre-commit
detect-secrets scan > .secrets.baseline
pre-commit install
```

### Phase 2 : Configuration (Jour 1-2)
- Créer `.pre-commit-config.yaml`
- Mettre à jour `.gitignore`
- Tester le pre-commit hook

### Phase 3 : Nettoyage (Jour 3-7)
- Scanner l'historique complet
- Retirer les secrets de l'historique si nécessaire
- Corriger les erreurs bandit

### Phase 4 : CI/CD (Semaine 2)
- Configurer GitHub Actions
- Intégrer au workflow de PR

### Phase 5 : Maintenance (Mensuel)
- Audit complet
- Mise à jour des dépendances
- Revue des faux positifs

## Messages d'erreur courants

### "Potential secrets about to be committed"
**Cause** : detect-secrets a trouvé un secret
**Solution** :
```bash
# Vérifier si c'est un vrai secret
detect-secrets audit .secrets.baseline

# Si faux positif, marquer comme tel
# Si vrai secret, le retirer du code
```

### "bandit: B105:hardcoded_password_string"
**Cause** : Chaîne ressemblant à un mot de passe en dur
**Solution** :
```python
# ❌ AVANT
password = "mysecret123"

# ✅ APRÈS
import os
password = os.getenv("PASSWORD")
```

### "pip-audit: GHSA-xxxx-xxxx-xxxx"
**Cause** : Dépendance avec vulnérabilité connue
**Solution** :
```bash
# Mettre à jour la dépendance
pip install --upgrade package-name

# Vérifier la compatibilité
pip check

# Mettre à jour requirements.txt
pip freeze > requirements.txt
```

### "pre-commit hook failed"
**Cause** : Un des hooks a détecté un problème
**Solution** :
```bash
# Voir les détails
pre-commit run --all-files

# Corriger les problèmes
# Relancer le commit
```
