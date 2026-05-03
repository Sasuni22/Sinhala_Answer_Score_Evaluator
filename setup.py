"""
Setup script: Initialize vector store, check Ollama, and verify system.
Run this ONCE before launching the Streamlit app.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def main():
    print("=" * 60)
    print("  SinhalaScore AI — System Setup")
    print("=" * 60)

    # 1. Check Ollama
    print("\n[1/3] Checking Ollama availability...")
    try:
        import ollama
        models = ollama.list()
        model_names = [m["name"] for m in models.get("models", [])]
        if model_names:
            print(f"  ✅ Ollama running. Available models: {model_names}")
        else:
            print("  ⚠  Ollama running but no models found.")
            print("     Run: ollama pull llama3.2:3b")
    except Exception as e:
        print(f"  ⚠  Ollama not available: {e}")
        print("     The system will use keyword-based fallback scoring.")

    # 2. Build vector store
    print("\n[2/3] Building knowledge base vector store...")
    try:
        from rag.retriever import build_vector_store
        collection = build_vector_store(force_rebuild=True)
        print(f"  ✅ Vector store built with {collection.count()} chunks")
    except Exception as e:
        print(f"  ❌ Error building vector store: {e}")

    # 3. Test ontology
    print("\n[3/3] Testing ontology...")
    try:
        from ontology.anuradhapura_ontology import build_ontology, get_ontology_concepts_for_answer
        g = build_ontology()
        print(f"  ✅ Ontology built with {len(g)} triples")
        test_concepts = get_ontology_concepts_for_answer("දුටුගැමුණු රජ රුවන්වැලිසෑය ඉදිකළේය")
        print(f"  ✅ Ontology test: found {len(test_concepts)} concepts")
    except Exception as e:
        print(f"  ❌ Error testing ontology: {e}")

    print("\n" + "=" * 60)
    print("  Setup complete!")
    print("  Run: streamlit run app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
