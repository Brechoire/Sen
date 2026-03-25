# Configuration Webhooks PayPal - À faire

> **Date de création** : 25 mars 2026  
> **Branche** : PayPal  
> **Commit** : 329d366

---

## ✅ Ce qui est implémenté

- [x] Endpoint webhook `/api/paypal/webhook/`
- [x] Validation de signature (mode sandbox/debug = permissif)
- [x] Traitement événement `CHECKOUT.ORDER.COMPLETED`
- [x] Traitement événement `PAYMENT.CAPTURE.REFUNDED`
- [x] Modèle `WebhookEvent` pour audit
- [x] Tests complets
- [x] Migration base de données

---

## 🔧 Configuration à faire

### 1. Configurer le webhook dans PayPal Developer

**Environnement Sandbox (test)** :
1. Aller sur https://developer.paypal.com/
2. Dashboard → My Apps & Credentials
3. Sélectionner votre application
4. Onglet "Webhooks" → "Add Webhook"
5. **URL** : `https://votre-site.com/boutique/api/paypal/webhook/`
6. **Événements** :
   - ✅ `CHECKOUT.ORDER.COMPLETED`
   - ✅ `PAYMENT.CAPTURE.REFUNDED`
   - Optionnel : `CHECKOUT.ORDER.APPROVED`
7. Cliquer "Save"
8. **Copier le Webhook ID** (format : `1AB23456CD789012E`)

**Environnement Production** :
- Répéter la même procédure avec l'application Production
- URL doit être en HTTPS

### 2. Variables d'environnement

Ajouter dans `.env` ou variables d'environnement serveur :

```bash
# PayPal (déjà configuré)
PAYPAL_CLIENT_ID=votre_client_id
PAYPAL_CLIENT_SECRET=votre_client_secret
PAYPAL_MODE=sandbox  # ou 'production'
PAYPAL_DEBUG=True    # ou 'False' en production

# NOUVEAU - Webhook ID
PAYPAL_WEBHOOK_ID=votre_webhook_id_copie_ci_dessus
```

### 3. Migrer la base de données

```bash
python manage.py migrate
```

### 4. Tester le webhook

**Méthode 1 : Via PayPal Developer**
1. Dans le dashboard PayPal, onglet Webhooks
2. Cliquer sur le webhook créé
3. "Send Test Event"
4. Sélectionner "Checkout order completed"
5. Vérifier dans l'admin Django que l'événement apparaît

**Méthode 2 : Test réel**
1. Faire un vrai paiement sur le site
2. Fermer le navigateur immédiatement après paiement PayPal
3. Vérifier que la commande est quand même confirmée (via webhook)

---

## 🚨 Important avant mise en production

### Sécurité à implémenter

Le code actuel accepte les webhooks sans validation stricte en mode sandbox.  
**En production**, il faut implémenter la vérification complète de signature :

**Fichier** : `shop/webhooks.py`  
**Fonction** : `verify_paypal_signature()`  
**Ligne** : ~35-60

```python
# TODO: Implémenter la vérification complète pour production
# https://developer.paypal.com/api/rest/webhooks/verify-signature/
```

### Nettoyage des événements

Les événements webhook s'accumulent dans la BDD. Prévoir un cleanup :

```bash
# Supprimer les événements de plus de 30 jours
python manage.py shell -c "
from datetime import timedelta
from django.utils import timezone
from shop.models import WebhookEvent
WebhookEvent.objects.filter(
    created_at__lt=timezone.now() - timedelta(days=30)
).delete()
"
```

Ou créer une commande Django planifiée (cron).

---

## 📝 Endpoints API

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/boutique/api/paypal/webhook/` | POST | Réception webhooks PayPal |
| `/boutique/api/paypal/create-order/` | POST | Créer commande PayPal (déjà existant) |
| `/boutique/api/paypal/capture-order/` | POST | Capturer paiement (déjà existant) |

---

## 🔍 Debugging

### Vérifier les webhooks reçus

**Admin Django** :
- Aller dans `/admin/shop/webhookevent/`
- Voir tous les événements reçus avec leur statut

**Filtres utiles** :
- Status = "failed" → Voir les erreurs
- Event type = "CHECKOUT.ORDER.COMPLETED" → Voir les paiements

### Logs

```bash
# Voir les logs webhook
tail -f logs/django.log | grep webhook

# Ou dans Django Admin → Log entries
```

### Tests

```bash
# Lancer les tests webhook
python manage.py test shop.tests.test_webhooks

# Avec verbose
python manage.py test shop.tests.test_webhooks -v 2
```

---

## ⚠️ Problèmes connus / Limitations

1. **Validation signature** : Non implémentée en production (mode permissif)
2. **Pas de retry** : Si le webhook échoue, PayPal retry automatiquement (jusqu'à 15 fois sur 3 jours)
3. **Pas de file d'attente** : Traitement synchrone (peut ralentir si beaucoup de webhooks)

---

## 🎯 Prochaines améliorations possibles

- [ ] Implémenter validation signature complète en production
- [ ] Ajouter traitement asynchrone (Celery/RQ) pour les webhooks
- [ ] Créer commande de cleanup automatique des vieux événements
- [ ] Ajouter monitoring/alertes si webhooks échouent
- [ ] Interface admin pour rejouer un webhook manuellement
- [ ] Statistiques de webhooks (taux de succès, etc.)

---

## 📚 Documentation utile

- [PayPal Webhooks Overview](https://developer.paypal.com/api/rest/webhooks/)
- [Verify Webhook Signature](https://developer.paypal.com/api/rest/webhooks/verify-signature/)
- [Checkout Webhook Events](https://developer.paypal.com/api/rest/webhooks/checkout-events/)

---

## 👤 Contact

Si problèmes avec les webhooks :
- Vérifier les logs Django
- Vérifier dans PayPal Developer → Webhooks → Recent Events
- Vérifier que l'URL webhook est accessible publiquement (pas de firewall)

---

**Dernière mise à jour** : 25 mars 2026
