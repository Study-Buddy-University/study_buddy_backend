#!/usr/bin/env python3
"""
Reset ChromaDB collection to fix embedding dimension mismatch.
Old collection: 384 dimensions (default all-MiniLM-L6-v2)
New collection: 3072 dimensions (Ollama llama3.2:3b)
"""

import chromadb

def reset_collection():
    try:
        client = chromadb.HttpClient(
            host="chromadb",
            port=8000,
        )
        
        collection_name = "studybuddy_documents"
        
        # Delete old collection
        try:
            client.delete_collection(name=collection_name)
            print(f"✅ Deleted old collection: {collection_name}")
        except Exception as e:
            print(f"⚠️  Collection might not exist: {e}")
        
        # List remaining collections
        collections = client.list_collections()
        print(f"📋 Remaining collections: {[c.name for c in collections]}")
        
        print("\n✅ ChromaDB reset complete!")
        print("🔄 New collection will be created on next document upload with correct dimensions (3072)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(reset_collection())
