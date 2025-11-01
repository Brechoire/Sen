@echo off
echo Configuration de l'annulation automatique des commandes expirées pour Windows
echo.

REM Créer une tâche planifiée qui s'exécute toutes les heures
echo Création de la tâche planifiée...

REM Remplacer C:\Python\Sen par le chemin réel de votre projet
set PROJECT_PATH=C:\Python\Sen
set PYTHON_PATH=%PROJECT_PATH%\env\Scripts\python.exe
set COMMAND="%PYTHON_PATH%" "%PROJECT_PATH%\manage.py" cancel_expired_orders

REM Créer la tâche planifiée (nécessite des droits administrateur)
schtasks /create /tn "AnnulationCommandesExpirees" /tr "%COMMAND%" /sc hourly /ru "SYSTEM" /f

if %errorlevel% equ 0 (
    echo.
    echo ✓ Tâche planifiée créée avec succès !
    echo   - Nom: AnnulationCommandesExpirees
    echo   - Fréquence: Toutes les heures
    echo   - Commande: %COMMAND%
    echo.
    echo Pour tester manuellement, exécutez:
    echo %COMMAND%
) else (
    echo.
    echo ✗ Erreur lors de la création de la tâche planifiée
    echo   Assurez-vous d'exécuter ce script en tant qu'administrateur
    echo.
    echo Pour exécuter manuellement, utilisez:
    echo %COMMAND%
)

echo.
pause











