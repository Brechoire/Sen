#!/bin/bash

# Script de vérification de sécurité pré-push
# Usage: ./security-check.sh [options]
# Options:
#   --full    : Scan complet incluant l'historique git
#   --quick   : Vérification rapide (défaut)
#   --ci      : Mode CI (sortie JSON uniquement)

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
FULL_SCAN=false
QUICK_MODE=true
CI_MODE=false
EXIT_CODE=0
REPORTS_DIR="security-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Fonction d'aide
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --full    Effectue un scan complet (inclut l'historique git)"
    echo "  --quick   Vérification rapide (défaut)"
    echo "  --ci      Mode CI - sortie JSON uniquement"
    echo "  --help    Affiche cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0                    # Vérification rapide"
    echo "  $0 --full             # Scan complet"
    echo "  $0 --ci               # Mode CI"
}

# Parse des arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            FULL_SCAN=true
            QUICK_MODE=false
            shift
            ;;
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --ci)
            CI_MODE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# Fonction d'affichage
print_header() {
    if [ "$CI_MODE" = false ]; then
        echo ""
        echo "========================================"
        echo "$1"
        echo "========================================"
    fi
}

print_success() {
    if [ "$CI_MODE" = false ]; then
        echo -e "${GREEN}✅ $1${NC}"
    fi
}

print_warning() {
    if [ "$CI_MODE" = false ]; then
        echo -e "${YELLOW}⚠️  $1${NC}"
    fi
}

print_error() {
    if [ "$CI_MODE" = false ]; then
        echo -e "${RED}❌ $1${NC}"
    fi
}

print_info() {
    if [ "$CI_MODE" = false ]; then
        echo -e "${BLUE}ℹ️  $1${NC}"
    fi
}

# Vérification des dépendances
check_dependencies() {
    print_header "Vérification des dépendances"
    
    local missing_deps=()
    
    if ! command -v detect-secrets &> /dev/null; then
        missing_deps+=("detect-secrets")
    fi
    
    if ! command -v bandit &> /dev/null; then
        missing_deps+=("bandit")
    fi
    
    if ! command -v pip-audit &> /dev/null; then
        missing_deps+=("pip-audit")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Outils manquants: ${missing_deps[*]}"
        print_info "Installation: pip install detect-secrets bandit pip-audit"
        exit 1
    fi
    
    print_success "Toutes les dépendances sont installées"
}

# Création du dossier de rapports
setup_reports_dir() {
    if [ "$CI_MODE" = true ]; then
        mkdir -p "$REPORTS_DIR"
    fi
}

# Vérification des secrets avec detect-secrets
check_secrets() {
    print_header "1. Vérification des secrets (detect-secrets)"
    
    if [ ! -f ".secrets.baseline" ]; then
        print_warning "Fichier .secrets.baseline non trouvé"
        print_info "Création de la baseline..."
        detect-secrets scan > .secrets.baseline
        print_success "Baseline créée: .secrets.baseline"
        print_warning "Vérifiez ce fichier et committez-le"
    fi
    
    if [ "$FULL_SCAN" = true ]; then
        print_info "Scan complet de l'historique git..."
        if detect-secrets scan --all-files --force-use-all-plugins --baseline .secrets.baseline > /dev/null 2>&1; then
            print_success "Aucun secret trouvé dans l'historique"
        else
            print_error "Secrets trouvés dans l'historique !"
            detect-secrets scan --all-files --force-use-all-plugins --baseline .secrets.baseline
            EXIT_CODE=1
        fi
    else
        print_info "Scan des fichiers actuels..."
        if detect-secrets scan --baseline .secrets.baseline > /dev/null 2>&1; then
            print_success "Aucun nouveau secret détecté"
        else
            print_error "Nouveaux secrets détectés !"
            detect-secrets scan --baseline .secrets.baseline
            print_info "Exécutez 'detect-secrets audit .secrets.baseline' pour examiner"
            EXIT_CODE=1
        fi
    fi
    
    if [ "$CI_MODE" = true ]; then
        detect-secrets scan --baseline .secrets.baseline --json > "$REPORTS_DIR/secrets-$TIMESTAMP.json" 2>/dev/null || true
    fi
}

# Analyse de sécurité avec bandit
check_bandit() {
    print_header "2. Analyse de sécurité du code (bandit)"
    
    local bandit_args="-r ."
    
    if [ "$CI_MODE" = true ]; then
        bandit_args="$bandit_args -f json -o $REPORTS_DIR/bandit-$TIMESTAMP.json"
    fi
    
    # Exclure les répertoires courants
    bandit_args="$bandit_args -x ./tests,./venv,./.venv,./env,./__pycache__,./build,./dist,./node_modules"
    
    print_info "Exécution de bandit..."
    
    if bandit $bandit_args -ll 2>/dev/null; then
        print_success "Aucune vulnérabilité HIGH/CRITICAL détectée"
    else
        local bandit_exit=$?
        if [ $bandit_exit -eq 1 ]; then
            print_error "Vulnérabilités détectées !"
            if [ "$CI_MODE" = false ]; then
                bandit -r . -x ./tests,./venv,./.venv,./env,./__pycache__ -ll 2>/dev/null || true
            fi
            EXIT_CODE=1
        fi
    fi
}

# Vérification des dépendances avec pip-audit
check_dependencies_vulns() {
    print_header "3. Vérification des dépendances (pip-audit)"
    
    local audit_args=""
    
    if [ "$CI_MODE" = true ]; then
        audit_args="-f json -o $REPORTS_DIR/pip-audit-$TIMESTAMP.json"
    else
        audit_args="--desc"
    fi
    
    if [ -f "requirements.txt" ]; then
        print_info "Audit de requirements.txt..."
        if pip-audit -r requirements.txt $audit_args 2>/dev/null; then
            print_success "Aucune vulnérabilité dans les dépendances"
        else
            local audit_exit=$?
            if [ $audit_exit -ne 0 ]; then
                print_error "Vulnérabilités détectées dans les dépendances !"
                if [ "$CI_MODE" = false ]; then
                    pip-audit -r requirements.txt --desc 2>/dev/null || true
                fi
                EXIT_CODE=1
            fi
        fi
    elif [ -f "pyproject.toml" ]; then
        print_info "Audit de pyproject.toml..."
        if pip-audit $audit_args 2>/dev/null; then
            print_success "Aucune vulnérabilité dans les dépendances"
        else
            local audit_exit=$?
            if [ $audit_exit -ne 0 ]; then
                print_error "Vulnérabilités détectées dans les dépendances !"
                if [ "$CI_MODE" = false ]; then
                    pip-audit --desc 2>/dev/null || true
                fi
                EXIT_CODE=1
            fi
        fi
    else
        print_warning "Aucun fichier requirements.txt ou pyproject.toml trouvé"
        print_info "Audit des packages installés..."
        if pip-audit $audit_args 2>/dev/null; then
            print_success "Aucune vulnérabilité détectée"
        else
            local audit_exit=$?
            if [ $audit_exit -ne 0 ]; then
                print_error "Vulnérabilités détectées !"
                EXIT_CODE=1
            fi
        fi
    fi
}

# Vérification des fichiers sensibles
check_sensitive_files() {
    print_header "4. Vérification des fichiers sensibles"
    
    local sensitive_files=()
    
    # Vérifier les fichiers traqués par git
    if command -v git &> /dev/null; then
        while IFS= read -r file; do
            case "$file" in
                *.env|.env|*.key|*.pem|*.p12|*.pfx|id_rsa|id_dsa|id_ecdsa|id_ed25519|.htpasswd|.netrc)
                    sensitive_files+=("$file")
                    ;;
            esac
        done < <(git ls-files 2>/dev/null | grep -E '\.(env|key|pem|p12|pfx)$|^(id_rsa|id_dsa|id_ecdsa|id_ed25519|.htpasswd|.netrc)' || true)
    fi
    
    if [ ${#sensitive_files[@]} -eq 0 ]; then
        print_success "Aucun fichier sensible traqué par git"
    else
        print_error "Fichiers sensibles traqués par git :"
        for file in "${sensitive_files[@]}"; do
            echo "  - $file"
        done
        print_info "Ajoutez ces fichiers à .gitignore et retirez-les avec: git rm --cached <fichier>"
        EXIT_CODE=1
    fi
}

# Vérification du .gitignore
check_gitignore() {
    print_header "5. Vérification du .gitignore"
    
    if [ ! -f ".gitignore" ]; then
        print_error "Fichier .gitignore non trouvé !"
        print_info "Créez un .gitignore avec les règles de base"
        EXIT_CODE=1
        return
    fi
    
    local required_patterns=(
        ".env"
        "*.key"
        "*.pem"
        "__pycache__/"
        "*.pyc"
        ".venv/"
        "venv/"
    )
    
    local missing_patterns=()
    
    for pattern in "${required_patterns[@]}"; do
        # Vérifier si le pattern existe ou si une variante équivalente existe
        case "$pattern" in
            "*.pyc")
                # *.pyc peut être couvert par *.py[cod]
                if ! grep -qE '\*\.pyc|\*\.py\[cod\]' .gitignore 2>/dev/null; then
                    missing_patterns+=("$pattern")
                fi
                ;;
            *)
                if ! grep -q "$pattern" .gitignore 2>/dev/null; then
                    missing_patterns+=("$pattern")
                fi
                ;;
        esac
    done
    
    if [ ${#missing_patterns[@]} -eq 0 ]; then
        print_success ".gitignore correctement configuré"
    else
        print_warning "Patterns manquants dans .gitignore :"
        for pattern in "${missing_patterns[@]}"; do
            echo "  - $pattern"
        done
        print_info "Ajoutez ces patterns à votre .gitignore"
    fi
}

# Scan de l'historique git (mode full uniquement)
check_git_history() {
    if [ "$FULL_SCAN" = false ]; then
        return
    fi
    
    print_header "6. Scan de l'historique git (mode full)"
    
    print_info "Recherche de gros fichiers..."
    local large_files=$(git rev-list --objects --all 2>/dev/null | \
        git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' 2>/dev/null | \
        awk '$1 == "blob" && $3 > 10485760' | \
        sort -k3 -rn | \
        head -10 || true)
    
    if [ -z "$large_files" ]; then
        print_success "Aucun gros fichier (>10MB) dans l'historique"
    else
        print_warning "Gros fichiers détectés dans l'historique :"
        echo "$large_files"
        print_info "Ces fichiers peuvent contenir des secrets binaires"
    fi
}

# Génération du rapport final
generate_report() {
    if [ "$CI_MODE" = true ]; then
        print_header "Rapports générés"
        echo "Les rapports JSON sont disponibles dans: $REPORTS_DIR/"
        ls -la "$REPORTS_DIR/" 2>/dev/null || true
    fi
}

# Résumé final
print_summary() {
    if [ "$CI_MODE" = false ]; then
        echo ""
        echo "========================================"
        echo "RÉSUMÉ"
        echo "========================================"
        
        if [ $EXIT_CODE -eq 0 ]; then
            print_success "Toutes les vérifications sont passées !"
            print_info "Vous pouvez push en toute sécurité"
            echo ""
            echo "Commande: git push"
        else
            print_error "Des problèmes de sécurité ont été détectés !"
            print_info "Corrigez les problèmes avant de push"
            echo ""
            echo "Pour ignorer temporairement (déconseillé):"
            echo "  git push --no-verify"
        fi
    fi
}

# Fonction principale
main() {
    if [ "$CI_MODE" = false ]; then
        echo ""
        echo "╔════════════════════════════════════════════════╗"
        echo "║   🔒 Vérification de Sécurité Pré-Push 🔒     ║"
        echo "╚════════════════════════════════════════════════╝"
        
        if [ "$FULL_SCAN" = true ]; then
            echo "Mode: Scan complet"
        else
            echo "Mode: Vérification rapide"
        fi
        echo ""
    fi
    
    check_dependencies
    setup_reports_dir
    check_secrets
    check_bandit
    check_dependencies_vulns
    check_sensitive_files
    check_gitignore
    check_git_history
    generate_report
    print_summary
    
    exit $EXIT_CODE
}

# Exécution
main
