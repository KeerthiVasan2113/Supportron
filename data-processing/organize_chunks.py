"""
Script to organize and compile extracted PDF chunks.
Removes duplicates, merges similar chunks, and organizes by source.
"""

import json
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict
import hashlib
from logger_utils import setup_logger

logger = setup_logger("logs/organize_chunks.log")


def calculate_chunk_hash(text: str) -> str:
    """
    Calculate a hash for a text chunk to identify duplicates.
    """
    # Normalize text for comparison
    normalized = text.lower().strip()
    normalized = ' '.join(normalized.split())  # Remove extra whitespace
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple similarity between two texts (word overlap).
    Returns a value between 0 and 1.
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def load_chunks_from_jsonl(file_path: str) -> List[Dict]:
    """
    Load chunks from a JSONL file.
    """
    chunks = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def remove_duplicates(chunks: List[Dict], similarity_threshold: float = 0.95) -> List[Dict]:
    """
    Remove duplicate and highly similar chunks.
    """
    seen_hashes: Set[str] = set()
    unique_chunks = []
    
    for chunk in chunks:
        chunk_hash = calculate_chunk_hash(chunk['text'])
        
        if chunk_hash not in seen_hashes:
            # Check for similar chunks
            is_duplicate = False
            for existing_chunk in unique_chunks:
                similarity = calculate_similarity(chunk['text'], existing_chunk['text'])
                if similarity >= similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_hashes.add(chunk_hash)
                unique_chunks.append(chunk)
    
    return unique_chunks


def organize_by_source(chunks: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Organize chunks by their source file.
    """
    organized = defaultdict(list)
    
    for chunk in chunks:
        source = chunk.get('source_file', 'unknown')
        organized[source].append(chunk)
    
    return dict(organized)


def merge_small_chunks(chunks: List[Dict], min_size: int = 200) -> List[Dict]:
    """
    Merge very small chunks with adjacent chunks if they're from the same source.
    """
    if not chunks:
        return chunks
    
    merged = []
    i = 0
    
    while i < len(chunks):
        current_chunk = chunks[i].copy()
        
        # If chunk is too small, try to merge with next chunk from same source
        if len(current_chunk['text']) < min_size and i + 1 < len(chunks):
            next_chunk = chunks[i + 1]
            
            if current_chunk['source_file'] == next_chunk['source_file']:
                # Merge chunks
                merged_text = current_chunk['text'] + ' ' + next_chunk['text']
                current_chunk['text'] = merged_text.strip()
                current_chunk['char_count'] = len(current_chunk['text'])
                current_chunk['end_pos'] = next_chunk.get('end_pos', current_chunk.get('end_pos', 0))
                i += 1  # Skip next chunk as it's merged
        
        merged.append(current_chunk)
        i += 1
    
    return merged


def compile_chunks(input_directory: str = "output", output_directory: str = "output") -> None:
    """
    Organize and compile all chunks from JSONL files.
    
    Args:
        input_directory: Directory containing chunk JSONL files
        output_directory: Directory to save organized chunks
    """
    input_path = Path(input_directory)
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all chunk JSONL files
    chunk_files = list(input_path.glob("*_chunks.jsonl"))
    
    if not chunk_files:
        logger.warning(f"No chunk files found in {input_directory}")
        return
    
    logger.info(f"Found {len(chunk_files)} chunk file(s)")
    
    all_chunks = []
    
    # Load all chunks
    for chunk_file in chunk_files:
        logger.info(f"Loading chunks from {chunk_file.name}...")
        chunks = load_chunks_from_jsonl(str(chunk_file))
        all_chunks.extend(chunks)
        logger.info(f"  Loaded {len(chunks)} chunks")
    
    logger.info(f"Total chunks before organization: {len(all_chunks)}")
    
    # Remove duplicates
    logger.info("Removing duplicates...")
    unique_chunks = remove_duplicates(all_chunks)
    logger.info(f"Chunks after removing duplicates: {len(unique_chunks)}")
    
    # Merge small chunks
    logger.info("Merging small chunks...")
    merged_chunks = merge_small_chunks(unique_chunks)
    logger.info(f"Chunks after merging: {len(merged_chunks)}")
    
    # Organize by source
    organized = organize_by_source(merged_chunks)
    
    # Save organized chunks by source
    for source, chunks in organized.items():
        output_file = output_path / f"{Path(source).stem}_organized.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
        logger.info(f"Saved {len(chunks)} organized chunks to {output_file}")
    
    # Save compiled chunks
    compiled_output = output_path / "compiled_chunks.jsonl"
    with open(compiled_output, 'w', encoding='utf-8') as f:
        for chunk in merged_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    logger.info(f"Compiled {len(merged_chunks)} total chunks to {compiled_output}")
    
    # Create summary statistics
    summary = {
        "total_chunks": len(merged_chunks),
        "chunks_by_source": {source: len(chunks) for source, chunks in organized.items()},
        "total_characters": sum(chunk['char_count'] for chunk in merged_chunks),
        "avg_chunk_size": sum(chunk['char_count'] for chunk in merged_chunks) / len(merged_chunks) if merged_chunks else 0
    }
    
    summary_file = output_path / "chunks_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Summary saved to {summary_file}")
    logger.info(f"Summary: Total chunks: {summary['total_chunks']}, "
                f"Total characters: {summary['total_characters']:,}, "
                f"Average chunk size: {summary['avg_chunk_size']:.0f} characters")
    for source, count in summary['chunks_by_source'].items():
        logger.info(f"  Chunks by source - {source}: {count}")


if __name__ == "__main__":
    input_directory = "output"
    output_directory = "output"
    
    compile_chunks(input_directory, output_directory)
