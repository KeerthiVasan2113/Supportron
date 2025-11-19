"""
Script to extract meaningful text chunks from PDFs using PyMuPDF.
Filters out irrelevant text like headers, footers, page numbers, etc.
"""

import fitz  # PyMuPDF
import os
import json
import re
from pathlib import Path
from typing import List, Dict
from contextlib import redirect_stderr
from io import StringIO
from logger_utils import setup_logger

logger = setup_logger("logs/extract_pdf_chunks.log")


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
    # These are often warnings about malformed PDFs but don't prevent text extraction
    error_buffer = StringIO()
    
    try:
        with redirect_stderr(error_buffer):
            doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Failed to open PDF {pdf_path}: {str(e)}")
        return chunks
    
    logger.info(f"Processing {pdf_path}...")
    logger.info(f"Total pages: {len(doc)}")
    
    full_text = ""
    pages_with_errors = 0
    
    # Extract text from all pages
    for page_num in range(len(doc)):
        try:
            # Suppress errors for individual pages
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
        # Count unique error types
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
            # Look for sentence endings near the chunk boundary
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


def extract_all_pdfs(pdf_directory: str, output_directory: str = "output") -> None:
    """
    Extract chunks from all PDFs in the specified directory.
    
    Args:
        pdf_directory: Directory containing PDF files
        output_directory: Directory to save extracted chunks
    """
    # Create output directory if it doesn't exist
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    
    pdf_path = Path(pdf_directory)
    pdf_files = list(pdf_path.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_directory}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF file(s)")
    
    all_chunks = []
    
    for pdf_file in pdf_files:
        try:
            chunks = extract_chunks_from_pdf(str(pdf_file))
            
            # Save individual PDF chunks
            output_file = Path(output_directory) / f"{pdf_file.stem}_chunks.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for chunk in chunks:
                    f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
            
            logger.info(f"Saved chunks to {output_file}")
            
            all_chunks.extend(chunks)
            
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {str(e)}", exc_info=True)
            continue
    
    # Save all chunks combined
    combined_output = Path(output_directory) / "all_chunks.jsonl"
    with open(combined_output, 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    logger.info(f"Total chunks extracted: {len(all_chunks)}")
    logger.info(f"Combined chunks saved to {combined_output}")


if __name__ == "__main__":
    pdf_directory = "training-data"
    output_directory = "output"
    
    extract_all_pdfs(pdf_directory, output_directory)
