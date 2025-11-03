-- ============================================
-- Schema de Base de Données pour Plateforme Juridique
-- Optimisé pour V1 (Navigation) et V2 (IA Conversationnelle)
-- ============================================

-- Extension pgvector pour recherche vectorielle
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 1. CATÉGORIES (Arborescence)
-- ============================================
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    parent_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    description TEXT,
    order_index INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_slug ON categories(slug);

-- ============================================
-- 2. DOCUMENTS JURIDIQUES (Table principale)
-- ============================================
CREATE TABLE legal_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT, -- Résumé automatique
    document_type TEXT NOT NULL CHECK (document_type IN ('loi', 'jurisprudence', 'synthese', 'template', 'article', 'guide')),
    category_id UUID REFERENCES categories(id),
    category_path TEXT[], -- Chemin complet: ['droit_travail', 'conges', 'payes']
    tags TEXT[],
    metadata JSONB DEFAULT '{}', -- {source, date_publication, auteur, niveau, references_legales}
    embedding VECTOR(1536), -- Embedding OpenAI ada-002
    search_keywords TEXT[], -- Mots-clés extraits
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

-- Index pour recherche vectorielle (cosine similarity)
CREATE INDEX idx_legal_documents_embedding ON legal_documents 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Index pour recherche full-text (français)
CREATE INDEX idx_legal_documents_fts ON legal_documents 
USING GIN (to_tsvector('french', COALESCE(title, '') || ' ' || COALESCE(content, '') || ' ' || COALESCE(summary, '')));

-- Index pour catégories
CREATE INDEX idx_legal_documents_category ON legal_documents(category_id);
CREATE INDEX idx_legal_documents_category_path ON legal_documents USING GIN (category_path);
CREATE INDEX idx_legal_documents_type ON legal_documents(document_type);
CREATE INDEX idx_legal_documents_tags ON legal_documents USING GIN (tags);

-- Index pour métadonnées JSONB
CREATE INDEX idx_legal_documents_metadata ON legal_documents USING GIN (metadata);

-- ============================================
-- 3. JURISPRUDENCE (Extension)
-- ============================================
CREATE TABLE jurisprudence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES legal_documents(id) ON DELETE CASCADE,
    court_name TEXT,
    case_number TEXT,
    decision_date DATE,
    summary TEXT,
    key_points TEXT[],
    parties TEXT[],
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_jurisprudence_document ON jurisprudence(document_id);
CREATE INDEX idx_jurisprudence_date ON jurisprudence(decision_date);
CREATE INDEX idx_jurisprudence_embedding ON jurisprudence 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================
-- 4. TEMPLATES (Extension)
-- ============================================
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES legal_documents(id) ON DELETE CASCADE,
    template_type TEXT CHECK (template_type IN ('lettre', 'contrat', 'procedure', 'declaration', 'autre')),
    variables JSONB, -- {variable_name: {type, description, required, default_value}}
    use_cases TEXT[],
    example_usage TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_templates_document ON templates(document_id);
CREATE INDEX idx_templates_type ON templates(template_type);
CREATE INDEX idx_templates_embedding ON templates 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================
-- 5. SYNTHÈSES (Extension)
-- ============================================
CREATE TABLE syntheses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES legal_documents(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    legal_basis TEXT[], -- Articles de loi, codes
    application_scope TEXT,
    key_references UUID[], -- Références vers autres documents
    related_topics TEXT[],
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_syntheses_document ON syntheses(document_id);
CREATE INDEX idx_syntheses_topic ON syntheses(topic);
CREATE INDEX idx_syntheses_embedding ON syntheses 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================
-- 6. RELATIONS ENTRE DOCUMENTS
-- ============================================
CREATE TABLE document_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_document_id UUID REFERENCES legal_documents(id) ON DELETE CASCADE,
    target_document_id UUID REFERENCES legal_documents(id) ON DELETE CASCADE,
    relation_type TEXT CHECK (relation_type IN ('references', 'implements', 'clarifies', 'contradicts', 'extends', 'supersedes')),
    strength FLOAT DEFAULT 1.0 CHECK (strength >= 0.0 AND strength <= 1.0),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_document_id, target_document_id, relation_type)
);

CREATE INDEX idx_relations_source ON document_relations(source_document_id);
CREATE INDEX idx_relations_target ON document_relations(target_document_id);
CREATE INDEX idx_relations_type ON document_relations(relation_type);

-- ============================================
-- 7. MÉTADONNÉES DE RECHERCHE
-- ============================================
CREATE TABLE search_metadata (
    document_id UUID PRIMARY KEY REFERENCES legal_documents(id) ON DELETE CASCADE,
    search_keywords TEXT[],
    common_queries TEXT[], -- Questions fréquentes
    click_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    relevance_score FLOAT DEFAULT 0.0,
    popularity_score FLOAT DEFAULT 0.0,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_search_metadata_keywords ON search_metadata USING GIN (search_keywords);
CREATE INDEX idx_search_metadata_popularity ON search_metadata(popularity_score DESC);

-- ============================================
-- 8. CONVERSATIONS (Pour V2 - IA)
-- ============================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    title TEXT,
    context_documents UUID[], -- Documents référencés dans la conversation
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_documents ON conversations USING GIN (context_documents);

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    retrieved_documents UUID[], -- Documents utilisés pour générer la réponse
    metadata JSONB DEFAULT '{}', -- {model, tokens, confidence, etc}
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON conversation_messages(conversation_id);
CREATE INDEX idx_messages_role ON conversation_messages(role);
CREATE INDEX idx_messages_created ON conversation_messages(created_at DESC);

-- ============================================
-- 9. FEEDBACK UTILISATEURS (Amélioration continue)
-- ============================================
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    document_id UUID REFERENCES legal_documents(id) ON DELETE SET NULL,
    message_id UUID REFERENCES conversation_messages(id) ON DELETE SET NULL,
    feedback_type TEXT CHECK (feedback_type IN ('helpful', 'not_helpful', 'incorrect', 'incomplete')),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_feedback_conversation ON user_feedback(conversation_id);
CREATE INDEX idx_feedback_document ON user_feedback(document_id);
CREATE INDEX idx_feedback_type ON user_feedback(feedback_type);

-- ============================================
-- 10. VUES UTILES
-- ============================================

-- Vue: Documents avec leurs relations
CREATE VIEW documents_with_relations AS
SELECT 
    d.id,
    d.title,
    d.document_type,
    d.category_path,
    COUNT(DISTINCT dr.target_document_id) as related_count,
    ARRAY_AGG(DISTINCT dr.relation_type) as relation_types
FROM legal_documents d
LEFT JOIN document_relations dr ON d.id = dr.source_document_id
GROUP BY d.id, d.title, d.document_type, d.category_path;

-- Vue: Statistiques par catégorie
CREATE VIEW category_stats AS
SELECT 
    c.id,
    c.name,
    c.slug,
    COUNT(d.id) as document_count,
    COUNT(DISTINCT d.document_type) as type_count
FROM categories c
LEFT JOIN legal_documents d ON d.category_id = c.id
GROUP BY c.id, c.name, c.slug;

-- ============================================
-- 11. FONCTIONS UTILES
-- ============================================

-- Fonction: Recherche vectorielle avec seuil
CREATE OR REPLACE FUNCTION vector_search(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10,
    doc_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    document_type TEXT,
    similarity FLOAT,
    category_path TEXT[]
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ld.id,
        ld.title,
        ld.content,
        ld.document_type,
        1 - (ld.embedding <=> query_embedding) as similarity,
        ld.category_path
    FROM legal_documents ld
    WHERE 
        (doc_type IS NULL OR ld.document_type = doc_type)
        AND ld.embedding IS NOT NULL
        AND 1 - (ld.embedding <=> query_embedding) > match_threshold
    ORDER BY ld.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Fonction: Mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers pour updated_at
CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_legal_documents_updated_at BEFORE UPDATE ON legal_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 12. DONNÉES DE TEST (Seed)
-- ============================================

-- Catégories exemple
INSERT INTO categories (name, slug, description, order_index) VALUES
('Droit du Travail', 'droit_travail', 'Réglementation du travail en France', 1),
('Congés', 'conges', 'Tous types de congés', 2),
('Contrats', 'contrats', 'Types de contrats de travail', 3);

-- Mettre à jour parent_id pour sous-catégories
UPDATE categories SET parent_id = (SELECT id FROM categories WHERE slug = 'droit_travail')
WHERE slug IN ('conges', 'contrats');

INSERT INTO categories (name, slug, parent_id, description, order_index) VALUES
('Congés Payés', 'conges_payes', (SELECT id FROM categories WHERE slug = 'conges'), 'Congés annuels payés', 1),
('Congés Maternité/Paternité', 'conges_familiaux', (SELECT id FROM categories WHERE slug = 'conges'), 'Congés pour naissance', 2),
('CDI', 'cdi', (SELECT id FROM categories WHERE slug = 'contrats'), 'Contrat à durée indéterminée', 1),
('CDD', 'cdd', (SELECT id FROM categories WHERE slug = 'contrats'), 'Contrat à durée déterminée', 2);
