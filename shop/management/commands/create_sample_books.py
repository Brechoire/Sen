from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from author.models import Author
from shop.models import Book, Category
from decimal import Decimal
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = 'Crée des livres de démonstration pour la boutique'

    def handle(self, *args, **options):
        # Créer des catégories si elles n'existent pas
        categories_data = [
            {
                'name': 'Littérature française',
                'slug': 'litterature-francaise',
                'description': 'Romans et nouvelles de la littérature française contemporaine et classique'
            },
            {
                'name': 'Poésie',
                'slug': 'poesie',
                'description': 'Recueils de poésie et anthologies poétiques'
            },
            {
                'name': 'Essais',
                'slug': 'essais',
                'description': 'Essais littéraires, philosophiques et culturels'
            },
            {
                'name': 'Théâtre',
                'slug': 'theatre',
                'description': 'Pièces de théâtre et dramaturgie contemporaine'
            },
            {
                'name': 'Biographies',
                'slug': 'biographies',
                'description': 'Biographies et mémoires d\'écrivains et personnalités'
            }
        ]

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Catégorie créée: {category.name}')

        # Récupérer les catégories
        litterature = Category.objects.get(slug='litterature-francaise')
        poesie = Category.objects.get(slug='poesie')
        essais = Category.objects.get(slug='essais')

        # Créer des auteurs de démonstration s'ils n'existent pas
        authors_data = [
            {
                'first_name': 'Marie',
                'last_name': 'Dubois',
                'pen_name': 'Marie Dubois',
                'biography': 'Marie Dubois est une romancière française née en 1975. Elle a publié plusieurs romans remarqués par la critique.',
                'short_bio': 'Romancière française contemporaine',
                'is_featured': True
            },
            {
                'first_name': 'Pierre',
                'last_name': 'Martin',
                'pen_name': 'Pierre Martin',
                'biography': 'Pierre Martin est un poète et essayiste français. Il enseigne la littérature à l\'université.',
                'short_bio': 'Poète et essayiste français',
                'is_featured': True
            },
            {
                'first_name': 'Sophie',
                'last_name': 'Leroy',
                'pen_name': 'Sophie Leroy',
                'biography': 'Sophie Leroy est une dramaturge française contemporaine. Ses pièces sont régulièrement jouées dans les théâtres parisiens.',
                'short_bio': 'Dramaturge française contemporaine',
                'is_featured': False
            }
        ]

        for author_data in authors_data:
            author, created = Author.objects.get_or_create(
                first_name=author_data['first_name'],
                last_name=author_data['last_name'],
                defaults=author_data
            )
            if created:
                self.stdout.write(f'Auteur créé: {author.display_name}')

        # Récupérer les auteurs
        marie = Author.objects.get(first_name='Marie', last_name='Dubois')
        pierre = Author.objects.get(first_name='Pierre', last_name='Martin')
        sophie = Author.objects.get(first_name='Sophie', last_name='Leroy')

        # Créer des livres de démonstration
        books_data = [
            {
                'title': 'Le Silence des Arbres',
                'slug': 'le-silence-des-arbres',
                'subtitle': 'Un roman sur la nature et l\'humanité',
                'author': marie,
                'category': litterature,
                'description': '<p>Dans ce roman poignant, Marie Dubois explore la relation complexe entre l\'homme et la nature. L\'histoire suit le parcours d\'une jeune femme qui découvre les secrets d\'une forêt mystérieuse.</p><p>Un récit captivant qui mêle réalisme et poésie, interrogeant notre place dans l\'écosystème et notre responsabilité envers l\'environnement.</p>',
                'short_description': 'Un roman poignant sur la relation entre l\'homme et la nature, mêlant réalisme et poésie.',
                'excerpt': 'La forêt murmurait des secrets que seuls les initiés pouvaient entendre. Sarah s\'avança entre les troncs centenaires, écoutant cette symphonie silencieuse qui résonnait dans son cœur.',
                'isbn': '978-2-123456-78-9',
                'publication_date': date(2024, 3, 15),
                'pages': 320,
                'language': 'Français',
                'format': 'broche',
                'price': Decimal('24.90'),
                'discount_price': Decimal('19.90'),
                'stock_quantity': 50,
                'is_available': True,
                'is_featured': True,
                'is_bestseller': True,
                'meta_title': 'Le Silence des Arbres - Marie Dubois | Éditions Sen',
                'meta_description': 'Découvrez Le Silence des Arbres, un roman poignant de Marie Dubois sur la relation entre l\'homme et la nature. Disponible aux Éditions Sen.',
                'keywords': 'roman, nature, écologie, littérature française, Marie Dubois'
            },
            {
                'title': 'Vers l\'Infini',
                'slug': 'vers-linfini',
                'subtitle': 'Poèmes de l\'âme',
                'author': pierre,
                'category': poesie,
                'description': '<p>Ce recueil de poésie explore les thèmes universels de l\'amour, de la mort et de l\'éternité. Pierre Martin nous offre une vision poétique du monde contemporain.</p><p>Chaque poème est une invitation à la contemplation et à la réflexion, dans une langue à la fois simple et profonde.</p>',
                'short_description': 'Un recueil de poésie explorant les thèmes universels de l\'amour, de la mort et de l\'éternité.',
                'excerpt': 'Vers l\'infini, je tends ma main / Dans l\'océan des possibles / Où chaque vague est un poème / Et chaque étoile, une promesse.',
                'isbn': '978-2-123456-79-6',
                'publication_date': date(2024, 1, 20),
                'pages': 128,
                'language': 'Français',
                'format': 'broche',
                'price': Decimal('18.50'),
                'stock_quantity': 30,
                'is_available': True,
                'is_featured': True,
                'is_bestseller': False,
                'meta_title': 'Vers l\'Infini - Pierre Martin | Éditions Sen',
                'meta_description': 'Découvrez Vers l\'Infini, un recueil de poésie de Pierre Martin. Poèmes sur l\'amour, la mort et l\'éternité.',
                'keywords': 'poésie, amour, mort, éternité, Pierre Martin'
            },
            {
                'title': 'L\'Art de Vivre',
                'slug': 'lart-de-vivre',
                'subtitle': 'Réflexions philosophiques sur l\'existence',
                'author': pierre,
                'category': essais,
                'description': '<p>Dans cet essai philosophique, Pierre Martin interroge les fondements de l\'existence humaine et propose une réflexion sur l\'art de vivre au XXIe siècle.</p><p>À travers une approche accessible et contemporaine, l\'auteur explore les grandes questions de la vie : le bonheur, la liberté, la responsabilité et le sens de l\'existence.</p>',
                'short_description': 'Un essai philosophique accessible sur l\'art de vivre au XXIe siècle.',
                'excerpt': 'Vivre, c\'est choisir. Chaque jour, nous sommes confrontés à des choix qui façonnent notre existence et définissent qui nous sommes.',
                'isbn': '978-2-123456-80-2',
                'publication_date': date(2023, 11, 10),
                'pages': 256,
                'language': 'Français',
                'format': 'broche',
                'price': Decimal('22.00'),
                'stock_quantity': 25,
                'is_available': True,
                'is_featured': False,
                'is_bestseller': False,
                'meta_title': 'L\'Art de Vivre - Pierre Martin | Éditions Sen',
                'meta_description': 'Découvrez L\'Art de Vivre, un essai philosophique de Pierre Martin sur l\'existence humaine au XXIe siècle.',
                'keywords': 'philosophie, existence, bonheur, liberté, Pierre Martin'
            },
            {
                'title': 'Les Ombres du Théâtre',
                'slug': 'les-ombres-du-theatre',
                'subtitle': 'Pièce en trois actes',
                'author': sophie,
                'category': Category.objects.get(slug='theatre'),
                'description': '<p>Cette pièce de théâtre contemporaine explore les relations humaines à travers le prisme de l\'art dramatique. Sophie Leroy nous plonge dans l\'univers fascinant des coulisses théâtrales.</p><p>Une œuvre qui questionne la frontière entre réalité et fiction, entre vie et représentation.</p>',
                'short_description': 'Une pièce de théâtre contemporaine explorant les relations humaines à travers l\'art dramatique.',
                'excerpt': 'Dans les coulisses, les masques tombent. Chaque acteur porte en lui mille personnages, mais lequel est le vrai ?',
                'isbn': '978-2-123456-81-9',
                'publication_date': date(2024, 2, 28),
                'pages': 180,
                'language': 'Français',
                'format': 'broche',
                'price': Decimal('20.50'),
                'stock_quantity': 40,
                'is_available': True,
                'is_featured': False,
                'is_bestseller': False,
                'meta_title': 'Les Ombres du Théâtre - Sophie Leroy | Éditions Sen',
                'meta_description': 'Découvrez Les Ombres du Théâtre, une pièce contemporaine de Sophie Leroy sur l\'art dramatique.',
                'keywords': 'théâtre, drame, relations humaines, Sophie Leroy'
            }
        ]

        for book_data in books_data:
            book, created = Book.objects.get_or_create(
                isbn=book_data['isbn'],
                defaults=book_data
            )
            if created:
                self.stdout.write(f'Livre créé: {book.title}')

        self.stdout.write(
            self.style.SUCCESS('Données de démonstration créées avec succès !')
        )
