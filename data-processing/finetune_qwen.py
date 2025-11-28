"""
Fine-tune Qwen model on RAG data using LoRA (Low-Rank Adaptation).
Optimized for CPU-only training with limited RAM.

Note: This script fine-tunes a local HuggingFace model. The main application uses
Ollama llama3.2:3b via the backend. If you want to fine-tune for local use, you can
use this script, but the primary model is Ollama llama3.2:3b.
"""

# Prevent bitsandbytes import to avoid Python 3.14+ compatibility issues
import os
os.environ["BITSANDBYTES_NOWELCOME"] = "1"
# Block bitsandbytes import early
import sys
import builtins
_original_import = builtins.__import__

def _import_without_bitsandbytes(name, *args, **kwargs):
    if name == "bitsandbytes" or name.startswith("bitsandbytes."):
        raise ImportError(f"bitsandbytes is not supported on Python 3.14+ and not needed for CPU training")
    return _original_import(name, *args, **kwargs)

builtins.__import__ = _import_without_bitsandbytes

import json
import torch
from pathlib import Path
from typing import List, Dict
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
from peft import LoraConfig, get_peft_model, TaskType
from logger_utils import setup_logger

logger = setup_logger("logs/finetune_qwen.log", console_output=True)


def prepare_training_data(
    chunks_file: str = "output/compiled_chunks.jsonl",
    output_file: str = "output/training_data.jsonl",
    max_samples: int = 300
) -> str:
    """
    Prepare training data from chunks in ChatML format for model fine-tuning.
    
    Args:
        chunks_file: Path to compiled chunks JSONL file
        output_file: Path to save training data
        max_samples: Maximum number of training samples (to manage memory)
    
    Returns:
        Path to prepared training data file
    """
    logger.info(f"Preparing training data from {chunks_file}...")
    
    chunks_path = Path(chunks_file)
    if not chunks_path.exists():
        raise FileNotFoundError(f"Chunks file not found: {chunks_file}")
    
    training_data = []
    
    # Read chunks and create Q&A pairs
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = [json.loads(line) for line in f]
    
    logger.info(f"Loaded {len(chunks)} chunks")
    
    # Create training samples from chunks
    # For each chunk, we'll create a question-answer pair
    sample_count = 0
    
    for i, chunk in enumerate(chunks[:max_samples]):
        text = chunk.get('text', '').strip()
        if not text or len(text) < 50:  # Skip very short chunks
            continue
        
        # Create a question based on the chunk content
        # Extract first sentence or key phrase as question
        sentences = text.split('.')
        if len(sentences) > 1:
            # Use first sentence as question context
            question_context = sentences[0].strip()
            if len(question_context) > 100:
                question_context = question_context[:100] + "..."
            
            # Create a question
            question = f"What is {question_context.lower()}?" if question_context else "What is this about?"
        else:
            # Fallback question
            question = "What is this about?"
        
        # Format in ChatML format for model fine-tuning
        # ChatML format: <|im_start|>system\n...<|im_end|>\n<|im_start|>user\n...<|im_end|>\n<|im_start|>assistant\n...<|im_end|>
        system_prompt = "You are a helpful assistant that answers questions based on the provided documentation context. Provide clear, structured, and accurate answers."
        
        # Truncate text to reasonable length for training (max 500 chars)
        answer_text = text[:500] if len(text) > 500 else text
        
        # Format as ChatML
        formatted_text = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n{answer_text}<|im_end|>"
        
        training_data.append({
            "text": formatted_text
        })
        
        sample_count += 1
        if sample_count >= max_samples:
            break
        
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{min(len(chunks), max_samples)} chunks...")
    
    # Save training data
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in training_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    logger.info(f"Created {len(training_data)} training samples. Saved to {output_file}")
    return str(output_path)


def create_tokenize_function(tokenizer, max_length: int = 512):
    """Create a tokenize function for the dataset."""
    def tokenize_function(examples):
        """Tokenize training examples."""
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_length,
            padding="max_length"
        )
    return tokenize_function


def fine_tune_qwen(
    model_name: str = "Qwen/Qwen2.5-3B-Instruct",  # HuggingFace model (for local fine-tuning; main app uses Ollama llama3.2:3b)
    training_data_file: str = "output/training_data.jsonl",
    output_dir: str = "fine_tuned_qwen",
    num_epochs: int = 2,
    batch_size: int = 1,  # Very small batch for limited RAM
    gradient_accumulation_steps: int = 16,  # Accumulate gradients
    learning_rate: float = 2e-4,
    max_length: int = 512
):
    """
    Fine-tune Qwen model using LoRA for efficient training.
    
    Note: This fine-tunes a local HuggingFace model. The main application uses
    Ollama llama3.2:3b via the backend. This script is for optional local fine-tuning.
    
    Args:
        model_name: Base model name (HuggingFace model path)
        training_data_file: Path to training data JSONL file
        output_dir: Directory to save fine-tuned model
        num_epochs: Number of training epochs
        batch_size: Training batch size (keep small for CPU/low RAM)
        gradient_accumulation_steps: Steps to accumulate gradients
        learning_rate: Learning rate
        max_length: Maximum sequence length
    """
    logger.info("="*60)
    logger.info(f"Fine-tuning {model_name} with LoRA")
    logger.info("="*60)
    
    # Check if training data exists
    if not Path(training_data_file).exists():
        raise FileNotFoundError(f"Training data file not found: {training_data_file}")
    
    # Load tokenizer
    logger.info(f"Loading tokenizer: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    
    # Fix pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    
    # Load model
    logger.info(f"Loading model: {model_name}...")
    logger.info("This may take a few minutes...")
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        torch_dtype=torch.float32,  # Use float32 for CPU (changed from dtype to torch_dtype)
        low_cpu_mem_usage=True,
        device_map="cpu"
    )
    
    # Configure LoRA
    logger.info("Configuring LoRA (Low-Rank Adaptation)...")
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=8,  # Rank - lower = less parameters, less memory
        lora_alpha=16,  # Scaling factor
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # Attention layers
        bias="none"
    )
    
    # Apply LoRA to model
    # bitsandbytes import is already blocked at module level
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Load training data
    logger.info(f"Loading training data from {training_data_file}...")
    training_texts = []
    with open(training_data_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            training_texts.append(data["text"])
    
    logger.info(f"Loaded {len(training_texts)} training samples")
    
    # Create dataset
    dataset = Dataset.from_dict({"text": training_texts})
    
    # Tokenize dataset
    logger.info("Tokenizing dataset...")
    tokenize_fn = create_tokenize_function(tokenizer, max_length)
    tokenized_dataset = dataset.map(
        tokenize_fn,
        batched=True,
        remove_columns=dataset.column_names
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False  # Causal LM, not masked LM
    )
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        fp16=False,  # Use fp32 for CPU
        logging_steps=10,
        save_steps=100,
        save_total_limit=2,
        evaluation_strategy="no",  # Skip evaluation for now
        save_strategy="steps",
        load_best_model_at_end=False,
        report_to="none",  # Disable wandb/tensorboard
        remove_unused_columns=False,
        dataloader_num_workers=0,  # Use single process for CPU
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
    )
    
    # Train
    logger.info("Starting training...")
    logger.info(f"Training for {num_epochs} epochs with batch size {batch_size}")
    logger.info(f"Effective batch size: {batch_size * gradient_accumulation_steps}")
    logger.info("This will take a while on CPU...")
    
    trainer.train()
    
    # Save model
    logger.info(f"Saving fine-tuned model to {output_dir}...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    logger.info("="*60)
    logger.info("Fine-tuning completed!")
    logger.info(f"Model saved to: {output_dir}")
    logger.info("="*60)
    
    return output_dir


def main():
    """Main function to run fine-tuning."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fine-tune Qwen model on RAG data (for local use; main app uses Ollama llama3.2:3b)")
    parser.add_argument(
        "--chunks-file",
        type=str,
        default="output/compiled_chunks.jsonl",
        help="Path to compiled chunks JSONL file"
    )
    parser.add_argument(
        "--training-data",
        type=str,
        default="output/training_data.jsonl",
        help="Path to save/load training data"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="fine_tuned_qwen",
        help="Directory to save fine-tuned model"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=500,  # Reduced for limited RAM
        help="Maximum number of training samples"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Training batch size (keep small for CPU/low RAM)"
    )
    parser.add_argument(
        "--gradient-accumulation",
        type=int,
        default=8,
        help="Gradient accumulation steps"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-4,
        help="Learning rate"
    )
    parser.add_argument(
        "--skip-prepare",
        action="store_true",
        help="Skip data preparation if training data already exists"
    )
    
    args = parser.parse_args()
    
    try:
        # Step 1: Prepare training data
        if not args.skip_prepare or not Path(args.training_data).exists():
            logger.info("Step 1: Preparing training data...")
            prepare_training_data(
                chunks_file=args.chunks_file,
                output_file=args.training_data,
                max_samples=args.max_samples
            )
        else:
            logger.info(f"Using existing training data: {args.training_data}")
        
        # Step 2: Fine-tune model
        logger.info("Step 2: Fine-tuning model...")
        fine_tune_qwen(
            training_data_file=args.training_data,
            output_dir=args.output_dir,
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            gradient_accumulation_steps=args.gradient_accumulation,
            learning_rate=args.learning_rate
        )
        
        logger.info("\n" + "="*60)
        logger.info("Fine-tuning pipeline completed successfully!")
        logger.info(f"Fine-tuned model saved to: {args.output_dir}")
        logger.info("\nTo use the fine-tuned model, update build_rag_model.py:")
        logger.info(f'  llm_model_name="{args.output_dir}"')
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error during fine-tuning: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

