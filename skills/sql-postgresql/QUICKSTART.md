# SQL/PostgreSQL - Démarrage Rapide

## Installation

```bash
# Installation PostgreSQL
sudo apt-get install postgresql postgresql-contrib  # Linux
brew install postgresql                            # macOS

# Connexion
psql -U username -d database_name

# Python
pip install psycopg2-binary sqlalchemy
```

## Commandes essentielles

```bash
# Connexion
psql -h localhost -U postgres -d ma_db

# Lister les bases
\l

# Changer de base
\c database_name

# Lister les tables
\dt

# Décrire une table
\d table_name

# Quitter
\q
```

## Checklist requête

### Avant d'écrire
- [ ] Index sur les colonnes filtrées ?
- [ ] Besoin de JOIN ou sous-requête ?
- [ ] Quelles colonnes sont vraiment nécessaires ?

### Après avoir écrit
```sql
-- EXPLAIN ANALYZE pour vérifier les performances
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM users WHERE email = 'test@example.com';
```

## Patterns courants

### Requête de base optimisée
```sql
-- Sélectionner les colonnes nécessaires uniquement
SELECT u.id, u.email, p.name
FROM users u
JOIN profiles p ON u.id = p.user_id
WHERE u.status = 'active'
  AND u.created_at > '2024-01-01'
ORDER BY u.created_at DESC
LIMIT 20;
```

### Insert avec RETURNING
```sql
INSERT INTO users (email, name)
VALUES ('test@example.com', 'John')
RETURNING id, created_at;
```

### Update avec condition
```sql
UPDATE products
SET price = price * 0.9
WHERE category_id = 5
  AND price > 100
RETURNING id, name, price;
```

### Upsert (Insert or Update)
```sql
INSERT INTO users (email, name)
VALUES ('test@example.com', 'John')
ON CONFLICT (email) 
DO UPDATE SET 
    name = EXCLUDED.name,
    updated_at = NOW()
RETURNING *;
```

## Anti-patterns à éviter

```sql
-- ❌ N+1 queries
def get_users_with_orders():
    users = db.query("SELECT * FROM users")
    for user in users:
        orders = db.query(f"SELECT * FROM orders WHERE user_id = {user['id']}")
        
-- ✅ Solution : JOIN
SELECT u.*, o.id as order_id, o.total
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;

-- ❌ SELECT *
SELECT * FROM large_table;

-- ✅ Sélectionner uniquement les colonnes nécessaires
SELECT id, name, email FROM users;

-- ❌ Pas d'index sur les colonnes filtrées fréquemment
-- ✅ Ajouter des indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
```

## Commandes de maintenance

```bash
# Mettre à jour les statistiques
ANALYZE;

# VACUUM pour nettoyer
VACUUM ANALYZE;

# Voir les requêces lentes
SELECT query, calls, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## Sécurité

- Utiliser TOUJOURS des requêtes paramétrées
- Jamais de concaténation de strings SQL
- Vérifier les permissions des rôles
- Activer SSL pour les connexions

## Ressources rapides

- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Explain Analyze](https://explain.dalibo.com/)
- [Use The Index, Luke](https://use-the-index-luke.com/)
