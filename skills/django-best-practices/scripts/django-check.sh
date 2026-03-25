#!/bin/bash
# Script de vérification des bonnes pratiques Django
# Usage: ./django-check.sh [full]

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🔍 Vérification des bonnes pratiques Django"
echo "=========================================="
echo ""

# Fonction pour afficher les résultats
check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1${NC}"
        if [ "$2" = "fatal" ]; then
            exit 1
        fi
    fi
}

# 1. Vérifier que Django est installé
echo "📦 Vérification de l'environnement..."
python -c "import django" 2>/dev/null
check_result "Django installé" "fatal"

# 2. Vérifier les migrations
echo ""
echo "🔄 Vérification des migrations..."
python manage.py makemigrations --check --dry-run 2>/dev/null
check_result "Migrations à jour"

# 3. Vérifier les erreurs Django
echo ""
echo "🔧 Vérification des erreurs Django..."
python manage.py check 2>/dev/null
check_result "Pas d'erreurs détectées"

# 4. Lancer les tests
echo ""
echo "🧪 Exécution des tests..."
if command -v pytest &> /dev/null; then
    pytest -x -q 2>/dev/null
    check_result "Tests passent"
else
    python manage.py test --verbosity=0 2>/dev/null
    check_result "Tests passent"
fi

# 5. Vérifier la sécurité (si bandit est installé)
echo ""
echo "🔒 Vérification de la sécurité..."
if command -v bandit &> /dev/null; then
    bandit -r apps/ -f txt -o /dev/null -q 2>/dev/null
    check_result "Bandit : pas de vulnérabilités critiques"
else
    echo -e "${YELLOW}⚠ Bandit non installé (pip install bandit)${NC}"
fi

# 6. Vérifier les secrets (si detect-secrets est installé)
echo ""
echo "🕵️  Vérification des secrets..."
if command -v detect-secrets &> /dev/null; then
    if [ -f .secrets.baseline ]; then
        detect-secrets scan --baseline .secrets.baseline 2>/dev/null
        check_result "Pas de nouveaux secrets détectés"
    else
        echo -e "${YELLOW}⚠ Baseline detect-secrets non trouvée${NC}"
        echo "   Créer avec: detect-secrets scan > .secrets.baseline"
    fi
else
    echo -e "${YELLOW}⚠ detect-secrets non installé (pip install detect-secrets)${NC}"
fi

# 7. Vérification complète si demandé
if [ "$1" = "full" ]; then
    echo ""
    echo "🔍 Vérification complète..."
    
    # Vérifier le déploiement
    echo "   Vérification de la configuration de production..."
    python manage.py check --deploy 2>/dev/null
    check_result "Configuration de production OK"
    
    # Couverture de tests
    if command -v pytest &> /dev/null; then
        echo "   Calcul de la couverture de tests..."
        pytest --cov=apps --cov-report=term-missing --cov-fail-under=80 -q 2>/dev/null
        check_result "Couverture de tests > 80%"
    fi
    
    # Linting avec ruff
    if command -v ruff &> /dev/null; then
        echo "   Vérification du linting..."
        ruff check apps/ 2>/dev/null
        check_result "Pas d'erreurs de linting"
    fi
    
    # Formatage avec black
    if command -v black &> /dev/null; then
        echo "   Vérification du formatage..."
        black --check apps/ 2>/dev/null
        check_result "Code correctement formaté"
    fi
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Vérifications terminées !${NC}"
echo "=========================================="
echo ""
echo "Prochaines étapes:"
echo "  - Corriger les erreurs éventuelles"
echo "  - Committer les changements"
echo "  - Pousser sur git"
