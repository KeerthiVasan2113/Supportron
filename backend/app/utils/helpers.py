"""
Helper functions for code formatting and language detection.
"""

import re
from enum import Enum
from functools import lru_cache
from typing import List, Tuple

from app.core.config import Config


class CodeLanguage(str, Enum):
    """Supported code languages for syntax highlighting."""
    PHP = "php"
    PYTHON = "python"
    APACHE = "apache"
    SQL = "sql"
    BASH = "bash"
    HTML = "html"
    NONE = ""


@lru_cache(maxsize=128)
def compile_regex_patterns() -> Tuple[re.Pattern, ...]:
    """Compile regex patterns once for better performance."""
    return tuple(re.compile(pattern, re.IGNORECASE) for pattern in [
        r'^\s*\$',
        r'^\s*#\s*[a-zA-Z]',
        r'^\s*<\?php',
        r'^\s*<\?',
        r'^\s*<IfModule',
        r'^\s*</IfModule',
        r'^\s*AuthType\s+',
        r'^\s*AuthName\s+',
        r'^\s*AuthUserFile\s+',
        r'^\s*Require\s+',
        r'^\s*import\s+[a-zA-Z]',
        r'^\s*from\s+[a-zA-Z]',
        r'^\s*def\s+[a-zA-Z_]',
        r'^\s*class\s+[a-zA-Z_]',
        r'^\s*if\s+[\(a-zA-Z_]',
        r'^\s*for\s+[\(a-zA-Z_]',
        r'^\s*while\s+[\(a-zA-Z_]',
        r'^\s*return\s+',
        r'^\s*SELECT\s+',
        r'^\s*INSERT\s+',
        r'^\s*UPDATE\s+',
        r'^\s*DELETE\s+',
        r'^\s*CREATE\s+',
        r'^\s*ALTER\s+',
        r'^\s*DROP\s+',
        r'^\s*curl\s+',
        r'^\s*npm\s+',
        r'^\s*pip\s+',
        r'^\s*sudo\s+',
        r'^\s*postconf\s+',
        r'^\s*git\s+',
        r'^\s*#!/',
    ])


def detect_language(code: str) -> CodeLanguage:
    """
    Detect programming language from code snippet.
    
    Args:
        code: Code snippet to analyze
        
    Returns:
        Detected language enum
    """
    code_lower = code.lower()
    
    # PHP detection
    if any(keyword in code_lower for keyword in ['php', '<?php', '<?', '$_session', 'echo']):
        return CodeLanguage.PHP
    
    # Python detection
    if any(keyword in code_lower for keyword in ['python', 'import', 'def ', 'class ', 'print(']):
        return CodeLanguage.PYTHON
    
    # Apache detection
    if any(keyword in code_lower for keyword in ['<ifmodule', 'authtype', 'require', 'authname', 'authuserfile', '</ifmodule']):
        return CodeLanguage.APACHE
    
    # SQL detection
    if any(keyword in code_lower for keyword in ['select', 'insert', 'update', 'delete', 'create', 'alter', 'drop']):
        return CodeLanguage.SQL
    
    # Bash/Shell detection
    if any(keyword in code_lower for keyword in ['$', 'npm', 'pip', 'curl', 'bash', 'shell', 'sudo', 'postconf', 'git', '#!/']):
        return CodeLanguage.BASH
    
    # HTML detection
    if any(keyword in code_lower for keyword in ['<html', '<div', '<script', '</html', '<', '>', 'html', 'xml']):
        return CodeLanguage.HTML
    
    return CodeLanguage.NONE


def clean_markdown_heading(line: str) -> str:
    """
    Clean markdown heading by removing markdown syntax.
    
    Removes:
    - `**` (bold markers)
    - `###`, `##`, `#` (heading markers)
    - Leading/trailing whitespace
    
    Args:
        line: Line that may be a markdown heading
        
    Returns:
        Cleaned heading text
    """
    cleaned = line.strip()
    
    # Remove markdown heading markers (###, ##, #)
    cleaned = re.sub(r'^#{1,6}\s+', '', cleaned)
    
    # Remove bold markers (**text**)
    cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
    
    # Remove single asterisks (*text*)
    cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
    
    # Remove any remaining leading/trailing asterisks
    cleaned = cleaned.strip('*').strip()
    
    return cleaned


def is_markdown_heading(line: str) -> bool:
    """
    Check if a line is a markdown heading.
    
    Args:
        line: Line to check
        
    Returns:
        True if line is a markdown heading
    """
    stripped = line.strip()
    
    # Check for markdown heading syntax (#, ##, ###, etc.)
    if re.match(r'^#{1,6}\s+', stripped):
        return True
    
    # Check for bold heading (**text**)
    if re.match(r'^\*\*.*\*\*$', stripped) and not re.search(r'[{}();=<>\[\]]', stripped):
        return True
    
    # Check for numbered heading with bold (e.g., "4. **Heading**")
    if re.match(r'^\d+\.\s+\*\*.*\*\*$', stripped):
        return True
    
    return False


def format_code_blocks(text: str) -> str:
    """
    Post-process text to ensure code blocks are properly formatted.
    
    Detects code patterns and wraps them in markdown code blocks.
    Only wraps pure code/commands/queries on their own lines.
    Also cleans up excessive punctuation and markdown headings.
    
    Args:
        text: Input text to format
        
    Returns:
        Formatted text with code blocks properly wrapped
    """
    if not text or not text.strip():
        return text
    
    lines = text.split('\n')
    formatted_lines: List[str] = []
    in_code_block = False
    code_block_lines: List[str] = []
    i = 0
    
    # Get compiled regex patterns for better performance
    code_indicators = compile_regex_patterns()
    
    # Compile command patterns once for better performance
    # Updated patterns to capture complete commands - use greedy matching for complete commands
    _command_patterns = [
        # Complete apt-get commands (capture full command including all flags)
        re.compile(r'(sudo\s+apt-get\s+(?:update|install|remove|upgrade|dist-upgrade|autoremove|clean|purge)\s+[^\n\.]+)', re.IGNORECASE),
        # Complete apt commands
        re.compile(r'(sudo\s+apt\s+(?:update|install|remove|upgrade|list|search|show)\s+[^\n\.]+)', re.IGNORECASE),
        # Complete systemctl commands
        re.compile(r'(sudo\s+systemctl\s+(?:start|stop|restart|enable|disable|status|reload)\s+[^\n\.]+)', re.IGNORECASE),
        # Complete docker commands
        re.compile(r'(sudo\s+docker\s+(?:run|build|pull|push|start|stop|restart|rm|rmi|ps|images|exec|logs)\s+[^\n\.]+)', re.IGNORECASE),
        # Generic sudo commands (capture complete command line)
        re.compile(r'(sudo\s+[a-zA-Z0-9_-]+(?:\s+[^\n\.]+)?)', re.IGNORECASE),
        # Other common commands
        re.compile(r'(postconf\s+[^\s]+(?:\s+(?:[^\s]+|[\'"][^\'"]*[\'"]))+)', re.IGNORECASE),
        re.compile(r'(curl\s+[^\s]+(?:\s+[^\s]+)+)', re.IGNORECASE),
        re.compile(r'(npm\s+[^\s]+(?:\s+[^\s]+)+)', re.IGNORECASE),
        re.compile(r'(pip\s+[^\s]+(?:\s+[^\s]+)+)', re.IGNORECASE),
        re.compile(r'(git\s+[^\s]+(?:\s+[^\s]+)+)', re.IGNORECASE),
        re.compile(r'(\$\s+[^\s]+(?:\s+[^\s]+)+)', re.IGNORECASE),
        # SQL commands
        re.compile(r'(SELECT\s+.*?;)', re.IGNORECASE | re.DOTALL),
        re.compile(r'(INSERT\s+.*?;)', re.IGNORECASE | re.DOTALL),
        re.compile(r'(UPDATE\s+.*?;)', re.IGNORECASE | re.DOTALL),
        re.compile(r'(DELETE\s+.*?;)', re.IGNORECASE | re.DOTALL),
        re.compile(r'(CREATE\s+.*?;)', re.IGNORECASE | re.DOTALL),
    ]
    _trailing_words_pattern = re.compile(r'\s+(using|with|by|via|through)\s*$', re.IGNORECASE)
    
    def extract_code_from_line(line: str) -> Tuple[str, str]:
        """
        Extract code from a line that might contain descriptive text.
        
        Args:
            line: Line that may contain both text and code
            
        Returns:
            Tuple of (text_part, code_part). If no code found, returns (line, '')
        """
        stripped = line.strip()
        if not stripped:
            return (line, '')
        
        # Look for common command patterns in the line
        for pattern in _command_patterns:
            match = pattern.search(stripped)
            if match:
                code_part = match.group(1).strip()
                code_start = match.start()
                text_part = stripped[:code_start].strip()
                
                # Only extract if there's substantial text before the code
                # and the code part is substantial (not just a word)
                if (len(text_part) > Config.MIN_TEXT_LENGTH_FOR_EXTRACTION and 
                    len(code_part) > Config.MIN_CODE_LENGTH):
                    # Clean up text part - remove trailing words like "using", "with", "by"
                    text_part = _trailing_words_pattern.sub('', text_part)
                    return (text_part, code_part)
        
        return (line, '')
    
    # Check if a line is PURELY code (no descriptive text mixed in)
    def is_pure_code_line(line: str) -> bool:
        """
        Check if a line is purely code with no descriptive text.
        A line is pure code if it:
        - Starts with a code indicator
        - Has code structure and minimal words
        - Doesn't look like a sentence
        
        Headings are NEVER considered code.
        """
        stripped = line.strip()
        if not stripped:
            return False
        
        # Already in a code block marker
        if stripped.startswith('```'):
            return True
        
        # NEVER treat markdown headings as code
        if is_markdown_heading(line):
            return False
        
        # Exclude numbered lists, bullet points, and regular text
        # Numbered lists: "1. ", "2. ", etc.
        if re.match(r'^\d+\.\s+', stripped):
            return False
        
        # Bullet points: "- ", "* ", etc. (but not code comments or commands)
        if re.match(r'^[-*]\s+[A-Z][a-z]', stripped):  # Bullet with capital letter (likely text)
            return False
        
        # Exclude lines that start with descriptive text (capital letter, many words)
        # If line starts with capital and has many words, it's likely descriptive text
        if re.match(r'^[A-Z][a-z]+', stripped):
            word_count = len(stripped.split())
            # If it has many words and looks like a sentence, it's not pure code
            if word_count > 8:
                return False
            # If it ends with punctuation and has many words, it's descriptive text
            if word_count > 5 and stripped.rstrip().endswith(('.', '!', '?', ':', ',')):
                return False
        
        # Check against strict code patterns (must match at the START)
        for pattern in code_indicators:
            if pattern.match(stripped):
                return True
        
        # Check for code-like content with strict criteria
        # Must have multiple code indicators to be considered code
        code_chars = ['{', '}', '(', ')', ';', '=', '[', ']']
        code_char_count = sum(1 for char in stripped if char in code_chars)
        
        # Must have at least 2 code characters AND not look like a sentence
        if code_char_count >= 2:
            word_count = len(stripped.split())
            ends_with_punct = stripped.rstrip().endswith(('.', '!', '?', ':', ','))
            
            # If it has many words and ends with punctuation, it's likely text
            if word_count > 6 and ends_with_punct:
                return False
            
            # Must have code structure (brackets, braces, or function calls)
            has_code_structure = (
                '{' in stripped or 
                '}' in stripped or 
                ('(' in stripped and ')' in stripped) or
                ('[' in stripped and ']' in stripped) or
                ('=' in stripped and '==' not in stripped)  # Assignment, not comparison
            )
            
            # Also check that it doesn't start with descriptive text
            # If it starts with a capital letter and has many words, it's likely mixed
            if has_code_structure and not re.match(r'^[A-Z][a-z]+\s+[a-z]+', stripped):
                return True
        
        # Check for HTML/XML tags (strict - must be actual tags, not in sentences)
        html_tag_match = re.search(r'<[A-Za-z][A-Za-z0-9]*[^>]*>', stripped)
        if html_tag_match:
            # Exclude if it's part of a sentence (many words)
            if len(stripped.split()) > 8:
                return False
            # Exclude if it starts with descriptive text
            if re.match(r'^[A-Z][a-z]+\s+', stripped):
                return False
            return True
        
        return False
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Handle markdown headings - clean them and never wrap in code blocks
        if is_markdown_heading(line):
            cleaned_heading = clean_markdown_heading(line)
            formatted_lines.append(cleaned_heading)
            i += 1
            continue
        
        # Handle existing code block markers
        if stripped.startswith('```'):
            if in_code_block:
                # End code block - add closing marker
                if code_block_lines:
                    # Add opening marker if not already added
                    if not formatted_lines or not formatted_lines[-1].strip().startswith('```'):
                        formatted_lines.append('```')
                    formatted_lines.extend(code_block_lines)
                    formatted_lines.append('```')
                else:
                    # Empty code block - still add markers
                    if not formatted_lines or not formatted_lines[-1].strip().startswith('```'):
                        formatted_lines.append('```')
                    formatted_lines.append('```')
                code_block_lines = []
                in_code_block = False
            else:
                # Start code block - extract language if present
                lang_match = re.match(r'^```([a-zA-Z0-9_-]*)$', stripped)
                lang = lang_match.group(1) if lang_match else ''
                formatted_lines.append(f'```{lang}' if lang else '```')
                in_code_block = True
                code_block_lines = []
            i += 1
            continue
        
        if in_code_block:
            # Inside code block - check if this line is explanatory text that should be outside
            # Detect explanatory text patterns: (Note: ...), (This example...), etc.
            stripped_lower = stripped.lower()
            is_explanatory_text = (
                stripped.startswith('(Note:') or
                stripped.startswith('(Note ') or
                stripped.startswith('Note:') or
                stripped.startswith('Note ') or
                stripped.startswith('(This example') or
                stripped.startswith('(This command') or
                stripped.startswith('(For ') or
                stripped.startswith('(When ') or
                stripped.startswith('(If ') or
                stripped.startswith('(Warning:') or
                stripped.startswith('(Important:') or
                # Match patterns like "(Note: This command is used for...)"
                (re.match(r'^\(Note[:\s]', stripped, re.IGNORECASE)) or
                # Match patterns like "(This example is for...)"
                (re.match(r'^\(This\s+(example|command|method|approach)', stripped, re.IGNORECASE)) or
                # Match any parenthetical note that's clearly explanatory
                (stripped.startswith('(') and ')' in stripped and len(stripped) < 200 and 
                 not any(c in stripped for c in ['{', '}', '=', ';']) and
                 (stripped.count('(') == 1 and stripped.count(')') == 1) and
                 any(word in stripped_lower for word in ['note', 'example', 'for', 'when', 'if', 'used', 'command', 'machine', 'scenario']))
            )
            
            # Also check if line looks like a sentence/explanation rather than code
            looks_like_text = (
                not any(pattern.match(stripped) for pattern in code_indicators) and
                (stripped.endswith('.') or stripped.endswith(')')) and
                len(stripped.split()) > 3 and
                not any(char in stripped for char in ['{', '}', '[', ']', '=', ';', '|', '&&', '||', '>', '<']) and
                # Check if it starts with common explanatory phrases
                (stripped.startswith('Note') or stripped.startswith('(Note') or 
                 stripped.startswith('This') or stripped.startswith('(This') or
                 stripped.startswith('For ') or stripped.startswith('(For ') or
                 stripped.startswith('When ') or stripped.startswith('(When ') or
                 stripped.startswith('If ') or stripped.startswith('(If ') or
                 'domain-joined' in stripped_lower or 'standalone' in stripped_lower or
                 'dual-boot' in stripped_lower or 'scenarios' in stripped_lower)
            )
            
            if is_explanatory_text or looks_like_text:
                # This is explanatory text - close code block, add text outside
                if code_block_lines:
                    # Close the current code block first
                    formatted_lines.extend(code_block_lines)
                    formatted_lines.append('```')
                    code_block_lines = []
                    in_code_block = False
                # Add the explanatory text as regular text (outside code block)
                formatted_lines.append(line)
                i += 1
                continue
            
            # Inside code block - accumulate all lines (including empty ones)
            code_block_lines.append(line)
            i += 1
            continue
        
        # Check if line has code mixed with text
        text_part, code_part = extract_code_from_line(line)
        
        if code_part:
            # Line has both text and code - separate them
            if text_part:
                # Add the descriptive text as regular text
                formatted_lines.append(text_part)
            # Add the code in its own code block
            lang = detect_language(code_part)
            formatted_lines.append(f'```{lang.value if lang != CodeLanguage.NONE else ""}')
            formatted_lines.append(code_part)
            formatted_lines.append('```')
            i += 1
        elif is_pure_code_line(line):
            # Pure code line - collect consecutive code lines
            code_lines = [line]
            i += 1
            
            # Look ahead for more code lines
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                
                # Stop if we hit a blank line followed by non-code
                if not next_stripped:
                    # Check the line after the blank
                    if i + 1 < len(lines):
                        if not is_pure_code_line(lines[i + 1]):
                            break
                    else:
                        break
                elif not is_pure_code_line(next_line):
                    break
                
                code_lines.append(next_line)
                i += 1
            
            # Wrap code lines in code block
            all_code = ' '.join(code_lines)
            lang = detect_language(all_code)
            formatted_lines.append(f'```{lang.value if lang != CodeLanguage.NONE else ""}')
            formatted_lines.extend(code_lines)
            formatted_lines.append('```')
        else:
            # Regular text line - clean up excessive punctuation and markdown artifacts
            cleaned_line = line
            
            # Remove markdown bold markers from regular text (**text**)
            cleaned_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_line)
            
            # Remove markdown heading markers if they appear in text
            cleaned_line = re.sub(r'^#{1,6}\s+', '', cleaned_line)
            
            # Remove multiple consecutive punctuation marks
            cleaned_line = re.sub(r'([.!?])\1{2,}', r'\1\1', cleaned_line)  # Multiple periods/exclamations
            cleaned_line = re.sub(r'([,;:])\1+', r'\1', cleaned_line)  # Multiple commas/semicolons/colons
            
            # Remove trailing multiple punctuation (keep only one)
            cleaned_line = re.sub(r'([.!?])+$', r'\1', cleaned_line)
            
            formatted_lines.append(cleaned_line)
            i += 1
    
    # Handle any remaining code block
    if in_code_block and code_block_lines:
        formatted_lines.append('```')
        formatted_lines.extend(code_block_lines)
        formatted_lines.append('```')
    
    result = '\n'.join(formatted_lines)
    
    # Final cleanup: remove excessive punctuation in the entire text
    # Remove multiple spaces
    result = re.sub(r' +', ' ', result)
    # Remove multiple newlines (more than 2)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result

