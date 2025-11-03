#!/usr/bin/env python3
"""
Script pour générer des embeddings pour les documents de la base de données
Utilise OpenAI ada-002 pour générer des embeddings vectoriels
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_values
from openai import OpenAI
import time
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/legal_db")
EMBEDDING_MODEL = "text-embedding-ada-002"
BATCH_SIZE = 100  # Nombre de documents à traiter par batch
MAX_RETRIES = 3

def get_db_connection():
    """Établit une connexion à la base de données"""
    return psycopg2.connect(DATABASE_URL)

def get_documents_without_embeddings(limit: Optional[int] = None):
    """Récupère les documents qui n'ont pas encore d'embedding"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
        SELECT id, title, content, summary, document_type
        FROM legal_documents
        WHERE embedding IS NULL
        ORDER BY created_at ASC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    cur.execute(query)
    documents = cur.fetchall()
    cur.close()
    conn.close()
    
    return documents

def generate_embedding(text: str, client: OpenAI) -> List[float]:
    """Génère un embedding pour un texte donné"""
    text = text.replace("\n", " ").strip()
    
    # Limiter la longueur du texte (max ~8000 tokens pour ada-002)
    if len(text) > 8000:
        text = text[:8000]
    
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Erreur lors de la génération d'embedding: {e}")
        raise

def generate_embeddings_batch(texts: List[str], client: OpenAI) -> List[List[float]]:
    """Génère des embeddings pour un batch de textes"""
    embeddings = []
    for text in texts:
        try:
            embedding = generate_embedding(text, client)
            embeddings.append(embedding)
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Erreur pour un document: {e}")
            embeddings.append(None)
    return embeddings

def prepare_text_for_embedding(title: str, content: str, summary: Optional[str] = None, doc_type: Optional[str] = None) -> str:
    """Prépare le texte pour l'embedding en combinant title, summary et content"""
    parts = []
    
    if title:
        parts.append(f"Titre: {title}")
    
    if summary:
        parts.append(f"Résumé: {summary}")
    
    if doc_type:
        parts.append(f"Type: {doc_type}")
    
    parts.append(f"Contenu: {content}")
    
    return "\n".join(parts)

def update_document_embeddings(document_ids: List[str], embeddings: List[List[float]]):
    """Met à jour les embeddings dans la base de données"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Préparer les données pour la mise à jour
    data = [(embedding, doc_id) for embedding, doc_id in zip(embeddings, document_ids) if embedding is not None]
    
    if not data:
        print("Aucun embedding valide à mettre à jour")
        cur.close()
        conn.close()
        return
    
    query = """
        UPDATE legal_documents
        SET embedding = %s::vector
        WHERE id = %s
    """
    
    execute_values(cur, query, data, template=None, page_size=100)
    conn.commit()
    
    updated_count = cur.rowcount
    cur.close()
    conn.close()
    
    print(f"✓ {updated_count} embeddings mis à jour dans la base de données")

def process_all_documents():
    """Traite tous les documents sans embedding"""
    print("🚀 Démarrage de la génération d'embeddings...")
    
    if not OPENAI_API_KEY:
        print("❌ Erreur: OPENAI_API_KEY non définie")
        sys.exit(1)
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    total_processed = 0
    total_errors = 0
    
    while True:
        # Récupérer un batch de documents
        documents = get_documents_without_embeddings(limit=BATCH_SIZE)
        
        if not documents:
            print(f"\n✅ Traitement terminé! {total_processed} documents traités")
            break
        
        print(f"\n📄 Traitement de {len(documents)} documents...")
        
        document_ids = []
        texts = []
        
        for doc_id, title, content, summary, doc_type in documents:
            document_ids.append(str(doc_id))
            text = prepare_text_for_embedding(title, content, summary, doc_type)
            texts.append(text)
        
        # Générer les embeddings
        try:
            embeddings = generate_embeddings_batch(texts, client)
            
            # Mettre à jour la base de données
            update_document_embeddings(document_ids, embeddings)
            
            successful = sum(1 for e in embeddings if e is not None)
            total_processed += successful
            total_errors += len(embeddings) - successful
            
            print(f"✓ Batch terminé: {successful}/{len(documents)} réussis")
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement du batch: {e}")
            total_errors += len(documents)
        
        # Attendre un peu avant le prochain batch
        time.sleep(1)
    
    print(f"\n📊 Résumé final:")
    print(f"   - Documents traités: {total_processed}")
    print(f"   - Erreurs: {total_errors}")

def process_single_document(doc_id: str):
    """Traite un document spécifique"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, title, content, summary, document_type
        FROM legal_documents
        WHERE id = %s
    """, (doc_id,))
    
    doc = cur.fetchone()
    cur.close()
    conn.close()
    
    if not doc:
        print(f"❌ Document {doc_id} non trouvé")
        return
    
    doc_id, title, content, summary, doc_type = doc
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    text = prepare_text_for_embedding(title, content, summary, doc_type)
    
    print(f"📄 Génération d'embedding pour: {title}")
    embedding = generate_embedding(text, client)
    update_document_embeddings([str(doc_id)], [embedding])
    print(f"✅ Embedding généré avec succès")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Traiter un document spécifique
        doc_id = sys.argv[1]
        process_single_document(doc_id)
    else:
        # Traiter tous les documents
        process_all_documents()
