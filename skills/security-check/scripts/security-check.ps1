# Script de verification de securite pre-push
# Usage: .\security-check.ps1 [-Full] [-CI]
# Options:
#   -Full    : Scan complet incluant l'historique git
#   -Quick   : Verification rapide (defaut)
#   -CI      : Mode CI (sortie JSON uniquement)

param(
    [switch]$Full,
    [switch]$Quick = $true,
    [switch]$CI
)

# Si -Full est specifie, desactiver le mode quick
if ($Full) {
    $Quick = $false
}

# Couleurs pour l'affichage
$Red = "`e[0;31m"
$Green = "`e[0;32m"
$Yellow = "`e[1;33m"
$Blue = "`e[0;34m"
$NC = "`e[0m"  # No Color

# Variables
$ExitCode = 0
$ReportsDir = "security-reports"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Fonctions d'affichage
function Print-Header {
    param([string]$Message)
    if (-not $CI) {
        Write-Host ""
        Write-Host "========================================"
        Write-Host $Message
        Write-Host "========================================"
    }
}

function Print-Success {
    param([string]$Message)
    if (-not $CI) {
        Write-Host "$Green[OK] $Message$NC"
    }
}

function Print-Warning {
    param([string]$Message)
    if (-not $CI) {
        Write-Host "$Yellow[!] $Message$NC"
    }
}

function Print-Error {
    param([string]$Message)
    if (-not $CI) {
        Write-Host "$Red[X] $Message$NC"
    }
}

function Print-Info {
    param([string]$Message)
    if (-not $CI) {
        Write-Host "$Blue[i] $Message$NC"
    }
}

# Verification des dependances
function Check-Dependencies {
    Print-Header "Verification des dependances"
    
    $MissingDeps = @()
    
    if (-not (Get-Command detect-secrets -ErrorAction SilentlyContinue)) {
        $MissingDeps += "detect-secrets"
    }
    
    if (-not (Get-Command bandit -ErrorAction SilentlyContinue)) {
        $MissingDeps += "bandit"
    }
    
    if (-not (Get-Command pip-audit -ErrorAction SilentlyContinue)) {
        $MissingDeps += "pip-audit"
    }
    
    if ($MissingDeps.Count -gt 0) {
        Print-Error "Outils manquants: $($MissingDeps -join ', ')"
        Print-Info "Installation: pip install detect-secrets bandit pip-audit"
        exit 1
    }
    
    Print-Success "Toutes les dependances sont installees"
}

# Creation du dossier de rapports
function Setup-ReportsDir {
    if ($CI) {
        New-Item -ItemType Directory -Force -Path $ReportsDir | Out-Null
    }
}

# Verification des secrets avec detect-secrets
function Check-Secrets {
    Print-Header "1. Verification des secrets (detect-secrets)"
    
    if (-not (Test-Path ".secrets.baseline")) {
        Print-Warning "Fichier .secrets.baseline non trouve"
        Print-Info "Creation de la baseline..."
        detect-secrets scan | Out-File -FilePath ".secrets.baseline" -Encoding UTF8
        Print-Success "Baseline creee: .secrets.baseline"
        Print-Warning "Verifiez ce fichier et committez-le"
    }
    
    if ($Full) {
        Print-Info "Scan complet de l'historique git..."
        $Output = detect-secrets scan --all-files --force-use-all-plugins --baseline .secrets.baseline 2>&1
        if ($LASTEXITCODE -eq 0) {
            Print-Success "Aucun secret trouve dans l'historique"
        } else {
            Print-Error "Secrets trouves dans l'historique !"
            Write-Host $Output
            $script:ExitCode = 1
        }
    } else {
        Print-Info "Scan des fichiers actuels..."
        $Output = detect-secrets scan --baseline .secrets.baseline 2>&1
        if ($LASTEXITCODE -eq 0) {
            Print-Success "Aucun nouveau secret detecte"
        } else {
            Print-Error "Nouveaux secrets detectes !"
            Write-Host $Output
            Print-Info "Executez 'detect-secrets audit .secrets.baseline' pour examiner"
            $script:ExitCode = 1
        }
    }
    
    if ($CI) {
        detect-secrets scan --baseline .secrets.baseline --json 2>$null | Out-File -FilePath "$ReportsDir\secrets-$Timestamp.json" -Encoding UTF8
    }
}

# Analyse de securite avec bandit
function Check-Bandit {
    Print-Header "2. Analyse de securite du code (bandit)"
    
    $BanditArgs = @("-r", ".")
    
    if ($CI) {
        $BanditArgs += @("-f", "json", "-o", "$ReportsDir\bandit-$Timestamp.json")
    }
    
    # Exclure les repertoires courants
    $BanditArgs += @("-x", "./tests,./venv,./.venv,./env,./__pycache__,./build,./dist,./node_modules")
    
    Print-Info "Execution de bandit..."
    
    $Output = bandit @BanditArgs -ll 2>&1
    $BanditExit = $LASTEXITCODE
    
    if ($BanditExit -eq 0) {
        Print-Success "Aucune vulnerabilite HIGH/CRITICAL detectee"
    } else {
        Print-Error "Vulnerabilites detectees !"
        if (-not $CI) {
            bandit -r . -x ./tests,./venv,./.venv,./env,./__pycache__ -ll 2>$null | Write-Host
        }
        $script:ExitCode = 1
    }
}

# Verification des dependances avec pip-audit
function Check-DependenciesVulns {
    Print-Header "3. Verification des dependances (pip-audit)"
    
    $AuditArgs = @()
    
    if ($CI) {
        $AuditArgs += @("-f", "json", "-o", "$ReportsDir\pip-audit-$Timestamp.json")
    } else {
        $AuditArgs += "--desc"
    }
    
    if (Test-Path "requirements.txt") {
        Print-Info "Audit de requirements.txt..."
        $Output = pip-audit -r requirements.txt @AuditArgs 2>&1
        $AuditExit = $LASTEXITCODE
        
        if ($AuditExit -eq 0) {
            Print-Success "Aucune vulnerabilite dans les dependances"
        } else {
            Print-Error "Vulnerabilites detectees dans les dependances !"
            if (-not $CI) {
                pip-audit -r requirements.txt --desc 2>$null | Write-Host
            }
            $script:ExitCode = 1
        }
    } elseif (Test-Path "pyproject.toml") {
        Print-Info "Audit de pyproject.toml..."
        $Output = pip-audit @AuditArgs 2>&1
        $AuditExit = $LASTEXITCODE
        
        if ($AuditExit -eq 0) {
            Print-Success "Aucune vulnerabilite dans les dependances"
        } else {
            Print-Error "Vulnerabilites detectees dans les dependances !"
            if (-not $CI) {
                pip-audit --desc 2>$null | Write-Host
            }
            $script:ExitCode = 1
        }
    } else {
        Print-Warning "Aucun fichier requirements.txt ou pyproject.toml trouve"
        Print-Info "Audit des packages installes..."
        $Output = pip-audit @AuditArgs 2>&1
        $AuditExit = $LASTEXITCODE
        
        if ($AuditExit -eq 0) {
            Print-Success "Aucune vulnerabilite detectee"
        } else {
            Print-Error "Vulnerabilites detectees !"
            $script:ExitCode = 1
        }
    }
}

# Verification des fichiers sensibles
function Check-SensitiveFiles {
    Print-Header "4. Verification des fichiers sensibles"
    
    $SensitiveFiles = @()
    
    # Verifier les fichiers traques par git
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $GitFiles = git ls-files 2>$null | Where-Object { 
            $_ -match '\.(env|key|pem|p12|pfx)$' -or 
            $_ -match '^(id_rsa|id_dsa|id_ecdsa|id_ed25519|.htpasswd|.netrc)$'
        }
        
        if ($GitFiles) {
            $SensitiveFiles += $GitFiles
        }
    }
    
    if ($SensitiveFiles.Count -eq 0) {
        Print-Success "Aucun fichier sensible traque par git"
    } else {
        Print-Error "Fichiers sensibles traques par git :"
        foreach ($file in $SensitiveFiles) {
            Write-Host "  - $file"
        }
        Print-Info "Ajoutez ces fichiers a .gitignore et retirez-les avec: git rm --cached <fichier>"
        $script:ExitCode = 1
    }
}

# Verification du .gitignore
function Check-Gitignore {
    Print-Header "5. Verification du .gitignore"
    
    if (-not (Test-Path ".gitignore")) {
        Print-Error "Fichier .gitignore non trouve !"
        Print-Info "Creez un .gitignore avec les regles de base"
        $script:ExitCode = 1
        return
    }
    
    $RequiredPatterns = @(
        ".env",
        "*.key",
        "*.pem",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        "venv/"
    )
    
    $MissingPatterns = @()
    $GitignoreContent = Get-Content ".gitignore" -Raw
    
    foreach ($pattern in $RequiredPatterns) {
        if ($GitignoreContent -notmatch [regex]::Escape($pattern)) {
            $MissingPatterns += $pattern
        }
    }
    
    if ($MissingPatterns.Count -eq 0) {
        Print-Success ".gitignore correctement configure"
    } else {
        Print-Warning "Patterns manquants dans .gitignore :"
        foreach ($pattern in $MissingPatterns) {
            Write-Host "  - $pattern"
        }
        Print-Info "Ajoutez ces patterns a votre .gitignore"
    }
}

# Scan de l'historique git (mode full uniquement)
function Check-GitHistory {
    if (-not $Full) {
        return
    }
    
    Print-Header "6. Scan de l'historique git (mode full)"
    
    Print-Info "Recherche de gros fichiers..."
    
    try {
        $LargeFiles = git rev-list --objects --all 2>$null | 
            git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' 2>$null |
            Where-Object { $_ -match '^blob\s+\S+\s+(\d+)' -and [int]$matches[1] -gt 10485760 } |
            Sort-Object { [int]($_ -split '\s+')[2] } -Descending |
            Select-Object -First 10
        
        if (-not $LargeFiles) {
            Print-Success "Aucun gros fichier (>10MB) dans l'historique"
        } else {
            Print-Warning "Gros fichiers detectes dans l'historique :"
            $LargeFiles | ForEach-Object { Write-Host "  $_" }
            Print-Info "Ces fichiers peuvent contenir des secrets binaires"
        }
    } catch {
        Print-Warning "Impossible de scanner l'historique git"
    }
}

# Generation du rapport final
function Generate-Report {
    if ($CI) {
        Print-Header "Rapports generes"
        Write-Host "Les rapports JSON sont disponibles dans: $ReportsDir\"
        Get-ChildItem "$ReportsDir\" -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "  - $($_.Name)"
        }
    }
}

# Resume final
function Print-Summary {
    if (-not $CI) {
        Write-Host ""
        Write-Host "========================================"
        Write-Host "RESUME"
        Write-Host "========================================"
        
        if ($ExitCode -eq 0) {
            Print-Success "Toutes les verifications sont passees !"
            Print-Info "Vous pouvez push en toute securite"
            Write-Host ""
            Write-Host "Commande: git push"
        } else {
            Print-Error "Des problemes de securite ont ete detectes !"
            Print-Info "Corrigez les problemes avant de push"
            Write-Host ""
            Write-Host "Pour ignorer temporairement (deconseille):"
            Write-Host "  git push --no-verify"
        }
    }
}

# Fonction principale
function Main {
    if (-not $CI) {
        Write-Host ""
        Write-Host "+------------------------------------------------+"
        Write-Host "|   [SECURITY CHECK] Pre-Push Security Check   |"
        Write-Host "+------------------------------------------------+"
        
        if ($Full) {
            Write-Host "Mode: Scan complet"
        } else {
            Write-Host "Mode: Verification rapide"
        }
        Write-Host ""
    }
    
    Check-Dependencies
    Setup-ReportsDir
    Check-Secrets
    Check-Bandit
    Check-DependenciesVulns
    Check-SensitiveFiles
    Check-Gitignore
    Check-GitHistory
    Generate-Report
    Print-Summary
    
    exit $ExitCode
}

# Execution
Main
