"""
Script to convert text chunks into vector database embeddings.
Uses sentence-transformers for free, local embeddings and stores in FAISS.
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from logger_utils import setup_logger
from gpu_utils import detect_gpu, get_device

logger = setup_logger("logs/create_embeddings.log")


def load_chunks_from_jsonl(file_path: str) -> List[Dict]:
    """
    Load chunks from a JSONL file.
    """
    chunks = []
    # Count lines first for progress bar
    with open(file_path, 'r', encoding='utf-8') as f:
        total_lines = sum(1 for _ in f)
    
    # Load with progress bar
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in tqdm(f, total=total_lines, desc="Loading chunks", unit="line"):
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def create_embeddings(
    chunks_file: str = "output/compiled_chunks.jsonl",
    vector_db_path: str = "vector_db",
    embedding_model: str = "all-MiniLM-L6-v2"  # Lightweight model for low-memory systems
) -> None:
    """
    Create embeddings for chunks and store in FAISS vector database.
    
    Args:
        chunks_file: Path to chunks JSONL file
        vector_db_path: Path to store the vector database
        embedding_model: Name of the sentence-transformers model to use
    """
    logger.info(f"Loading chunks from {chunks_file}...")
    print(f"Loading chunks from {chunks_file}...")
    chunks = load_chunks_from_jsonl(chunks_file)
    logger.info(f"Loaded {len(chunks)} chunks")
    print(f"Loaded {len(chunks)} chunks")
    
    if not chunks:
        logger.warning("No chunks to process!")
        return
    
    # Detect GPU and set device
    has_gpu, gpu_name, device_type = detect_gpu()
    device = get_device()
    
    # Initialize sentence transformer model for embeddings
    logger.info(f"Loading embedding model: {embedding_model}...")
    print(f"Loading embedding model: {embedding_model}...")
    if has_gpu:
        print(f"  Using GPU: {gpu_name}")
        logger.info(f"Using GPU: {gpu_name} for embeddings")
    else:
        print(f"  Using CPU (GPU not available)")
        logger.info("Using CPU for embeddings (GPU not available)")
    print("This may take a moment on first run (downloading model)...")
    model = SentenceTransformer(embedding_model, device=device)
    print("Model loaded successfully!")
    
    # Get embedding dimension
    sample_embedding = model.encode(["sample text"])
    embedding_dim = sample_embedding.shape[1]
    logger.info(f"Embedding dimension: {embedding_dim}")
    
    # Create output directory
    Path(vector_db_path).mkdir(parents=True, exist_ok=True)
    
    # Process chunks in batches for efficiency
    # Reduced batch size for systems with limited RAM (1GB available)
    batch_size = 50  # Reduced from 100 for low-memory systems
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    
    logger.info(f"Creating embeddings and storing in FAISS vector database...")
    print(f"\nCreating embeddings and storing in FAISS vector database...")
    print(f"Processing {len(chunks)} chunks in {total_batches} batch(es)...\n")
    
    # Initialize FAISS index (L2 distance)
    index = faiss.IndexFlatL2(embedding_dim)
    
    # Store metadata for each vector
    metadata_list = []
    texts_list = []
    
    # Use tqdm for progress bar
    with tqdm(total=len(chunks), desc="Processing chunks", unit="chunk") as pbar:
        for batch_idx in range(0, len(chunks), batch_size):
            batch = chunks[batch_idx:batch_idx + batch_size]
            batch_num = (batch_idx // batch_size) + 1
            
            # Extract texts
            texts = [chunk['text'] for chunk in batch]
            
            # Generate embeddings with progress bar
            # Use GPU if available for faster encoding
            pbar.set_description(f"Batch {batch_num}/{total_batches}: Generating embeddings")
            embeddings = model.encode(
                texts, 
                device=device,
                show_progress_bar=True, 
                convert_to_numpy=True
            )
            
            # Convert to numpy array
            embeddings = np.array(embeddings).astype('float32')
            
            # Add to FAISS index
            pbar.set_description(f"Batch {batch_num}/{total_batches}: Adding to index")
            index.add(embeddings)
            
            # Store metadata and texts
            for i, chunk in enumerate(batch):
                metadata_list.append({
                    'source_file': chunk.get('source_file', 'unknown'),
                    'chunk_id': chunk.get('chunk_id', batch_idx + i),
                    'char_count': chunk.get('char_count', 0),
                    'text_preview': chunk['text'][:500]  # Store preview
                })
                texts_list.append(chunk['text'])
            
            # Update progress bar
            pbar.update(len(batch))
            logger.info(f"  Batch {batch_num}/{total_batches}: Stored {len(batch)} chunks")
    
    # Save FAISS index
    print("\nSaving FAISS index...")
    index_file = Path(vector_db_path) / "faiss.index"
    faiss.write_index(index, str(index_file))
    logger.info(f"FAISS index saved to {index_file}")
    print(f"✓ FAISS index saved to {index_file}")
    
    # Save metadata and texts
    print("Saving metadata and texts...")
    metadata_file = Path(vector_db_path) / "metadata.pkl"
    with open(metadata_file, 'wb') as f:
        pickle.dump(metadata_list, f)
    logger.info(f"Metadata saved to {metadata_file}")
    print(f"✓ Metadata saved to {metadata_file}")
    
    texts_file = Path(vector_db_path) / "texts.pkl"
    with open(texts_file, 'wb') as f:
        pickle.dump(texts_list, f)
    logger.info(f"Texts saved to {texts_file}")
    print(f"✓ Texts saved to {texts_file}")
    
    logger.info(f"Vector database created successfully at {vector_db_path}")
    logger.info(f"Total documents indexed: {len(chunks)}")
    logger.info(f"Index size: {index.ntotal} vectors")
    
    print(f"\n{'='*60}")
    print(f"Vector database created successfully!")
    print(f"{'='*60}")
    print(f"Total documents indexed: {len(chunks)}")
    print(f"Index size: {index.ntotal} vectors")
    print(f"Location: {vector_db_path}")
    
    # Test the vector store
    logger.info("Testing vector store with a sample query...")
    print(f"\nTesting vector store with a sample query...")
    test_query = "system configuration"
    test_embedding = model.encode(
        [test_query], 
        device=device,
        show_progress_bar=False
    ).astype('float32')
    
    # Search for top 3 similar vectors
    k = 3
    distances, indices = index.search(test_embedding, k)
    
    logger.info(f"Sample query: '{test_query}'")
    print(f"Sample query: '{test_query}'")
    if len(indices[0]) > 0:
        logger.info(f"Found {len(indices[0])} similar documents")
        top_idx = indices[0][0]
        logger.info(f"Top result preview: {texts_list[top_idx][:200]}...")
        print(f"✓ Found {len(indices[0])} similar documents")
        print(f"Top result preview: {texts_list[top_idx][:200]}...")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    chunks_file = "output/compiled_chunks.jsonl"
    vector_db_path = "vector_db"
    
    create_embeddings(chunks_file, vector_db_path)
