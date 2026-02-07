#!/usr/bin/env python3
"""
SentinelAI Document CLI - Dokumente verarbeiten und durchsuchen
"""

import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import ollama
import chromadb
from chromadb.config import Settings

# Konfiguration
DATA_DIR = Path(__file__).parent / "data"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = os.environ.get('LLM_MODEL', 'mistral-nemo:latest')


def ensure_dirs():
    """Erstellt notwendige Verzeichnisse"""
    DATA_DIR.mkdir(exist_ok=True)
    VECTORSTORE_DIR.mkdir(exist_ok=True)


def get_collection():
    """Gibt ChromaDB Collection zurück"""
    client = chromadb.PersistentClient(path=str(VECTORSTORE_DIR))
    return client.get_or_create_collection("documents")


def extract_text(filepath: Path) -> str:
    """Extrahiert Text aus verschiedenen Dateiformaten"""
    suffix = filepath.suffix.lower()
    
    if suffix == '.txt' or suffix == '.md':
        return filepath.read_text(encoding='utf-8')
    
    elif suffix == '.pdf':
        try:
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            print("\033[31mFehler: pypdf nicht installiert. Nutze: pip install pypdf\033[0m")
            return ""
    
    elif suffix in ['.docx', '.doc']:
        try:
            from docx import Document
            doc = Document(filepath)
            return "\n".join(para.text for para in doc.paragraphs)
        except ImportError:
            print("\033[31mFehler: python-docx nicht installiert. Nutze: pip install python-docx\033[0m")
            return ""
    
    else:
        print(f"\033[33mWarnung: Unbekanntes Format {suffix}\033[0m")
        return ""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """Teilt Text in Chunks"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks


def get_embedding(text: str) -> list:
    """Generiert Embedding mit lokalem Modell"""
    response = ollama.embed(model=EMBEDDING_MODEL, input=text)
    return response['embeddings'][0]


def cmd_add(args):
    """Fügt ein Dokument hinzu"""
    filepath = Path(args.file)
    
    if not filepath.exists():
        print(f"\033[31mDatei nicht gefunden: {filepath}\033[0m")
        return
    
    print(f"📄 Verarbeite: {filepath.name}")
    
    # Text extrahieren
    text = extract_text(filepath)
    if not text:
        print("\033[31mKonnte keinen Text extrahieren\033[0m")
        return
    
    print(f"   └─ {len(text)} Zeichen extrahiert")
    
    # In Chunks aufteilen
    chunks = chunk_text(text)
    print(f"   └─ {len(chunks)} Chunks erstellt")
    
    # Embeddings generieren und speichern
    collection = get_collection()
    
    for i, chunk in enumerate(chunks):
        print(f"   └─ Embedding {i+1}/{len(chunks)}...", end="\r")
        embedding = get_embedding(chunk)
        
        doc_id = f"{filepath.stem}_{i}"
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[{"filename": filepath.name, "chunk": i}]
        )
    
    print(f"\n\033[32m✓ {filepath.name} erfolgreich indexiert ({len(chunks)} Chunks)\033[0m")


def cmd_search(args):
    """Durchsucht die Wissensbasis"""
    query = " ".join(args.query)
    n_results = args.n
    
    print(f"\n🔍 Suche: \"{query}\"\n")
    
    collection = get_collection()
    
    if collection.count() == 0:
        print("\033[33mKeine Dokumente indexiert. Nutze: ./docs.py add <datei>\033[0m")
        return
    
    # Query-Embedding
    query_embedding = get_embedding(query)
    
    # Suchen
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count())
    )
    
    if not results['documents'][0]:
        print("\033[33mKeine relevanten Ergebnisse gefunden.\033[0m")
        return
    
    print(f"\033[1mGefunden: {len(results['documents'][0])} Ergebnisse\033[0m\n")
    
    for i, (doc, meta, dist) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        score = 1 - (dist / 2)  # Normalisierte Ähnlichkeit
        print(f"\033[36m[{i+1}] {meta['filename']} (Score: {score:.2f})\033[0m")
        
        # Zeige Vorschau
        preview = doc[:200] + "..." if len(doc) > 200 else doc
        print(f"    {preview}\n")


def cmd_ask(args):
    """Beantwortet eine Frage basierend auf Dokumenten"""
    question = " ".join(args.question)
    
    print(f"\n🤔 Frage: \"{question}\"\n")
    
    collection = get_collection()
    
    if collection.count() == 0:
        print("\033[33mKeine Dokumente indexiert. Nutze: ./docs.py add <datei>\033[0m")
        return
    
    # Relevante Chunks finden
    query_embedding = get_embedding(question)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )
    
    if not results['documents'][0]:
        print("\033[33mKeine relevanten Dokumente gefunden.\033[0m")
        return
    
    # Kontext zusammenbauen
    context = "\n\n---\n\n".join(results['documents'][0])
    sources = set(m['filename'] for m in results['metadatas'][0])
    
    # LLM fragen
    prompt = f"""Beantworte die folgende Frage basierend NUR auf dem bereitgestellten Kontext.
Wenn die Antwort nicht im Kontext zu finden ist, sage das ehrlich.

KONTEXT:
{context}

FRAGE:
{question}

ANTWORT:"""

    print("\033[36mSentinell:\033[0m ", end="", flush=True)
    
    stream = ollama.chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    
    for chunk in stream:
        content = chunk.get('message', {}).get('content', '')
        print(content, end="", flush=True)
    
    print(f"\n\n\033[90mQuellen: {', '.join(sources)}\033[0m\n")


def cmd_list(args):
    """Listet indexierte Dokumente auf"""
    collection = get_collection()
    
    if collection.count() == 0:
        print("\n\033[33mKeine Dokumente indexiert.\033[0m")
        print("Nutze: ./docs.py add <datei>\n")
        return
    
    # Hole alle Metadaten
    results = collection.get(include=["metadatas"])
    
    # Zähle pro Datei
    files = {}
    for meta in results['metadatas']:
        fname = meta.get('filename', 'unknown')
        files[fname] = files.get(fname, 0) + 1
    
    print(f"\n\033[1mIndexierte Dokumente: {len(files)}\033[0m")
    print(f"Gesamt Chunks: {collection.count()}\n")
    
    for fname, count in sorted(files.items()):
        print(f"  📄 {fname} ({count} Chunks)")
    
    print()


def cmd_clear(args):
    """Löscht alle Dokumente"""
    confirm = input("\033[31mAlle Dokumente löschen? (ja/nein): \033[0m")
    
    if confirm.lower() != 'ja':
        print("Abgebrochen.")
        return
    
    # Lösche Collection
    client = chromadb.PersistentClient(path=str(VECTORSTORE_DIR))
    try:
        client.delete_collection("documents")
        print("\033[32m✓ Alle Dokumente gelöscht.\033[0m")
    except Exception as e:
        print(f"\033[31mFehler: {e}\033[0m")


def main():
    ensure_dirs()
    
    parser = argparse.ArgumentParser(
        description="SentinelAI Dokument-CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  ./docs.py add vertrag.pdf         # Dokument indexieren
  ./docs.py add *.txt               # Mehrere Dateien
  ./docs.py list                    # Indexierte Dokumente auflisten
  ./docs.py search Kündigungsfrist  # Dokumente durchsuchen
  ./docs.py ask "Was ist die Kündigungsfrist?"  # Frage stellen
  ./docs.py clear                   # Alle Dokumente löschen
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Befehle')
    
    # add
    add_parser = subparsers.add_parser('add', help='Dokument hinzufügen')
    add_parser.add_argument('file', help='Pfad zur Datei')
    add_parser.set_defaults(func=cmd_add)
    
    # search
    search_parser = subparsers.add_parser('search', help='Dokumente durchsuchen')
    search_parser.add_argument('query', nargs='+', help='Suchbegriffe')
    search_parser.add_argument('-n', type=int, default=5, help='Anzahl Ergebnisse')
    search_parser.set_defaults(func=cmd_search)
    
    # ask
    ask_parser = subparsers.add_parser('ask', help='Frage stellen (RAG)')
    ask_parser.add_argument('question', nargs='+', help='Frage')
    ask_parser.set_defaults(func=cmd_ask)
    
    # list
    list_parser = subparsers.add_parser('list', help='Dokumente auflisten')
    list_parser.set_defaults(func=cmd_list)
    
    # clear
    clear_parser = subparsers.add_parser('clear', help='Alle Dokumente löschen')
    clear_parser.set_defaults(func=cmd_clear)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\033[33mAbgebrochen.\033[0m")
    except Exception as e:
        print(f"\033[31mFehler: {e}\033[0m")


if __name__ == "__main__":
    main()
