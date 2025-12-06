"""
Example usage of the CV parsers with chunking functionality.
Demonstrates parsing CVs, chunking text, and preparing data for vector database.
"""

import sys
import os
from typing import List, Dict, Any, Tuple

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.parsers import CVCollection
from app.chunker import SimpleChunker


def chunk_cv_data(
    cv_collection: CVCollection, 
    chunker: SimpleChunker,
    chunk_method: str = "sentences"
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """
    Chunk all CVs in the collection for vector database insertion.
    
    Args:
        cv_collection: Collection of parsed CVs
        chunker: Instance of SimpleChunker
        chunk_method: Chunking method ("sentences", "words", or "fixed")
    
    Returns:
        Tuple of (chunked_metadatas, chunked_texts, chunk_ids)
    """
    chunked_metadatas = []
    chunked_texts = []
    chunk_ids = []
    
    for cv in cv_collection.cvs:
        # Select chunking method
        if chunk_method == "sentences":
            chunks = chunker.chunk_by_sentences(cv.text)
        elif chunk_method == "words":
            chunks = chunker.chunk_by_words(cv.text)
        elif chunk_method == "fixed":
            chunks = chunker.chunk_by_fixed_size(cv.text)
        else:
            raise ValueError(f"Unknown chunk method: {chunk_method}")
        
        # Create metadata and IDs for each chunk
        for i, chunk in enumerate(chunks):
            chunk_id = f"{cv.cv_id}_chunk_{i}"
            chunk_metadata = {
                **cv.metadata,
                "chunk_id": chunk_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_method": chunk_method
            }
            
            chunk_ids.append(chunk_id)
            chunked_metadatas.append(chunk_metadata)
            chunked_texts.append(chunk)
    
    return chunked_metadatas, chunked_texts, chunk_ids


def display_chunking_statistics(
    cv_collection: CVCollection,
    chunked_metadatas: list[dict[str, Any]],
    chunked_texts: list[str]
) -> None:
    """Display statistics about chunking results."""
    print("\n" + "="*60)
    print("CHUNKING STATISTICS")
    print("="*60)
    
    # Basic statistics
    print(f"\nTotal CVs parsed: {len(cv_collection.cvs)}")
    print(f"Total chunks created: {len(chunked_texts)}")
    print(f"Average chunks per CV: {len(chunked_texts) / len(cv_collection.cvs):.1f}")
    
    # CV-specific statistics
    cv_chunk_counts = {}
    for metadata in chunked_metadatas:
        cv_id = metadata["CV_id"]
        cv_chunk_counts[cv_id] = cv_chunk_counts.get(cv_id, 0) + 1
    
    print(f"\nChunks per CV:")
    for cv_id, count in cv_chunk_counts.items():
        cv_name = cv_id.split('_')[0] if '_' in cv_id else cv_id
        print(f"  {cv_name}: {count} chunks")
    
    # Text length statistics
    chunk_lengths = [len(text) for text in chunked_texts]
    if chunk_lengths:
        avg_length = sum(chunk_lengths) / len(chunk_lengths)
        max_length = max(chunk_lengths)
        min_length = min(chunk_lengths)
        
        print(f"\nChunk text length statistics:")
        print(f"  Average length: {avg_length:.0f} characters")
        print(f"  Maximum length: {max_length} characters")
        print(f"  Minimum length: {min_length} characters")
        print(f"  Total text processed: {sum(chunk_lengths):,} characters")
    
    # Show sample chunks
    print(f"\n" + "="*60)
    print("SAMPLE CHUNKS (first 3)")
    print("="*60)
    
    for i in range(min(3, len(chunked_texts))):
        print(f"\nChunk {i+1}:")
        print(f"ID: {chunked_metadatas[i].get('chunk_id', 'N/A')}")
        print(f"From CV: {chunked_metadatas[i].get('name', 'N/A')}")
        print(f"Text preview (first 150 chars):")
        print(f"  {chunked_texts[i][:150]}...")


def prepare_for_vector_db(
    chunked_metadatas: list[dict[str, Any]],
    chunked_texts: list[str],
    chunk_ids: list[str]
) -> dict[str, Any]:
    """
    Prepare data for insertion into vector database.
    
    Returns:
        Dictionary with data ready for vector DB insertion
    """
    return {
        "metadatas": chunked_metadatas,
        "documents": chunked_texts,
        "ids": chunk_ids,
        "count": len(chunk_ids)
    }


def main():
    """Main example demonstrating CV parsing and chunking."""
    # Initialize components
    collection = CVCollection()
    chunker = SimpleChunker(chunk_size=500, overlap=50)  # Smaller chunks for demo
    
    print("="*60)
    print("CV PARSING AND CHUNKING DEMO")
    print("="*60)
    
    try:
        # Add CVs from files
        cv_files = [
            "cv_lev.docx",
            "cv.docx", 
            "cv_ivan.docx",
            "cv_K.docx"
        ]
        
        print("\nParsing CV files...")
        successful_parses = 0
        
        for cv_file in cv_files:
            # Check if file exists in current directory
            if not os.path.exists(cv_file):
                print(f"  ✗ {cv_file}: File not found")
                continue
            
            try:
                cv_id = collection.add_cv_from_file(cv_file)  # File is in current directory
                cv_name = collection.cvs[-1].personal_info.name
                print(f"  ✓ {cv_file}: '{cv_name}' (ID: {cv_id})")
                successful_parses += 1
            except Exception as e:
                print(f"  ✗ {cv_file}: Error - {e}")
        
        if successful_parses == 0:
            print("\nNo CVs were successfully parsed. Exiting.")
            return
        
        # Display parsed CV information
        print(f"\nSuccessfully parsed {successful_parses} CV(s)")
        print("\n" + "-"*60)
        print("PARSED CV INFORMATION")
        print("-"*60)
        
        for i, cv in enumerate(collection.cvs, 1):
            print(f"\nCV {i}: {cv.personal_info.name}")
            print(f"  Level: {cv.personal_info.level or 'Not specified'}")
            print(f"  Roles: {', '.join(cv.personal_info.roles) if cv.personal_info.roles else 'None'}")
            print(f"  Languages: {', '.join(cv.personal_info.languages) if cv.personal_info.languages else 'None'}")
            print(f"  Projects: {len(cv.projects)}")
            print(f"  Description length: {len(cv.text)} characters")
            print(f"  CV ID: {cv.cv_id}")
        
        # Chunk the CV texts
        print("\n" + "-"*60)
        print("CHUNKING CV TEXTS")
        print("-"*60)
        
        chunk_method = "sentences"  # Try: "sentences", "words", or "fixed"
        print(f"\nUsing chunking method: '{chunk_method}'")
        print(f"Chunk size: {chunker.chunk_size}, Overlap: {chunker.overlap}")
        
        chunked_metadatas, chunked_texts, chunk_ids = chunk_cv_data(
            collection, chunker, chunk_method
        )
        
        # Display statistics
        display_chunking_statistics(collection, chunked_metadatas, chunked_texts)
        
        # Prepare for vector database
        print("\n" + "-"*60)
        print("VECTOR DATABASE PREPARATION")
        print("-"*60)
        
        vector_db_data = prepare_for_vector_db(chunked_metadatas, chunked_texts, chunk_ids)
        
        print(f"\nData ready for vector database insertion:")
        print(f"  Total items: {vector_db_data['count']}")
        print(f"  Metadata fields per item: {len(vector_db_data['metadatas'][0]) if vector_db_data['metadatas'] else 0}")
        
        # Example: How to use with your VectorDBManager
        print("\n" + "="*60)
        print("EXAMPLE: INSERTING INTO VECTOR DATABASE")
        print("="*60)
        

        # Example code to insert into vector database:

        from app.db_manager import VectorDBFactory, ConnectionParams, CustomEmbedder

        # Initialize vector DB manager
        embedder = CustomEmbedder("embedding/models/all-MiniLM-L12-v2")
        db_manager = VectorDBFactory.create_manager(
            db_type="qdrant",
            embedder=embedder
        )

        # Connect to database
        params = ConnectionParams(host="localhost", port=6333)
        if db_manager.connect(params):
            # Create or get collection
            collection_name = "cv_chunks"
            if collection_name not in db_manager.list_collections():
                col_meatadata = {
                    "data":"chunks"
                }
                db_manager.create_collection(collection_name,col_meatadata)
            
            # Insert chunked data
            success = db_manager.insert_documents(
                collection_name=collection_name,
                documents=vector_db_data["documents"],
                metadatas=vector_db_data["metadatas"],
                ids=vector_db_data["ids"]
            )
            
            if success:
                print(f"Successfully inserted {len(vector_db_data['ids'])} chunks")
            else:
                print("Failed to insert chunks")

        
    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if chunker module exists
    try:
        import re  # Required by chunker
        from app.chunker import SimpleChunker
        main()
    except ImportError as e:
        print(f"Import error: {e}")
        print("\nPlease ensure:")
        print("1. chunker.py exists in app/ directory")
        print("2. The chunker.py file contains the SimpleChunker class")
        print("3. You're running from the project root directory")
        
        # Show directory structure
        print("\nCurrent directory structure:")
        for root, dirs, files in os.walk("."):
            level = root.replace(".", "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files:
                if file.endswith(".py"):
                    print(f"{subindent}{file}")