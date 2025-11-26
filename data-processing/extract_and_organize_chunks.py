"""
Combined script to extract meaningful text chunks from PDFs and organize them.
Extracts from PDFs, removes duplicates, merges similar chunks, and saves only the final compiled output.
Deletes intermediate files after processing.
"""

import fitz  # PyMuPDF
import os
import json
import re
import shutil
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict
from contextlib import redirect_stderr
from io import StringIO
import hashlib
from logger_utils import setup_logger

logger = setup_logger("logs/extract_and_organize_chunks.log")


def is_meaningful_text(text: str) -> bool:
    """
    Filter out irrelevant text chunks.
    Returns True if the text is meaningful and should be kept.
    """
    if not text or len(text.strip()) < 20:  # Too short
        return False
    
    text = text.strip()
    
    # Filter out page numbers (single numbers or "Page X of Y")
    if re.match(r'^\d+$', text) or re.match(r'^Page \d+ of \d+$', text, re.IGNORECASE):
        return False
    
    # Filter out common header/footer patterns
    header_footer_patterns = [
        r'^Table of Contents$',
        r'^Chapter \d+',
        r'^Section \d+',
        r'^\d{1,2}/\d{1,2}/\d{4}$',  # Dates
        r'^©.*$',  # Copyright notices
        r'^Confidential$',
        r'^Draft$',
    ]
    
    for pattern in header_footer_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return False
    
    # Filter out text that's mostly special characters or whitespace
    if len(re.sub(r'[\s\W]', '', text)) < len(text) * 0.3:
        return False
    
    # Filter out very short lines that are likely headers/footers
    if len(text) < 30 and text.count('\n') == 0:
        # Check if it's likely a header/footer (repeated patterns)
        if text.isupper() and len(text.split()) < 5:
            return False
    
    return True


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    # Remove multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def extract_chunks_from_pdf(pdf_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Dict]:
    """
    Extract text chunks from a PDF file using PyMuPDF.
    
    Args:
        pdf_path: Path to the PDF file
        chunk_size: Target size for each chunk (in characters)
        chunk_overlap: Overlap between chunks (in characters)
    
    Returns:
        List of dictionaries containing chunk data
    """
    chunks = []
    
    # Suppress MuPDF error messages to stderr
    error_buffer = StringIO()
    
    try:
        with redirect_stderr(error_buffer):
            doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Failed to open PDF {pdf_path}: {str(e)}")
        return chunks
    
    logger.info(f"Processing {os.path.basename(pdf_path)}...")
    logger.info(f"Total pages: {len(doc)}")
    
    full_text = ""
    pages_with_errors = 0
    
    # Extract text from all pages
    for page_num in range(len(doc)):
        try:
            with redirect_stderr(error_buffer):
                page = doc[page_num]
                text = page.get_text()
            
            if text and text.strip():
                full_text += text + "\n\n"
        except Exception as e:
            pages_with_errors += 1
            logger.warning(f"Error extracting text from page {page_num + 1} of {os.path.basename(pdf_path)}: {str(e)}")
            continue
    
    # Log summary of errors if any occurred
    error_output = error_buffer.getvalue()
    if error_output:
        error_lines = error_output.strip().split('\n')
        unique_errors = {}
        for line in error_lines:
            if 'error:' in line.lower():
                error_type = line.split('error:')[-1].strip() if 'error:' in line else line.strip()
                unique_errors[error_type] = unique_errors.get(error_type, 0) + 1
        
        if unique_errors:
            logger.warning(f"Encountered MuPDF warnings/errors in {os.path.basename(pdf_path)}:")
            for error_type, count in unique_errors.items():
                logger.warning(f"  - {error_type}: {count} occurrence(s)")
            logger.info("These are usually non-critical warnings and text extraction continues...")
    
    if pages_with_errors > 0:
        logger.warning(f"Skipped {pages_with_errors} page(s) due to errors, but extracted text from {len(doc) - pages_with_errors} page(s)")
    
    try:
        doc.close()
    except Exception:
        pass  # Ignore errors on close
    
    # Clean the full text
    full_text = clean_text(full_text)
    
    # Split into chunks with overlap
    start = 0
    chunk_id = 0
    
    while start < len(full_text):
        end = start + chunk_size
        
        # Try to break at sentence boundaries
        if end < len(full_text):
            sentence_end = max(
                full_text.rfind('.', start, end),
                full_text.rfind('!', start, end),
                full_text.rfind('?', start, end),
                full_text.rfind('\n', start, end)
            )
            
            if sentence_end > start + chunk_size * 0.5:  # Only break if we're past halfway
                end = sentence_end + 1
        
        chunk_text = full_text[start:end].strip()
        
        # Only keep meaningful chunks
        if is_meaningful_text(chunk_text):
            chunk_data = {
                "chunk_id": chunk_id,
                "source_file": os.path.basename(pdf_path),
                "text": chunk_text,
                "char_count": len(chunk_text),
                "start_pos": start,
                "end_pos": end
            }
            chunks.append(chunk_data)
            chunk_id += 1
        
        # Move start position with overlap
        start = end - chunk_overlap
        if start >= len(full_text):
            break
    
    logger.info(f"Extracted {len(chunks)} meaningful chunks from {os.path.basename(pdf_path)}")
    return chunks


def calculate_chunk_hash(text: str) -> str:
    """
    Calculate a hash for a text chunk to identify duplicates.
    """
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


def remove_duplicates(chunks: List[Dict], seen_hashes: Set[str], similarity_threshold: float = 0.95) -> tuple[List[Dict], Set[str]]:
    """
    Remove duplicate and highly similar chunks.
    Updates the seen_hashes set and returns unique chunks.
    """
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
    
    return unique_chunks, seen_hashes


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


def clean_intermediate_files(output_directory: Path) -> None:
    """
    Delete intermediate files (individual chunk files, organized files, etc.)
    Keep only compiled_chunks.jsonl and chunks_summary.json
    """
    logger.info("Cleaning up intermediate files...")
    
    # Files to keep (never delete these)
    files_to_keep = {
        "compiled_chunks.jsonl",
        "chunks_summary.json"
    }
    
    files_to_delete = [
        "*_chunks.jsonl",
        "*_organized.jsonl",
        "all_chunks.jsonl"
    ]
    
    deleted_count = 0
    for pattern in files_to_delete:
        for file_path in output_directory.glob(pattern):
            # Double-check: never delete the final output files
            if file_path.name in files_to_keep:
                logger.debug(f"Skipping protected file: {file_path.name}")
                continue
                
            try:
                file_path.unlink()
                deleted_count += 1
                logger.debug(f"Deleted: {file_path.name}")
            except Exception as e:
                logger.warning(f"Failed to delete {file_path.name}: {str(e)}")
    
    if deleted_count > 0:
        logger.info(f"Deleted {deleted_count} intermediate file(s)")


def extract_and_organize_pdfs(
    pdf_directory: str,
    output_directory: str = "output",
    similarity_threshold: float = 0.95,
    min_chunk_size: int = 200
) -> None:
    """
    Extract chunks from all PDFs, organize them (remove duplicates, merge small chunks),
    and save only the final compiled output. Deletes intermediate files.
    
    Args:
        pdf_directory: Directory containing PDF files (can be absolute or relative path)
        output_directory: Directory to save compiled chunks (can be absolute or relative path)
        similarity_threshold: Threshold for duplicate detection (0.0 to 1.0)
        min_chunk_size: Minimum size for chunks before merging (in characters)
    """
    # Convert to Path objects and resolve to absolute paths
    pdf_path = Path(pdf_directory).resolve()
    output_path = Path(output_directory).resolve()
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Check if PDF directory exists
    if not pdf_path.exists():
        logger.error(f"PDF directory does not exist: {pdf_path}")
        return
    
    if not pdf_path.is_dir():
        logger.error(f"PDF path is not a directory: {pdf_path}")
        return
    
    pdf_files = list(pdf_path.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_path}")
        logger.info(f"Looking in: {pdf_path.absolute()}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF file(s) in {pdf_path}")
    logger.info("="*60)
    
    # Clean up old intermediate files first (but keep compiled_chunks.jsonl if it exists)
    clean_intermediate_files(output_path)
    
    # Track all chunks and seen hashes across all PDFs
    all_organized_chunks = []
    seen_hashes: Set[str] = set()
    total_extracted = 0
    
    # Process each PDF: extract, organize, and accumulate
    for pdf_file in pdf_files:
        try:
            logger.info(f"\nProcessing: {pdf_file.name}")
            logger.info("-"*60)
            
            # Step 1: Extract chunks from PDF
            chunks = extract_chunks_from_pdf(str(pdf_file))
            total_extracted += len(chunks)
            
            if not chunks:
                logger.warning(f"No chunks extracted from {pdf_file.name}")
                continue
            
            logger.info(f"Extracted {len(chunks)} chunks")
            
            # Step 2: Remove duplicates (against all previously seen chunks)
            logger.info("Removing duplicates...")
            unique_chunks, seen_hashes = remove_duplicates(chunks, seen_hashes, similarity_threshold)
            logger.info(f"After deduplication: {len(unique_chunks)} unique chunks")
            
            # Step 3: Merge small chunks
            logger.info("Merging small chunks...")
            merged_chunks = merge_small_chunks(unique_chunks, min_chunk_size)
            logger.info(f"After merging: {len(merged_chunks)} chunks")
            
            # Step 4: Add to accumulated organized chunks
            all_organized_chunks.extend(merged_chunks)
            logger.info(f"Total organized chunks so far: {len(all_organized_chunks)}")
            
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {str(e)}", exc_info=True)
            continue
    
    logger.info("\n" + "="*60)
    logger.info("Final Organization")
    logger.info("="*60)
    logger.info(f"Total chunks extracted: {total_extracted}")
    logger.info(f"Total organized chunks: {len(all_organized_chunks)}")
    
    if not all_organized_chunks:
        logger.error("No organized chunks to save! Check if PDFs were processed correctly.")
        return
    
    # Save compiled chunks (final output)
    compiled_output = output_path / "compiled_chunks.jsonl"
    try:
        logger.info(f"Writing compiled chunks to {compiled_output}...")
        chunk_count = 0
        import os
        with open(compiled_output, 'w', encoding='utf-8') as f:
            for chunk in all_organized_chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
                chunk_count += 1
                # Flush every 100 chunks to ensure data is written
                if chunk_count % 100 == 0:
                    f.flush()
            # Force flush before closing
            f.flush()
            # Force OS to write to disk
            if hasattr(f, 'fileno'):
                try:
                    os.fsync(f.fileno())
                except (OSError, AttributeError):
                    pass  # Some file handles don't support fsync
        
        # Verify file was created and has content
        if compiled_output.exists():
            file_size = compiled_output.stat().st_size
            logger.info(f"✓ Successfully saved {len(all_organized_chunks)} compiled chunks to {compiled_output}")
            logger.info(f"  File size: {file_size:,} bytes")
            logger.info(f"  Full path: {compiled_output.resolve()}")
        else:
            logger.error(f"✗ Failed to create {compiled_output}!")
            logger.error(f"  Expected path: {compiled_output.resolve()}")
            return
    except Exception as e:
        logger.error(f"Error saving compiled chunks: {str(e)}", exc_info=True)
        return
    
    # Organize by source for summary
    organized_by_source = defaultdict(list)
    for chunk in all_organized_chunks:
        source = chunk.get('source_file', 'unknown')
        organized_by_source[source].append(chunk)
    
    # Create summary statistics
    summary = {
        "total_chunks": len(all_organized_chunks),
        "chunks_by_source": {source: len(chunks) for source, chunks in organized_by_source.items()},
        "total_characters": sum(chunk['char_count'] for chunk in all_organized_chunks),
        "avg_chunk_size": sum(chunk['char_count'] for chunk in all_organized_chunks) / len(all_organized_chunks) if all_organized_chunks else 0
    }
    
    summary_file = output_path / "chunks_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Summary saved to {summary_file}")
    logger.info(f"\nSummary Statistics:")
    logger.info(f"  Total chunks: {summary['total_chunks']}")
    logger.info(f"  Total characters: {summary['total_characters']:,}")
    logger.info(f"  Average chunk size: {summary['avg_chunk_size']:.0f} characters")
    for source, count in summary['chunks_by_source'].items():
        logger.info(f"  {source}: {count} chunks")
    
    # Final cleanup of any remaining intermediate files
    clean_intermediate_files(output_path)
    
    # Verify final output file still exists after cleanup
    if not compiled_output.exists():
        logger.error(f"ERROR: {compiled_output.name} was deleted during cleanup!")
        logger.error("This should not happen. Re-saving the file...")
        try:
            with open(compiled_output, 'w', encoding='utf-8') as f:
                for chunk in all_organized_chunks:
                    f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
            logger.info(f"Re-saved {compiled_output.name}")
        except Exception as e:
            logger.error(f"Failed to re-save {compiled_output.name}: {str(e)}")
    else:
        file_size = compiled_output.stat().st_size
        logger.info(f"✓ Verified: {compiled_output.name} exists ({file_size:,} bytes)")
    
    logger.info("\n" + "="*60)
    logger.info("Processing complete! Only compiled_chunks.jsonl and chunks_summary.json remain.")
    logger.info("="*60)


if __name__ == "__main__":
    # Use paths relative to script location
    script_dir = Path(__file__).parent
    pdf_directory = str(script_dir / "training-data")
    output_directory = str(script_dir / "output")
    
    extract_and_organize_pdfs(pdf_directory, output_directory)

