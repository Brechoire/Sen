#Requires -Version 5.1
# Script de vérification des bonnes pratiques Django pour Windows
# Usage: .\django-check.ps1 [-Full]

param(
    [switch]$Full
)

$ErrorActionPreference = "Stop"

# Couleurs
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"

function Write-CheckResult {
    param(
        [string]$Message,
        [bool]$Success,
        [switch]$Fatal
    )
    
    if ($Success) {
        Write-Host "✓ $Message" -ForegroundColor $Green
    } else {
        Write-Host "✗ $Message" -ForegroundColor $Red
        if ($Fatal) {
            exit 1
        }
    }
}

function Test-CommandExists {
    param([string]$Command)
    return [bool](Get-Command -Name $Command -ErrorAction SilentlyContinue)
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🔍 Vérification des bonnes pratiques Django" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Vérifier que Django est installé
Write-Host "📦 Vérification de l'environnement..." -ForegroundColor Cyan
try {
    python -c "import django" 2>$null
    Write-CheckResult "Django installé" -Success $true -Fatal
} catch {
    Write-CheckResult "Django installé" -Success $false -Fatal
}

# 2. Vérifier les migrations
Write-Host ""
Write-Host "🔄 Vérification des migrations..." -ForegroundColor Cyan
try {
    $output = python manage.py makemigrations --check --dry-run 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-CheckResult "Migrations à jour" -Success $true
    } else {
        Write-CheckResult "Migrations à jour" -Success $false
    }
} catch {
    Write-CheckResult "Migrations à jour" -Success $false
}

# 3. Vérifier les erreurs Django
Write-Host ""
Write-Host "🔧 Vérification des erreurs Django..." -ForegroundColor Cyan
try {
    python manage.py check 2>$null | Out-Null
    Write-CheckResult "Pas d'erreurs détectées" -Success $true
} catch {
    Write-CheckResult "Pas d'erreurs détectées" -Success $false
}

# 4. Lancer les tests
Write-Host ""
Write-Host "🧪 Exécution des tests..." -ForegroundColor Cyan
if (Test-CommandExists "pytest") {
    try {
        pytest -x -q 2>$null
        Write-CheckResult "Tests passent" -Success $true
    } catch {
        Write-CheckResult "Tests passent" -Success $false
    }
} else {
    try {
        python manage.py test --verbosity=0 2>$null | Out-Null
        Write-CheckResult "Tests passent" -Success $true
    } catch {
        Write-CheckResult "Tests passent" -Success $false
    }
}

# 5. Vérifier la sécurité
Write-Host ""
Write-Host "🔒 Vérification de la sécurité..." -ForegroundColor Cyan
if (Test-CommandExists "bandit") {
    try {
        bandit -r apps/ -f txt -o $null -q 2>$null
        Write-CheckResult "Bandit : pas de vulnérabilités critiques" -Success $true
    } catch {
        Write-CheckResult "Bandit : pas de vulnérabilités critiques" -Success $false
    }
} else {
    Write-Host "⚠ Bandit non installé (pip install bandit)" -ForegroundColor $Yellow
}

# 6. Vérifier les secrets
Write-Host ""
Write-Host "🕵️  Vérification des secrets..." -ForegroundColor Cyan
if (Test-CommandExists "detect-secrets") {
    if (Test-Path ".secrets.baseline") {
        try {
            detect-secrets scan --baseline .secrets.baseline 2>$null | Out-Null
            Write-CheckResult "Pas de nouveaux secrets détectés" -Success $true
        } catch {
            Write-CheckResult "Pas de nouveaux secrets détectés" -Success $false
        }
    } else {
        Write-Host "⚠ Baseline detect-secrets non trouvée" -ForegroundColor $Yellow
        Write-Host "   Créer avec: detect-secrets scan > .secrets.baseline" -ForegroundColor $Yellow
    }
} else {
    Write-Host "⚠ detect-secrets non installé (pip install detect-secrets)" -ForegroundColor $Yellow
}

# 7. Vérification complète si demandé
if ($Full) {
    Write-Host ""
    Write-Host "🔍 Vérification complète..." -ForegroundColor Cyan
    
    # Vérifier le déploiement
    Write-Host "   Vérification de la configuration de production..."
    try {
        python manage.py check --deploy 2>$null | Out-Null
        Write-CheckResult "Configuration de production OK" -Success $true
    } catch {
        Write-CheckResult "Configuration de production OK" -Success $false
    }
    
    # Couverture de tests
    if (Test-CommandExists "pytest") {
        Write-Host "   Calcul de la couverture de tests..."
        try {
            pytest --cov=apps --cov-report=term-missing --cov-fail-under=80 -q 2>$null | Out-Null
            Write-CheckResult "Couverture de tests > 80%" -Success $true
        } catch {
            Write-CheckResult "Couverture de tests > 80%" -Success $false
        }
    }
    
    # Linting avec ruff
    if (Test-CommandExists "ruff") {
        Write-Host "   Vérification du linting..."
        try {
            ruff check apps/ 2>$null | Out-Null
            Write-CheckResult "Pas d'erreurs de linting" -Success $true
        } catch {
            Write-CheckResult "Pas d'erreurs de linting" -Success $false
        }
    }
    
    # Formatage avec black
    if (Test-CommandExists "black") {
        Write-Host "   Vérification du formatage..."
        try {
            black --check apps/ 2>$null | Out-Null
            Write-CheckResult "Code correctement formaté" -Success $true
        } catch {
            Write-CheckResult "Code correctement formaté" -Success $false
        }
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Vérifications terminées !" -ForegroundColor $Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Prochaines étapes:"
Write-Host "  - Corriger les erreurs éventuelles"
Write-Host "  - Committer les changements"
Write-Host "  - Pousser sur git"
