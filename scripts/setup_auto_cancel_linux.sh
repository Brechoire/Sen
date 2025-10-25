#!/bin/bash

echo "Configuration de l'annulation automatique des commandes expirées pour Linux/Mac"
echo

# Chemin O2Switch (à adapter selon votre configuration)
PROJECT_PATH="/home/[votre-nom-utilisateur]/[nom-du-site]"
PYTHON_PATH="$PROJECT_PATH/venv/bin/python"
COMMAND="$PYTHON_PATH $PROJECT_PATH/manage.py cancel_expired_orders"

echo "Création du script cron..."

# Créer le script d'exécution
cat > "$PROJECT_PATH/cancel_expired_orders.sh" << EOF
#!/bin/bash
cd $PROJECT_PATH
$COMMAND >> logs/cancel_expired_orders.log 2>&1
EOF

chmod +x "$PROJECT_PATH/cancel_expired_orders.sh"

# Créer le répertoire de logs s'il n'existe pas
mkdir -p "$PROJECT_PATH/logs"

# Ajouter la tâche cron (s'exécute toutes les heures)
(crontab -l 2>/dev/null; echo "0 * * * * $PROJECT_PATH/cancel_expired_orders.sh") | crontab -

if [ $? -eq 0 ]; then
    echo
    echo "✓ Configuration terminée avec succès !"
    echo "  - Script créé: $PROJECT_PATH/cancel_expired_orders.sh"
    echo "  - Cron configuré: Exécution toutes les heures"
    echo "  - Logs: $PROJECT_PATH/logs/cancel_expired_orders.log"
    echo
    echo "Pour tester manuellement:"
    echo "$COMMAND"
    echo
    echo "Pour voir les tâches cron:"
    echo "crontab -l"
else
    echo
    echo "✗ Erreur lors de la configuration"
    echo "  Assurez-vous d'avoir les permissions nécessaires"
fi

echo
