# 🤖 AUTO-INCOME AI : Agent Autonome de Génération de Revenus

> **Système d'automatisation cloud et local à coût zéro (0 USD)** conçu pour analyser le marché international, concevoir des actifs numériques monétisables et fonctionner 24h/24 même appareil éteint.

---

## 🌟 Points Forts & Spécifications

- **💰 Budget initial : 0,00 $** (Aucun abonnement payant, aucun capital de départ).
- **🌍 Marché ciblé : International** (Clients francophones et anglophones).
- **🇲🇬 Utilisateur : Basé à Madagascar** (Encaissement direct compatible MVola, Orange Money, Payoneer, virement bancaire).
- **☁️ Exécution Cloud 24h/24** : Fonctionne de manière autonome via **GitHub Actions** toutes les 6 heures, ordinateur et téléphone éteints.
- **📱 Compatible Android & Mobile** : Exécutable sous **Termux**, tableau de bord HTML responsive consultable hors-ligne ou via GitHub Pages.
- **🛡️ Éthique & Zéro Spam** : Aucune donnée fictive, aucun spam, respect scrupuleux des conditions d'utilisation des plateformes.

---

## 🚀 Les 5 Modèles de Revenus Pris en Charge

1. **Produits Numériques Téléchargeables** : Guides pratiques, modèles de documents opérationnels, checklists professionnelles.
2. **Microservices Freelance Clés en Main** : Fiches de services prêtes à publier sur ComeUp, Fiverr ou Upwork avec grille tarifaire et FAQ.
3. **Marketing de Contenu SEO** : Articles spécialisés approfondis avec balisage sémantique et appels à l'action monétisés.
4. **Listes de Prospects B2B Qualifiés** : Données publiques d'entreprises cibles avec propositions de valeur personnalisées.
5. **Micro-Outils Logiciels Web** : Mini-applications HTML/JS interactives autonomes hébergeables gratuitement sur GitHub Pages.

---

## 📂 Architecture des Fichiers

```text
├── config.json                 # Configuration centrale, canaux de paiement et seuils
├── main.py                     # Orchestrateur du cycle autonome en 12 étapes
├── opportunity_engine.py       # Collecte multi-sources, déduplication et scoring /100
├── content_factory.py          # Usine de production des livrables et audit qualité
├── monetization.py             # Calculateur de marge nette et rails d'encaissement Madagascar
├── storage.py                  # Persistance SQLite et export d'état JSON idempotent
├── report.py                   # Générateur du rapport console et du dashboard HTML
├── requirements.txt            # Dépendances ultra-légères
├── .env.example                # Modèle de variables d'environnement (sans secrets)
├── .gitignore                  # Exclusion des caches et données sensibles
├── AGENTS.md                   # Guide d'architecture pour agents IA
├── tests/                      # Suite de tests unitaires automatisés
├── site/                       # Dossier de publication (compatible GitHub Pages)
│   ├── index.html              # Tableau de bord exécutif responsive pour mobile
│   └── deliverables/           # Catalogue des actifs numériques prêts à la vente
└── .github/workflows/
    └── agent.yml               # Workflow cloud GitHub Actions planifié (toutes les 6h)
```

---

## ⚡ Démarrage Rapide sous Android (Termux)

### 1. Prérequis & Installation (en 30 secondes) :
```bash
# Dans votre terminal Termux :
cd /data/data/com.termux/files/home

# Lancer la suite de tests unitaires
python3 -m unittest discover -s tests -p "test_*.py"
```

### 2. Lancer un cycle autonome :
```bash
# Exécution d'un cycle complet avec recherche d'opportunités
python3 main.py --run

# Ou en mode simulation (démo hors-ligne immédiate)
python3 main.py --simulate
```

### 3. Consulter le tableau de bord sur Android :
Ouvrez le fichier généré `site/index.html` dans Chrome ou votre navigateur mobile :
```bash
# Exemple via le navigateur Termux ou visualiseur local :
termux-open site/index.html
```

---

## ☁️ Activer l'Exécution Cloud 24h/24 (Ordinateur Éteint)

Grâce au fichier configuré `.github/workflows/agent.yml` :

1. **Créer un dépôt GitHub** :
   Créez un dépôt privé ou public sur GitHub (ex: `auto-income-ai`).
2. **Pousser le code** :
   ```bash
   git init
   git add .
   git commit -m "feat: initial commit auto-income ai"
   git remote add origin https://github.com/VOTRE_PSEUDO/auto-income-ai.git
   git push -u origin main
   ```
3. **Activer GitHub Actions** :
   - Rendez-vous sur votre dépôt dans l'onglet **Actions**.
   - Le workflow *Auto-Income AI Autonomous Cloud Engine* est déjà paramétré pour s'exécuter automatiquement **toutes les 6 heures**.
   - Vous pouvez également cliquer sur **Run workflow** pour déclencher un cycle à la demande.
4. **Activer GitHub Pages (Facultatif mais recommandé)** :
   - Dans **Settings > Pages**, choisissez de publier depuis le dossier `/site` ou la branche configurée.
   - Votre tableau de bord et vos livrables seront accessibles partout dans le monde via une URL sécurisée `https://VOTRE_PSEUDO.github.io/auto-income-ai`.

---

## 🇲🇬 Comment Encaisser vos Premiers Revenus depuis Madagascar

| Canal de Vente | Plateforme Recommandée | Comment Retirer son Argent à Madagascar |
| :--- | :--- | :--- |
| **Micro-Paiements & Crypto** | Vente directe / P2P | Adresse USDT TRC20 ➔ Conversion directe en **MVola** ou **Orange Money** via Binance P2P (< 10 min). |
| **Microservices Freelance** | ComeUp (5euros) | Virement bancaire direct vers compte bancaire local (BNI, BOA, BMOI) ou compte Payoneer. |
| **Produits Digitaux** | Gumroad / Ko-fi | Payout hebdomadaire vers votre compte Payoneer, puis retrait par carte Mastercard ou virement local. |

---

## 🧪 Résultats des Tests

L'intégralité du système est couverte par des tests unitaires automatisés validant :
- L'audit qualité (QA Score > 80/100).
- La déduplication par empreinte SHA-256.
- La persistance des transactions financières à coût 0,00 $.
- Le respect strict des contraintes techniques pour débutants.
