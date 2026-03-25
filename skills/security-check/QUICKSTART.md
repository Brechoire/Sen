# QuickStart - Vérification de Sécurité Pré-Push

## Installation (2 minutes)

```bash
# 1. Installer les outils
pip install detect-secrets bandit pip-audit pre-commit

# 2. Initialiser detect-secrets
detect-secrets scan > .secrets.baseline

# 3. Installer le pre-commit hook
pre-commit install
```

## Utilisation quotidienne (30 secondes)

### Avant chaque push

```bash
# Linux/Mac
./skills/security-check/scripts/security-check.sh

# Windows PowerShell
.\skills\security-check\scripts\security-check.ps1
```

### Résultats

- ✅ **Vert** : Tout est bon, vous pouvez push
- ❌ **Rouge** : Problèmes détectés, corrigez avant de push

## Checklist rapide pré-push

- [ ] Script de sécurité exécuté sans erreur
- [ ] Pas de secrets dans `git status`
- [ ] Pas de fichiers `.env`, `*.key`, `*.pem` traqués
- [ ] `.secrets.baseline` commité si modifié

## Commandes essentielles

```bash
# Vérification rapide (défaut)
./scripts/security-check.sh

# Scan complet (historique git inclus)
./scripts/security-check.sh --full

# Mode CI (sortie JSON)
./scripts/security-check.sh --ci

# Examiner les secrets trouvés
detect-secrets audit .secrets.baseline

# Mettre à jour la baseline
detect-secrets scan > .secrets.baseline
```

## Résolution des problèmes courants

### "Potential secrets about to be committed"

```bash
# Vérifier si c'est un vrai secret
detect-secrets audit .secrets.baseline

# Si faux positif : marquer comme tel dans l'audit
# Si vrai secret : retirer du code et utiliser variables d'environnement
```

### "bandit: B105:hardcoded_password_string"

```python
# ❌ AVANT
password = "mysecret123"

# ✅ APRÈS
import os
password = os.getenv("PASSWORD")
```

### "pip-audit: GHSA-xxxx-xxxx-xxxx"

```bash
# Mettre à jour le package
pip install --upgrade package-name
pip freeze > requirements.txt
```

### Fichier sensible traqué par git

```bash
# Retirer du git (mais pas du disque)
git rm --cached fichier.env
git commit -m "remove sensitive file"

# Ajouter à .gitignore
echo "fichier.env" >> .gitignore
```

## Configuration minimale .gitignore

```gitignore
# Secrets
.env
.env.local
*.key
*.pem
*.p12

# Python
__pycache__/
*.pyc
.venv/
venv/

# IDE
.vscode/
.idea/
```

## Intégration CI/CD

Le skill inclut une configuration GitHub Actions prête à l'emploi dans `.github/workflows/security.yml`.

Activez-la en copiant le fichier dans votre repo :

```bash
mkdir -p .github/workflows
cp skills/security-check/.github/workflows/security.yml .github/workflows/
git add .github/workflows/security.yml
git commit -m "ci: add security checks"
```

## Besoin d'aide ?

- Documentation complète : `SKILL.md`
- Commandes détaillées : `SKILL.md` section "Utilisation détaillée des outils"
- Cas d'usage : `SKILL.md` section "Cas d'usage"
- Pièges à éviter : `SKILL.md` section "Pièges à éviter"

## Raccourcis

| Action | Commande |
|--------|----------|
| Vérification rapide | `./scripts/security-check.sh` |
| Scan complet | `./scripts/security-check.sh --full` |
| Examiner secrets | `detect-secrets audit .secrets.baseline` |
| Audit dépendances | `pip-audit` |
| Scan sécurité code | `bandit -r .` |
