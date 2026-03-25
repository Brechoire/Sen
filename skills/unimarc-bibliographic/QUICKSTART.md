# UNIMARC & Import Bibliographique - Démarrage Rapide

## Installation rapide

```bash
# Installer les dépendances
pip install pymarc lxml

# Créer les apps Django
cd apps/
django-admin startapp catalog
django-admin startapp authorities
django-admin startapp items
django-admin startapp unimarc_import
```

## Structure des apps

```
apps/
├── catalog/           # Notices (Notice, Collection, Serie, Note)
├── authorities/       # Auteurs, Éditeurs, Sujets, Mots-clés
├── items/            # Exemplaires, Localisations
└── unimarc_import/   # Logique d'import UNIMARC
```

## Mapping PMB → Django

| Zone UNIMARC | Modèle Django | Champ |
|--------------|---------------|-------|
| `001` | Notice | `pmb_id` |
| `200 $a` | Notice | `titre` |
| `200 $e` | Notice | `complement_titre` |
| `010 $a` | Notice | `isbn` |
| `700/701/702` | Auteur (via Contribution) | `nom`, `prenom`, `role` |
| `210/214 $c` | Editeur | `nom` |
| `215 $a` | Notice | `pagination` |
| `300 $a` | Note | `contenu` |
| `330 $a` | Notice | `resume` |
| `606 $a` | Sujet | `terme` |
| `610 $a` | MotCle | `terme` |
| `676 $a` | Notice | `cote_dewey` |
| `900 $n/$a` | Notice | `champs_personnalises` |
| `995 $f` | Exemplaire | `code_barres` |
| `995 $k` | Exemplaire | `cote` |
| `996 $e` | TypeDocument | `nom` |

## Codes de rôle ($4)

```
070 = Auteur principal
090 = Scénariste
100 = Auteur adapté/scénario
440 = Illustrateur
730 = Traducteur
340 = Préfacier
440 = Illustrateur
730 = Traducteur
020 = Directeur de publication
```

## Commandes essentielles

```bash
# Créer les tables
python manage.py makemigrations catalog authorities items unimarc_import
python manage.py migrate

# Créer les données de base (statuts, types)
python manage.py shell << EOF
from apps.items.models import TypeDocument, StatutExemplaire
TypeDocument.objects.get_or_create(code='LIVRE', defaults={'nom': 'Livre'})
TypeDocument.objects.get_or_create(code='BD', defaults={'nom': 'Bande-dessinée'})
StatutExemplaire.objects.get_or_create(
    code='DISPONIBLE',
    defaults={'nom': 'Empruntable', 'empruntable': True}
)
EOF

# Importer un fichier
python manage.py import_unimarc xml/Anor.xml --batch-size=100

# Simulation (sans sauvegarder)
python manage.py import_unimarc xml/Anor.xml --dry-run
```

## Exemple de parsing simple

```python
from apps.unimarc_import.parsers import UnimarcXMLParser

parser = UnimarcXMLParser('xml/Anor.xml')

for notice_data in parser.parse():
    print(f"ID: {notice_data['pmb_id']}")
    print(f"Titre: {notice_data['titre']}")
    print(f"ISBN: {notice_data['isbn']}")
    
    for auteur in notice_data['auteurs']:
        print(f"  Auteur: {auteur['prenom']} {auteur['nom']} (rôle: {auteur['role']})")
    
    for ex in notice_data['exemplaires']:
        print(f"  Exemplaire: {ex['cote']} - {ex['code_barres']}")
```

## Modèles de base

### Notice (catalog)
```python
class Notice(models.Model):
    pmb_id = models.CharField(max_length=50, unique=True)
    isbn = models.CharField(max_length=20, blank=True)
    titre = models.TextField()
    complement_titre = models.TextField(blank=True)
    annee_publication = models.IntegerField(null=True, blank=True)
    resume = models.TextField(blank=True)
    cote_dewey = models.CharField(max_length=20, blank=True)
    auteurs = models.ManyToManyField('authorities.Auteur', through='Contribution')
```

### Auteur (authorities)
```python
class Auteur(models.Model):
    pmb_id = models.CharField(max_length=50, unique=True, null=True)
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255, blank=True)
    nom_complet = models.CharField(max_length=511, db_index=True)
```

### MotCle (authorities)
```python
class MotCle(models.Model):
    terme = models.CharField(max_length=255, db_index=True)
    terme_normalise = models.CharField(max_length=255, db_index=True)
```

### Note (catalog)
```python
class Note(models.Model):
    TYPE_CHOICES = [
        ('general', 'Note générale'),
        ('content', 'Note de contenu'),
    ]
    type_note = models.CharField(max_length=20, choices=TYPE_CHOICES)
    contenu = models.TextField()
```

### Exemplaire (items)
```python
class Exemplaire(models.Model):
    pmb_id = models.CharField(max_length=50, unique=True, null=True)
    notice = models.ForeignKey('catalog.Notice', related_name='exemplaires')
    code_barres = models.CharField(max_length=50, unique=True)
    cote = models.CharField(max_length=50)
    localisation = models.ForeignKey('Localisation')
    statut = models.ForeignKey('StatutExemplaire')
```

## Zones essentielles UNIMARC

### Titres et responsabilités
- `200` : Titre propre ($a), complément ($e)
- `700` : Auteur principal ($a=nom, $b=prénom, $4=role)
- `701` : Co-auteur
- `702` : Auteur secondaire

### Identification
- `001` : Identifiant PMB
- `010` : ISBN
- `009` : Date de création

### Édition
- `210/214` : Lieu ($a), éditeur ($c), date ($d)

### Description
- `215` : Pagination ($a), ill. ($c), dimensions ($d)

### Contenu
- `300` : Note générale ($a)
- `330` : Résumé
- `327` : Contenu détaillé
- `606` : Sujet ($a) - Thésaurus contrôlé
- `610` : Mots-clés libres ($a, séparés par ;)

### Exemplaires (zones PMB)
- `900` : Champs personnalisés PMB (multiples, $n=nom, $a=valeur)
- `995` : Bibliothèque ($a), code-barres ($f), cote ($k)
- `996` : Type doc, statut, localisation
- `999` : Champs personnalisés (date d'acquisition, origine)

## Gestion des erreurs courantes

### Encodage
```python
# Si problème d'encodage
import codecs
with codecs.open('fichier.xml', 'r', encoding='utf-8', errors='ignore') as f:
    # Traiter le fichier
```

### ISBN dupliqués
```python
# Dans la commande d'import
if Notice.objects.filter(isbn=data['isbn']).exists():
    # Mettre à jour plutôt que créer
    pass
```

### Auteurs en double
```python
# Normaliser le nom avant recherche
nom_normalise = auteur_data['nom'].upper().strip()
auteur, created = Auteur.objects.get_or_create(
    nom=nom_normalise,
    prenom=auteur_data['prenom'].strip(),
    defaults={'pmb_id': auteur_data.get('pmb_id')}
)
```

## Checklist import

### Avant
- [ ] Apps créées et migrées
- [ ] Types de document créés (Livre, BD, etc.)
- [ ] Statuts exemplaires créés
- [ ] Fichier XML valide

### Pendant
- [ ] Utiliser --dry-run d'abord
- [ ] Vérifier les logs d'erreur
- [ ] Contrôler les compteurs

### Après
- [ ] Vérifier quelques notices
- [ ] Tester les relations (auteurs, sujets)
- [ ] Vérifier les exemplaires
- [ ] Tester la recherche

## Commandes utiles

```bash
# Compter les notices
python manage.py shell -c "from apps.catalog.models import Notice; print(Notice.objects.count())"

# Vérifier les doublons d'ISBN
python manage.py shell -c "
from apps.catalog.models import Notice
from django.db.models import Count
duplicates = Notice.objects.values('isbn').annotate(count=Count('id')).filter(count__gt=1)
print(list(duplicates))
"

# Exporter un rapport
python manage.py shell -c "
from apps.catalog.models import Notice
for n in Notice.objects.all()[:10]:
    print(f'{n.pmb_id}: {n.titre[:50]} ({n.exemplaires.count()} ex.)')
"
```

## Ressources rapides

- [Documentation pymarc](https://pymarc.readthedocs.io/)
- [Spécification UNIMARC](http://www.bnf.fr/unimarc)
- [Codes de rôle UNIMARC](https://www.ifla.org/unimarc)
