# Structure de Base de Données pour Requêtage IA

## Résumé Exécutif

Cette proposition décrit une architecture de base de données optimisée pour:
1. **V1**: Navigation hiérarchique, filtres, recherche textuelle
2. **V2**: Requêtes conversationnelles IA (style ChatGPT) sur base fermée

## Architecture Recommandée

### Option 1: Base de Données Hybride (Recommandée)

**Stack technique:**
- **PostgreSQL** pour données structurées et relations
- **Vector Database (Qdrant/Pinecone/Weaviate)** pour embeddings et recherche sémantique
- **Elasticsearch** optionnel pour recherche full-text avancée

### Option 2: Solution Unifiée Moderne

**Stack technique:**
- **PostgreSQL + pgvector** extension (intègre vecteurs dans PostgreSQL)
- **Supabase** (PostgreSQL + Real-time + Vector Search)
- **Neon** (Serverless PostgreSQL avec pgvector)

---

## Schéma de Base de Données

### 1. Tables Principales

#### Table: `legal_documents`
```sql
CREATE TABLE legal_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    document_type TEXT NOT NULL, -- 'loi', 'jurisprudence', 'synthese', 'template'
    category_path TEXT[], -- ['droit_travail', 'conges', 'annuel']
    tags TEXT[],
    metadata JSONB, -- {source, date_publication, auteur, etc}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    embedding VECTOR(1536) -- Pour recherche sémantique (OpenAI ada-002)
);

-- Index pour recherche vectorielle
CREATE INDEX ON legal_documents USING ivfflat (embedding vector_cosine_ops);

-- Index pour recherche textuelle
CREATE INDEX ON legal_documents USING GIN (to_tsvector('french', title || ' ' || content));

-- Index pour catégories
CREATE INDEX ON legal_documents USING GIN (category_path);
```

#### Table: `categories` (Arborescence)
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    parent_id UUID REFERENCES categories(id),
    description TEXT,
    order_index INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index pour hiérarchie
CREATE INDEX ON categories(parent_id);
```

#### Table: `jurisprudence`
```sql
CREATE TABLE jurisprudence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES legal_documents(id),
    court_name TEXT,
    case_number TEXT,
    decision_date DATE,
    summary TEXT,
    key_points TEXT[],
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Table: `templates`
```sql
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES legal_documents(id),
    template_type TEXT, -- 'lettre', 'contrat', 'procedure'
    variables JSONB, -- {variable_name: {type, description, required}}
    use_cases TEXT[],
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Table: `syntheses`
```sql
CREATE TABLE syntheses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES legal_documents(id),
    topic TEXT NOT NULL,
    legal_basis TEXT[],
    application_scope TEXT,
    key_references UUID[], -- Références vers autres documents
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Table: `conversations` (Pour V2 - Historique)
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    context_documents UUID[], -- Documents référencés dans la conversation
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    role TEXT NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    retrieved_documents UUID[], -- Documents utilisés pour la réponse
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Table de Relations et Métadonnées

#### Table: `document_relations`
```sql
CREATE TABLE document_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_document_id UUID REFERENCES legal_documents(id),
    target_document_id UUID REFERENCES legal_documents(id),
    relation_type TEXT, -- 'references', 'implements', 'clarifies', 'contradicts'
    strength FLOAT, -- 0.0 à 1.0
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_document_id, target_document_id, relation_type)
);
```

#### Table: `search_metadata`
```sql
CREATE TABLE search_metadata (
    document_id UUID REFERENCES legal_documents(id),
    search_keywords TEXT[],
    common_queries TEXT[],
    click_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    relevance_score FLOAT
);
```

---

## Stratégie de Classification et Maintenance

### 1. Taxonomie Hiérarchique Recommandée

```
Droit du Travail
├── Congés
│   ├── Congés Payés
│   │   ├── Calcul
│   │   ├── Prise
│   │   └── Solde
│   ├── Congés Maternité/Paternité
│   └── Congés Sans Solde
├── Contrats
│   ├── CDI
│   ├── CDD
│   └── Stage
└── Procédures
    ├── Licenciement
    └── Démission
```

### 2. Métadonnées Standardisées

Chaque document doit avoir:
- **Type**: loi, jurisprudence, synthèse, template
- **Catégorie**: chemin hiérarchique complet
- **Tags**: mots-clés libres
- **Dates**: publication, validité, mise à jour
- **Source**: origine du document
- **Références légales**: articles de loi, codes
- **Niveau de complexité**: débutant, intermédiaire, expert

### 3. Embeddings et Indexation

**Processus d'indexation:**
1. Générer embeddings pour chaque document (via OpenAI ada-002 ou équivalent)
2. Extraire entités nommées (lois, articles, dates)
3. Créer résumé automatique
4. Identifier relations entre documents
5. Indexer pour recherche full-text

---

## Implémentation V1 (Navigation/Recherche)

### Requêtes Typiques

```sql
-- Recherche par catégorie
SELECT * FROM legal_documents 
WHERE 'conges' = ANY(category_path)
AND document_type = 'synthese';

-- Recherche full-text
SELECT *, ts_rank(to_tsvector('french', title || ' ' || content), query) AS rank
FROM legal_documents, to_tsquery('french', 'congés & payés') query
WHERE to_tsvector('french', title || ' ' || content) @@ query
ORDER BY rank DESC;

-- Recherche avec filtres multiples
SELECT * FROM legal_documents
WHERE document_type = ANY(ARRAY['jurisprudence', 'synthese'])
AND category_path && ARRAY['droit_travail', 'conges']
AND metadata->>'niveau' = 'intermediaire';
```

---

## Implémentation V2 (Conversation IA)

### Architecture RAG (Retrieval-Augmented Generation)

**Workflow:**
1. **User Query** → "Quels sont mes droits en cas de licenciement abusif?"
2. **Embedding Query** → Vector search dans la base
3. **Retrieval** → Top-K documents pertinents (k=5-10)
4. **Context Building** → Construire contexte avec documents + métadonnées
5. **LLM Query** → Envoyer à GPT-4/5 avec contexte + instructions
6. **Response** → Réponse avec citations des sources

### Schéma de Requête RAG

```python
# Pseudo-code pour requête RAG
def query_rag(user_question: str):
    # 1. Générer embedding de la question
    question_embedding = openai.embeddings.create(
        input=user_question,
        model="text-embedding-ada-002"
    )
    
    # 2. Recherche vectorielle (cosine similarity)
    similar_docs = vector_search(
        query_vector=question_embedding,
        limit=10,
        threshold=0.7
    )
    
    # 3. Enrichir avec contexte hiérarchique
    enriched_context = []
    for doc in similar_docs:
        # Ajouter catégorie, références, métadonnées
        enriched_context.append({
            'content': doc.content,
            'title': doc.title,
            'category': doc.category_path,
            'type': doc.document_type,
            'references': get_references(doc.id)
        })
    
    # 4. Construire prompt pour LLM
    prompt = build_rag_prompt(
        question=user_question,
        context=enriched_context,
        instructions="Répondre en français, citer les sources, proposer des solutions pratiques"
    )
    
    # 5. Appel LLM
    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Tu es un expert en droit du travail français..."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    # 6. Sauvegarder conversation
    save_conversation(user_question, response, similar_docs)
    
    return response
```

### Optimisations pour V2

1. **Chunking Intelligent**: Diviser gros documents en chunks avec overlap
2. **Re-ranking**: Utiliser modèle de re-ranking (Cohere rerank) après vector search
3. **Hybrid Search**: Combiner vector search + keyword search
4. **Context Window Management**: Gérer tokens limit du LLM
5. **Caching**: Cache réponses pour questions fréquentes

---

## Structure de Fichiers Recommandée

```
database/
├── migrations/
│   ├── 001_initial_schema.sql
│   ├── 002_add_embeddings.sql
│   └── 003_add_conversations.sql
├── seeds/
│   ├── categories.sql
│   └── sample_documents.sql
└── scripts/
    ├── generate_embeddings.py
    ├── import_documents.py
    └── build_index.py

data/
├── raw/
│   ├── lois/
│   ├── jurisprudence/
│   ├── syntheses/
│   └── templates/
├── processed/
│   └── embeddings/
└── metadata/
    └── taxonomy.json
```

---

## Plan d'Action Immédiat

### Phase 1: Setup Infrastructure (Semaine 1)
- [ ] Installer PostgreSQL + pgvector ou setup Supabase/Neon
- [ ] Créer schéma de base de données
- [ ] Setup pipeline d'import de documents

### Phase 2: Classification Initiale (Semaine 2-3)
- [ ] Définir taxonomie complète (catégories)
- [ ] Classifier documents existants
- [ ] Générer embeddings pour tous les documents
- [ ] Créer index de recherche

### Phase 3: Métadonnées et Relations (Semaine 4)
- [ ] Extraire métadonnées (dates, références légales)
- [ ] Identifier relations entre documents
- [ ] Créer table de relations
- [ ] Valider qualité classification

### Phase 4: V1 Implementation (Semaine 5-6)
- [ ] API endpoints pour navigation
- [ ] Recherche full-text
- [ ] Filtres par catégorie/type
- [ ] Interface utilisateur

### Phase 5: V2 RAG Setup (Semaine 7-8)
- [ ] Implémenter vector search
- [ ] Créer pipeline RAG
- [ ] Intégrer avec LLM (OpenAI/Anthropic)
- [ ] Système de conversation persistante

---

## Outils et Services Recommandés

### Base de Données
- **Supabase**: PostgreSQL + pgvector + Real-time (gratuit jusqu'à 500MB)
- **Neon**: Serverless PostgreSQL avec branchement (gratuit jusqu'à 3GB)
- **Qdrant**: Vector DB dédiée (self-hosted ou cloud)

### Embeddings
- **OpenAI ada-002**: 1536 dimensions, $0.0001/1K tokens
- **Cohere**: Embeddings multilingues français
- **HuggingFace**: Models open-source (sentence-transformers)

### LLM pour RAG
- **OpenAI GPT-4 Turbo**: Meilleure qualité, $10/1M tokens input
- **Anthropic Claude**: Excellent pour français, bon contexte
- **Mistral**: Open-source, performant en français

### Outils de Classification
- **spaCy**: NLP pour extraction entités, classification
- **LangChain**: Framework pour RAG applications
- **LlamaIndex**: Optimisé pour recherche documentaire

---

## Bonnes Pratiques

1. **Versioning**: Versionner les documents (changements de loi)
2. **Validation**: Valider classification manuellement au début
3. **Monitoring**: Tracker qualité des réponses IA (feedback users)
4. **Mise à jour**: Processus régulier pour nouveaux documents
5. **Backup**: Backup automatique base + embeddings
6. **Sécurité**: Chiffrement données sensibles, accès contrôlé

---

## Métriques de Succès

- **V1**: Temps de réponse < 200ms, précision recherche > 90%
- **V2**: Pertinence réponses IA > 85%, citations correctes > 95%
- **Maintenance**: Documents classés < 24h après ajout

---

## Questions à Résoudre

1. Volume attendu de documents? (100, 1000, 10000+)
2. Fréquence de mise à jour? (quotidienne, hebdomadaire, mensuelle)
3. Budget pour LLM/embeddings?
4. Sensibilité des données? (RGPD, sécurité)
5. Équipe technique disponible?

---

## Conclusion

Cette structure permet:
- ✅ Navigation hiérarchique efficace (V1)
- ✅ Recherche sémantique avancée (V2)
- ✅ Requêtage conversationnel IA
- ✅ Scalabilité et maintenabilité
- ✅ Évolution future (versioning, analytics)

Prochaine étape: Valider cette architecture et commencer Phase 1.
