"""
Text Extractor Module
Extracts text from PDF files with CID font decoding
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import pdfplumber
import re

from .utils import decode_cid_character, decode_shifted_character


class TextExtractor:
    """
    Extracts text from electoral roll PDFs with proper character decoding
    """
    
    def __init__(self, config: Dict):
        """
        Initialize text extractor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Load extraction settings
        extraction_config = config.get('extraction', {})
        self.cid_mappings = extraction_config.get('cid_mappings', {})
        self.char_mappings = extraction_config.get('char_mappings', {})
        
        # Build comprehensive CID mapping
        self._build_cid_mappings()
    
    def _build_cid_mappings(self):
        """Build comprehensive CID character mappings"""
        # Add digit mappings (cid:19 = 0, cid:20 = 1, etc.)
        for i in range(10):
            self.cid_mappings[f'cid:{19+i}'] = str(i)
        
        # Add special characters
        self.cid_mappings.update({
            'cid:17': '.',
            'cid:18': '/',
        })
    
    def decode_text(self, text: str) -> str:
        """
        Decode text with CID and character transformations
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Decoded text
        """
        if not text:
            return ""
        
        # Step 1: Decode CID characters
        # Match patterns like (cid:19)
        cid_pattern = r'\(cid:(\d+)\)'
        
        def replace_cid(match):
            cid_key = f"cid:{match.group(1)}"
            return self.cid_mappings.get(cid_key, match.group(0))
        
        text = re.sub(cid_pattern, replace_cid, text)
        
        # Step 2: Decode shifted characters
        decoded_chars = []
        for char in text:
            decoded_chars.append(self.char_mappings.get(char, char))
        
        return ''.join(decoded_chars)
    
    def extract_text_from_pdf(self, pdf_path: Path) -> List[str]:
        """
        Extract text lines from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of text lines
        """
        self.logger.debug(f"Extracting text from: {pdf_path}")
        
        lines = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract text
                    page_text = page.extract_text()
                    
                    if page_text:
                        # Split into lines
                        page_lines = page_text.split('\n')
                        
                        # Decode each line
                        for line in page_lines:
                            decoded_line = self.decode_text(line)
                            
                            # Skip blank lines if configured
                            if self.config.get('extraction', {}).get('skip_blank_lines', True):
                                if decoded_line.strip():
                                    lines.append(decoded_line.strip())
                            else:
                                lines.append(decoded_line)
                    
                    self.logger.debug(f"Extracted {len(page_lines)} lines from page {page_num}")
        
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise
        
        self.logger.info(f"Extracted {len(lines)} total lines from {pdf_path.name}")
        return lines
    
    def extract_with_layout(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extract text with layout information (positions, fonts, etc.)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of text objects with layout information
        """
        self.logger.debug(f"Extracting text with layout from: {pdf_path}")
        
        text_objects = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract words with positions
                    words = page.extract_words()
                    
                    for word in words:
                        decoded_text = self.decode_text(word['text'])
                        
                        text_objects.append({
                            'text': decoded_text,
                            'page': page_num,
                            'x0': word['x0'],
                            'y0': word['y0'],
                            'x1': word['x1'],
                            'y1': word['y1'],
                            'fontname': word.get('fontname'),
                            'size': word.get('size')
                        })
        
        except Exception as e:
            self.logger.error(f"Error extracting layout from {pdf_path}: {e}")
            raise
        
        return text_objects
    
    def extract_tables(self, pdf_path: Path) -> List[List[List[str]]]:
        """
        Extract tables from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of tables (each table is a list of rows)
        """
        self.logger.debug(f"Extracting tables from: {pdf_path}")
        
        all_tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    
                    for table in tables:
                        # Decode each cell
                        decoded_table = []
                        for row in table:
                            decoded_row = [
                                self.decode_text(cell) if cell else ""
                                for cell in row
                            ]
                            decoded_table.append(decoded_row)
                        
                        all_tables.append(decoded_table)
        
        except Exception as e:
            self.logger.error(f"Error extracting tables from {pdf_path}: {e}")
            raise
        
        self.logger.info(f"Extracted {len(all_tables)} tables from {pdf_path.name}")
        return all_tables
    
    def extract_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract PDF metadata
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing metadata
        """
        metadata = {
            'filename': pdf_path.name,
            'filepath': str(pdf_path),
            'pages': 0,
            'pdf_info': {}
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata['pages'] = len(pdf.pages)
                metadata['pdf_info'] = pdf.metadata
        
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {pdf_path}: {e}")
        
        return metadata
    
    def batch_extract(self, pdf_dir: Path, pattern: str = "*.pdf") -> Dict[str, List[str]]:
        """
        Extract text from multiple PDFs
        
        Args:
            pdf_dir: Directory containing PDFs
            pattern: File pattern to match
            
        Returns:
            Dictionary mapping filenames to extracted lines
        """
        pdf_dir = Path(pdf_dir)
        pdf_files = list(pdf_dir.glob(pattern))
        
        self.logger.info(f"Batch extracting {len(pdf_files)} PDFs from {pdf_dir}")
        
        results = {}
        
        for pdf_file in pdf_files:
            try:
                lines = self.extract_text_from_pdf(pdf_file)
                results[pdf_file.name] = lines
            except Exception as e:
                self.logger.error(f"Failed to extract {pdf_file.name}: {e}")
                results[pdf_file.name] = []
        
        return results
