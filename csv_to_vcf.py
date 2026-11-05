#! /usr/bin/env python3
"""
Convertit out.csv en fichier de contacts vCard (.vcf) pour iPhone.
Chaque entreprise devient un contact avec :
- Nom de la société
- Téléphone
- Ville, Code Postal, Pays
- Description dans les notes
- Lien vers la fiche Kompass
"""

import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, 'out.csv')
VCF_FILE = os.path.join(BASE_DIR, 'contacts.vcf')


def clean_phone(phone):
    """Nettoie le numéro de téléphone pour le format standard international."""
    if not phone or phone == 'N/A':
        return None
    # Conserver uniquement les chiffres et le '+'
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    return cleaned if cleaned else phone


def convert_csv_to_vcf(csv_path, vcf_path):
    if not os.path.exists(csv_path):
        print(f"Erreur : fichier {csv_path} introuvable.")
        return

    contacts_count = 0

    with open(csv_path, 'r', encoding='utf-8-sig') as f_in, \
         open(vcf_path, 'w', encoding='utf-8') as f_out:

        reader = csv.DictReader(f_in)

        for row in reader:
            name = (row.get('Nom') or '').strip()
            phone = clean_phone(row.get('Téléphone'))
            city = (row.get('Ville') or '').strip()
            cp = (row.get('Code Postal') or '').strip()
            country = (row.get('Pays') or '').strip()
            ctype = (row.get('Type') or '').strip()
            activites = (row.get('Activités') or '').strip()
            desc = (row.get('Description') or '').strip()
            link = (row.get('Lien') or '').strip()
            effectif = (row.get('Effectif') or '').strip()

            if not name:
                continue

            # Construction des notes enrichies pour iPhone
            notes = []
            if ctype and ctype != 'N/A':
                notes.append(f"Activité : {ctype}")

            if activites and activites != 'N/A':
                notes.append("Produits & Services :\n" + activites)

            if desc and desc != 'N/A':
                notes.append("Description :\n" + desc)

            if effectif and effectif != 'N/A':
                notes.append(f"Effectif : {effectif}")

            if link and link != 'N/A':
                notes.append(f"Fiche Kompass : {link}")

            # Encodage vCard des retours à la ligne
            note_text = "\\n\\n".join(notes).replace("\r", "").replace("\n", "\\n")

            # Format vCard 3.0 (compatible iOS / macOS / Android)
            f_out.write("BEGIN:VCARD\n")
            f_out.write("VERSION:3.0\n")
            f_out.write(f"FN:{name}\n")
            f_out.write(f"ORG:{name}\n")

            if ctype and ctype != 'N/A':
                f_out.write(f"TITLE:{ctype}\n")

            if phone:
                f_out.write(f"TEL;TYPE=WORK,VOICE:{phone}\n")

            # Adresse : PO Box; Extended; Street; Locality (City); Region; PostalCode; Country
            loc = city if city != 'N/A' else ''
            postal = cp if cp != 'N/A' else ''
            ctry = country if country != 'N/A' else ''
            if loc or postal or ctry:
                f_out.write(f"ADR;TYPE=WORK:;;;{loc};;{postal};{ctry}\n")

            if link and link != 'N/A':
                f_out.write(f"URL;TYPE=WORK:{link}\n")

            if note_text:
                f_out.write(f"NOTE:{note_text}\n")

            f_out.write("END:VCARD\n")
            contacts_count += 1

    print(f"[OK] {contacts_count} contacts generes avec succes dans {vcf_path}")


if __name__ == '__main__':
    convert_csv_to_vcf(CSV_FILE, VCF_FILE)
