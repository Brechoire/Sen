# Generated manually to fix migration dependency issue
# The index shop_book_author__c28b8c_idx was already removed in migration 0013_change_author_to_authors
# This migration exists only to maintain the migration graph consistency

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0014_add_preorder_fields'),
    ]

    operations = [
        # Migration vide - l'index a déjà été supprimé dans 0013_change_author_to_authors
        # Cette migration existe uniquement pour maintenir la cohérence du graphe de migrations
        # et permettre à la migration 0016_remove_author_index_safely de fonctionner correctement
    ]



