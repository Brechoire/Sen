# Git Workflow - Démarrage Rapide

## Installation (5 minutes)

```bash
# 1. Configuration de base
git config --global user.name "Votre Nom"
git config --global user.email "votre@email.com"
git config --global core.editor "code --wait"
git config --global pull.rebase true

# 2. Aliases recommandés
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.lg "log --oneline --graph --decorate --all"
git config --global alias.last "log -1 HEAD --stat"
git config --global alias.undo "reset --soft HEAD~1"

# 3. Hook pre-commit (empêche commit sur main)
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
  echo "❌ Commit direct sur $branch interdit !"
  exit 1
fi
EOF
chmod +x .git/hooks/pre-commit
```

## Workflow Quotidien

### Créer une feature

```bash
# 1. Synchroniser
git checkout main
git pull origin main

# 2. Créer branche
git checkout -b feature/nom-de-la-feature

# 3. Développer et commiter
git add .
git commit -m "feat(scope): description"

# 4. Pousser
git push -u origin feature/nom-de-la-feature

# 5. Créer PR (avec GitHub CLI)
gh pr create --title "feat: description" --body "## Changes..."
```

### Types de commits

```bash
feat:     nouvelle fonctionnalité
fix:      correction de bug
docs:     documentation
style:    formatage (pas de code)
refactor: refactoring
perf:     performance
test:     tests
chore:    maintenance
ci:       CI/CD
build:    build system
revert:   annulation
```

### Exemples

```bash
git commit -m "feat(auth): add JWT login endpoint"
git commit -m "fix(api): resolve 500 error on user creation"
git commit -m "docs(readme): update installation steps"
git commit -m "test(auth): add login unit tests"
git commit -m "chore(deps): update Django to 5.0"
```

## Commandes essentielles

```bash
# État
git status                    # Voir les modifications
git lg                        # Historique graphique
git last                      # Dernier commit

# Navigation
git checkout main             # Aller sur main
git checkout -b feature/x     # Nouvelle branche
git checkout -                # Branche précédente

# Modifications
git add -p                    # Ajouter par morceaux
git commit --amend            # Modifier dernier commit
git undo                      # Annuler dernier commit (soft)

# Synchronisation
git pull origin main          # Récupérer main
git fetch origin              # Récupérer sans merger
git rebase origin/main        # Rebaser sur main

# Stash
git stash push -m "msg"       # Sauvegarder temporairement
git stash pop                 # Restaurer
git stash list                # Voir les stashs

# Nettoyage
git branch -d feature/x       # Supprimer branche locale
git push origin --delete feature/x  # Supprimer branche distante
```

## Conventions

### Messages de commit

```bash
# ✅ Format
type(scope): description en minuscule sans point final

# ✅ Exemples
git commit -m "feat(auth): add password reset"
git commit -m "fix(api): correct pagination count"
git commit -m "docs: add API examples"

# ❌ À éviter
git commit -m "Added feature"           # Pas de type
git commit -m "feat: Added feature"     # Majuscule
git commit -m "feat: add feature."      # Point final
git commit -m "feat(auth):Add feature"  # Pas d'espace après :
```

### Noms de branches

```bash
# Format
type/description-courte

# ✅ Exemples
feature/user-authentication
bugfix/login-error-500
hotfix/security-patch
chore/update-dependencies
refactor/user-service

# ❌ À éviter
feature_branch              # Pas de underscore
Feature-Auth                # Pas de majuscule
my-feature                  # Pas de type
```

## Résolution de problèmes

```bash
# Oublie de créer une branche (commit sur main)
git checkout -b feature/xxx    # Créer branche depuis main
git checkout main              # Retourner sur main
git reset --hard HEAD~1        # Annuler dernier commit sur main
git checkout feature/xxx       # Retourner sur la branche

# Conflits de merge
git status                     # Voir fichiers en conflit
# Éditer les fichiers (rechercher <<<<<< HEAD)
git add <fichier>              # Marquer comme résolu
git rebase --continue          # Continuer

# Commit sur mauvaise branche
git reset --soft HEAD~1        # Annuler dernier commit
git checkout feature/xxx       # Changer de branche
git commit -m "..."            # Recommiter

# Pousser sur main par erreur
git revert HEAD                # Créer un commit d'annulation
# OU (si pas encore poussé)
git reset --hard HEAD~1
```

## Template de PR

```markdown
## Description
[Description brève]

## Type
- [ ] Bug fix
- [ ] Feature
- [ ] Refactoring
- [ ] Documentation

## Checklist
- [ ] Tests passent
- [ ] Code review OK
- [ ] Documentation à jour

## Ticket
Closes #XXX
```

## Checklist rapide

- [ ] `git pull origin main` avant de créer une branche
- [ ] Nom de branche : `type/description`
- [ ] Commits atomiques et fréquents
- [ ] Message : `type(scope): description`
- [ ] Pas de commit sur main
- [ ] PR petite (< 400 lignes)
- [ ] Rebase sur main avant merge
- [ ] Supprimer la branche après merge
