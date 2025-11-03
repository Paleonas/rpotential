#!/usr/bin/env python3
"""
Implémentation RAG (Retrieval-Augmented Generation) pour requêtes conversationnelles
Utilise PostgreSQL + pgvector pour la recherche vectorielle et OpenAI GPT-4 pour la génération
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI
from typing import List, Dict, Optional
from dotenv import load_dotenv
import json

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/legal_db")
EMBEDDING_MODEL = "text-embedding-ada-002"
LLM_MODEL = "gpt-4-turbo-preview"
MAX_CONTEXT_DOCUMENTS = 10
SIMILARITY_THRESHOLD = 0.7

class RAGQueryEngine:
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.db_conn = psycopg2.connect(DATABASE_URL)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Génère un embedding pour un texte"""
        response = self.openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    
    def vector_search(self, query_embedding: List[float], limit: int = MAX_CONTEXT_DOCUMENTS) -> List[Dict]:
        """Recherche vectorielle dans la base de données"""
        cur = self.db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Convertir embedding en format PostgreSQL
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        query = """
            SELECT 
                id,
                title,
                content,
                summary,
                document_type,
                category_path,
                metadata,
                1 - (embedding <=> %s::vector) as similarity
            FROM legal_documents
            WHERE embedding IS NOT NULL
            AND 1 - (embedding <=> %s::vector) > %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        cur.execute(query, (embedding_str, embedding_str, SIMILARITY_THRESHOLD, embedding_str, limit))
        results = cur.fetchall()
        cur.close()
        
        return [dict(row) for row in results]
    
    def hybrid_search(self, query: str, query_embedding: List[float], limit: int = MAX_CONTEXT_DOCUMENTS) -> List[Dict]:
        """Recherche hybride: vectorielle + full-text"""
        cur = self.db_conn.cursor(cursor_factory=RealDictCursor)
        
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        # Recherche hybride combinant vector search et full-text search
        query_sql = """
            WITH vector_results AS (
                SELECT 
                    id,
                    title,
                    content,
                    summary,
                    document_type,
                    category_path,
                    metadata,
                    1 - (embedding <=> %s::vector) as similarity,
                    'vector' as search_type
                FROM legal_documents
                WHERE embedding IS NOT NULL
                AND 1 - (embedding <=> %s::vector) > %s
            ),
            text_results AS (
                SELECT 
                    id,
                    title,
                    content,
                    summary,
                    document_type,
                    category_path,
                    metadata,
                    ts_rank(to_tsvector('french', title || ' ' || COALESCE(content, '') || ' ' || COALESCE(summary, '')), 
                            to_tsquery('french', %s)) as similarity,
                    'text' as search_type
                FROM legal_documents
                WHERE to_tsvector('french', title || ' ' || COALESCE(content, '') || ' ' || COALESCE(summary, '')) 
                      @@ to_tsquery('french', %s)
            )
            SELECT DISTINCT ON (id)
                id,
                title,
                content,
                summary,
                document_type,
                category_path,
                metadata,
                COALESCE(vr.similarity, tr.similarity) as similarity,
                COALESCE(vr.search_type, tr.search_type) as search_type
            FROM vector_results vr
            FULL OUTER JOIN text_results tr USING (id)
            ORDER BY id, similarity DESC
            LIMIT %s
        """
        
        # Préparer query pour full-text search
        query_terms = ' & '.join(query.split())
        query_terms = query_terms.replace("'", "''")
        
        cur.execute(query_sql, (embedding_str, embedding_str, SIMILARITY_THRESHOLD, query_terms, query_terms, limit))
        results = cur.fetchall()
        cur.close()
        
        return [dict(row) for row in results]
    
    def build_context(self, documents: List[Dict]) -> str:
        """Construit le contexte pour le prompt LLM"""
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            doc_str = f"""
[Document {i}]
Titre: {doc['title']}
Type: {doc['document_type']}
Catégorie: {' > '.join(doc.get('category_path', []))}
Score de similarité: {doc.get('similarity', 0):.3f}
"""
            if doc.get('summary'):
                doc_str += f"Résumé: {doc['summary']}\n"
            
            # Limiter la longueur du contenu
            content = doc.get('content', '')[:2000]  # ~500 tokens
            doc_str += f"Contenu: {content}\n"
            
            if doc.get('metadata'):
                metadata = doc.get('metadata', {})
                if isinstance(metadata, dict):
                    if metadata.get('references_legales'):
                        doc_str += f"Références légales: {', '.join(metadata.get('references_legales', []))}\n"
            
            doc_str += "\n---\n"
            context_parts.append(doc_str)
        
        return "\n".join(context_parts)
    
    def build_prompt(self, user_question: str, context: str) -> str:
        """Construit le prompt pour le LLM"""
        system_instruction = """Tu es un expert en droit du travail français. Tu assistes les utilisateurs en répondant à leurs questions sur la base de documents juridiques fournis.

Instructions:
1. Réponds TOUJOURS en français
2. Utilise UNIQUEMENT les informations fournies dans les documents du contexte
3. Cite les sources (titre, type, catégorie) quand tu fais référence à un document
4. Si tu ne trouves pas la réponse dans les documents, dis-le clairement
5. Propose des solutions pratiques et concrètes quand c'est possible
6. Mentionne les références légales (articles, codes) si disponibles
7. Sois précis et factuel

Format de réponse:
- Réponse directe à la question
- Citations des sources utilisées
- Références légales si disponibles
- Conseils pratiques si applicable"""
        
        user_prompt = f"""Question de l'utilisateur: {user_question}

Documents de référence:
{context}

Réponds à la question de l'utilisateur en utilisant uniquement les informations des documents ci-dessus."""
        
        return system_instruction, user_prompt
    
    def query(self, user_question: str, use_hybrid: bool = True) -> Dict:
        """Effectue une requête RAG complète"""
        print(f"🔍 Recherche de documents pertinents pour: {user_question[:100]}...")
        
        # 1. Générer embedding de la question
        query_embedding = self.generate_embedding(user_question)
        
        # 2. Recherche vectorielle ou hybride
        if use_hybrid:
            documents = self.hybrid_search(user_question, query_embedding)
        else:
            documents = self.vector_search(query_embedding)
        
        if not documents:
            return {
                "answer": "Je n'ai pas trouvé de documents pertinents dans la base de données pour répondre à votre question.",
                "documents": [],
                "metadata": {
                    "model": LLM_MODEL,
                    "documents_found": 0
                }
            }
        
        print(f"✓ {len(documents)} documents pertinents trouvés")
        
        # 3. Construire le contexte
        context = self.build_context(documents)
        
        # 4. Construire le prompt
        system_instruction, user_prompt = self.build_prompt(user_question, context)
        
        # 5. Appel au LLM
        print(f"🤖 Génération de la réponse avec {LLM_MODEL}...")
        
        response = self.openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        answer = response.choices[0].message.content
        
        # 6. Préparer la réponse avec métadonnées
        result = {
            "answer": answer,
            "documents": [
                {
                    "id": str(doc["id"]),
                    "title": doc["title"],
                    "type": doc["document_type"],
                    "category": doc.get("category_path", []),
                    "similarity": float(doc.get("similarity", 0))
                }
                for doc in documents
            ],
            "metadata": {
                "model": LLM_MODEL,
                "documents_found": len(documents),
                "similarity_threshold": SIMILARITY_THRESHOLD,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
            }
        }
        
        return result
    
    def save_conversation(self, user_id: Optional[str], user_question: str, response: Dict):
        """Sauvegarde la conversation dans la base de données"""
        cur = self.db_conn.cursor()
        
        # Créer ou récupérer la conversation
        cur.execute("""
            INSERT INTO conversations (user_id, title)
            VALUES (%s, %s)
            RETURNING id
        """, (user_id, user_question[:100]))
        
        conversation_id = cur.fetchone()[0]
        
        # Sauvegarder le message utilisateur
        document_ids = [doc["id"] for doc in response["documents"]]
        
        cur.execute("""
            INSERT INTO conversation_messages (conversation_id, role, content, retrieved_documents, metadata)
            VALUES (%s, 'user', %s, %s, %s)
            RETURNING id
        """, (conversation_id, user_question, document_ids, json.dumps({})))
        
        user_message_id = cur.fetchone()[0]
        
        # Sauvegarder la réponse de l'assistant
        cur.execute("""
            INSERT INTO conversation_messages (conversation_id, role, content, retrieved_documents, metadata)
            VALUES (%s, 'assistant', %s, %s, %s)
        """, (conversation_id, response["answer"], document_ids, json.dumps(response["metadata"])))
        
        # Mettre à jour les documents référencés dans la conversation
        cur.execute("""
            UPDATE conversations
            SET context_documents = %s
            WHERE id = %s
        """, (document_ids, conversation_id))
        
        self.db_conn.commit()
        cur.close()
        
        return conversation_id
    
    def close(self):
        """Ferme la connexion à la base de données"""
        self.db_conn.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python rag_query.py 'Votre question ici'")
        sys.exit(1)
    
    user_question = " ".join(sys.argv[1:])
    
    engine = RAGQueryEngine()
    
    try:
        result = engine.query(user_question, use_hybrid=True)
        
        print("\n" + "="*80)
        print("RÉPONSE:")
        print("="*80)
        print(result["answer"])
        print("\n" + "="*80)
        print("SOURCES UTILISÉES:")
        print("="*80)
        for i, doc in enumerate(result["documents"], 1):
            print(f"\n{i}. {doc['title']}")
            print(f"   Type: {doc['type']}")
            print(f"   Catégorie: {' > '.join(doc.get('category', []))}")
            print(f"   Similarité: {doc['similarity']:.3f}")
        
        # Sauvegarder la conversation (optionnel)
        # conversation_id = engine.save_conversation(None, user_question, result)
        # print(f"\n✓ Conversation sauvegardée (ID: {conversation_id})")
        
    finally:
        engine.close()

if __name__ == "__main__":
    main()
