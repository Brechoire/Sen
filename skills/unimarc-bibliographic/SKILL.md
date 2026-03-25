# Skill : UNIMARC & Import de Données Bibliographiques

## Objectif

Ce skill permet d'importer et gérer des notices bibliographiques et exemplaires au format UNIMARC depuis PMB (ou autres sources) vers une application Django avec une architecture modulaire et découplée.

## Quand utiliser ce skill

- Migration depuis PMB vers Django
- Import de catalogues bibliographiques
- Intégration de données UNIMARC
- Développement d'un SIGB (Système Intégré de Gestion de Bibliothèque)

## Architecture des Apps Django

### Structure recommandée

```
apps/
├── catalog/                    # Notices bibliographiques
│   ├── models.py              # Notice, Collection, Serie
│   ├── admin.py
│   └── urls.py
├── authorities/                # Entités d'autorité
│   ├── models.py              # Auteur, Editeur, Sujet
│   ├── admin.py
│   └── urls.py
├── items/                      # Exemplaires (copies physiques)
│   ├── models.py              # Exemplaire, Localisation, Statut
│   ├── admin.py
│   └── urls.py
└── unimarc_import/            # Logique d'import
    ├── models.py              # ImportBatch, ImportLog
    ├── parsers.py             # Parsing pymarc
    ├── mappers.py             # Mapping UNIMARC → Django
    └── management/
        └── commands/
            └── import_unimarc.py
```

### Relations entre modèles

```
Notice (catalog)
├── ManyToMany → Auteur (authorities) via Contribution
├── ManyToMany → Sujet (authorities)
├── ForeignKey → Editeur (authorities)
├── ForeignKey → Collection (catalog)
├── ForeignKey → Serie (catalog)
└── OneToMany  → Exemplaire (items)

Exemplaire (items)
├── ForeignKey → Notice (catalog)
├── ForeignKey → Localisation (items)
└── ForeignKey → Statut (items)
```

## Fondamentaux UNIMARC

### Structure d'une notice UNIMARC XML (format PMB)

```xml
<?xml version="1.0" encoding="utf-8"?>
<unimarc>
  <notice>
    <rs>n</rs>                    <!-- Type de notice -->
    <dt>a</dt>                    <!-- Type de document -->
    <bl>m</bl>                    <!-- Niveau bibliographique -->
    <hl>0</hl>                    <!-- Niveau hiérarchique -->
    <el>1</el>                    <!-- Elaboration -->
    <ru>i</ru>                    <!-- Règles utilisées -->
    
    <!-- Zones de contrôle -->
    <f c="001">90</f>            <!-- Identifiant PMB -->
    <f c="009">
      <s c="a">2001-01-01</s>    <!-- Date de création -->
    </f>
    
    <!-- Zone 100 : données codées -->
    <f c="100" ind="  ">
      <s c="a">20030901u        u  u0frey50      ba</s>
    </f>
    
    <!-- Zone 200 : titre -->
    <f c="200" ind="1 ">
      <s c="a">Dictionnaire compact français/allemand</s>
    </f>
    
    <!-- Zone 010 : ISBN -->
    <f c="010" ind="  ">
      <s c="a">978-2-03-540008-6</s>
    </f>
    
    <!-- Zone 101 : langue -->
    <f c="101" ind="0 ">
      <s c="a">fre</s>
    </f>
    
    <!-- Zone 215 : description physique -->
    <f c="215" ind="  ">
      <s c="a">628 p.</s>
      <s c="d">20 cm</s>
    </f>
    
    <!-- Zone 700 : auteur principal -->
    <f c="700" ind=" 1">
      <s c="a">Watterson</s>
      <s c="b">Bill</s>
      <s c="4">070</s>             <!-- Code rôle : 070 = Auteur -->
      <s c="9">id:40352</s>       <!-- ID PMB -->
    </f>
    
    <!-- Zone 701 : co-auteur -->
    <f c="701" ind=" 1">
      <s c="a">Moynard</s>
      <s c="b">Hélène</s>
      <s c="4">440</s>             <!-- 440 = Illustrateur -->
    </f>
    
    <!-- Zone 210/214 : édition -->
    <f c="210" ind="  ">
      <s c="a">Paris</s>          <!-- Lieu -->
      <s c="c">Larousse</s>       <!-- Éditeur -->
      <s c="d">2001</s>           <!-- Date -->
    </f>
    
    <!-- Zone 606 : sujet -->
    <f c="606" ind=" 1">
      <s c="a">Allemand langue</s>
    </f>
    
    <!-- Zone 995 : exemplaire (format PMB) -->
    <f c="995" ind="  ">
      <s c="a">Le 36 - Anor</s>   <!-- Bibliothèque -->
      <s c="f">5901204903</s>     <!-- Code-barres -->
      <s c="k">430 DIC</s>        <!-- Cote -->
    </f>
    
    <!-- Zone 996 : détails exemplaire (PMB) -->
    <f c="996" ind="  ">
      <s c="f">5901204903</s>     <!-- Code-barres -->
      <s c="k">430 DIC</s>        <!-- Cote -->
      <s c="e">Livre</s>          <!-- Type de document -->
      <s c="1">Empruntable</s>    <!-- Statut -->
      <s c="9">expl_id:140327</s> <!-- ID exemplaire PMB -->
    </f>
    
    <!-- Zone 999 : champs personnalisés PMB -->
    <f c="999" ind="  ">
      <s c="a">29/11/2023</s>
      <s c="l">Date d'acquisition</s>
    </f>
  </notice>
</unimarc>
```

### Codes de rôle importants ($4 dans zones 700-702)

| Code | Signification |
|------|---------------|
| 070  | Auteur principal |
| 090  | Scénariste |
| 100  | Auteur adapté/scénario |
| 440  | Illustrateur |
| 730  | Traducteur |
| 020  | Directeur de publication |
| 300  | Auteur présumé |
| 340  | Préfacier |
| 650  | Éditeur scientifique |

### Zones essentielles

**Zones de contrôle (001-099)**
- `001` : Identifiant de la notice
- `009` : Date de création
- `100` : Données codées (date, langue, pays)

**Titres et responsabilités (200-299)**
- `200` : Titre propre ($a = titre, $e = complément)
- `205` : Mention d'édition
- `210/214` : Édition (lieu $a, éditeur $c, date $d)
- `215` : Description physique ($a = pagination, $d = dimensions)

**Numéros (300-399)**
- `010` : ISBN ($a = ISBN, $d = prix)

**Notes (300-399)**
- `300` : Note générale ($a = texte de la note)
- `330` : Résumé
- `327` : Contenu (pour les recueils)

**Auteurs et responsabilités (700-799)**
- `700` : Auteur principal ($a = nom, $b = prénom, $4 = rôle)
- `701` : Co-auteur
- `702` : Auteur secondaire

**Sujets et indexation (600-699)**
- `606` : Sujet ($a = terme) - Thésaurus contrôlé
- `610` : Descripteurs non contrôlés ($a = termes séparés par ;)
- `676` : Indexation Dewey ($a = cote, $l = libellé)

**Exemplaires (900-999 zones locales PMB)**
- `900` : Champs personnalisés PMB (multiples - $n = nom du champ, $a = valeur, $l = libellé)
- `995` : Informations exemplaire (bibliothèque, cote, code-barres)
- `996` : Détails exemplaire (type doc, statut, localisation)
- `999` : Champs personnalisés (date d'acquisition, origine)

## Installation

```bash
# Dépendances Python
pip install pymarc lxml django-extensions

# Créer les apps Django
cd apps/
django-admin startapp catalog
django-admin startapp authorities
django-admin startapp items
django-admin startapp unimarc_import
```

## Modèles Django complets

### 1. App `catalog` - Notices bibliographiques

```python
# apps/catalog/models.py
from django.db import models
from apps.shared.models import TimeStampedModel


class Collection(TimeStampedModel):
    """Collection éditoriale (ex: "Les Encyclopes")."""
    nom = models.CharField(max_length=255)
    editeur = models.ForeignKey(
        'authorities.Editeur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collections'
    )
    issn = models.CharField(max_length=20, blank=True)
    
    class Meta:
        verbose_name = "Collection"
        verbose_name_plural = "Collections"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom


class Serie(TimeStampedModel):
    """Série/titre uniforme (ex: "Les aventures de Tintin")."""
    nom = models.CharField(max_length=255)
    numero = models.CharField(max_length=10, blank=True)
    
    class Meta:
        verbose_name = "Série"
        verbose_name_plural = "Séries"
        ordering = ['nom', 'numero']
    
    def __str__(self):
        if self.numero:
            return f"{self.nom} - Tome {self.numero}"
        return self.nom


class Notice(TimeStampedModel):
    """Notice bibliographique principale."""
    
    # Identifiants
    pmb_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Identifiant PMB original"
    )
    isbn = models.CharField(
        max_length=20,
        blank=True,
        help_text="ISBN-10 ou ISBN-13"
    )
    isbn_clean = models.CharField(
        max_length=13,
        blank=True,
        db_index=True,
        help_text="ISBN nettoyé (sans tirets)"
    )
    
    # Titres
    titre = models.TextField()
    titre_cle = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Clé de tri (sans articles)"
    )
    complement_titre = models.TextField(
        blank=True,
        help_text="Sous-titre ou complément"
    )
    
    # Édition
    annee_publication = models.IntegerField(null=True, blank=True)
    mention_edition = models.CharField(max_length=255, blank=True)
    
    # Description physique
    pagination = models.CharField(max_length=100, blank=True)
    illustrations = models.CharField(max_length=255, blank=True)
    dimensions = models.CharField(max_length=50, blank=True)
    
    # Contenu
    resume = models.TextField(blank=True)
    contenu = models.TextField(
        blank=True,
        help_text="Contenu détaillé (pour recueils)"
    )
    
    # Langue
    langue = models.CharField(
        max_length=3,
        default='fre',
        help_text="Code ISO 639-2 (fre, eng, spa...)"
    )
    langue_originale = models.CharField(
        max_length=3,
        blank=True,
        help_text="Langue originale si traduction"
    )
    
    # Classification
    cote_dewey = models.CharField(max_length=20, blank=True)
    libelle_dewey = models.CharField(max_length=255, blank=True)
    
    # Relations
    auteurs = models.ManyToManyField(
        'authorities.Auteur',
        through='Contribution',
        related_name='notices'
    )
    sujets = models.ManyToManyField(
        'authorities.Sujet',
        blank=True,
        related_name='notices'
    )
    mots_cles = models.ManyToManyField(
        'authorities.MotCle',
        blank=True,
        related_name='notices',
        help_text="Mots-clés libres (zone 610)"
    )
    notes = models.ManyToManyField(
        'Note',
        blank=True,
        related_name='notices'
    )
    champs_personnalises = models.JSONField(
        default=dict,
        blank=True,
        help_text="Champs personnalisés PMB (zones 900)"
    )
    editeur = models.ForeignKey(
        'authorities.Editeur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notices_publiees'
    )
    collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notices'
    )
    serie = models.ForeignKey(
        Serie,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notices'
    )
    
    # Média
    image_url = models.URLField(blank=True)
    
    # Statut
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Notice"
        verbose_name_plural = "Notices"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['titre_cle']),
            models.Index(fields=['isbn_clean']),
            models.Index(fields=['cote_dewey']),
        ]
    
    def __str__(self):
        return f"{self.titre[:80]}..." if len(self.titre) > 80 else self.titre
    
    def save(self, *args, **kwargs):
        # Nettoyer ISBN pour l'indexation
        if self.isbn:
            self.isbn_clean = self.isbn.replace('-', '').replace(' ', '')
        super().save(*args, **kwargs)
    
    @property
    def auteurs_principaux(self):
        """Retourne les auteurs principaux (rôle 070)."""
        return self.contribution_set.filter(role='070').select_related('auteur')


class Contribution(models.Model):
    """Table de liaison Notice ↔ Auteur avec rôle."""
    
    ROLE_CHOICES = [
        ('070', 'Auteur'),
        ('090', 'Scénariste'),
        ('100', 'Auteur adapté'),
        ('440', 'Illustrateur'),
        ('730', 'Traducteur'),
        ('020', 'Directeur'),
        ('650', 'Éditeur scientifique'),
        ('340', 'Préfacier'),
        ('300', 'Auteur présumé'),
    ]
    
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE)
    auteur = models.ForeignKey('authorities.Auteur', on_delete=models.CASCADE)
    role = models.CharField(
        max_length=3,
        choices=ROLE_CHOICES,
        default='070'
    )
    ordre = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        verbose_name = "Contribution"
        verbose_name_plural = "Contributions"
        ordering = ['ordre']
        unique_together = ['notice', 'auteur', 'role']
    
    def __str__(self):
        return f"{self.auteur} ({self.get_role_display()}) - {self.notice.titre[:50]}"


class Note(TimeStampedModel):
    """Note bibliographique (zone 300 UNIMARC)."""
    
    TYPE_CHOICES = [
        ('general', 'Note générale'),
        ('content', 'Note de contenu'),
        ('edition', 'Note sur l\'édition'),
        ('binding', 'Note sur la reliure'),
        ('original', 'Note sur l\'original'),
        ('other', 'Autre'),
    ]
    
    type_note = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='general'
    )
    contenu = models.TextField()
    
    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        ordering = ['type_note', 'created_at']
    
    def __str__(self):
        return f"{self.get_type_note_display()}: {self.contenu[:50]}..."
```

### 2. App `authorities` - Entités d'autorité

```python
# apps/authorities/models.py
from django.db import models
from apps.shared.models import TimeStampedModel


class Auteur(TimeStampedModel):
    """Auteur/Personne (entité d'autorité)."""
    
    pmb_id = models.CharField(max_length=50, null=True, blank=True, unique=True)
    
    # Nom
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255, blank=True)
    nom_complet = models.CharField(
        max_length=511,
        db_index=True,
        help_text="Nom complet formaté (NOM, Prénom)"
    )
    
    # Dates
    date_naissance = models.CharField(max_length=20, blank=True)
    date_deces = models.CharField(max_length=20, blank=True)
    
    # Informations
    biographie = models.TextField(blank=True)
    pays = models.CharField(max_length=100, blank=True)
    
    # Identifiants externes
    viaf_id = models.CharField(max_length=50, blank=True, help_text="Virtual International Authority File")
    isni = models.CharField(max_length=50, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Auteur"
        verbose_name_plural = "Auteurs"
        ordering = ['nom_complet']
        indexes = [
            models.Index(fields=['nom_complet']),
        ]
    
    def __str__(self):
        return self.nom_complet
    
    def save(self, *args, **kwargs):
        # Formater le nom complet
        if self.prenom:
            self.nom_complet = f"{self.nom.upper()}, {self.prenom}"
        else:
            self.nom_complet = self.nom.upper()
        super().save(*args, **kwargs)
    
    @property
    def notices_count(self):
        return self.notices.filter(is_active=True).count()


class Editeur(TimeStampedModel):
    """Maison d'édition."""
    
    pmb_id = models.CharField(max_length=50, null=True, blank=True, unique=True)
    
    nom = models.CharField(max_length=255)
    ville = models.CharField(max_length=100, blank=True)
    pays = models.CharField(max_length=100, blank=True)
    
    site_web = models.URLField(blank=True)
    
    class Meta:
        verbose_name = "Éditeur"
        verbose_name_plural = "Éditeurs"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom


class Sujet(TimeStampedModel):
    """Terme de sujet/thésaurus."""
    
    pmb_id = models.CharField(max_length=50, null=True, blank=True)
    
    terme = models.CharField(max_length=255, db_index=True)
    terme_normalise = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Version normalisée pour la recherche"
    )
    
    # Thésaurus
    thesaurus = models.CharField(
        max_length=100,
        default='Général',
        help_text="Nom du thésaurus"
    )
    thesaurus_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="ID dans le thésaurus"
    )
    
    # Relations
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enfants'
    )
    
    class Meta:
        verbose_name = "Sujet"
        verbose_name_plural = "Sujets"
        ordering = ['terme']
        unique_together = ['terme', 'thesaurus']
    
    def __str__(self):
        return self.terme
    
    def save(self, *args, **kwargs):
        # Normaliser le terme (minuscules, sans accents pour recherche)
        import unicodedata
        self.terme_normalise = ''.join(
            c for c in unicodedata.normalize('NFD', self.terme.lower())
            if unicodedata.category(c) != 'Mn'
        )
        super().save(*args, **kwargs)


class MotCle(TimeStampedModel):
    """Mot-clé libre non contrôlé (zone 610 UNIMARC)."""
    
    terme = models.CharField(max_length=255, db_index=True)
    terme_normalise = models.CharField(
        max_length=255,
        db_index=True,
        blank=True,
        help_text="Version normalisée pour la recherche"
    )
    
    class Meta:
        verbose_name = "Mot-clé"
        verbose_name_plural = "Mots-clés"
        ordering = ['terme']
    
    def __str__(self):
        return self.terme
    
    def save(self, *args, **kwargs):
        # Normaliser le terme (minuscules, sans accents pour recherche)
        import unicodedata
        self.terme_normalise = ''.join(
            c for c in unicodedata.normalize('NFD', self.terme.lower())
            if unicodedata.category(c) != 'Mn'
        )
        super().save(*args, **kwargs)
```

### 3. App `items` - Exemplaires

```python
# apps/items/models.py
from django.db import models
from apps.shared.models import TimeStampedModel


class Localisation(TimeStampedModel):
    """Localisation/site de la bibliothèque."""
    
    nom = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    adresse = models.TextField(blank=True)
    
    # Pour réseaux de bibliothèques
    bibliotheque_reseau = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nom dans le réseau (ex: 'Le 36 - Anor')"
    )
    site_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Code site (ex: 'Site 10')"
    )
    
    class Meta:
        verbose_name = "Localisation"
        verbose_name_plural = "Localisations"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom


class StatutExemplaire(TimeStampedModel):
    """Statut d'un exemplaire (empruntable, consultable sur place, etc.)."""
    
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    empruntable = models.BooleanField(default=True)
    visible_opac = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Statut d'exemplaire"
        verbose_name_plural = "Statuts d'exemplaire"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom


class TypeDocument(TimeStampedModel):
    """Type de document (livre, CD, DVD, etc.)."""
    
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    
    # Média
    icone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Classe CSS ou nom d'icône"
    )
    
    class Meta:
        verbose_name = "Type de document"
        verbose_name_plural = "Types de document"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom


class Section(TimeStampedModel):
    """Section/Rayon de la bibliothèque."""
    
    nom = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    localisation = models.ForeignKey(
        Localisation,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    
    class Meta:
        verbose_name = "Section"
        verbose_name_plural = "Sections"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.localisation.nom} - {self.nom}"


class Exemplaire(TimeStampedModel):
    """Exemplaire physique d'une notice."""
    
    pmb_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=True,
        help_text="ID exemplaire PMB"
    )
    
    # Lien vers la notice
    notice = models.ForeignKey(
        'catalog.Notice',
        on_delete=models.CASCADE,
        related_name='exemplaires'
    )
    
    # Identifiants
    code_barres = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Code-barres de l'exemplaire"
    )
    cote = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Cote/call number (ex: '430 DIC')"
    )
    
    # Localisation
    localisation = models.ForeignKey(
        Localisation,
        on_delete=models.PROTECT,
        related_name='exemplaires'
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exemplaires'
    )
    
    # Caractéristiques
    type_document = models.ForeignKey(
        TypeDocument,
        on_delete=models.PROTECT,
        related_name='exemplaires'
    )
    statut = models.ForeignKey(
        StatutExemplaire,
        on_delete=models.PROTECT,
        related_name='exemplaires'
    )
    
    # Gestion
    date_acquisition = models.DateField(null=True, blank=True)
    origine = models.CharField(
        max_length=100,
        blank=True,
        help_text="Achat, Don, etc."
    )
    prix = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Commentaire
    commentaire = models.TextField(blank=True)
    
    # Statut de prêt
    est_empruntable = models.BooleanField(default=True)
    est_disponible = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Exemplaire"
        verbose_name_plural = "Exemplaires"
        ordering = ['cote']
        indexes = [
            models.Index(fields=['code_barres']),
            models.Index(fields=['cote']),
            models.Index(fields=['notice', 'localisation']),
        ]
    
    def __str__(self):
        return f"{self.cote} ({self.code_barres}) - {self.notice.titre[:50]}"
    
    @property
    def disponibilite(self):
        """Retourne le statut de disponibilité."""
        if not self.est_empruntable:
            return "Non empruntable"
        if not self.est_disponible:
            return "En prêt"
        return "Disponible"
```

### 4. App `shared` - Modèles de base

```python
# apps/shared/models.py
from django.db import models


class TimeStampedModel(models.Model):
    """Modèle abstrait avec created_at et updated_at."""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
```

### 5. App `unimarc_import` - Import

```python
# apps/unimarc_import/models.py
from django.db import models
from apps.shared.models import TimeStampedModel


class ImportBatch(TimeStampedModel):
    """Lot d'import UNIMARC."""
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('running', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
    ]
    
    nom = models.CharField(max_length=255)
    fichier = models.FileField(upload_to='imports/unimarc/')
    
    # Statistiques
    total_notices = models.PositiveIntegerField(default=0)
    notices_importees = models.PositiveIntegerField(default=0)
    notices_mises_a_jour = models.PositiveIntegerField(default=0)
    notices_ignores = models.PositiveIntegerField(default=0)
    erreurs_count = models.PositiveIntegerField(default=0)
    
    statut = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Logs
    log = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Lot d'import"
        verbose_name_plural = "Lots d'import"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nom} ({self.statut})"


class ImportLog(TimeStampedModel):
    """Log détaillé par notice importée."""
    
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Avertissement'),
        ('error', 'Erreur'),
    ]
    
    batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    
    pmb_id = models.CharField(max_length=50, blank=True)
    titre = models.CharField(max_length=255, blank=True)
    niveau = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    message = models.TextField()
    
    class Meta:
        verbose_name = "Log d'import"
        verbose_name_plural = "Logs d'import"
        ordering = ['-created_at']
```

## Parsing UNIMARC avec pymarc

```python
# apps/unimarc_import/parsers.py
import xml.etree.ElementTree as ET
from pymarc import marcxml
from typing import Iterator, Dict, Any


class UnimarcXMLParser:
    """Parser pour fichiers UNIMARC XML (format PMB)."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    def parse(self) -> Iterator[Dict[str, Any]]:
        """
        Parse le fichier XML et yield chaque notice.
        
        Returns:
            Dict avec:
                - pmb_id: identifiant PMB
                - titre: titre principal
                - auteurs: liste des auteurs avec rôles
                - isbn: ISBN
                - editeur: informations éditeur
                - sujets: liste des sujets
                - exemplaires: liste des exemplaires
                - ... et autres champs
        """
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        
        for notice_elem in root.findall('notice'):
            yield self._parse_notice(notice_elem)
    
    def _parse_notice(self, notice_elem) -> Dict[str, Any]:
        """Parse une notice individuelle."""
        data = {
            'pmb_id': self._get_control_field(notice_elem, '001'),
            'titre': '',
            'complement_titre': '',
            'auteurs': [],
            'isbn': '',
            'editeur': {},
            'annee': None,
            'description': {},
            'sujets': [],
            'resume': '',
            'contenu': '',
            'collection': {},
            'serie': {},
            'cote_dewey': '',
            'libelle_dewey': '',
            'image_url': '',
            'exemplaires': [],
            'custom_fields': [],
            'notes': [],
            'mots_cles': [],
            'champs_perso': {},  # Zones 900 multiples
        }
        
        # Zone 200 : titre
        titre_field = self._get_data_field(notice_elem, '200')
        if titre_field:
            data['titre'] = self._get_subfield(titre_field, 'a', '')
            data['complement_titre'] = self._get_subfield(titre_field, 'e', '')
        
        # Zone 010 : ISBN
        isbn_field = self._get_data_field(notice_elem, '010')
        if isbn_field:
            data['isbn'] = self._get_subfield(isbn_field, 'a', '')
        
        # Zones 700, 701, 702 : auteurs
        for tag in ['700', '701', '702']:
            for field in notice_elem.findall(f"f[@c='{tag}']"):
                auteur = {
                    'nom': self._get_subfield(field, 'a', ''),
                    'prenom': self._get_subfield(field, 'b', ''),
                    'role': self._get_subfield(field, '4', '070'),
                    'pmb_id': self._extract_pmb_id(self._get_subfield(field, '9', '')),
                }
                if auteur['nom']:
                    data['auteurs'].append(auteur)
        
        # Zones 210/214 : édition
        for tag in ['210', '214']:
            ed_field = self._get_data_field(notice_elem, tag)
            if ed_field:
                data['editeur'] = {
                    'ville': self._get_subfield(ed_field, 'a', ''),
                    'nom': self._get_subfield(ed_field, 'c', ''),
                    'date': self._get_subfield(ed_field, 'd', ''),
                    'pmb_id': self._extract_pmb_id(self._get_subfield(ed_field, '9', '')),
                }
                if ed_field.find("s[@c='d']") is not None:
                    try:
                        data['annee'] = int(self._get_subfield(ed_field, 'd', '0'))
                    except ValueError:
                        pass
                break  # Prendre la première zone trouvée
        
        # Zone 215 : description physique
        desc_field = self._get_data_field(notice_elem, '215')
        if desc_field:
            data['description'] = {
                'pagination': self._get_subfield(desc_field, 'a', ''),
                'illustrations': self._get_subfield(desc_field, 'c', ''),
                'dimensions': self._get_subfield(desc_field, 'd', ''),
            }
        
        # Zone 330 : résumé
        resume_field = self._get_data_field(notice_elem, '330')
        if resume_field:
            data['resume'] = self._get_subfield(resume_field, 'a', '')
        
        # Zone 327 : contenu
        contenu_field = self._get_data_field(notice_elem, '327')
        if contenu_field:
            data['contenu'] = self._get_subfield(contenu_field, 'a', '')
        
        # Zone 300 : notes générales
        for field in notice_elem.findall("f[@c='300']"):
            note = {
                'type': 'general',
                'contenu': self._get_subfield(field, 'a', ''),
            }
            if note['contenu']:
                data['notes'].append(note)
        
        # Zone 610 : mots-clés libres (non contrôlés)
        for field in notice_elem.findall("f[@c='610']"):
            mots = self._get_subfield(field, 'a', '')
            # Les mots-clés peuvent être séparés par des points-virgules
            for mot in mots.split(';'):
                mot = mot.strip()
                if mot:
                    data['mots_cles'].append(mot)
        
        # Zones 900 : champs personnalisés PMB (multiples)
        for field in notice_elem.findall("f[@c='900']"):
            nom_champ = self._get_subfield(field, 'n', '')
            valeur = self._get_subfield(field, 'a', '')
            libelle = self._get_subfield(field, 'l', '')
            if nom_champ:
                data['champs_perso'][nom_champ] = {
                    'valeur': valeur,
                    'libelle': libelle,
                }
        
        # Zone 606 : sujets
        for field in notice_elem.findall("f[@c='606']"):
            sujet = {
                'terme': self._get_subfield(field, 'a', ''),
                'pmb_id': self._extract_pmb_id(self._get_subfield(field, '9', '')),
            }
            if sujet['terme']:
                data['sujets'].append(sujet)
        
        # Zone 676 : Dewey
        dewey_field = self._get_data_field(notice_elem, '676')
        if dewey_field:
            data['cote_dewey'] = self._get_subfield(dewey_field, 'a', '')
            data['libelle_dewey'] = self._get_subfield(dewey_field, 'l', '')
        
        # Zone 896 : image
        image_field = self._get_data_field(notice_elem, '896')
        if image_field:
            data['image_url'] = self._get_subfield(image_field, 'a', '')
        
        # Zone 461/225 : collection/série
        coll_field = self._get_data_field(notice_elem, '225')
        if coll_field:
            data['collection'] = {
                'nom': self._get_subfield(coll_field, 'a', ''),
                'issn': self._get_subfield(coll_field, 'x', ''),
                'pmb_id': self._extract_pmb_id(self._get_subfield(coll_field, '9', '')),
            }
        
        serie_field = self._get_data_field(notice_elem, '461')
        if serie_field:
            data['serie'] = {
                'nom': self._get_subfield(serie_field, 't', ''),
                'numero': self._get_subfield(serie_field, 'v', ''),
            }
        
        # Zones 995/996 : exemplaires
        for field in notice_elem.findall("f[@c='995']"):
            exemplaire = self._parse_exemplaire_995(field)
            if exemplaire:
                data['exemplaires'].append(exemplaire)
        
        # Zone 999 : champs personnalisés
        for field in notice_elem.findall("f[@c='999']"):
            custom = {
                'valeur': self._get_subfield(field, 'a', ''),
                'libelle': self._get_subfield(field, 'l', ''),
                'nom_champ': self._get_subfield(field, 'n', ''),
                'type': self._get_subfield(field, 't', ''),
                'code_barres': self._get_subfield(field, 'f', ''),
            }
            data['custom_fields'].append(custom)
        
        return data
    
    def _parse_exemplaire_995(self, field) -> Dict[str, Any]:
        """Parse une zone 995 (exemplaire PMB)."""
        # Chercher la zone 996 correspondante
        # Pour simplifier, on extrait juste les infos de base ici
        return {
            'bibliotheque': self._get_subfield(field, 'a', ''),
            'code_barres': self._get_subfield(field, 'f', ''),
            'cote': self._get_subfield(field, 'k', ''),
            'section': self._get_subfield(field, 'q', ''),
        }
    
    def _get_control_field(self, notice_elem, tag: str) -> str:
        """Récupère une zone de contrôle."""
        field = notice_elem.find(f"f[@c='{tag}']")
        return field.text if field is not None else ''
    
    def _get_data_field(self, notice_elem, tag: str):
        """Récupère une zone de données."""
        return notice_elem.find(f"f[@c='{tag}']")
    
    def _get_subfield(self, field, code: str, default: str = '') -> str:
        """Récupère une sous-zone."""
        if field is None:
            return default
        subfield = field.find(f"s[@c='{code}']")
        return subfield.text if subfield is not None else default
    
    def _extract_pmb_id(self, value: str) -> str:
        """Extrait l'ID PMB d'une sous-zone (format: 'id:12345')."""
        if value.startswith('id:'):
            return value[3:]
        return ''
```

## Commande d'import Django

```python
# apps/unimarc_import/management/commands/import_unimarc.py
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.unimarc_import.parsers import UnimarcXMLParser
from apps.unimarc_import.models import ImportBatch, ImportLog
from apps.catalog.models import Notice, Collection, Serie, Contribution, Note
from apps.authorities.models import Auteur, Editeur, Sujet, MotCle
from apps.items.models import Exemplaire, Localisation, TypeDocument, StatutExemplaire


class Command(BaseCommand):
    help = 'Importe un fichier UNIMARC XML'
    
    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Chemin vers le fichier XML')
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Nombre de notices à traiter par batch'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler l\'import sans sauvegarder'
        )
    
    def handle(self, *args, **options):
        file_path = options['file_path']
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        
        # Créer le batch
        batch = ImportBatch.objects.create(
            nom=file_path.split('/')[-1],
            statut='running'
        )
        
        try:
            parser = UnimarcXMLParser(file_path)
            notices = list(parser.parse())
            batch.total_notices = len(notices)
            
            self.stdout.write(
                self.style.SUCCESS(f'Total notices trouvées: {len(notices)}')
            )
            
            for i, notice_data in enumerate(notices):
                try:
                    with transaction.atomic():
                        self._import_notice(notice_data, batch, dry_run)
                        
                        if not dry_run:
                            batch.notices_importees += 1
                        
                        if (i + 1) % batch_size == 0:
                            self.stdout.write(f'Progression: {i + 1}/{len(notices)}')
                            if not dry_run:
                                batch.save()
                
                except Exception as e:
                    batch.erreurs_count += 1
                    ImportLog.objects.create(
                        batch=batch,
                        pmb_id=notice_data.get('pmb_id', ''),
                        titre=notice_data.get('titre', '')[:100],
                        niveau='error',
                        message=str(e)
                    )
                    self.stdout.write(
                        self.style.ERROR(
                            f'Erreur notice {notice_data.get("pmb_id")}: {e}'
                        )
                    )
            
            if not dry_run:
                batch.statut = 'completed'
                batch.save()
            
            self.stdout.write(self.style.SUCCESS('Import terminé !'))
            
        except Exception as e:
            batch.statut = 'failed'
            batch.log = str(e)
            batch.save()
            self.stdout.write(self.style.ERROR(f'Import échoué: {e}'))
    
    def _import_notice(self, data: dict, batch: ImportBatch, dry_run: bool):
        """Importe une notice et ses relations."""
        
        if dry_run:
            return
        
        # Créer ou récupérer la notice
        notice, created = Notice.objects.update_or_create(
            pmb_id=data['pmb_id'],
            defaults={
                'titre': data['titre'],
                'complement_titre': data['complement_titre'],
                'isbn': data['isbn'],
                'annee_publication': data['annee'],
                'resume': data['resume'],
                'contenu': data['contenu'],
                'cote_dewey': data['cote_dewey'],
                'libelle_dewey': data['libelle_dewey'],
                'image_url': data['image_url'],
                'pagination': data['description'].get('pagination', ''),
                'illustrations': data['description'].get('illustrations', ''),
                'dimensions': data['description'].get('dimensions', ''),
            }
        )
        
        # Gérer les auteurs
        for i, auteur_data in enumerate(data['auteurs']):
            auteur, _ = Auteur.objects.update_or_create(
                pmb_id=auteur_data['pmb_id'] or None,
                defaults={
                    'nom': auteur_data['nom'],
                    'prenom': auteur_data['prenom'],
                }
            )
            
            Contribution.objects.update_or_create(
                notice=notice,
                auteur=auteur,
                role=auteur_data['role'],
                defaults={'ordre': i}
            )
        
        # Gérer l'éditeur
        if data['editeur'].get('nom'):
            editeur, _ = Editeur.objects.update_or_create(
                pmb_id=data['editeur'].get('pmb_id') or None,
                defaults={
                    'nom': data['editeur']['nom'],
                    'ville': data['editeur'].get('ville', ''),
                }
            )
            notice.editeur = editeur
            notice.save()
        
        # Gérer les sujets
        for sujet_data in data['sujets']:
            sujet, _ = Sujet.objects.update_or_create(
                terme=sujet_data['terme'],
                thesaurus='Général',
                defaults={'pmb_id': sujet_data.get('pmb_id') or None}
            )
            notice.sujets.add(sujet)
        
        # Gérer les mots-clés libres (zone 610)
        for mot_cle in data['mots_cles']:
            mot, _ = MotCle.objects.get_or_create(terme=mot_cle)
            notice.mots_cles.add(mot)
        
        # Gérer les notes (zone 300)
        for note_data in data['notes']:
            note, _ = Note.objects.get_or_create(
                type_note=note_data['type'],
                contenu=note_data['contenu']
            )
            notice.notes.add(note)
        
        # Stocker les champs personnalisés (zones 900)
        if data['champs_perso']:
            notice.champs_personnalises = data['champs_perso']
            notice.save()
        
        # Créer les exemplaires
        for i, exemplaire_data in enumerate(data['exemplaires']):
            if exemplaire_data.get('code_barres'):
                # Déterminer ou créer la localisation
                localisation, _ = Localisation.objects.get_or_create(
                    bibliotheque_reseau=exemplaire_data.get('bibliotheque', ''),
                    defaults={'nom': exemplaire_data.get('bibliotheque', 'Bibliothèque')}
                )
                
                # Type de document par défaut
                type_doc, _ = TypeDocument.objects.get_or_create(
                    code='LIVRE',
                    defaults={'nom': 'Livre'}
                )
                
                # Statut par défaut
                statut, _ = StatutExemplaire.objects.get_or_create(
                    code='DISPONIBLE',
                    defaults={
                        'nom': 'Empruntable',
                        'empruntable': True
                    }
                )
                
                Exemplaire.objects.update_or_create(
                    code_barres=exemplaire_data['code_barres'],
                    defaults={
                        'notice': notice,
                        'cote': exemplaire_data.get('cote', ''),
                        'localisation': localisation,
                        'type_document': type_doc,
                        'statut': statut,
                    }
                )
```

## Utilisation

```bash
# Importer un fichier
python manage.py import_unimarc xml/Anor.xml --batch-size=100

# Simulation (dry run)
python manage.py import_unimarc xml/Anor.xml --dry-run

# Avec un batch plus petit
python manage.py import_unimarc xml/Anor.xml --batch-size=50
```

## Checklist pour l'import

### Avant l'import
- [ ] Créer les apps Django (`catalog`, `authorities`, `items`)
- [ ] Appliquer les migrations (`python manage.py migrate`)
- [ ] Créer les statuts/types de document de base
- [ ] Vérifier l'encodage du fichier XML (UTF-8)

### Pendant l'import
- [ ] Surveiller les logs d'erreur
- [ ] Vérifier les notices avec ISBN dupliqués
- [ ] Contrôler les auteurs créés (doublons possibles)

### Après l'import
- [ ] Vérifier le nombre de notices importées
- [ ] Contrôler quelques notices au hasard
- [ ] Vérifier les relations (auteurs, sujets)
- [ ] Tester la recherche

## Ressources

- [Spécification UNIMARC](http://www.bnf.fr/fr/professionnels/lis_z39_50/s.actualite_z3950.html)
- [Documentation pymarc](https://pymarc.readthedocs.io/)
- [Codes de rôle UNIMARC](https://www.ifla.org/publications/unimarc-formats-and-related-documentation)
