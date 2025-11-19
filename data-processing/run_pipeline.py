"""
Main pipeline script to run all steps in sequence.
"""

from pathlib import Path
from logger_utils import setup_logger

# Import our scripts
from extract_pdf_chunks import extract_all_pdfs
from organize_chunks import compile_chunks
from create_embeddings import create_embeddings
from build_rag_model import build_rag_model, test_rag_model

logger = setup_logger("logs/pipeline.log")


def run_full_pipeline(
    pdf_directory: str = "training-data",
    output_directory: str = "output",
    vector_db_path: str = "vector_db"
):
    """
    Run the complete pipeline:
    1. Extract PDF chunks
    2. Organize chunks
    3. Create embeddings
    4. Build RAG model
    5. Test the model
    """
    logger.info("="*60)
    logger.info("RAG Pipeline - Complete Workflow")
    logger.info("="*60)
    
    # Step 1: Extract PDF chunks
    logger.info("[Step 1/4] Extracting PDF chunks...")
    logger.info("-"*60)
    extract_all_pdfs(pdf_directory, output_directory)
    
    # Step 2: Organize chunks
    logger.info("[Step 2/4] Organizing and compiling chunks...")
    logger.info("-"*60)
    compile_chunks(output_directory, output_directory)
    
    # Step 3: Create embeddings
    logger.info("[Step 3/4] Creating embeddings and vector database...")
    logger.info("-"*60)
    chunks_file = Path(output_directory) / "compiled_chunks.jsonl"
    
    if not chunks_file.exists():
        logger.error(f"{chunks_file} not found!")
        return
    
    create_embeddings(str(chunks_file), vector_db_path)
    
    # Step 4: Build and test RAG model
    logger.info("[Step 4/4] Building RAG model...")
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
    pdf_directory = "training-data"
    output_directory = "output"
    vector_db_path = "vector_db"
    
    run_full_pipeline(pdf_directory, output_directory, vector_db_path)
