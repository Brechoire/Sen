# Système d'annulation automatique des commandes expirées

## 📋 Description

Ce système annule automatiquement les commandes en attente de paiement après 24 heures. Il comprend :

- **Commande Django** : `cancel_expired_orders`
- **Signal automatique** : Vérification lors de la création de nouvelles commandes
- **Scripts de configuration** : Pour Windows et Linux/Mac
- **Script de test** : Pour vérifier le fonctionnement

## 🚀 Utilisation

### 1. Exécution manuelle

```bash
# Voir les commandes qui seraient annulées (mode test)
python manage.py cancel_expired_orders --dry-run

# Annuler les commandes expirées
python manage.py cancel_expired_orders

# Annuler après 12h au lieu de 24h
python manage.py cancel_expired_orders --hours 12
```

### 2. Configuration automatique

#### Windows
```cmd
# Exécuter en tant qu'administrateur
scripts\setup_auto_cancel_windows.bat
```

#### Linux/Mac
```bash
# Rendre exécutable et lancer
chmod +x scripts/setup_auto_cancel_linux.sh
./scripts/setup_auto_cancel_linux.sh
```

### 3. Test du système

```bash
# Tester le fonctionnement complet
python scripts/test_auto_cancel.py
```

## ⚙️ Fonctionnement

### Critères d'annulation
- Statut de commande : `pending`
- Statut de paiement : `pending`
- Âge : Plus de 24h (configurable)

### Actions effectuées
1. **Changement de statut** : `pending` → `cancelled`
2. **Changement de paiement** : `pending` → `failed`
3. **Historique** : Enregistrement du changement avec note automatique
4. **Logs** : Enregistrement des opérations

### Signal automatique
Le signal se déclenche à chaque création de commande et vérifie s'il y a des commandes expirées à nettoyer.

## 📊 Monitoring

### Logs
- **Django** : `logger.info()` pour les annulations réussies
- **Django** : `logger.error()` pour les erreurs
- **Fichier** : `logs/cancel_expired_orders.log` (Linux/Mac)

### Vérification manuelle
```bash
# Compter les commandes en attente
python manage.py shell -c "from shop.models import Order; print(Order.objects.filter(status='pending', payment_status='pending').count())"

# Voir les commandes expirées
python manage.py shell -c "from shop.models import Order; from django.utils import timezone; from datetime import timedelta; cutoff = timezone.now() - timedelta(hours=24); print(Order.objects.filter(status='pending', payment_status='pending', created_at__lt=cutoff).count())"
```

## 🔧 Configuration

### Modifier la durée
```python
# Dans shop/management/commands/cancel_expired_orders.py
parser.add_argument(
    '--hours',
    type=int,
    default=24,  # Changer cette valeur
    help='Nombre d\'heures après lesquelles annuler les commandes',
)
```

### Désactiver le signal automatique
```python
# Dans shop/apps.py
def ready(self):
    # Commenter cette ligne pour désactiver
    # import shop.signals
    pass
```

## 🚨 Dépannage

### Problèmes courants

1. **Signal ne se déclenche pas**
   - Vérifier que `shop.apps.ShopConfig` est dans `INSTALLED_APPS`
   - Redémarrer le serveur Django

2. **Tâche planifiée ne fonctionne pas**
   - Vérifier les permissions (Windows : administrateur)
   - Vérifier le chemin vers Python et manage.py
   - Consulter les logs de la tâche planifiée

3. **Commandes non annulées**
   - Vérifier les critères (statut, âge)
   - Exécuter en mode `--dry-run` pour diagnostiquer
   - Vérifier les logs Django

### Logs utiles
```bash
# Voir les logs Django
tail -f logs/django.log

# Voir les logs de la tâche (Linux/Mac)
tail -f logs/cancel_expired_orders.log

# Voir les tâches planifiées (Windows)
schtasks /query /tn "AnnulationCommandesExpirees"
```

## 📈 Statistiques

Le système enregistre :
- Nombre de commandes annulées
- Date/heure d'annulation
- Raison de l'annulation
- Utilisateur responsable (système automatique)

Ces informations sont disponibles dans :
- `OrderStatusHistory` (historique des changements)
- Logs Django
- Logs de la tâche planifiée



