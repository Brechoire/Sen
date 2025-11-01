#!/bin/bash

echo "Configuration de l'annulation automatique pour O2Switch"
echo

# Configuration O2Switch
PROJECT_PATH="/home/[votre-nom-utilisateur]/[nom-du-site]"
PYTHON_PATH="$PROJECT_PATH/venv/bin/python"
COMMAND="$PYTHON_PATH $PROJECT_PATH/manage.py cancel_expired_orders"

echo "IMPORTANT: Remplacez [votre-nom-utilisateur] et [nom-du-site] par vos vraies valeurs !"
echo "Exemple: /home/monsite/monprojet"
echo

read -p "Entrez le chemin complet de votre projet: " PROJECT_PATH
PYTHON_PATH="$PROJECT_PATH/venv/bin/python"
COMMAND="$PYTHON_PATH $PROJECT_PATH/manage.py cancel_expired_orders"

echo "Création du script d'exécution..."

# Créer le script d'exécution
cat > "$PROJECT_PATH/cancel_expired_orders.sh" << EOF
#!/bin/bash
cd $PROJECT_PATH
source venv/bin/activate
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
    echo "cd $PROJECT_PATH && source venv/bin/activate && python manage.py cancel_expired_orders"
    echo
    echo "Pour voir les tâches cron:"
    echo "crontab -l"
else
    echo
    echo "✗ Erreur lors de la configuration"
    echo "  Assurez-vous d'avoir les permissions nécessaires"
fi

echo











