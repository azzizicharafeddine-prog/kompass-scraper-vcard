# 🚀 Kompass Scraper & vCard Exporter

Un scraper moderne et rapide pour extraire les entreprises depuis **Kompass** (tous pays : `dz.kompass.com`, `fr.kompass.com`, etc.), avec contournement des protections anti-bot (DataDome), export **Excel (CSV)** et génération automatique de fiches contacts **vCard (.vcf)** pour iPhone et Android.

---

## ✨ Fonctionnalités

- 🛡️ **Anti-Détection DataDome** : Utilise `undetected-chromedriver` pour contourner les protections anti-bot sans se faire bannir l'IP.
- ⚡ **Extraction Rapide via Schema.org** : Récupère directement les données structurées sans avoir à ouvrir chaque fiche entreprise une par une.
- 📞 **Données Complètes** :
  - Nom de l'entreprise
  - Téléphone direct (format international)
  - Type (Producteur, Distributeur, Prestataire de services, etc.)
  - Secteur & Liste détaillée des produits / activités
  - Ville, Code Postal, Pays
  - Effectif (Nombre d'employés)
  - Description de l'entreprise
  - Lien direct vers la fiche Kompass
- 📱 **Génération Contact iPhone (`contact.vcf`)** : Crée un fichier vCard 3.0 importable en 1 clic sur iOS / macOS / Android avec toutes les notes et coordonnées.
- 📂 **Organisation Automatique** : Crée un sous-dossier propre pour chaque catégorie / recherche.
- 📋 **Automatisation 1-Clic** : Détecte directement l'URL Kompass depuis le presse-papier Windows et lance le scraping sans configuration.

---

## 📦 Installation

1. Cloner ce dépôt ou télécharger les fichiers :
   ```bash
   git clone https://github.com/votre-nom-utilisateur/kompass-scraper.git
   cd kompass-scraper
   ```

2. Installer les dépendances Python :
   ```bash
   pip install -r requirements.txt
   ```

3. Avoir **Google Chrome** installé sur votre machine.

---

## 🚀 Utilisation

### Méthode 1 : Raccourci 1-Clic (Recommandée sous Windows)

1. Copiez l'URL d'une page Kompass (<kbd>Ctrl</kbd> + <kbd>C</kbd>) depuis votre navigateur (ex : `https://dz.kompass.com/a/vaseline-pour-cosmetiques/2197236/`).
2. Double-cliquez sur **`LANCER_SCRAPER.bat`**.
3. Le script démarre automatiquement, scrape 4 pages par défaut et crée les fichiers.

### Méthode 2 : Ligne de commande

```bash
python kompasScraper.py
```

Renseignez l'URL et le nombre de pages souhaité.

---

## 📁 Résultats générés

Pour chaque recherche, un sous-dossier est créé (ex: `lubrifiants-a-base-de-petrole_21820/`) contenant :
- **`out.csv`** : Tableau prêt pour Excel (encodé en UTF-8 BOM avec accents et arabe préservés).
- **`contact.vcf`** : Fichier contact contenant toutes les entreprises avec téléphones, types et listes de produits dans les notes.

---

## 📱 Importer sur iPhone

1. Envoyez-vous le fichier `contact.vcf` par **WhatsApp**, **Telegram** ou **Email**.
2. Sur l'iPhone, ouvrez le fichier.
3. Touchez **« Ajouter tous les contacts »**.

---

## ⚖️ Licence

Ce projet est sous licence MIT. À des fins éducatives et de recherche.
