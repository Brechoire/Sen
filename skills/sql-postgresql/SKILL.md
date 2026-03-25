# Skill : Bonnes Pratiques SQL/PostgreSQL

## Objectif

Ce skill permet d'écrire des requêtes SQL optimisées et sécurisées avec PostgreSQL. Il couvre la modélisation, l'optimisation des performances, la sécurité et les bonnes pratiques de la communauté.

## Quand utiliser ce skill

- Conception de schémas de base de données
- Optimisation de requêtes lentes
- Migration de données
- Configuration PostgreSQL
- Revue de code SQL

## Architecture et modélisation

### Structure de schéma recommandée

```sql
-- Utiliser des schémas pour organiser les données
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS archive;

-- Set search path
SET search_path TO app, public;
```

### Conventions de nommage

```sql
-- Tables : pluriel, snake_case
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Colonnes : snake_case, éviter les abréviations
-- ❌ Mauvais
CREATE TABLE usr (
    uid SERIAL PRIMARY KEY,
    em VARCHAR(100)
);

-- ✅ Bon
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);

-- Index : idx_<table>_<colonne>
CREATE INDEX idx_users_email ON users(email);

-- Contraintes : chk_<table>_<description>
ALTER TABLE users ADD CONSTRAINT chk_users_email_format 
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Clés étrangères : fk_<table>_<table_reference>
ALTER TABLE posts ADD CONSTRAINT fk_posts_user_id 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

## Bonnes pratiques de modélisation

### 1. Types de données

```sql
-- Utiliser les bons types
CREATE TABLE articles (
    id BIGSERIAL PRIMARY KEY,                    -- Auto-incrément 64-bit
    title VARCHAR(255) NOT NULL,                 -- Texte court avec limite
    content TEXT,                                -- Texte long illimité
    price DECIMAL(10, 2),                        -- Précision monétaire
    is_published BOOLEAN DEFAULT FALSE,          -- Flag booléen
    published_at TIMESTAMPTZ,                    -- Timestamp avec timezone
    tags TEXT[],                                 -- Array PostgreSQL
    metadata JSONB,                              -- JSON binaire (indexable)
    search_vector TSVECTOR,                      -- Pour recherche full-text
    
    -- Contraintes
    CONSTRAINT chk_articles_price_positive CHECK (price >= 0)
);

-- Enumérations
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended');

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    status user_status DEFAULT 'active',
    -- ...
);
```

### 2. Normalisation

```sql
-- ❌ Mauvais : données redondantes
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100),
    customer_email VARCHAR(100),
    product_name VARCHAR(100),
    product_price DECIMAL(10,2)
);

-- ✅ Bon : normalisation 3NF
CREATE TABLE customers (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL
);

CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT REFERENCES customers(id),
    order_date TIMESTAMPTZ DEFAULT NOW(),
    total_amount DECIMAL(10,2)
);

CREATE TABLE order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT REFERENCES orders(id),
    product_id BIGINT REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL
);
```

### 3. Indexation stratégique

```sql
-- Index B-tree (défaut) pour égalité et range
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Index composite pour requêtes multi-colonnes
CREATE INDEX idx_orders_customer_date ON orders(customer_id, created_at DESC);

-- Index partiel pour les données fréquemment filtrées
CREATE INDEX idx_orders_pending ON orders(status) WHERE status = 'pending';

-- Index GIN pour JSONB et arrays
CREATE INDEX idx_articles_metadata ON articles USING GIN(metadata);
CREATE INDEX idx_articles_tags ON articles USING GIN(tags);

-- Index pour recherche full-text
CREATE INDEX idx_articles_search ON articles USING GIN(search_vector);

-- Index d'unicité partiel
CREATE UNIQUE INDEX idx_users_active_email ON users(email) WHERE status = 'active';

-- Expression index
CREATE INDEX idx_users_email_lower ON users(LOWER(email));
```

## Requêtes optimisées

### 1. Requêtes de base efficaces

```sql
-- ❌ Mauvais : SELECT *
SELECT * FROM users WHERE email = 'test@example.com';

-- ✅ Bon : sélectionner uniquement les colonnes nécessaires
SELECT id, email, created_at FROM users WHERE email = 'test@example.com';

-- ✅ Encore mieux : utiliser des requêtes préparées (depuis l'application)
-- Django ORM, SQLAlchemy, etc. gèrent ça automatiquement
```

### 2. Jointures optimisées

```sql
-- ❌ Mauvais : sous-requête corrélée lente
SELECT 
    c.name,
    (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id) as order_count
FROM customers c;

-- ✅ Bon : jointure avec GROUP BY
SELECT 
    c.name,
    COUNT(o.id) as order_count
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name;

-- ❌ Mauvais : jointure sans condition
SELECT * FROM orders o, customers c WHERE o.customer_id = c.id;

-- ✅ Bon : jointure explicite avec JOIN
SELECT o.id, o.total_amount, c.name
FROM orders o
INNER JOIN customers c ON o.customer_id = c.id
WHERE o.created_at > '2024-01-01';
```

### 3. Agrégations et fenêtres

```sql
-- Statistiques par catégorie
SELECT 
    category_id,
    COUNT(*) as product_count,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price
FROM products
GROUP BY category_id;

-- Fonctions de fenêtre pour classements
SELECT 
    id,
    name,
    price,
    category_id,
    ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY price DESC) as rank_in_category,
    AVG(price) OVER (PARTITION BY category_id) as category_avg_price,
    price - AVG(price) OVER (PARTITION BY category_id) as diff_from_avg
FROM products;

-- Cumulative sum
SELECT 
    date_trunc('month', created_at) as month,
    SUM(amount) as monthly_revenue,
    SUM(SUM(amount)) OVER (ORDER BY date_trunc('month', created_at)) as cumulative_revenue
FROM orders
GROUP BY date_trunc('month', created_at);
```

### 4. Recherche full-text

```sql
-- Créer la colonne TSVECTOR
ALTER TABLE articles ADD COLUMN search_vector TSVECTOR;

-- Créer un index
CREATE INDEX idx_articles_search ON articles USING GIN(search_vector);

-- Mettre à jour la colonne (à faire dans un trigger)
UPDATE articles 
SET search_vector = 
    setweight(to_tsvector('french', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('french', COALESCE(content, '')), 'B') ||
    setweight(to_tsvector('french', COALESCE(tags::text, '')), 'C');

-- Recherche avec ranking
SELECT 
    id,
    title,
    ts_rank_cd(search_vector, query) as rank
FROM articles, 
     plainto_tsquery('french', 'python django') query
WHERE search_vector @@ query
ORDER BY rank DESC
LIMIT 10;
```

## Optimisation des performances

### 1. Analyser les requêtes lentes

```sql
-- Activer le logging des requêtes lentes (postgresql.conf)
-- log_min_duration_statement = 1000  -- 1 seconde

-- EXPLAIN ANALYZE pour analyser une requête
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT o.*, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.created_at > '2024-01-01'
ORDER BY o.created_at DESC
LIMIT 100;

-- Voir les requêces lentes en cours
SELECT 
    pid,
    now() - query_start as duration,
    query
FROM pg_stat_activity
WHERE state = 'active' 
  AND query NOT LIKE '%pg_stat_activity%'
ORDER BY duration DESC;
```

### 2. Maintenance de la base

```sql
-- Mettre à jour les statistiques
ANALYZE VERBOSE;

-- Réindexer (peut bloquer les écritures sur les tables importantes)
REINDEX INDEX CONCURRENTLY idx_users_email;

-- VACUUM pour récupérer l'espace
VACUUM ANALYZE;

-- VACUUM FULL (bloque la table, à faire en maintenance)
VACUUM FULL;

-- Reconstruire les statistiques sur une table spécifique
ANALYZE orders;
```

### 3. Partitionnement

```sql
-- Partitionnement par date pour les logs
CREATE TABLE events (
    id BIGSERIAL,
    event_type VARCHAR(50),
    data JSONB,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Créer les partitions
CREATE TABLE events_2024_01 PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE events_2024_02 PARTITION OF events
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Partitionnement par liste
CREATE TABLE users_by_region (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100),
    region VARCHAR(20)
) PARTITION BY LIST (region);

CREATE TABLE users_europe PARTITION OF users_by_region
    FOR VALUES IN ('EU', 'UK', 'FR', 'DE');

CREATE TABLE users_americas PARTITION OF users_by_region
    FOR VALUES IN ('US', 'CA', 'BR', 'MX');
```

## Sécurité

### 1. Requêtes paramétrées (obligatoire)

```python
# ❌ JAMAIS faire ça (injection SQL)
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")

# ✅ Python avec psycopg2
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# ✅ Django ORM (protégé automatiquement)
User.objects.filter(email=email)

# ✅ SQLAlchemy
session.query(User).filter(User.email == email)
```

### 2. Gestion des droits

```sql
-- Créer des rôles avec le minimum de privilèges
CREATE ROLE app_read;
CREATE ROLE app_write;
CREATE ROLE app_admin;

-- Accorder les droits
GRANT USAGE ON SCHEMA app TO app_read;
GRANT SELECT ON ALL TABLES IN SCHEMA app TO app_read;

GRANT USAGE ON SCHEMA app TO app_write;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO app_write;

-- Rôle pour l'application
CREATE USER app_user WITH PASSWORD 'secure_password';
GRANT app_write TO app_user;

-- Révoquer les droits publics
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
```

### 3. Masquage des données sensibles

```sql
-- Créer une vue avec masquage
CREATE VIEW users_masked AS
SELECT 
    id,
    CONCAT(LEFT(email, 2), '***@***.***') as email_masked,
    created_at
FROM users;

-- Accorder l'accès uniquement à la vue
GRANT SELECT ON users_masked TO analyst_role;

-- Row Level Security (RLS)
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_documents_policy ON documents
    FOR ALL
    TO app_user
    USING (user_id = current_setting('app.current_user_id')::bigint);
```

## Bonnes pratiques spécifiques PostgreSQL

### 1. Utiliser les fonctionnalités avancées

```sql
-- Table inheritance (attention aux limitations)
CREATE TABLE cities (
    name TEXT,
    population INTEGER,
    elevation INTEGER
);

CREATE TABLE capitals (
    state CHAR(2)
) INHERITS (cities);

-- Lateral joins
SELECT 
    u.id,
    u.email,
    recent_orders.order_id,
    recent_orders.total
FROM users u
LEFT JOIN LATERAL (
    SELECT id as order_id, total_amount as total
    FROM orders
    WHERE customer_id = u.id
    ORDER BY created_at DESC
    LIMIT 3
) recent_orders ON true;

-- CTE récursives pour hiérarchies
WITH RECURSIVE category_tree AS (
    SELECT id, name, parent_id, 0 as level
    FROM categories
    WHERE parent_id IS NULL
    
    UNION ALL
    
    SELECT c.id, c.name, c.parent_id, ct.level + 1
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree;
```

### 2. Triggers et fonctions

```sql
-- Fonction pour mise à jour automatique de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger pour audit
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name TEXT,
    operation TEXT,
    old_data JSONB,
    new_data JSONB,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    changed_by TEXT
);

CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_log (table_name, operation, old_data, changed_by)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), current_user);
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_log (table_name, operation, old_data, new_data, changed_by)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), row_to_json(NEW), current_user);
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_log (table_name, operation, new_data, changed_by)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(NEW), current_user);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_audit
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger();
```

## Checklist avant mise en production

### Schéma
- [ ] Contraintes d'intégrité définies (PK, FK, CHECK, UNIQUE)
- [ ] Index créés pour les colonnes fréquemment filtrées/jointes
- [ ] Types de données appropriés utilisés
- [ ] Valeurs par défaut définies
- [ ] NOT NULL sur les colonnes obligatoires

### Sécurité
- [ ] Requêtes paramétrées uniquement
- [ ] Rôles avec privilèges minimaux
- [ ] Pas de mot de passe en dur dans le code
- [ ] Connexions SSL/TLS
- [ ] Row Level Security si nécessaire

### Performance
- [ ] EXPLAIN ANALYZE sur les requêtes principales
- [ ] Index appropriés créés
- [ ] Partitionnement pour les grandes tables
- [ ] Configuration PostgreSQL optimisée
- [ ] Statistiques à jour (ANALYZE)

### Maintenance
- [ ] Backups automatisés configurés
- [ ] Monitoring des requêtes lentes activé
- [ ] Plan de VACUUM régulier
- [ ] Documentation du schéma

## Commandes utiles

```bash
# Connexion
psql -h localhost -U username -d database_name

# Dump et restore
pg_dump -h localhost -U username database_name > backup.sql
psql -h localhost -U username database_name < backup.sql

# Dump compressé
pg_dump -h localhost -U username database_name | gzip > backup.sql.gz
gunzip < backup.sql.gz | psql -h localhost -U username database_name

# Taille des tables
psql -c "SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) 
         FROM pg_catalog.pg_statio_user_tables 
         ORDER BY pg_total_relation_size(relid) DESC;"

# Statistiques de connexion
psql -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Réinitialiser les statistiques
psql -c "SELECT pg_stat_reset();"

# Vérifier les locks
psql -c "SELECT * FROM pg_locks WHERE NOT granted;"
```

## Ressources

- [Documentation PostgreSQL](https://www.postgresql.org/docs/)
- [PostgreSQL Exercises](https://pgexercises.com/)
- [Use The Index, Luke](https://use-the-index-luke.com/)
- [PostgreSQL Wiki - Optimization](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [pgMustard - Explain Analyze visualizer](https://pgmustard.com/)
