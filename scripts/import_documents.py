#!/usr/bin/env python3
"""
Script pour importer des documents dans la base de données
Supporte plusieurs formats: JSON, CSV, ou Reddit chat data
"""

import os
import sys
import json
import csv
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/legal_db")

def get_db_connection():
    """Établit une connexion à la base de données"""
    return psycopg2.connect(DATABASE_URL)

def get_category_id(category_path: List[str], conn) -> Optional[str]:
    """Récupère ou crée les catégories nécessaires et retourne l'ID final"""
    cur = conn.cursor()
    
    parent_id = None
    for category_slug in category_path:
        # Nettoyer le slug
        category_slug = category_slug.lower().replace(' ', '_')
        
        # Chercher la catégorie
        cur.execute("""
            SELECT id FROM categories WHERE slug = %s
        """, (category_slug,))
        
        result = cur.fetchone()
        
        if result:
            parent_id = result[0]
        else:
            # Créer la catégorie
            category_name = category_slug.replace('_', ' ').title()
            cur.execute("""
                INSERT INTO categories (name, slug, parent_id)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (category_name, category_slug, parent_id))
            
            parent_id = cur.fetchone()[0]
            conn.commit()
    
    cur.close()
    return parent_id

def import_document(
    title: str,
    content: str,
    document_type: str,
    category_path: List[str],
    summary: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict] = None,
    conn = None
) -> str:
    """Importe un document dans la base de données"""
    if conn is None:
        conn = get_db_connection()
        close_conn = True
    else:
        close_conn = False
    
    cur = conn.cursor()
    
    # Récupérer ou créer la catégorie
    category_id = None
    if category_path:
        category_id = get_category_id(category_path, conn)
    
    # Insérer le document
    cur.execute("""
        INSERT INTO legal_documents (
            title, content, summary, document_type,
            category_id, category_path, tags, metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        RETURNING id
    """, (
        title,
        content,
        summary,
        document_type,
        category_id,
        category_path,
        tags or [],
        json.dumps(metadata or {})
    ))
    
    doc_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    
    if close_conn:
        conn.close()
    
    return doc_id

def import_from_json(json_file: str):
    """Importe des documents depuis un fichier JSON"""
    print(f"📂 Lecture du fichier JSON: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        data = [data]
    
    conn = get_db_connection()
    imported = 0
    errors = 0
    
    for doc_data in data:
        try:
            # Valider les champs requis
            title = doc_data.get('title', 'Sans titre')
            content = doc_data.get('content', doc_data.get('text', ''))
            
            if not content:
                print(f"⚠️  Document ignoré (pas de contenu): {title}")
                errors += 1
                continue
            
            doc_id = import_document(
                title=title,
                content=content,
                document_type=doc_data.get('document_type', 'article'),
                category_path=doc_data.get('category_path', []),
                summary=doc_data.get('summary'),
                tags=doc_data.get('tags', []),
                metadata=doc_data.get('metadata', {}),
                conn=conn
            )
            
            imported += 1
            print(f"✓ Importé: {title} (ID: {doc_id})")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'import: {e}")
            errors += 1
    
    conn.close()
    print(f"\n📊 Résumé: {imported} documents importés, {errors} erreurs")

def import_from_csv(csv_file: str):
    """Importe des documents depuis un fichier CSV"""
    print(f"📂 Lecture du fichier CSV: {csv_file}")
    
    conn = get_db_connection()
    imported = 0
    errors = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                title = row.get('title', 'Sans titre')
                content = row.get('content', row.get('text', ''))
                
                if not content:
                    print(f"⚠️  Document ignoré (pas de contenu): {title}")
                    errors += 1
                    continue
                
                # Parser category_path si présent
                category_path = []
                if row.get('category_path'):
                    category_path = [c.strip() for c in row['category_path'].split('>')]
                
                # Parser tags si présent
                tags = []
                if row.get('tags'):
                    tags = [t.strip() for t in row['tags'].split(',')]
                
                # Parser metadata si présent
                metadata = {}
                if row.get('metadata'):
                    try:
                        metadata = json.loads(row['metadata'])
                    except:
                        pass
                
                doc_id = import_document(
                    title=title,
                    content=content,
                    document_type=row.get('document_type', 'article'),
                    category_path=category_path,
                    summary=row.get('summary'),
                    tags=tags,
                    metadata=metadata,
                    conn=conn
                )
                
                imported += 1
                print(f"✓ Importé: {title} (ID: {doc_id})")
                
            except Exception as e:
                print(f"❌ Erreur lors de l'import: {e}")
                errors += 1
    
    conn.close()
    print(f"\n📊 Résumé: {imported} documents importés, {errors} erreurs")

def import_from_reddit_chat(reddit_file: str):
    """Importe des données depuis un fichier Reddit chat"""
    print(f"📂 Lecture du fichier Reddit: {reddit_file}")
    
    # Format attendu: JSON avec messages Reddit
    with open(reddit_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conn = get_db_connection()
    imported = 0
    errors = 0
    
    # Adapter selon le format exact de votre fichier Reddit
    # Cette fonction est un template à adapter
    
    messages = data.get('messages', []) if isinstance(data, dict) else data
    
    for msg in messages:
        try:
            # Extraire le contenu du message Reddit
            # À adapter selon votre format exact
            title = msg.get('subject', msg.get('title', 'Message Reddit'))
            content = msg.get('body', msg.get('content', msg.get('selftext', '')))
            
            if not content:
                continue
            
            # Déterminer le type et la catégorie
            # À adapter selon votre logique métier
            doc_type = 'article'  # ou déterminer depuis metadata
            category_path = ['reddit', 'import']  # À adapter
            
            doc_id = import_document(
                title=title,
                content=content,
                document_type=doc_type,
                category_path=category_path,
                summary=None,
                tags=['reddit', 'import'],
                metadata={
                    'source': 'reddit',
                    'original_id': msg.get('id'),
                    'author': msg.get('author'),
                    'created_utc': msg.get('created_utc'),
                    'url': msg.get('url')
                },
                conn=conn
            )
            
            imported += 1
            print(f"✓ Importé: {title[:50]}... (ID: {doc_id})")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'import: {e}")
            errors += 1
    
    conn.close()
    print(f"\n📊 Résumé: {imported} documents importés, {errors} erreurs")
    print("\n⚠️  Note: Vous devrez peut-être adapter cette fonction selon votre format de fichier Reddit exact")

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python import_documents.py json <fichier.json>")
        print("  python import_documents.py csv <fichier.csv>")
        print("  python import_documents.py reddit <fichier_reddit.json>")
        sys.exit(1)
    
    format_type = sys.argv[1].lower()
    file_path = sys.argv[2]
    
    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        sys.exit(1)
    
    if format_type == 'json':
        import_from_json(file_path)
    elif format_type == 'csv':
        import_from_csv(file_path)
    elif format_type == 'reddit':
        import_from_reddit_chat(file_path)
    else:
        print(f"❌ Format non supporté: {format_type}")
        print("Formats supportés: json, csv, reddit")
        sys.exit(1)

if __name__ == "__main__":
    main()
