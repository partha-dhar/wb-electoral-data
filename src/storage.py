"""
Data Storage Module
Handles storing voter data in JSON/YAML format and SQLite database
"""

import json
import yaml
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import gzip


class DataStorage:
    """
    Stores voter data in structured JSON/YAML format
    """
    
    def __init__(self, config: Dict):
        """
        Initialize data storage
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Setup directories
        self.output_dir = Path(config['directories']['output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage settings
        storage_config = config.get('storage', {})
        self.format = storage_config.get('format', 'json')
        self.indent = storage_config.get('indent', 2)
        self.ensure_ascii = storage_config.get('ensure_ascii', False)
        self.pretty_print = storage_config.get('pretty_print', True)
        self.compression = storage_config.get('compression', False)
    
    def save_voters(self, voters: List[Dict[str, Any]], 
                   ac_number: int, part_number: int,
                   metadata: Optional[Dict[str, Any]] = None) -> Path:
        """
        Save voter data to file
        
        Args:
            voters: List of voter dictionaries
            ac_number: AC number
            part_number: Part number
            metadata: Optional metadata
            
        Returns:
            Path to saved file
        """
        # Build output structure
        output_data = {
            'metadata': {
                'ac_number': ac_number,
                'part_number': part_number,
                'extraction_date': datetime.now().isoformat(),
                'total_voters': len(voters),
                'format_version': '1.0'
            },
            'voters': voters
        }
        
        # Add custom metadata
        if metadata:
            output_data['metadata'].update(metadata)
        
        # Generate filename
        filename = f"AC_{ac_number:03d}_Part_{part_number:03d}"
        
        # Save based on format
        if self.format == 'yaml':
            output_path = self.output_dir / f"{filename}.yaml"
            self._save_yaml(output_data, output_path)
        else:
            output_path = self.output_dir / f"{filename}.json"
            self._save_json(output_data, output_path)
        
        self.logger.info(f"Saved {len(voters)} voters to {output_path}")
        return output_path
    
    def _save_json(self, data: Dict[str, Any], filepath: Path) -> None:
        """
        Save data as JSON
        
        Args:
            data: Data to save
            filepath: Output file path
        """
        # Determine indent
        indent = self.indent if self.pretty_print else None
        
        json_str = json.dumps(
            data,
            indent=indent,
            ensure_ascii=self.ensure_ascii
        )
        
        # Save with optional compression
        if self.compression:
            filepath = filepath.with_suffix('.json.gz')
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                f.write(json_str)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
    
    def _save_yaml(self, data: Dict[str, Any], filepath: Path) -> None:
        """
        Save data as YAML
        
        Args:
            data: Data to save
            filepath: Output file path
        """
        # Save with optional compression
        if self.compression:
            filepath = filepath.with_suffix('.yaml.gz')
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
    
    def load_voters(self, filepath: Path) -> Dict[str, Any]:
        """
        Load voter data from file
        
        Args:
            filepath: Path to data file
            
        Returns:
            Dictionary containing voter data
        """
        filepath = Path(filepath)
        
        # Check if compressed
        is_compressed = filepath.suffix == '.gz'
        
        # Determine format
        if '.yaml' in filepath.name:
            return self._load_yaml(filepath, is_compressed)
        else:
            return self._load_json(filepath, is_compressed)
    
    def _load_json(self, filepath: Path, compressed: bool = False) -> Dict[str, Any]:
        """
        Load JSON file
        
        Args:
            filepath: Path to JSON file
            compressed: Whether file is gzip compressed
            
        Returns:
            Loaded data
        """
        if compressed:
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def _load_yaml(self, filepath: Path, compressed: bool = False) -> Dict[str, Any]:
        """
        Load YAML file
        
        Args:
            filepath: Path to YAML file
            compressed: Whether file is gzip compressed
            
        Returns:
            Loaded data
        """
        if compressed:
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
    
    def save_validation_report(self, report: Dict[str, Any], 
                              ac_number: int, part_number: int) -> Path:
        """
        Save validation report
        
        Args:
            report: Validation report dictionary
            ac_number: AC number
            part_number: Part number
            
        Returns:
            Path to saved report
        """
        filename = f"AC_{ac_number:03d}_Part_{part_number:03d}_validation"
        output_path = self.output_dir / f"{filename}.json"
        
        report['metadata'] = {
            'ac_number': ac_number,
            'part_number': part_number,
            'validation_date': datetime.now().isoformat()
        }
        
        self._save_json(report, output_path)
        self.logger.info(f"Saved validation report to {output_path}")
        
        return output_path
    
    def save_statistics(self, stats: Dict[str, Any], 
                       ac_number: Optional[int] = None) -> Path:
        """
        Save statistics report
        
        Args:
            stats: Statistics dictionary
            ac_number: Optional AC number (None for all)
            
        Returns:
            Path to saved statistics
        """
        if ac_number:
            filename = f"AC_{ac_number:03d}_statistics.json"
        else:
            filename = "west_bengal_statistics.json"
        
        output_path = self.output_dir / filename
        
        stats['metadata'] = {
            'generated_date': datetime.now().isoformat()
        }
        
        self._save_json(stats, output_path)
        self.logger.info(f"Saved statistics to {output_path}")
        
        return output_path
    
    def organize_by_district(self, ac_number: int, district_number: int) -> Path:
        """
        Organize output files by district structure
        
        Args:
            ac_number: AC number
            district_number: District number
            
        Returns:
            Path to district directory
        """
        district_dir = self.output_dir / f"District_{district_number:02d}"
        ac_dir = district_dir / f"AC_{ac_number:03d}"
        ac_dir.mkdir(parents=True, exist_ok=True)
        
        return ac_dir
    
    def export_to_csv(self, voters: List[Dict[str, Any]], 
                     output_path: Path) -> None:
        """
        Export voter data to CSV format
        
        Args:
            voters: List of voter dictionaries
            output_path: Output CSV file path
        """
        import csv
        
        if not voters:
            self.logger.warning("No voters to export")
            return
        
        # Get all field names
        fieldnames = list(voters[0].keys())
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(voters)
        
        self.logger.info(f"Exported {len(voters)} voters to CSV: {output_path}")
    
    def export_to_excel(self, voters: List[Dict[str, Any]], 
                       output_path: Path) -> None:
        """
        Export voter data to Excel format
        
        Args:
            voters: List of voter dictionaries
            output_path: Output Excel file path
        """
        try:
            import pandas as pd
            
            df = pd.DataFrame(voters)
            df.to_excel(output_path, index=False, engine='openpyxl')
            
            self.logger.info(f"Exported {len(voters)} voters to Excel: {output_path}")
        
        except ImportError:
            self.logger.error("pandas and openpyxl required for Excel export")
            raise
    
    def create_index(self, directory: Optional[Path] = None) -> Dict[str, Any]:
        """
        Create an index of all stored data files
        
        Args:
            directory: Directory to index (default: output_dir)
            
        Returns:
            Index dictionary
        """
        if directory is None:
            directory = self.output_dir
        
        index = {
            'created': datetime.now().isoformat(),
            'files': [],
            'total_files': 0,
            'total_voters': 0
        }
        
        # Find all data files
        for filepath in directory.glob('**/*.json'):
            if 'validation' not in filepath.name and 'statistics' not in filepath.name:
                try:
                    data = self.load_voters(filepath)
                    
                    file_info = {
                        'path': str(filepath.relative_to(directory)),
                        'ac_number': data['metadata'].get('ac_number'),
                        'part_number': data['metadata'].get('part_number'),
                        'total_voters': data['metadata'].get('total_voters'),
                        'extraction_date': data['metadata'].get('extraction_date')
                    }
                    
                    index['files'].append(file_info)
                    index['total_files'] += 1
                    index['total_voters'] += file_info['total_voters']
                
                except Exception as e:
                    self.logger.warning(f"Error indexing {filepath}: {e}")
        
        # Save index
        index_path = directory / 'index.json'
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
        
        self.logger.info(f"Created index with {index['total_files']} files")
        return index


class Database:
    """SQLite database for voter data with verification support."""
    
    def __init__(self, db_path: str = 'data/voters.db'):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.logger = logging.getLogger(__name__)
        
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        # Main voters table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS voters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                epic_number TEXT,
                ac_number INTEGER,
                part_number INTEGER,
                serial_number INTEGER,
                name TEXT,
                age INTEGER,
                gender TEXT,
                relation_type TEXT,
                relation_name TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT NULL,
                verification_date TIMESTAMP DEFAULT NULL,
                api_data TEXT DEFAULT NULL,
                UNIQUE(epic_number, ac_number, part_number, serial_number)
            )
        """)
        
        # Index for faster lookups
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ac_part_serial 
            ON voters(ac_number, part_number, serial_number)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_epic 
            ON voters(epic_number)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verified 
            ON voters(verified)
        """)
        
        self.conn.commit()
        self.logger.info("Database tables initialized")
    
    def insert_voter(self, voter_data: Dict[str, Any]) -> Optional[int]:
        """
        Insert a voter record.
        
        Args:
            voter_data: Dictionary with voter information
        
        Returns:
            Inserted row ID or None if already exists
        """
        try:
            self.cursor.execute("""
                INSERT INTO voters (
                    epic_number, ac_number, part_number, serial_number,
                    name, age, gender, relation_type, relation_name, address
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                voter_data.get('epic_number'),
                voter_data.get('ac_number'),
                voter_data.get('part_number'),
                voter_data.get('serial_number'),
                voter_data.get('name'),
                voter_data.get('age'),
                voter_data.get('gender'),
                voter_data.get('relation_type'),
                voter_data.get('relation_name'),
                voter_data.get('address')
            ))
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Voter already exists
            return None
    
    def get_voters_by_ac(self, ac_number: int) -> List[Tuple]:
        """
        Get all voters for an assembly constituency.
        
        Args:
            ac_number: Assembly constituency number
        
        Returns:
            List of voter tuples (id, epic, part_no, serial_no, age, ...)
        """
        self.cursor.execute("""
            SELECT id, epic_number, part_number, serial_number, age, 
                   name, gender, verified
            FROM voters
            WHERE ac_number = ?
            ORDER BY part_number, serial_number
        """, (ac_number,))
        return self.cursor.fetchall()
    
    def mark_voter_verified(
        self, 
        voter_id: int, 
        verified: bool, 
        api_data: Optional[Dict] = None
    ):
        """
        Mark a voter as verified with API data.
        
        Args:
            voter_id: Voter database ID
            verified: Whether verification was successful
            api_data: Optional API response data
        """
        api_json = json.dumps(api_data) if api_data else None
        
        self.cursor.execute("""
            UPDATE voters 
            SET verified = ?, 
                verification_date = CURRENT_TIMESTAMP,
                api_data = ?
            WHERE id = ?
        """, (verified, api_json, voter_id))
    
    def get_verification_stats(self, ac_number: Optional[int] = None) -> Dict:
        """
        Get verification statistics.
        
        Args:
            ac_number: Optional AC number filter
        
        Returns:
            Statistics dictionary
        """
        where_clause = "WHERE ac_number = ?" if ac_number else ""
        params = (ac_number,) if ac_number else ()
        
        self.cursor.execute(f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) as verified,
                SUM(CASE WHEN verified = 0 THEN 1 ELSE 0 END) as not_verified,
                SUM(CASE WHEN verified IS NULL THEN 1 ELSE 0 END) as pending
            FROM voters
            {where_clause}
        """, params)
        
        row = self.cursor.fetchone()
        return {
            'total': row[0],
            'verified': row[1] or 0,
            'not_verified': row[2] or 0,
            'pending': row[3] or 0
        }
    
    def close(self):
        """Close database connection."""
        self.conn.commit()
        self.conn.close()
        self.logger.info("Database connection closed")

