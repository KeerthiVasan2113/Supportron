"""
Main pipeline script to run all steps in sequence.
"""

from pathlib import Path
from logger_utils import setup_logger

# Import our scripts
from extract_and_organize_chunks import extract_and_organize_pdfs
from create_embeddings import create_embeddings
from build_rag_model import build_rag_model, test_rag_model

logger = setup_logger("logs/pipeline.log")


def run_full_pipeline(
    pdf_directory: str = None,
    output_directory: str = None,
    vector_db_path: str = None
):
    """
    Run the complete pipeline:
    1. Extract and organize PDF chunks (combined step)
    2. Create embeddings
    3. Build RAG model
    4. Test the model
    
    Args:
        pdf_directory: Directory containing PDF files (defaults to training-data relative to script)
        output_directory: Directory to save extracted chunks (defaults to output relative to script)
        vector_db_path: Path for vector database (defaults to vector_db relative to script)
    """
    # Use paths relative to script location if not provided
    script_dir = Path(__file__).parent
    if pdf_directory is None:
        pdf_directory = str(script_dir / "training-data")
    if output_directory is None:
        output_directory = str(script_dir / "output")
    if vector_db_path is None:
        vector_db_path = str(script_dir / "vector_db")
    logger.info("="*60)
    logger.info("RAG Pipeline - Complete Workflow")
    logger.info("="*60)
    
    # Step 1: Extract and organize PDF chunks (combined)
    logger.info("[Step 1/3] Extracting and organizing PDF chunks...")
    logger.info("-"*60)
    extract_and_organize_pdfs(pdf_directory, output_directory)
    
    # Step 2: Create embeddings
    logger.info("[Step 2/3] Creating embeddings and vector database...")
    logger.info("-"*60)
    chunks_file = Path(output_directory) / "compiled_chunks.jsonl"
    
    if not chunks_file.exists():
        logger.error(f"{chunks_file} not found!")
        return
    
    create_embeddings(str(chunks_file), vector_db_path)
    
    # Step 3: Build and test RAG model
    logger.info("[Step 3/3] Building RAG model...")
    logger.info("-"*60)
    
    try:
        rag_model = build_rag_model(vector_db_path)
        
        # Test with sample questions
        test_questions = [
            "What is Red Hat Enterprise Linux?",
            "How do I configure basic system settings?",
            "What are the key features of RHEL 9?",
        ]
        
        test_rag_model(rag_model, test_questions)
        
        logger.info("="*60)
        logger.info("Pipeline completed successfully!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error building RAG model: {e}", exc_info=True)


if __name__ == "__main__":
    # Use paths relative to script location
    script_dir = Path(__file__).parent
    pdf_directory = str(script_dir / "training-data")
    output_directory = str(script_dir / "output")
    vector_db_path = str(script_dir / "vector_db")
    
    run_full_pipeline(pdf_directory, output_directory, vector_db_path)
