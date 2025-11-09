"""
Voter Data Parser Module
Parses extracted text to structure voter information
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime


class VoterParser:
    """
    Parses voter information from extracted text lines
    """
    
    def __init__(self, config: Dict):
        """
        Initialize voter parser
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Extraction settings
        extraction_config = config.get('extraction', {})
        self.min_age = extraction_config.get('min_age', 18)
        self.max_age = extraction_config.get('max_age', 120)
    
    def parse_voter_record(self, lines: List[str], start_idx: int) -> Optional[Dict[str, Any]]:
        """
        Parse a single voter record from text lines
        
        Args:
            lines: List of text lines
            start_idx: Starting index in lines
            
        Returns:
            Dictionary containing voter information or None
        """
        # This is a placeholder - actual implementation depends on PDF format
        # You'll need to adapt this based on the actual structure of your PDFs
        
        voter = {
            'serial_no': None,
            'name': None,
            'relative_name': None,
            'relation_type': None,
            'house_no': None,
            'age': None,
            'gender': None,
            'epic_no': None,
            'section': None,
            'part_no': None
        }
        
        try:
            # Example parsing logic (customize based on your PDF structure)
            current_line = start_idx
            
            # Line 1: Serial number and Name
            if current_line < len(lines):
                line = lines[current_line]
                # Extract serial and name
                match = re.match(r'^(\d+)\s+(.+)$', line)
                if match:
                    voter['serial_no'] = int(match.group(1))
                    voter['name'] = match.group(2).strip()
                current_line += 1
            
            # Line 2: Relative information
            if current_line < len(lines):
                line = lines[current_line]
                # Extract relation and relative name
                # Pattern: "Father: JOHN DOE" or "Husband: JANE DOE"
                match = re.match(r'^(Father|Mother|Husband):\s*(.+)$', line, re.IGNORECASE)
                if match:
                    voter['relation_type'] = match.group(1).capitalize()
                    voter['relative_name'] = match.group(2).strip()
                current_line += 1
            
            # Line 3: House number and age
            if current_line < len(lines):
                line = lines[current_line]
                # Extract house no and age
                # Pattern: "House: 5/1  Age: 52  Gender: M"
                house_match = re.search(r'House:\s*([^\s]+)', line)
                age_match = re.search(r'Age:\s*(\d+)', line)
                gender_match = re.search(r'Gender:\s*([MF])', line, re.IGNORECASE)
                
                if house_match:
                    voter['house_no'] = house_match.group(1)
                if age_match:
                    voter['age'] = int(age_match.group(1))
                if gender_match:
                    voter['gender'] = gender_match.group(1).upper()
                current_line += 1
            
            # Line 4: EPIC number
            if current_line < len(lines):
                line = lines[current_line]
                # Extract EPIC
                epic_match = re.search(r'(WB[/\d]+)', line)
                if epic_match:
                    voter['epic_no'] = epic_match.group(1)
                current_line += 1
            
            # Validate parsed data
            if voter['name'] and voter['age']:
                return voter
            else:
                return None
        
        except Exception as e:
            self.logger.error(f"Error parsing voter record at line {start_idx}: {e}")
            return None
    
    def parse_pdf_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Parse all voter records from PDF text lines
        
        Args:
            lines: List of text lines from PDF
            
        Returns:
            List of voter dictionaries
        """
        voters = []
        
        # Skip header lines (customize based on your PDF)
        start_line = 0
        for i, line in enumerate(lines):
            if re.search(r'Serial|S\.?No\.?|Sl\.?No\.?', line, re.IGNORECASE):
                start_line = i + 1
                break
        
        self.logger.debug(f"Starting parse at line {start_line}")
        
        i = start_line
        while i < len(lines):
            # Check if this line starts a voter record (usually begins with number)
            if re.match(r'^\d+\s', lines[i]):
                voter = self.parse_voter_record(lines, i)
                
                if voter:
                    # Validate voter data
                    if self._validate_voter(voter):
                        voters.append(voter)
                        self.logger.debug(f"Parsed voter: {voter['name']}")
                    else:
                        self.logger.warning(f"Invalid voter data at line {i}: {voter}")
                
                # Move to next record (estimate 4 lines per record)
                i += 4
            else:
                i += 1
        
        self.logger.info(f"Parsed {len(voters)} voters from {len(lines)} lines")
        return voters
    
    def _validate_voter(self, voter: Dict[str, Any]) -> bool:
        """
        Validate voter data
        
        Args:
            voter: Voter dictionary
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not voter.get('name'):
            return False
        
        # Validate age
        age = voter.get('age')
        if age:
            if not (self.min_age <= age <= self.max_age):
                self.logger.warning(f"Invalid age: {age}")
                return False
        
        # Validate gender
        gender = voter.get('gender')
        if gender and gender not in ['M', 'F', 'O']:
            return False
        
        return True
    
    def parse_part_metadata(self, lines: List[str]) -> Dict[str, Any]:
        """
        Extract metadata from PDF (AC, Part number, etc.)
        
        Args:
            lines: Text lines from PDF
            
        Returns:
            Dictionary with metadata
        """
        metadata = {
            'ac_number': None,
            'ac_name': None,
            'part_number': None,
            'section_name': None,
            'polling_station': None
        }
        
        # Parse first few lines for metadata
        for line in lines[:20]:  # Check first 20 lines
            # AC Number and Name
            ac_match = re.search(r'Assembly\s+Constituency.*?(\d+).*?[:-]\s*([A-Z\s]+)', line, re.IGNORECASE)
            if ac_match:
                metadata['ac_number'] = int(ac_match.group(1))
                metadata['ac_name'] = ac_match.group(2).strip()
            
            # Part Number
            part_match = re.search(r'Part\s+No\.?\s*[:-]?\s*(\d+)', line, re.IGNORECASE)
            if part_match:
                metadata['part_number'] = int(part_match.group(1))
            
            # Section
            section_match = re.search(r'Section\s*[:-]\s*([A-Z0-9\s]+)', line, re.IGNORECASE)
            if section_match:
                metadata['section_name'] = section_match.group(1).strip()
        
        return metadata
    
    def format_epic_number(self, epic: str) -> str:
        """
        Format EPIC number with proper structure
        
        Args:
            epic: Raw EPIC number
            
        Returns:
            Formatted EPIC number (WB/12/345/678901)
        """
        if not epic:
            return ""
        
        # Remove spaces and convert to uppercase
        epic = epic.upper().replace(' ', '').replace('/', '')
        
        # Remove WB prefix if exists
        if epic.startswith('WB'):
            epic = epic[2:]
        
        # Format: WB/XX/XXX/XXXXXX
        if len(epic) >= 11:
            part1 = epic[:2]    # State part: e.g., 12
            part2 = epic[2:5]   # AC part: e.g., 345
            part3 = epic[5:]    # Voter part: e.g., 678901
            
            return f"WB/{part1}/{part2}/{part3}"
        
        return f"WB/{epic}"
    
    def parse_batch(self, pdf_texts: Dict[str, List[str]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse multiple PDFs
        
        Args:
            pdf_texts: Dictionary mapping filenames to text lines
            
        Returns:
            Dictionary mapping filenames to voter lists
        """
        results = {}
        
        for filename, lines in pdf_texts.items():
            self.logger.info(f"Parsing {filename}")
            voters = self.parse_pdf_lines(lines)
            results[filename] = voters
        
        return results
    
    def extract_statistics(self, voters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics from voter list
        
        Args:
            voters: List of voter dictionaries
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_voters': len(voters),
            'male_voters': 0,
            'female_voters': 0,
            'other_voters': 0,
            'with_epic': 0,
            'without_epic': 0,
            'age_distribution': {},
            'avg_age': 0
        }
        
        ages = []
        
        for voter in voters:
            # Gender count
            gender = voter.get('gender', 'O')
            if gender == 'M':
                stats['male_voters'] += 1
            elif gender == 'F':
                stats['female_voters'] += 1
            else:
                stats['other_voters'] += 1
            
            # EPIC count
            if voter.get('epic_no'):
                stats['with_epic'] += 1
            else:
                stats['without_epic'] += 1
            
            # Age stats
            age = voter.get('age')
            if age:
                ages.append(age)
                age_group = f"{(age // 10) * 10}-{(age // 10) * 10 + 9}"
                stats['age_distribution'][age_group] = stats['age_distribution'].get(age_group, 0) + 1
        
        # Calculate average age
        if ages:
            stats['avg_age'] = round(sum(ages) / len(ages), 1)
        
        return stats
