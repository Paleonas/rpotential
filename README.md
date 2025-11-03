# Plateforme Juridique - Structure Base de Données pour IA

## 🎯 Objectif

Cette structure permet de:
1. **V1**: Navigation hiérarchique, filtres, recherche textuelle
2. **V2**: Conversations IA (style ChatGPT) sur base de données fermée

## 📁 Structure du Projet

```
.
├── DATABASE_STRUCTURE_PROPOSAL.md  # Documentation complète de l'architecture
├── database/
│   └── schema.sql                  # Schéma SQL complet
├── scripts/
│   ├── generate_embeddings.py     # Génération d'embeddings
│   ├── rag_query.py                # Moteur RAG pour requêtes IA
│   └── import_documents.py         # Import de documents
├── requirements.txt                # Dépendances Python
├── .env.example                    # Template de configuration
└── README.md                       # Ce fichier
```

## 🚀 Installation Rapide

### 1. Prérequis

- PostgreSQL 14+ avec extension `pgvector`
- Python 3.9+
- Clé API OpenAI

### 2. Installation PostgreSQL + pgvector

```bash
# Installer PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Installer pgvector
sudo apt-get install postgresql-14-pgvector
# ou via Docker:
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password pgvector/pgvector:pg14
```

### 3. Configuration Python

```bash
# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt
```

### 4. Configuration Base de Données

```bash
# Créer la base de données
createdb legal_db

# Exécuter le schéma
psql legal_db < database/schema.sql
```

### 5. Configuration Environnement

```bash
# Copier le template
cp .env.example .env

# Éditer .env avec vos credentials
# DATABASE_URL=postgresql://user:password@localhost:5432/legal_db
# OPENAI_API_KEY=your_key_here
```

## 📊 Utilisation

### Importer des Documents

```bash
# Depuis JSON
python scripts/import_documents.py json data/documents.json

# Depuis CSV
python scripts/import_documents.py csv data/documents.csv

# Depuis Reddit chat (à adapter selon votre format)
python scripts/import_documents.py reddit data/reddit_chat.json
```

### Générer des Embeddings

```bash
# Pour tous les documents
python scripts/generate_embeddings.py

# Pour un document spécifique
python scripts/generate_embeddings.py <document_id>
```

### Requêtes RAG (Conversation IA)

```bash
python scripts/rag_query.py "Quels sont mes droits en cas de licenciement abusif?"
```

## 🗄️ Architecture de la Base de Données

### Tables Principales

- **`legal_documents`**: Documents juridiques avec embeddings
- **`categories`**: Hiérarchie de catégories
- **`jurisprudence`**: Cas de jurisprudence
- **`templates`**: Templates de documents
- **`syntheses`**: Synthèses juridiques
- **`conversations`**: Historique des conversations IA
- **`document_relations`**: Relations entre documents

Voir `DATABASE_STRUCTURE_PROPOSAL.md` pour la documentation complète.

## 🔍 Recherche

### V1: Navigation/Recherche Classique

- Recherche full-text avec PostgreSQL
- Filtres par catégorie, type, tags
- Navigation hiérarchique

### V2: Requêtes Conversationnelles IA

- Recherche vectorielle (cosine similarity)
- Recherche hybride (vector + full-text)
- RAG avec GPT-4 pour génération de réponses

## 📝 Format de Document

### JSON

```json
{
  "title": "Congés payés - Calcul",
  "content": "Le calcul des congés payés...",
  "summary": "Synthèse sur le calcul",
  "document_type": "synthese",
  "category_path": ["droit_travail", "conges", "conges_payes"],
  "tags": ["congés", "calcul", "droit"],
  "metadata": {
    "source": "Code du travail",
    "references_legales": ["Article L.3141-1", "Article L.3141-3"],
    "niveau": "intermediaire"
  }
}
```

### CSV

```csv
title,content,document_type,category_path,tags
"Congés payés","Contenu...",synthese,"droit_travail > conges","congés,calcul"
```

## 🔧 Personnalisation

### Adapter pour Reddit Chat

1. Modifier `scripts/import_documents.py` → fonction `import_from_reddit_chat()`
2. Adapter selon votre format de fichier Reddit exact
3. Définir la logique de catégorisation automatique si nécessaire

### Changer le Modèle LLM

Modifier dans `.env`:
```
LLM_MODEL=gpt-4-turbo-preview  # ou gpt-3.5-turbo, claude-3-opus, etc.
```

### Ajuster les Paramètres RAG

Modifier dans `scripts/rag_query.py`:
- `MAX_CONTEXT_DOCUMENTS`: Nombre de documents dans le contexte
- `SIMILARITY_THRESHOLD`: Seuil de similarité (0.0 à 1.0)

## 📚 Documentation Complète

Voir `DATABASE_STRUCTURE_PROPOSAL.md` pour:
- Architecture détaillée
- Stratégies de classification
- Plan d'action complet
- Bonnes pratiques
- Métriques de succès

## 🆘 Support

Pour questions ou problèmes:
1. Vérifier la configuration dans `.env`
2. Vérifier les logs d'erreur
3. Adapter les scripts selon votre format de données

## 📄 Licence

Ce projet est fourni tel quel pour votre usage interne.
