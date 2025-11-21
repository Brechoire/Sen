#!/bin/bash

echo "=== Déploiement sur O2Switch ==="
echo

# Configuration
PROJECT_NAME="[nom-du-site]"
USERNAME="[votre-nom-utilisateur]"
DOMAIN="[votre-domaine]"

echo "Configuration:"
echo "  - Projet: $PROJECT_NAME"
echo "  - Utilisateur: $USERNAME"
echo "  - Domaine: $DOMAIN"
echo

# 1. Connexion SSH et préparation
echo "1. Connexion SSH..."
ssh $USERNAME@$DOMAIN << 'EOF'
    # Aller dans le répertoire du projet
    cd /home/$USER/$PROJECT_NAME
    
    # Créer l'environnement virtuel s'il n'existe pas
    if [ ! -d "venv" ]; then
        echo "Création de l'environnement virtuel..."
        python3 -m venv venv
    fi
    
    # Activer l'environnement virtuel
    source venv/bin/activate
    
    # Installer les dépendances
    echo "Installation des dépendances..."
    pip install -r requirements.txt
    
    # Appliquer les migrations
    echo "Application des migrations..."
    python manage.py migrate
    
    # Collecter les fichiers statiques
    echo "Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput
    
    # Créer le répertoire de logs
    mkdir -p logs
    
    echo "✓ Configuration de base terminée"
EOF

# 2. Configuration du cron
echo "2. Configuration du cron..."
ssh $USERNAME@$DOMAIN << 'EOF'
    cd /home/$USER/$PROJECT_NAME
    
    # Créer le script d'exécution
    cat > cancel_expired_orders.sh << 'SCRIPT_EOF'
#!/bin/bash
cd /home/$USER/$PROJECT_NAME
source venv/bin/activate
python manage.py cancel_expired_orders >> logs/cancel_expired_orders.log 2>&1
SCRIPT_EOF
    
    chmod +x cancel_expired_orders.sh
    
    # Ajouter la tâche cron
    (crontab -l 2>/dev/null; echo "0 * * * * /home/$USER/$PROJECT_NAME/cancel_expired_orders.sh") | crontab -
    
    echo "✓ Cron configuré"
EOF

# 3. Test
echo "3. Test du système..."
ssh $USERNAME@$DOMAIN << 'EOF'
    cd /home/$USER/$PROJECT_NAME
    source venv/bin/activate
    
    # Test de la commande
    echo "Test de la commande d'annulation..."
    python manage.py cancel_expired_orders --dry-run
    
    echo "✓ Test terminé"
EOF

echo
echo "=== Déploiement terminé ==="
echo
echo "Vérifications à faire:"
echo "1. Vérifier que le site fonctionne: https://$DOMAIN"
echo "2. Tester une commande et vérifier l'annulation automatique"
echo "3. Vérifier les logs: ssh $USERNAME@$DOMAIN 'tail -f /home/$USER/$PROJECT_NAME/logs/cancel_expired_orders.log'"
echo



















