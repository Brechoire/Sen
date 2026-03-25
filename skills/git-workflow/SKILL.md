# Skill : Git Workflow

## Objectif

Standardiser l'utilisation de Git pour garantir un historique clair, des revues de code efficaces et une collaboration fluide en équipe.

## Quand utiliser ce skill

- Création d'un nouveau dépôt Git
- Mise en place de conventions d'équipe
- Avant chaque commit
- Création de Pull Requests
- Revue de code

## Conventional Commits

### Format standard

```
<type>(<scope>): <description>

[body]

[footer(s)]
```

### Types de commits

| Type | Description | Exemple |
|------|-------------|---------|
| `feat` | Nouvelle fonctionnalité | `feat(auth): add JWT authentication` |
| `fix` | Correction de bug | `fix(api): resolve null pointer exception` |
| `docs` | Documentation uniquement | `docs(readme): update installation steps` |
| `style` | Formatage (pas de changement de logique) | `style(lint): fix indentation` |
| `refactor` | Refactoring du code | `refactor(models): extract user service` |
| `perf` | Amélioration de performance | `perf(db): add index on user_email` |
| `test` | Ajout/modification de tests | `test(auth): add login unit tests` |
| `chore` | Maintenance (build, deps, etc.) | `chore(deps): update Django to 5.0` |
| `ci` | CI/CD | `ci(github): add lint workflow` |
| `build` | Build system | `build(docker): optimize image size` |
| `revert` | Annulation d'un commit | `revert(auth): revert JWT changes` |

### Exemples complets

```bash
# Commit simple
feat: add user registration

# Commit avec scope
feat(api): add user registration endpoint

# Commit avec description détaillée
feat(api): add user registration endpoint

- Implement POST /api/users/register
- Add email validation
- Send welcome email
- Add rate limiting (5 attempts/minute)

Closes #123

# Commit avec BREAKING CHANGE
feat(api): change authentication method

BREAKING CHANGE: API now requires JWT token in Authorization header
instead of session cookies.

Migration guide:
- Add Authorization: Bearer <token> header
- Remove session cookie handling
```

### Bonnes pratiques

```bash
# ✅ Messages au présent impératif
git commit -m "feat: add validation"

# ❌ Pas au passé ou futur
git commit -m "feat: added validation"
git commit -m "feat: will add validation"

# ✅ Première lettre en minuscule
git commit -m "feat: add user model"

# ❌ Pas de majuscule
git commit -m "feat: Add user model"

# ✅ Pas de point final
git commit -m "feat: fix bug"

# ❌ Avec point
git commit -m "feat: fix bug."
```

## Stratégie de branches

### GitHub Flow (recommandé pour la plupart des projets)

```
main
  │
  ├── feature/user-auth
  ├── feature/payment-integration
  ├── bugfix/login-error
  └── hotfix/security-patch
```

**Workflow :**

```bash
# 1. Synchroniser main
git checkout main
git pull origin main

# 2. Créer une branche feature
git checkout -b feature/description-claire

# 3. Développer et commiter
git add .
git commit -m "feat: implement feature"

# 4. Pousser la branche
git push -u origin feature/description-claire

# 5. Créer une Pull Request
gh pr create --title "feat: description" --body "## Changes..."

# 6. Après merge, nettoyer
git checkout main
git pull origin main
git branch -d feature/description-claire
```

### Git Flow (pour projets avec versions releases)

```
main (production)
  │
  ├── develop (intégration)
  │     │
  │     ├── feature/* (développement)
  │     └── release/* (préparation release)
  │
  └── hotfix/* (corrections urgentes)
```

```bash
# Initialisation
git checkout -b develop main

# Nouvelle feature
git checkout -b feature/login develop
# ... développement ...
git checkout develop
git merge --no-ff feature/login

# Préparation release
git checkout -b release/1.2.0 develop
# ... corrections finales ...
git checkout main
git merge --no-ff release/1.2.0
git tag -a v1.2.0 -m "Version 1.2.0"
git checkout develop
git merge --no-ff release/1.2.0
```

### Conventions de nommage des branches

```bash
# Format : type/description-courte

# Features
feature/user-authentication
feature/api-pagination

# Corrections
bugfix/login-error-500
hotfix/security-vulnerability

# Maintenance
chore/update-dependencies
refactor/extract-service

# Documentation
docs/api-endpoints
```

## Revue de code (Code Review)

### Avant de demander une revue

```bash
# ✅ Checklist pre-PR
- [ ] Tests passent localement
- [ ] Code linté (black, flake8, etc.)
- [ ] Pas de secrets/commit accidentels
- [ ] Description de PR claire et complète
- [ ] Screenshots si UI modifiée
- [ ] Ticket lié (Closes #XXX)
```

### Template de Pull Request

```markdown
## Description
Brève description des changements

## Type de changement
- [ ] Bug fix
- [ ] Nouvelle fonctionnalité
- [ ] Breaking change
- [ ] Refactoring
- [ ] Documentation

## Checklist
- [ ] Tests ajoutés/mis à jour
- [ ] Documentation mise à jour
- [ ] Code review effectuée
- [ ] Pas de régression détectée

## Screenshots (si applicable)
[Ajouter captures d'écran]

## Ticket lié
Closes #123
```

### Bonnes pratiques de review

**Pour l'auteur :**
- Garder les PR petites (< 400 lignes)
- Une PR = une fonctionnalité/un fix
- Répondre aux commentaires rapidement
- Ne pas prendre les critiques personnellement

**Pour le reviewer :**
- Reviewer dans les 24h
- Poser des questions plutôt qu'imposer
- Distinguer blocking vs suggestions
- Approuver avec conditions si mineur

```
# Commentaires de review
🔴 Blocking - Doit être corrigé
🟡 Suggestion - À considérer
🟢 Nitpick - Détail mineur
💡 Question - Pour comprendre
```

## Configuration Git recommandée

### Configuration globale

```bash
# Nom et email
git config --global user.name "Votre Nom"
git config --global user.email "votre@email.com"

# Éditeur par défaut
git config --global core.editor "code --wait"

# Aliases utiles
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.lg "log --oneline --graph --decorate --all"
git config --global alias.last "log -1 HEAD --stat"
git config --global alias.unstage "reset HEAD --"
git config --global alias.undo "reset --soft HEAD~1"

# Configuration du rebase par défaut pour pull
git config --global pull.rebase true

# Gestion des fins de ligne (Windows)
git config --global core.autocrlf true
# Gestion des fins de ligne (Mac/Linux)
git config --global core.autocrlf input
```

### Hooks Git utiles

**pre-commit** (empêche commit sur main)

```bash
#!/bin/sh
# .git/hooks/pre-commit

branch=$(git rev-parse --abbrev-ref HEAD)

if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
  echo "❌ Commit direct sur $branch interdit !"
  echo "Créez une branche feature: git checkout -b feature/xxx"
  exit 1
fi

# Vérification du message de commit
commit_msg_file=$1
commit_msg=$(head -n1 "$commit_msg_file")

# Regex pour Conventional Commits
conventional_commit_regex="^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\(.+\))?: .+$"

if ! echo "$commit_msg" | grep -qE "$conventional_commit_regex"; then
  echo "❌ Message de commit invalide !"
  echo "Format attendu: <type>(<scope>): <description>"
  echo "Types: feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert"
  exit 1
fi

exit 0
```

**commit-msg** (validation Conventional Commits)

```bash
#!/bin/sh
# .git/hooks/commit-msg

commit_msg_file=$1
commit_msg=$(head -n1 "$commit_msg_file")

# Regex pour Conventional Commits
conventional_commit_regex="^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\(.+\))?!?: .+$"

if ! echo "$commit_msg" | grep -qE "$conventional_commit_regex"; then
  echo ""
  echo "❌ Message de commit invalide !"
  echo ""
  echo "Format attendu: <type>(<scope>): <description>"
  echo ""
  echo "Types valides:"
  echo "  feat:     Nouvelle fonctionnalité"
  echo "  fix:      Correction de bug"
  echo "  docs:     Documentation"
  echo "  style:    Formatage"
  echo "  refactor: Refactoring"
  echo "  perf:     Performance"
  echo "  test:     Tests"
  echo "  chore:    Maintenance"
  echo "  ci:       CI/CD"
  echo "  build:    Build"
  echo "  revert:   Annulation"
  echo ""
  echo "Exemples:"
  echo "  feat(auth): add login endpoint"
  echo "  fix(api): resolve null pointer"
  echo "  docs(readme): update instructions"
  echo ""
  exit 1
fi

exit 0
```

## Commandes avancées

### Réécrire l'historique (avec prudence)

```bash
# Modifier le dernier commit
git commit --amend -m "nouveau message"
git commit --amend --no-edit  # garder le message

# Modifier plusieurs commits (interactif)
git rebase -i HEAD~3

# Squash commits en un seul
git rebase -i HEAD~3
# Dans l'éditeur, remplacer 'pick' par 'squash' ou 's'

# Split un commit
git rebase -i HEAD~3
# Choisir 'edit' sur le commit à splitter
git reset HEAD^
git add -p  # ajouter par morceaux
git commit -m "premier commit"
git add .
git commit -m "deuxième commit"
git rebase --continue
```

### Gestion des conflits

```bash
# Voir les fichiers en conflit
git status

# Outil de merge interactif
git mergetool

# Marquer comme résolu
git add <fichier>

# Annuler le merge en cours
git merge --abort

# Annuler un rebase
git rebase --abort
```

### Stash (sauvegarde temporaire)

```bash
# Sauvegarder les modifications en cours
git stash push -m "description"

# Lister les stashes
git stash list

# Appliquer le dernier stash
git stash pop

# Appliquer un stash spécifique
git stash apply stash@{2}

# Supprimer un stash
git stash drop stash@{1}

# Appliquer stash sur une nouvelle branche
git stash branch nouvelle-branche
```

## Intégration CI/CD

### GitHub Actions - Vérification des commits

```yaml
# .github/workflows/commit-lint.yml
name: Commit Lint

on: [pull_request]

jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Check Conventional Commits
        uses: wagoid/commitlint-github-action@v5
        with:
          configFile: .commitlintrc.json
```

### Configuration commitlint

```json
// .commitlintrc.json
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [2, "always", [
      "feat", "fix", "docs", "style", "refactor",
      "perf", "test", "chore", "ci", "build", "revert"
    ]],
    "subject-case": [2, "never", ["sentence-case", "start-case", "pascal-case"]]
  }
}
```

## Checklist Git Workflow

### Avant de commencer
- [ ] Git configuré (nom, email)
- [ ] Aliases utiles créés
- [ ] Hooks installés
- [ ] Stratégie de branches définie

### Pendant le développement
- [ ] Branche créée depuis main à jour
- [ ] Commits fréquents et atomiques
- [ ] Messages suivent Conventional Commits
- [ ] Pas de commit sur main

### Avant la PR
- [ ] Rebase sur main
git fetch origin && git rebase origin/main
- [ ] Tests passent
- [ ] Lint OK
- [ ] Description de PR complète
- [ ] Screenshots si UI

### Pendant la review
- [ ] Réponses sous 24h
- [ ] Discussion constructive
- [ ] Corrections poussées
- [ ] Rebase si nécessaire avant merge

### Après le merge
- [ ] Branche locale supprimée
- [ ] Branche distante supprimée
- [ ] Ticket mis à jour

## Ressources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Git Aliases](https://git-scm.com/book/en/v2/Git-Basics-Git-Aliases)
