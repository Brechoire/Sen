#!/usr/bin/env python
"""
Script pour mettre à jour le statut des factures existantes de 'draft' à 'sent'
"""
import os
import sys
import django
from django.utils import timezone

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from shop.models import Invoice


def update_invoice_status():
    """Met à jour le statut des factures de 'draft' à 'sent'"""
    print("=== Mise à jour du statut des factures ===")
    
    # Trouver toutes les factures en statut 'draft'
    draft_invoices = Invoice.objects.filter(status='draft')
    count = draft_invoices.count()
    
    if count == 0:
        print("Aucune facture en statut 'Brouillon' trouvée.")
        return True
    
    print(f"Trouvé {count} facture(s) en statut 'Brouillon'")
    
    # Mettre à jour le statut
    updated_count = draft_invoices.update(status='sent')
    
    print(f"[OK] {updated_count} facture(s) mise(s) à jour vers le statut 'Envoyée'")
    
    # Vérifier le résultat
    remaining_drafts = Invoice.objects.filter(status='draft').count()
    sent_invoices = Invoice.objects.filter(status='sent').count()
    
    print(f"\nStatistiques après mise à jour:")
    print(f"  - Factures 'Brouillon': {remaining_drafts}")
    print(f"  - Factures 'Envoyée': {sent_invoices}")
    
    return True


def main():
    """Fonction principale"""
    try:
        success = update_invoice_status()
        
        if success:
            print("\n[SUCCES] Mise à jour terminée avec succès !")
            return True
        else:
            print("\n[ECHEC] Erreur lors de la mise à jour.")
            return False
            
    except Exception as e:
        print(f"\n[ERREUR] Erreur lors de la mise à jour: {e}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)











