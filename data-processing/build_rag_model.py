"""
Script to build a custom RAG (Retrieval-Augmented Generation) model.
Uses template-based answer generation from retrieved context (Ollama llama3.2:3b is used via the backend).
Uses FAISS for vector search.
"""

import pickle
import re
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import torch
from logger_utils import setup_logger

logger = setup_logger("logs/build_rag_model.log")


class SimpleRAGModel:
    """RAG model with template-based generation (Ollama llama3.2:3b is used via the backend for answer generation)."""
    
    def __init__(
        self,
        vector_db_path: str = "vector_db",
        embedding_model: str = "all-MiniLM-L6-v2",  # Lightweight model optimized for low-memory systems
        top_k: int = 6,  # Increased for better context retrieval
        use_llm: bool = False,  # We use Ollama llama3.2:3b via backend instead
        llm_model_name: str = "llama3.2:3b",  # Model name for reference (not used when use_llm=False)
        use_quantization: bool = True  # Use 8-bit quantization for CPU
    ):
        """
        Initialize the RAG model.
        
        Args:
            vector_db_path: Path to the vector database
            embedding_model: Name of the embedding model
            top_k: Number of top documents to retrieve
            use_llm: Whether to use LLM for answer generation (default: True)
            llm_model_name: Name of the LLM model to use
            use_quantization: Use 8-bit quantization for lower memory usage
        """
        logger.info(f"Loading embedding model: {embedding_model}...")
        print(f"Loading embedding model: {embedding_model}...")
        self.embedding_model = SentenceTransformer(embedding_model)
        print("✓ Embedding model loaded successfully!")
        
        logger.info(f"Loading FAISS index from {vector_db_path}...")
        print(f"\nLoading FAISS index from {vector_db_path}...")
        
        # Load FAISS index
        index_file = Path(vector_db_path) / "faiss.index"
        if not index_file.exists():
            error_msg = f"FAISS index not found at {index_file}. Please run create_embeddings.py first."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        print("  Loading index file...")
        self.index = faiss.read_index(str(index_file))
        print("  ✓ Index loaded")
        
        # Load metadata and texts
        metadata_file = Path(vector_db_path) / "metadata.pkl"
        texts_file = Path(vector_db_path) / "texts.pkl"
        
        if not metadata_file.exists() or not texts_file.exists():
            error_msg = f"Metadata or texts file not found in {vector_db_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        print("  Loading metadata...")
        with open(metadata_file, 'rb') as f:
            self.metadata = pickle.load(f)
        print("  ✓ Metadata loaded")
        
        print("  Loading texts...")
        with open(texts_file, 'rb') as f:
            self.texts = pickle.load(f)
        print("  ✓ Texts loaded")
        
        self.top_k = top_k
        self.use_llm = use_llm
        self.llm_model = None
        self.llm_tokenizer = None
        
        # Load LLM if requested
        if use_llm:
            try:
                self._load_llm(llm_model_name, use_quantization)
            except Exception as e:
                logger.warning(f"Failed to load LLM: {e}. Falling back to template-based generation.")
                print(f"⚠ Warning: Could not load LLM ({e}). Using template-based generation.")
                self.use_llm = False
        
        logger.info(f"RAG model initialized. Total documents: {self.index.ntotal}")
        print(f"\n{'='*60}")
        print(f"RAG model initialized successfully!")
        print(f"{'='*60}")
        print(f"Total documents: {self.index.ntotal}")
        print(f"Embedding dimension: {self.index.d}")
        print(f"Top-K retrieval: {self.top_k}")
        print(f"Answer generation: {'LLM (local)' if self.use_llm else 'Template-based (Ollama via backend)'}")
        print(f"{'='*60}\n")
    
    def _load_llm(self, model_name: str, use_quantization: bool = True):
        """Load LLM with optional quantization for low memory usage (not used - Ollama is used via backend)."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        except ImportError:
            raise ImportError("transformers library not installed. Install with: pip install transformers accelerate")
        
        logger.info(f"Loading LLM: {model_name}...")
        print(f"\nLoading LLM: {model_name}...")
        print("This may take a few minutes on first run (downloading model)...")
        
        # Load tokenizer
        self.llm_tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        
        # Fix pad token issue (Qwen uses eos_token as pad_token by default)
        if self.llm_tokenizer.pad_token is None:
            self.llm_tokenizer.pad_token = self.llm_tokenizer.eos_token
        if self.llm_tokenizer.pad_token_id is None:
            self.llm_tokenizer.pad_token_id = self.llm_tokenizer.eos_token_id
        
        # Configure quantization for CPU (8-bit)
        if use_quantization and not torch.cuda.is_available():
            logger.info("Using 8-bit quantization for CPU inference...")
            print("Using 8-bit quantization for lower memory usage...")
            # For CPU, we use load_in_8bit=False but will use torch_dtype=torch.float16 if possible
            # Actually, for CPU we should use float32 or int8 quantization
            # Let's use a simpler approach: load with low_cpu_mem_usage
            self.llm_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                torch_dtype=torch.float32,  # Use torch_dtype for CPU
                low_cpu_mem_usage=True,
                device_map="cpu"
            )
        else:
            # Load normally
            self.llm_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                torch_dtype=torch.float32,  # Use torch_dtype for CPU
                low_cpu_mem_usage=True,
                device_map="cpu"
            )
        
        # Set pad token in model config if needed
        if hasattr(self.llm_model.config, 'pad_token_id') and self.llm_model.config.pad_token_id is None:
            self.llm_model.config.pad_token_id = self.llm_tokenizer.pad_token_id
        
        self.llm_model.eval()  # Set to evaluation mode
        logger.info("LLM loaded successfully!")
        print("✓ LLM loaded successfully!")
    
    def _expand_query(self, query: str) -> str:
        """
        Expand query with synonyms and related terms for better matching.
        
        Args:
            query: Original query
        
        Returns:
            Expanded query
        """
        query_lower = query.lower()
        
        # Query expansion dictionary for common Linux/developer terms
        expansions = {
            'cmd': ['command', 'commands', 'cli', 'terminal', 'shell'],
            'command': ['cmd', 'commands', 'cli', 'terminal', 'shell'],
            'commands': ['cmd', 'command', 'cli', 'terminal', 'shell'],
            'basic': ['essential', 'fundamental', 'common', 'important', 'essential'],
            'developer': ['programmer', 'dev', 'software engineer', 'coder'],
            'linux': ['unix', 'bash', 'shell', 'terminal'],
            'must know': ['essential', 'important', 'fundamental', 'common'],
        }
        
        # Add expanded terms
        expanded_terms = [query]
        words = query_lower.split()
        
        for word in words:
            if word in expansions:
                expanded_terms.extend(expansions[word])
        
        # Create expanded query
        expanded_query = ' '.join(expanded_terms)
        return expanded_query
    
    def retrieve(self, query: str) -> List[Dict]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The search query
        
        Returns:
            List of relevant documents with metadata, sorted by relevance
        """
        # Expand query for better matching
        expanded_query = self._expand_query(query)
        
        # Generate query embedding from both original and expanded
        query_embedding = self.embedding_model.encode([query]).astype('float32')
        expanded_embedding = self.embedding_model.encode([expanded_query]).astype('float32')
        
        # Search in FAISS index - retrieve more candidates for better filtering
        search_k = min(self.top_k * 3, self.index.ntotal)
        distances1, indices1 = self.index.search(query_embedding, search_k)
        distances2, indices2 = self.index.search(expanded_embedding, search_k)
        
        # Combine and deduplicate results
        all_candidates = {}
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Process original query results
        for i, idx in enumerate(indices1[0]):
            if idx < len(self.texts) and idx < len(self.metadata):
                distance = float(distances1[0][i])
                if idx not in all_candidates or all_candidates[idx]['distance'] > distance:
                    all_candidates[idx] = {
                        'distance': distance,
                        'source': 'original'
                    }
        
        # Process expanded query results
        for i, idx in enumerate(indices2[0]):
            if idx < len(self.texts) and idx < len(self.metadata):
                distance = float(distances2[0][i])
                if idx not in all_candidates:
                    all_candidates[idx] = {
                        'distance': distance,
                        'source': 'expanded'
                    }
                elif all_candidates[idx]['distance'] > distance:
                    all_candidates[idx]['distance'] = distance
        
        # Format results and filter by relevance threshold
        documents = []
        
        for idx, candidate_info in all_candidates.items():
            distance = candidate_info['distance']
            text = self.texts[idx]
            
            # Stricter filtering - only accept documents with good relevance
            if distance > 1.5:  # Stricter threshold
                continue
            
            # Calculate relevance score (inverse of distance, normalized)
            relevance_score = 1 / (1 + distance)
            
            # Calculate word overlap score with emphasis on key terms
            text_lower = text.lower()
            
            # Check for key Linux command-related terms
            command_keywords = ['command', 'cmd', 'cli', 'terminal', 'shell', 'bash', 
                              'ls', 'cd', 'mkdir', 'rm', 'cp', 'mv', 'grep', 'find',
                              'chmod', 'chown', 'sudo', 'apt', 'yum', 'systemctl',
                              'ps', 'top', 'kill', 'nano', 'vim', 'cat', 'less', 'more']
            
            has_command_keywords = any(keyword in text_lower for keyword in command_keywords)
            
            # Word overlap calculation
            word_overlap = sum(1 for word in query_words if word in text_lower)
            word_overlap_score = word_overlap / max(len(query_words), 1)
            
            # Bonus for documents containing command keywords when query is about commands
            if 'cmd' in query_lower or 'command' in query_lower:
                if has_command_keywords:
                    word_overlap_score *= 1.5
            
            # Penalty for documents that seem unrelated (e.g., about documentation contribution)
            unrelated_keywords = ['contribution', 'code of conduct', 'coda', 'technical writing',
                                'documentation contribution', 'submit', 'review']
            has_unrelated = any(keyword in text_lower for keyword in unrelated_keywords)
            if has_unrelated and not any(qw in text_lower for qw in query_words):
                word_overlap_score *= 0.3  # Heavy penalty
            
            # Combined relevance score
            combined_score = (relevance_score * 0.6) + (word_overlap_score * 0.4)
            
            doc = {
                'text': text,
                'source_file': self.metadata[idx].get('source_file', 'unknown'),
                'chunk_id': self.metadata[idx].get('chunk_id', 0),
                'distance': distance,
                'relevance_score': combined_score
            }
            documents.append(doc)
        
        # Sort by relevance score (highest first) and take top_k
        documents.sort(key=lambda x: x['relevance_score'], reverse=True)
        documents = documents[:self.top_k]
        
        logger.debug(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
        return documents
    
    def _is_how_to_question(self, query: str) -> bool:
        """Check if the query is a 'how-to' or procedural question."""
        how_to_phrases = ['how to', 'how do i', 'how can i', 'steps to', 'guide to',
                          'setup', 'set up', 'install', 'configure', 'create', 'build']
        query_lower = query.lower()
        return any(phrase in query_lower for phrase in how_to_phrases)
    
    def _extract_instructions(self, text: str, query_words: set) -> List[str]:
        """Extract instruction-like sentences from text."""
        import re
        instructions = []
        
        # Look for numbered steps, bullet points, or imperative sentences
        # Split by common delimiters
        sentences = re.split(r'(?<=[.!?])\s+|(?<=:)\s+', text)
        
        instruction_indicators = ['install', 'configure', 'setup', 'set up', 'create',
                                 'run', 'execute', 'start', 'stop', 'enable', 'disable',
                                 'add', 'remove', 'update', 'download', 'extract',
                                 'copy', 'move', 'edit', 'modify', 'change', 'set']
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30:
                continue
            
            sentence_lower = sentence.lower()
            
            # Check if sentence contains instruction verbs
            has_instruction = any(indicator in sentence_lower for indicator in instruction_indicators)
            
            # Check if sentence contains query terms
            has_query_terms = any(word in sentence_lower for word in query_words)
            
            # Check if it's a numbered step or bullet point
            is_numbered = bool(re.match(r'^\d+[\.\)]\s+', sentence))
            is_bullet = sentence.startswith('•') or sentence.startswith('-')
            
            if (has_instruction or is_numbered or is_bullet) and (has_query_terms or has_instruction):
                # Clean up the sentence
                sentence = re.sub(r'^\d+[\.\)]\s*', '', sentence)  # Remove numbering
                sentence = re.sub(r'^[•\-]\s*', '', sentence)  # Remove bullets
                if sentence:
                    instructions.append(sentence)
        
        return instructions
    
    def _generate_with_llm(self, query: str, context_docs: List[Dict]) -> str:
        """Generate answer using local LLM with retrieved context (not used - Ollama llama3.2:3b is used via backend)."""
        if not self.llm_model or not self.llm_tokenizer:
            raise ValueError("LLM not loaded")
        
        # Prepare context from retrieved documents (limit to avoid token limit)
        context_text = "\n\n".join([
            f"Document {i+1}:\n{doc['text'][:800]}"  # Limit each doc to 800 chars
            for i, doc in enumerate(context_docs[:3])  # Use top 3 docs
        ])
        
        # Create prompt for LLM (ChatML format - not used, Ollama llama3.2:3b is used via backend)
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions based on the provided documentation context. Provide clear, structured, and accurate answers. Use markdown formatting for headings (##), code blocks (```bash), bold text (**text**), and inline code (`text`). CRITICAL: When providing commands, ALWAYS provide COMPLETE, EXECUTABLE commands. Never truncate commands."
            },
            {
                "role": "user",
                "content": f"""Context from documentation:
{context_text}

Question: {query}

Please provide a comprehensive answer based on the context above. Format your answer with:
- Headings (##) for major sections
- Code blocks (```bash) for commands
- Bold text (**text**) for important keywords, port numbers, and IP addresses
- Inline code (`text`) for file paths

CRITICAL: When providing commands (sudo, apt-get, systemctl, docker, etc.), ALWAYS provide COMPLETE, EXECUTABLE commands. Each command must be complete and ready to run. Never truncate or cut off commands mid-way."""
            }
        ]
        
        # Apply chat template (ChatML format - not used, Ollama llama3.2:3b is used via backend)
        try:
            prompt = self.llm_tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        except Exception:
            # Fallback to manual format if apply_chat_template fails
            prompt = f"""<|im_start|>system
You are a helpful assistant that answers questions based on the provided documentation context. 
Provide clear, structured, and accurate answers. Use markdown formatting for headings and code blocks.
<|im_end|>
<|im_start|>user
Context from documentation:
{context_text}

Question: {query}

Please provide a comprehensive answer based on the context above. Format your answer with:
- Headings (##) for major sections
- Code blocks (```bash) for commands
- Bold text (**text**) for important keywords, port numbers, and IP addresses
- Inline code (`text`) for file paths
<|im_end|>
<|im_start|>assistant
"""
        
        # Tokenize with attention mask
        inputs = self.llm_tokenizer(
            prompt, 
            return_tensors="pt", 
            truncation=True, 
            max_length=1536,  # Leave room for generation
            padding=False,
            return_attention_mask=True
        )
        
        # Generate with memory-efficient settings
        with torch.no_grad():
            outputs = self.llm_model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,  # Pass attention mask
                max_new_tokens=512,  # Limit response length
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.llm_tokenizer.pad_token_id,
                eos_token_id=self.llm_tokenizer.eos_token_id,
                repetition_penalty=1.1
            )
        
        # Decode response
        response = self.llm_tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the assistant's response
        if "<|im_start|>assistant" in response:
            response = response.split("<|im_start|>assistant")[-1].strip()
        if "<|im_end|>" in response:
            response = response.split("<|im_end|>")[0].strip()
        
        # Remove the prompt part if it's still there
        if prompt in response:
            response = response.replace(prompt, "").strip()
        
        return response
    
    def _format_answer_with_markdown(self, answer: str, query: str, is_how_to: bool) -> str:
        """
        Format answer with markdown structure (headings, code blocks, etc.).
        
        Args:
            answer: Raw answer text
            query: Original query
            is_how_to: Whether this is a how-to question
        
        Returns:
            Formatted answer with markdown
        """
        import re
        
        # Extract commands - ONLY match standalone command lines, not commands in sentences
        # Commands typically appear at start of line or after certain phrases
        commands = []
        placeholders = []
        
        # Pattern to match complete command lines (stops at newline, period, or explanation words)
        # This pattern matches commands that are standalone, not embedded in explanatory text
        command_line_pattern = r'(?:^|\n|\.\s+|:\s+)(sudo\s+(?:apt|yum|systemctl|postconf|dpkg-reconfigure|update-exim4\.conf|ufw|iptables|ifconfig|vi|nano|setenforce|sestatus)\s+[^\n\.]+?)(?=\s+[A-Z]|\s+[Tt]his|\s+[Tt]he|\s+[Yy]ou|\s+[Ii]f|\s+[Ww]hen|\s+[Aa]fter|\s+[Bb]efore|\.|$|\n)'
        
        # More precise: Match commands that appear as standalone lines or after colons
        # Split by lines first to better detect standalone commands
        lines = answer.split('\n')
        text_with_placeholders_lines = []
        command_index = 0
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                text_with_placeholders_lines.append(line)
                continue
            
            # Check if this line starts with a command
            # Enhanced pattern to match common command prefixes including docker, apt-get, etc.
            command_prefix_match = re.match(r'^(sudo\s+(?:apt-get|apt|yum|dnf|systemctl|docker|service|postconf|dpkg-reconfigure|update-exim4\.conf|ufw|iptables|ifconfig|vi|nano|setenforce|sestatus|wget|curl|git|npm|pip)\s+|apt-get\s+|apt\s+|yum\s+|dnf\s+|systemctl\s+|docker\s+|service\s+|postconf\s+|dpkg-reconfigure\s+|update-exim4\.conf\s+|ufw\s+|iptables\s+|ifconfig\s+|vi\s+|nano\s+|setenforce\s+|sestatus\s+|wget\s+|curl\s+|git\s+|npm\s+|pip\s+)', line_stripped, re.IGNORECASE)
            
            if command_prefix_match:
                # Extract complete command - take the entire line until we hit a period, newline, or clear sentence boundary
                # For commands, we want to capture everything until a clear break
                command_end_pattern = r'[\.\n]|(?:\s+)(?:This|The|You|If|When|After|Before|To|For|How|What|Where|Why|Note|Important|Warning|Error)(?:\s+[a-z])'
                command_match = re.search(command_end_pattern, line_stripped)
                
                if command_match:
                    # Command ends at the match position
                    command = line_stripped[:command_match.start()].strip()
                    remaining_text = line_stripped[command_match.start():].strip()
                else:
                    # No clear end found, take the whole line as command
                    command = line_stripped.strip()
                    remaining_text = ''
                
                # Clean up command - remove trailing punctuation but keep the command intact
                command = re.sub(r'[.,;:]$', '', command).strip()
                
                # Validate command - must have at least the prefix and one more word
                command_parts = command.split()
                if len(command_parts) >= 2 and len(command) > 5:  # Valid command
                    placeholder = f"__COMMAND_{command_index}__"
                    commands.append(command)
                    placeholders.append(placeholder)
                    
                    # Replace ONLY the command, keep everything after as regular text
                    if remaining_text:
                        text_with_placeholders_lines.append(placeholder + ' ' + remaining_text)
                    else:
                        text_with_placeholders_lines.append(placeholder)
                    command_index += 1
                    continue
            
            # Also check for commands in the middle of sentences (but be VERY careful)
            # Only match if it's clearly a standalone command, not part of explanation
            inline_command_pattern = r'\b(sudo\s+(?:apt-get|apt|yum|dnf|systemctl|docker|service|postconf|dpkg-reconfigure|update-exim4\.conf|ufw|iptables|ifconfig|vi|nano|setenforce|sestatus|wget|curl|git|npm|pip)\s+)'
            match = re.search(inline_command_pattern, line_stripped, re.IGNORECASE)
            
            if match and match.start() > 0:  # Command not at start of line
                # Extract complete command from the match position
                prefix_start = match.start()
                prefix_end = match.end()
                prefix_text = match.group(1).strip()
                
                # Get text after the command prefix
                text_after_prefix = line_stripped[prefix_end:].strip()
                
                # Find where the command ends (period, newline, or sentence starter)
                command_end_pattern = r'[\.\n]|(?:\s+)(?:This|The|You|If|When|After|Before|To|For|How|What|Where|Why|Note|Important|Warning|Error)(?:\s+[a-z])'
                end_match = re.search(command_end_pattern, text_after_prefix)
                
                if end_match:
                    command_suffix = text_after_prefix[:end_match.start()].strip()
                    remaining_text = text_after_prefix[end_match.start():].strip()
                else:
                    # Take all remaining text as part of command
                    command_suffix = text_after_prefix
                    remaining_text = ''
                
                command = prefix_text + ' ' + command_suffix
                command = re.sub(r'[.,;:]$', '', command).strip()
                
                # Validate command
                command_parts = command.split()
                if len(command_parts) >= 2 and len(command) > 5:
                    placeholder = f"__COMMAND_{command_index}__"
                    commands.append(command)
                    placeholders.append(placeholder)
                    
                    # Replace command, keep explanation as text
                    before_command = line_stripped[:prefix_start]
                    
                    if remaining_text:
                        text_with_placeholders_lines.append(before_command + placeholder + ' ' + remaining_text)
                    else:
                        text_with_placeholders_lines.append(before_command + placeholder)
                    command_index += 1
                else:
                    text_with_placeholders_lines.append(line)
            else:
                text_with_placeholders_lines.append(line)
        
        text_with_placeholders = '\n'.join(text_with_placeholders_lines)
        
        # Split into sentences, preserving structure
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text_with_placeholders)
        
        formatted_parts = []
        current_heading = None
        paragraph_buffer = []
        
        # Enhanced section detection keywords
        section_keywords = {
            'mailbox format': '## Mailbox Format',
            'configure mailbox': '## Configure Mailbox',
            'tuned': '## TuneD',
            'configure': '## Configuration',
            'install': '## Installation',
            'setup': '## Setup',
            'dynamic tuning': '## Dynamic Tuning',
            'static tuning': '## Static Tuning',
            'to configure': '## Configuration',
            'to install': '## Installation',
            'to set up': '## Setup',
            'install dovecot': '## Install Dovecot',
            'configure dovecot': '## Configure Dovecot',
            'parallel start': '## Performance Features',
            'on-demand activation': '## Performance Features',
            'postconf': '## Postfix Configuration',
            'exim4': '## Exim4 Configuration',
        }
        
        # Topic transition words that indicate new sections
        topic_transitions = {
            'for example': '### Example',
            'note that': '### Note',
            'important': '### Important',
            'additionally': '### Additional Information',
        }
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue
            
            sentence_lower = sentence.lower()
            
            # Check for major section headers
            found_section = False
            for keyword, heading in section_keywords.items():
                if keyword in sentence_lower:
                    # Flush current paragraph
                    if paragraph_buffer:
                        formatted_parts.append(' '.join(paragraph_buffer))
                        paragraph_buffer = []
                    
                    if current_heading != heading:
                        formatted_parts.append(f'\n{heading}\n')
                        current_heading = heading
                    found_section = True
                    # Remove the keyword from sentence and capitalize
                    sentence = re.sub(keyword, '', sentence, flags=re.IGNORECASE).strip()
                    if sentence:
                        sentence = sentence[0].upper() + sentence[1:] if sentence else sentence
                    break
            
            # Check for topic transitions
            found_transition = False
            if not found_section:
                for keyword, heading in topic_transitions.items():
                    if sentence_lower.startswith(keyword):
                        if paragraph_buffer:
                            formatted_parts.append(' '.join(paragraph_buffer))
                            paragraph_buffer = []
                        formatted_parts.append(f'\n{heading}\n')
                        found_transition = True
                        sentence = sentence[len(keyword):].strip()
                        if sentence:
                            sentence = sentence[0].upper() + sentence[1:] if sentence else sentence
                        break
            
            # Restore commands from placeholders
            for j, placeholder in enumerate(placeholders):
                if placeholder in sentence:
                    command = commands[j]
                    # Split sentence at the placeholder
                    parts = sentence.split(placeholder, 1)
                    before_command = parts[0].strip() if parts[0] else ''
                    after_command = parts[1].strip() if len(parts) > 1 else ''
                    
                    # Add text before command to buffer
                    if before_command:
                        paragraph_buffer.append(before_command)
                    
                    # Flush buffer and add command in code block
                    if paragraph_buffer:
                        formatted_parts.append(' '.join(paragraph_buffer))
                        paragraph_buffer = []
                    
                    # Add command in code block (compact spacing)
                    formatted_parts.append(f'\n```bash\n{command}\n```')
                    
                    # Add text after command to buffer (explanation)
                    if after_command:
                        paragraph_buffer.append(after_command)
                    
                    sentence = ''  # Already processed
                    break
            
            # Clean up sentence
            sentence = re.sub(r'\s+', ' ', sentence).strip()
            
            if sentence:
                paragraph_buffer.append(sentence)
                
                # Flush paragraph buffer if it gets too long or we hit a natural break
                if len(' '.join(paragraph_buffer)) > 300 or i == len(sentences) - 1:
                    formatted_parts.append(' '.join(paragraph_buffer))
                    paragraph_buffer = []
        
        # Flush any remaining paragraph
        if paragraph_buffer:
            formatted_parts.append(' '.join(paragraph_buffer))
        
        # Join all parts with compact spacing (no empty lines)
        formatted = ''
        for i, part in enumerate(formatted_parts):
            part = part.strip()
            if not part:
                continue
                
            if part.startswith('##') or part.startswith('###'):
                # Headings get single newline before (but not at start)
                if formatted:
                    formatted += '\n' + part
                else:
                    formatted = part
            elif part.startswith('```'):
                # Code blocks get single newline before
                if formatted and not formatted.endswith('\n'):
                    formatted += '\n'
                formatted += part
            else:
                # Regular paragraphs - each part is a separate paragraph, start on new line (single newline, no empty lines)
                if formatted:
                    if formatted.endswith('```') or formatted.endswith('```\n'):
                        formatted += '\n' + part
                    elif formatted.endswith('\n'):
                        # Previous was heading or code block, start new paragraph on new line
                        formatted += part
                    else:
                        # Previous was regular text - this is a new paragraph, start on new line
                        formatted += '\n' + part
                else:
                    formatted = part
        
        # Highlight important numbers and file paths (but NOT keywords - only headings are bold)
        # Port numbers - highlight with inline code
        formatted = re.sub(r'\b(\d{1,5})\s+(port|Port)\b', r'`\1` \2', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bport\s+(\d{1,5})\b', r'port `\1`', formatted, flags=re.IGNORECASE)
        # Standalone port numbers (e.g., "port 8080" or "on port 22")
        formatted = re.sub(r'\b(?:on\s+)?port\s+(\d{1,5})\b', r'port `\1`', formatted, flags=re.IGNORECASE)
        # IP addresses - highlight with inline code
        formatted = re.sub(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', r'`\1`', formatted)
        # IPv6 addresses
        formatted = re.sub(r'\b([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b', r'`\1`', formatted)
        # File paths - highlight with inline code (already done, but ensure all patterns)
        formatted = re.sub(r'(/[a-zA-Z0-9_\-/]+\.(?:conf|config|sh|py|yaml|yml|log|json|txt|md))', r'`\1`', formatted)
        formatted = re.sub(r'(\/etc\/[a-zA-Z0-9_\-/]+)', r'`\1`', formatted)
        formatted = re.sub(r'(\/home\/[a-zA-Z0-9_\-/]+)', r'`\1`', formatted)
        formatted = re.sub(r'(\/usr\/[a-zA-Z0-9_\-/]+)', r'`\1`', formatted)
        formatted = re.sub(r'(\/var\/[a-zA-Z0-9_\-/]+)', r'`\1`', formatted)
        formatted = re.sub(r'(\/opt\/[a-zA-Z0-9_\-/]+)', r'`\1`', formatted)
        # Remove any bold formatting from keywords (only headings should be bold)
        # This ensures we don't accidentally bold keywords that aren't headings
        
        # Clean up excessive spacing - remove all double+ newlines
        formatted = re.sub(r'\n{3,}', '\n', formatted)  # Max 1 newline
        formatted = re.sub(r'\n\n', '\n', formatted)  # Remove all double newlines
        formatted = re.sub(r'```\n\n+```', '```\n```', formatted)  # No blank lines in code blocks
        
        # Clean up spaces
        formatted = re.sub(r' +', ' ', formatted)  # Multiple spaces to single
        formatted = re.sub(r'\n +', '\n', formatted)  # Remove leading spaces after newlines
        formatted = re.sub(r' \n', '\n', formatted)  # Remove trailing spaces before newlines
        
        # Ensure code blocks have proper format
        formatted = re.sub(r'```bash\s+', '```bash\n', formatted)
        formatted = re.sub(r'\s+```', '\n```', formatted)
        
        # Ensure answer doesn't end mid-sentence - but don't truncate if we have most of it
        if formatted and formatted[-1] not in '.!?':
            # Try to find last complete sentence
            last_period = formatted.rfind('.')
            last_exclamation = formatted.rfind('!')
            last_question = formatted.rfind('?')
            last_end = max(last_period, last_exclamation, last_question)
            # Only truncate if we have a clear sentence boundary in the last 10% of text
            if last_end > len(formatted) * 0.9:
                formatted = formatted[:last_end + 1]
            # Otherwise, keep the full text even if it doesn't end with punctuation
        
        # Final structure validation and cleanup
        formatted = self._validate_and_clean_structure(formatted)
        
        formatted = formatted.strip()
        
        return formatted
    
    def _validate_and_clean_structure(self, text: str) -> str:
        """
        Validate and clean the markdown structure of the response.
        Ensures proper formatting before sending to user.
        """
        import re
        
        # Remove any bold formatting that's not part of headings
        # Headings should be: ## Heading or ### Heading
        # We need to preserve bold in headings but remove it elsewhere
        
        # Split by lines to process headings separately
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Check if this is a heading
            is_heading = stripped.startswith('##') or stripped.startswith('###')
            
            # Determine line type for processing
            line_type = (
                'heading' if is_heading else
                'code_marker' if stripped.startswith('```') else
                'regular'
            )
            
            match line_type:
                case 'heading':
                    # Headings can have bold, keep them as is
                    cleaned_lines.append(line)
                case 'code_marker':
                    # Code block markers, keep as is
                    cleaned_lines.append(line)
                case 'regular':
                    # Regular text - remove any **bold** that's not in code blocks
                    # But preserve inline code `text`
                    # We'll handle this more carefully to avoid breaking code blocks
                    cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Remove bold formatting from non-heading text (but preserve in headings and code)
        # This is tricky - we need to process line by line
        lines = text.split('\n')
        result_lines = []
        in_code_block = False
        
        for line in lines:
            stripped = line.strip()
            
            # Track code blocks
            if stripped.startswith('```'):
                in_code_block = not in_code_block
                result_lines.append(line)
                continue
            
            # Inside code blocks, don't modify
            if in_code_block:
                result_lines.append(line)
                continue
            
            # Check if this is a heading
            if stripped.startswith('##') or stripped.startswith('###'):
                # Headings can have formatting, keep as is
                result_lines.append(line)
            else:
                # Remove **bold** from regular text (but keep inline code `text`)
                # We need to be careful not to break inline code
                # First, protect inline code
                protected_parts = []
                parts = re.split(r'(`[^`]+`)', line)
                
                for part in parts:
                    if part.startswith('`') and part.endswith('`'):
                        # This is inline code, keep as is
                        protected_parts.append(part)
                    else:
                        # Remove **bold** but keep the text
                        part = re.sub(r'\*\*([^*]+)\*\*', r'\1', part)
                        protected_parts.append(part)
                
                result_lines.append(''.join(protected_parts))
        
        text = '\n'.join(result_lines)
        
        # Ensure code blocks are properly closed
        code_block_count = text.count('```')
        if code_block_count % 2 != 0:
            # Unclosed code block, try to fix
            # Find the last ``` and ensure it's closed
            last_code_start = text.rfind('```')
            if last_code_start != -1:
                # Check if there's content after it
                after_code = text[last_code_start + 3:].strip()
                if after_code and not after_code.startswith('\n```'):
                    # Add closing ```
                    text = text[:last_code_start + 3] + '\n```' + text[last_code_start + 3:]
        
        # Clean up any remaining formatting issues
        # Remove empty bold markers
        text = re.sub(r'\*\*\s*\*\*', '', text)
        # Remove bold with no content
        text = re.sub(r'\*\*([\s]*)\*\*', r'\1', text)
        
        # Ensure headings are on their own lines
        text = re.sub(r'([^\n])(##)', r'\1\n\2', text)
        text = re.sub(r'(##)([^\n])', r'\1 \2', text)
        
        # Clean up spacing around headings
        text = re.sub(r'\n(##[^\n]+)\n+', r'\n\1\n', text)
        
        # Ensure code blocks are properly formatted
        text = re.sub(r'```bash([^\n])', r'```bash\n\1', text)
        text = re.sub(r'([^\n])```', r'\1\n```', text)
        
        return text
    
    def generate_answer(self, query: str, context_docs: List[Dict]) -> str:
        """
        Generate a structured, relevant answer from query and retrieved context.
        Uses LLM if available, otherwise falls back to template-based generation.
        
        Args:
            query: The user's question
            context_docs: Retrieved context documents (sorted by relevance)
        
        Returns:
            Generated answer
        """
        if not context_docs:
            return "I couldn't find any relevant information in the documentation to answer your question."
        
        # Use LLM if available
        if self.use_llm and self.llm_model:
            try:
                logger.info("Generating answer using LLM...")
                answer = self._generate_with_llm(query, context_docs)
                # Format the LLM response
                is_how_to = self._is_how_to_question(query)
                answer = self._format_answer_with_markdown(answer, query, is_how_to)
                return answer
            except Exception as e:
                logger.warning(f"LLM generation failed: {e}. Falling back to template-based generation.")
                # Fall through to template-based generation
        
        # Template-based generation (fallback or default)
        query_lower = query.lower()
        query_words = set(query_lower.split())
        is_how_to = self._is_how_to_question(query)
        
        # Remove common stop words for better matching
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                     'could', 'may', 'might', 'must', 'can', 'what', 'how', 'why', 'when',
                     'where', 'which', 'who', 'this', 'that', 'these', 'those', 'i', 'you',
                     'he', 'she', 'it', 'we', 'they', 'to', 'of', 'in', 'on', 'at', 'for',
                     'with', 'by', 'from', 'as', 'and', 'or', 'but', 'if', 'about', 'that'}
        query_words = {w for w in query_words if w not in stop_words and len(w) > 2}
        
        # Add important query terms even if they're short
        important_terms = {'ls', 'cd', 'rm', 'cp', 'mv', 'cat', 'grep', 'find', 'chmod', 
                          'sudo', 'apt', 'yum', 'ps', 'top', 'kill', 'vim', 'nano'}
        query_words.update({w for w in query_lower.split() if w in important_terms})
        
        # Extract and rank sentences from most relevant documents
        sentence_scores = []
        instructions_list = []  # For how-to questions
        
        # Process top documents (prioritize by relevance)
        for doc_idx, doc in enumerate(context_docs[:4]):  # Process more docs for better coverage
            text = doc['text']
            relevance_weight = 1.0 / (doc_idx + 1)  # Higher weight for more relevant docs
            
            # For how-to questions, extract instructions first
            if is_how_to:
                instructions = self._extract_instructions(text, query_words)
                for instruction in instructions:
                    instructions_list.append({
                        'instruction': instruction,
                        'source': doc['source_file'],
                        'relevance': relevance_weight
                    })
            
            # Better sentence splitting (handle abbreviations)
            sentences = re.split(r'(?<=[.!?])\s+', text)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 30:  # Skip very short sentences
                    continue
                
                sentence_lower = sentence.lower()
                
                # Calculate relevance score for this sentence
                word_matches = sum(1 for word in query_words if word in sentence_lower)
                match_ratio = word_matches / max(len(query_words), 1)
                
                # Check if sentence contains key query terms
                query_terms_in_sentence = any(word in sentence_lower for word in query_words)
                
                # Check for unrelated content (documentation contribution, etc.)
                unrelated_phrases = ['code of conduct', 'contribution', 'coda repository', 
                                   'technical writing', 'submit a guide', 'documentation contribution',
                                   'collection of related tutorials', 'how-to guides', 'reference section']
                has_unrelated = any(phrase in sentence_lower for phrase in unrelated_phrases)
                
                # Skip sentences with low relevance or unrelated content
                if not query_terms_in_sentence and match_ratio < 0.3:
                    continue
                
                # Heavy penalty for unrelated sentences (especially meta-documentation)
                if has_unrelated and match_ratio < 0.5:
                    continue
                
                # Score calculation
                base_score = match_ratio * relevance_weight
                
                # Bonus for sentences that start with important words
                if any(sentence_lower.startswith(word) for word in query_words):
                    base_score *= 1.5
                
                # Bonus for instruction-like sentences in how-to questions
                if is_how_to:
                    instruction_verbs = ['install', 'configure', 'setup', 'set up', 'create',
                                        'run', 'execute', 'start', 'enable', 'add', 'download']
                    if any(verb in sentence_lower for verb in instruction_verbs):
                        base_score *= 1.3
                
                # Bonus for sentences mentioning specific tools/technologies from query
                if 'web server' in query_lower:
                    web_server_terms = ['apache', 'nginx', 'httpd', 'webserver', 'web server']
                    if any(term in sentence_lower for term in web_server_terms):
                        base_score *= 1.4
                
                # Penalty for very long sentences (might be less focused)
                if len(sentence) > 300:
                    base_score *= 0.8
                
                sentence_scores.append({
                    'sentence': sentence,
                    'score': base_score,
                    'source': doc['source_file']
                })
        
        # For how-to questions, prioritize instructions
        if is_how_to and instructions_list:
            # Sort instructions by relevance
            instructions_list.sort(key=lambda x: x['relevance'], reverse=True)
            
            # Build structured answer
            answer_parts = []
            seen_instructions = set()
            
            # Add introductory sentence if available
            intro_sentences = [s for s in sentence_scores if s['score'] > 0.5]
            if intro_sentences:
                intro_sentences.sort(key=lambda x: x['score'], reverse=True)
                best_intro = intro_sentences[0]['sentence']
                if len(best_intro) < 200:  # Keep intro concise
                    answer_parts.append(best_intro)
            
            # Add instructions - get more for complete answers
            for inst in instructions_list[:20]:  # Increased limit for complete instructions
                inst_text = inst['instruction']
                inst_key = inst_text.lower()[:50]
                if inst_key not in seen_instructions:
                    answer_parts.append(inst_text)
                    seen_instructions.add(inst_key)
            
            if answer_parts:
                answer = ' '.join(answer_parts)
                # Clean up
                answer = re.sub(r'\s+', ' ', answer)
                answer = re.sub(r'\s+([.!?])', r'\1', answer)
                # Don't truncate - let formatting handle structure
            else:
                # Fallback to regular sentence selection
                sentence_scores.sort(key=lambda x: x['score'], reverse=True)
                selected = [s['sentence'] for s in sentence_scores[:20]]  # Get many more sentences for complete answers
                answer = ' '.join(selected) if selected else context_docs[0]['text']
        elif not sentence_scores:
            # Fallback: use the most relevant document's beginning
            best_doc = context_docs[0]
            text = best_doc['text']
            # Try to find a good starting point
            sentences = re.split(r'(?<=[.!?])\s+', text)
            if sentences:
                # Take first few sentences that are substantial
                answer_parts = [s.strip() for s in sentences[:5] if len(s.strip()) > 50]
                if answer_parts:
                    answer = ' '.join(answer_parts)
                    # Don't truncate - keep full answer
                else:
                    answer = text if len(text) > 0 else text
            else:
                answer = text  # Use full text, don't truncate
        else:
            # Sort by score and select top sentences
            sentence_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Select sentences ensuring coherence and avoiding redundancy
            selected_sentences = []
            seen_content = set()
            # No max_length limit - get all relevant sentences
            
            for item in sentence_scores:
                sentence = item['sentence']
                # Simple deduplication check
                sentence_key = sentence.lower()[:50]
                if sentence_key in seen_content:
                    continue
                
                selected_sentences.append(sentence)
                seen_content.add(sentence_key)
                
                # Get more sentences for complete answers (increased from 8 to 20)
                if len(selected_sentences) >= 20:
                    break
            
            if selected_sentences:
                # Join sentences with proper spacing
                answer = ' '.join(selected_sentences)
                
                # Clean up multiple spaces and ensure proper punctuation
                answer = re.sub(r'\s+', ' ', answer)
                answer = re.sub(r'\s+([.!?])', r'\1', answer)
                
                # Ensure it ends properly
                if not answer[-1] in '.!?':
                    answer += '.'
            else:
                # Fallback - use more of the text
                answer = context_docs[0]['text'][:2000] if len(context_docs[0]['text']) > 2000 else context_docs[0]['text']
        
        # Format answer with markdown structure
        answer = self._format_answer_with_markdown(answer, query, is_how_to)
        
        return answer
    
    def query(self, question: str) -> Dict:
        """
        Query the RAG model with a question.
        
        Args:
            question: The user's question
        
        Returns:
            Dictionary with answer and source documents
        """
        logger.info(f"Processing query: {question}")
        # Retrieve relevant documents
        context_docs = self.retrieve(question)
        
        # Generate answer
        answer = self.generate_answer(question, context_docs)
        
        logger.info(f"Generated answer (length: {len(answer)} chars, sources: {len(context_docs)})")
        
        return {
            "answer": answer,
            "question": question,
            "sources": context_docs
        }


def build_rag_model(
    vector_db_path: str = "vector_db",
    embedding_model: str = "all-MiniLM-L6-v2",
    use_llm: bool = False,
    llm_model_name: str = "llama3.2:3b",
    use_quantization: bool = True
) -> SimpleRAGModel:
    """
    Build a RAG model with optional LLM support.
    
    Args:
        vector_db_path: Path to the vector database
        embedding_model: Name of the embedding model
        use_llm: Whether to use LLM for answer generation (default: True)
        llm_model_name: Name of the LLM model to use
        use_quantization: Use quantization for lower memory usage
    
    Returns:
        RAG model instance
    """
    return SimpleRAGModel(
        vector_db_path, 
        embedding_model,
        use_llm=use_llm,
        llm_model_name=llm_model_name,
        use_quantization=use_quantization
    )


def test_rag_model(rag_model: SimpleRAGModel, test_questions: List[str] = None):
    """
    Test the RAG model with sample questions.
    
    Args:
        rag_model: The RAG model to test
        test_questions: List of test questions (optional)
    """
    if test_questions is None:
        test_questions = [
            "What is Red Hat Enterprise Linux?",
            "How do I configure system settings?",
            "What are the basic system configuration steps?",
        ]
    
    logger.info("="*60)
    logger.info("Testing RAG Model")
    logger.info("="*60)
    
    print("\n" + "="*60)
    print("Testing RAG Model")
    print("="*60)
    
    for idx, question in enumerate(test_questions, 1):
        logger.info(f"Question {idx}: {question}")
        logger.info("-" * 60)
        
        print(f"\n[Question {idx}/{len(test_questions)}]")
        print(f"Question: {question}")
        print("-" * 60)
        
        try:
            print("Processing...")
            result = rag_model.query(question)
            answer = result["answer"]
            sources = result.get("sources", [])
            
            logger.info(f"Answer: {answer}")
            
            print(f"\nAnswer:")
            print(f"{answer}")
            
            if sources:
                logger.info(f"Sources ({len(sources)}):")
                print(f"\nSources ({len(sources)}):")
                for i, source in enumerate(sources[:2], 1):  # Show first 2 sources
                    logger.info(f"  {i}. {source.get('source_file', 'unknown')}")
                    logger.info(f"     Preview: {source['text'][:150]}...")
                    print(f"  {i}. {source.get('source_file', 'unknown')}")
                    print(f"     Preview: {source['text'][:150]}...")
            print()
        
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            print(f"Error: {str(e)}")
    
    print("="*60)
    print("Testing completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    vector_db_path = "vector_db"
    
    # Build the RAG model
    rag_model = build_rag_model(vector_db_path)
    
    # Test with sample questions
    test_questions = [
        "What is Red Hat Enterprise Linux?",
        "How do I configure basic system settings?",
        "What are the key features of RHEL 9?",
    ]
    
    test_rag_model(rag_model, test_questions)
