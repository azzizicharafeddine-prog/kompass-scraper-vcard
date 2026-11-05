#! /usr/bin/env python3
"""
Scraper Kompass optimisé & anti-détection.
- Crée un sous-dossier par catégorie/URL
- Génère automatiquement out.csv et contact.vcf dans chaque sous-dossier
- Extraction complète via JSON-LD (Nom, Téléphone, Ville, CP, Effectif, Description, Lien)
"""

import csv
import json
import time
import html
import re
import os
from urllib.parse import urlparse, urljoin
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

# Supprimer le bug WinError 6 du garbage collector Windows sur undetected_chromedriver
uc.Chrome.__del__ = lambda self: None

from csv_to_vcf import convert_csv_to_vcf


def setup_browser():
    """Initialise Chrome en mode furtif."""
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=fr-FR')
    driver = uc.Chrome(options=options)
    return driver


def wait_for_real_content(driver, timeout=120):
    """Attend que la page se charge sans CAPTCHA ni blocage."""
    start = time.time()
    while time.time() - start < timeout:
        source = driver.page_source.lower()
        if 'captcha-delivery' in source:
            print("  ⏳ CAPTCHA détecté — résous-le dans la fenêtre Chrome...")
            time.sleep(4)
        elif 'temporairement restreint' in source:
            print("  ⏳ Accès restreint — pause de sécurité...")
            time.sleep(5)
        else:
            return True
    print("  ⏰ Temps d'attente dépassé.")
    return False


def get_subfolder_name(url):
    """Extrait un nom de dossier propre à partir de l'URL."""
    path = urlparse(url).path.strip('/')
    parts = [p for p in path.split('/') if p]

    # Exemples d'URL Kompass:
    # /a/lubrifiants-pour-vehicules-automobiles/2292021/ -> lubrifiants-pour-vehicules-automobiles_2292021
    if len(parts) >= 3 and parts[0] in ['a', 'c', 's']:
        name = f"{parts[1]}_{parts[2]}"
    elif len(parts) >= 2 and parts[0] in ['a', 'c', 's']:
        name = parts[1]
    elif parts:
        name = parts[-1]
    else:
        name = "export_kompass"

    # Nettoyage des caractères interdits sous Windows
    clean_name = re.sub(r'[^\w\-]', '_', name)
    return clean_name or "export_kompass"


def extract_page_companies(soup, base_domain):
    """
    Extrait les données complètes des entreprises en combinant :
    - Le JSON-LD (Téléphones, Villes, Code Postal, Pays, Effectif)
    - Les cartes HTML (Types d'activités : Producteur/Distributeur/Service + Liste détaillée des produits/activités)
    """
    # 1. Indexation des données JSON-LD par URL et par Nom
    json_by_url = {}
    json_by_name = {}
    scripts = soup.find_all('script', type='application/ld+json')

    for script in scripts:
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
            items = []
            if isinstance(data, dict):
                main_entity = data.get('mainEntity', {})
                if isinstance(main_entity, dict) and 'itemListElement' in main_entity:
                    items = main_entity.get('itemListElement', [])
                elif 'itemListElement' in data:
                    items = data.get('itemListElement', [])

            for it in items:
                org = it.get('item', {}) if isinstance(it, dict) else {}
                if not org or org.get('@type') != 'Organization':
                    continue

                u = (org.get('url') or '').strip().rstrip('/')
                n = (org.get('name') or '').strip().lower()
                if u:
                    json_by_url[u] = org
                if n:
                    json_by_name[n] = org
        except Exception:
            continue

    companies = []
    seen_urls = set()

    # 2. Extraction depuis les cartes HTML
    cards = soup.find_all('div', class_='cardCompany')
    for card in cards:
        a_tag = card.find('a', class_='titleSpan')
        if not a_tag or not a_tag.get('href') or '/c/' not in a_tag['href']:
            continue

        raw_href = a_tag['href']
        full_url = urljoin(base_domain, raw_href).strip()
        norm_url = full_url.rstrip('/')
        if norm_url in seen_urls:
            continue
        seen_urls.add(norm_url)

        name = a_tag.get_text(strip=True)

        # Type d'activité (Producteur, Distributeur, Service, etc.)
        type_tags = [t.get_text(strip=True) for t in card.find_all('span', class_=lambda c: c and 'tagOrange' in c)]
        ctype = ', '.join(type_tags) if type_tags else 'N/A'

        # Liste des activités / produits détaillés
        ul_act = card.find('ul', class_='listActivity')
        if ul_act:
            items_act = [li.get_text(strip=True) for li in ul_act.find_all('li') if li.get_text(strip=True)]
            activites = '\n'.join([f"- {it}" for it in items_act]) if items_act else 'N/A'
        else:
            activites = 'N/A'

        # Description courte de la carte
        p_desc = card.find('p', class_='product-summary') or card.find('p', class_='description')
        card_desc = p_desc.get_text(' ', strip=True) if p_desc else ''

        # Association avec JSON-LD
        org = json_by_url.get(norm_url) or json_by_name.get(name.lower(), {})
        tel = org.get('telephone', 'N/A')
        addr_dict = org.get('address', {})
        city = addr_dict.get('addressLocality', 'N/A') if isinstance(addr_dict, dict) else 'N/A'
        cp = addr_dict.get('postalCode', 'N/A') if isinstance(addr_dict, dict) else 'N/A'
        country = addr_dict.get('addressCountry', 'N/A') if isinstance(addr_dict, dict) else 'N/A'
        employees = org.get('numberOfEmployees', {}).get('value', 'N/A') if isinstance(org.get('numberOfEmployees'), dict) else 'N/A'

        json_desc = org.get('description', '')
        if json_desc:
            desc = html.unescape(json_desc).strip()
        else:
            desc = card_desc if card_desc else 'N/A'

        companies.append({
            'Nom': name,
            'Téléphone': tel,
            'Type': ctype,
            'Activités': activites,
            'Ville': city,
            'Code Postal': cp,
            'Pays': country,
            'Effectif': employees,
            'Description': desc,
            'Lien': full_url
        })

    # 3. Fallback direct JSON-LD si aucune carte HTML trouvée
    if not companies and json_by_url:
        for u, org in json_by_url.items():
            name = org.get('name', '').strip()
            tel = org.get('telephone', 'N/A')
            desc = html.unescape(org.get('description', '')).strip() if org.get('description') else 'N/A'
            addr_dict = org.get('address', {})
            city = addr_dict.get('addressLocality', 'N/A') if isinstance(addr_dict, dict) else 'N/A'
            cp = addr_dict.get('postalCode', 'N/A') if isinstance(addr_dict, dict) else 'N/A'
            country = addr_dict.get('addressCountry', 'N/A') if isinstance(addr_dict, dict) else 'N/A'
            employees = org.get('numberOfEmployees', {}).get('value', 'N/A') if isinstance(org.get('numberOfEmployees'), dict) else 'N/A'
            link = org.get('url', u)

            companies.append({
                'Nom': name,
                'Téléphone': tel,
                'Type': 'N/A',
                'Activités': 'N/A',
                'Ville': city,
                'Code Postal': cp,
                'Pays': country,
                'Effectif': employees,
                'Description': desc,
                'Lien': link
            })

    return companies


def get_clipboard_text():
    """Récupère le texte du presse-papier Windows avec multi-méthodes fiables."""
    # Méthode 1 : PowerShell natif Windows (100% fiable pour capturer l'URL copiée)
    try:
        import subprocess
        CREATE_NO_WINDOW = 0x08000000
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard"],
            text=True,
            encoding="utf-8",
            errors="ignore",
            creationflags=CREATE_NO_WINDOW
        )
        if out and out.strip():
            return out.strip()
    except Exception:
        pass

    # Méthode 2 : Windows API ctypes 64-bit
    try:
        import ctypes
        from ctypes import wintypes
        u32 = ctypes.windll.user32
        k32 = ctypes.windll.kernel32
        u32.GetClipboardData.restype = wintypes.HANDLE
        u32.GetClipboardData.argtypes = [wintypes.UINT]
        k32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        k32.GlobalLock.restype = wintypes.LPVOID
        k32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]

        if u32.OpenClipboard(None):
            try:
                h_glb = u32.GetClipboardData(13)  # CF_UNICODETEXT
                if h_glb:
                    p_glb = k32.GlobalLock(h_glb)
                    if p_glb:
                        try:
                            val = ctypes.c_wchar_p(p_glb).value
                            if val:
                                return val
                        finally:
                            k32.GlobalUnlock(h_glb)
            finally:
                u32.CloseClipboard()
    except Exception:
        pass

    return ""


def main():
    clipboard_val = get_clipboard_text().strip()
    # Recherche automatique d'un lien Kompass dans le presse-papier
    match = re.search(r'https?://[^\s\'"]*kompass\.com[^\s\'"]*', clipboard_val)

    if match:
        base_url = match.group(0).strip()
        total_pages = 4
        print("\n" + "="*60)
        print(f"📋 Lien détecté automatiquement :")
        print(f"   {base_url}")
        print(f"📄 Nombre de pages : {total_pages} (par défaut)")
        print("="*60 + "\n")
    else:
        print("\n⚠️ Aucun lien Kompass trouvé dans le presse-papier.")
        base_url = input("Colle l'URL Kompass ici :\n").strip()
        pages_input = input("Nombre de pages [Défaut: 4] :\n").strip()
        total_pages = int(pages_input) if pages_input.isdigit() and int(pages_input) > 0 else 4

    if not base_url.endswith('/'):
        base_url += '/'

    parsed = urlparse(base_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"

    # Création du sous-dossier dédié à ce lien
    base_dir = os.path.dirname(os.path.abspath(__file__))
    subfolder_name = get_subfolder_name(base_url)
    output_dir = os.path.join(base_dir, subfolder_name)
    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, 'out.csv')
    vcf_path = os.path.join(output_dir, 'contact.vcf')

    print(f"\n📂 Dossier de destination : {output_dir}")
    print(f"Domaine cible : {domain}")
    print("Démarrage du navigateur...")
    driver = setup_browser()
    count_comp = 0
    seen_links = set()

    # Session d'accueil pour initialiser les cookies et résoudre le CAPTCHA initial
    print("\n🔓 Initialisation sur la page d'accueil...")
    driver.get(domain)
    time.sleep(4)
    wait_for_real_content(driver)
    time.sleep(2)

    try:
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csv_file:
            fields = ['Nom', 'Téléphone', 'Type', 'Activités', 'Ville', 'Code Postal', 'Pays', 'Effectif', 'Description', 'Lien']
            writer = csv.DictWriter(csv_file, fieldnames=fields)
            writer.writeheader()

            for page in range(1, total_pages + 1):
                page_url = f"{base_url}page-{page}" if page > 1 else base_url
                print(f"\n{'='*60}")
                print(f"📄 Page {page}/{total_pages} : {page_url}")
                print('='*60)

                driver.get(page_url)
                time.sleep(3 + (page % 2))

                if not wait_for_real_content(driver):
                    print("  ⚠️ Impossible d'accéder à la page.")
                    continue

                # Scroll léger pour déclencher l'affichage complet
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(1)

                soup = BeautifulSoup(driver.page_source, 'lxml')

                # Extraction combinée : cartes d'entreprises (avec activités/produits) + JSON-LD (téléphone/adresse)
                page_companies = extract_page_companies(soup, domain)

                print(f"  ✅ {len(page_companies)} entreprises trouvées sur la page.")

                for comp in page_companies:
                    comp_link = comp['Lien']
                    if comp_link in seen_links:
                        continue
                    seen_links.add(comp_link)

                    writer.writerow(comp)
                    count_comp += 1
                    type_info = f" | 🏷️ {comp['Type']}" if comp['Type'] != 'N/A' else ""
                    print(f"     ✓ {comp['Nom']}{type_info} | 📞 {comp['Téléphone']} | 📍 {comp['Ville']}")

                csv_file.flush()
                time.sleep(2)

    finally:
        print(f"\n{'='*60}")
        print(f"🏁 Terminé ! {count_comp} entreprises enregistrées dans :")
        print(f"   📄 {csv_path}")
        print('='*60)

        # Génération automatique du fichier contact.vcf dans le même sous-dossier
        convert_csv_to_vcf(csv_path, vcf_path)
        print(f"   📱 {vcf_path}")

        input("\nAppuie sur Entrée pour fermer le navigateur...")
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == '__main__':
    main()
