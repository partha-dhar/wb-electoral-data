"""
Utility functions and helpers for the West Bengal Electoral Data project
"""

import os
import yaml
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urljoin, quote
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager


class SSLContextAdapter(HTTPAdapter):
    """
    Custom SSL adapter to handle legacy SSL servers
    """
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary containing configuration
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        # Try example config
        example_config = config_file.parent / "config.example.yaml"
        if example_config.exists():
            logging.warning(f"Config file not found, using example: {example_config}")
            config_file = example_config
        else:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured logger
    """
    log_config = config.get('logging', {})
    level = getattr(logging, log_config.get('level', 'INFO'))
    
    # Create logs directory
    logs_dir = Path(config.get('directories', {}).get('logs_dir', './logs'))
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    logging.basicConfig(
        level=level,
        format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(logs_dir / 'app.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


def ensure_directories(config: Dict[str, Any]) -> None:
    """
    Create necessary directories if they don't exist
    
    Args:
        config: Configuration dictionary
    """
    directories = config.get('directories', {})
    
    for key, path in directories.items():
        Path(path).mkdir(parents=True, exist_ok=True)


def get_session_with_ssl() -> requests.Session:
    """
    Create a requests session with SSL adapter
    
    Returns:
        Configured requests session
    """
    session = requests.Session()
    session.mount('https://', SSLContextAdapter())
    return session


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to be filesystem-safe
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    return filename.strip()


def calculate_file_hash(filepath: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of a file
    
    Args:
        filepath: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256)
        
    Returns:
        Hexadecimal hash string
    """
    hash_func = hashlib.new(algorithm)
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def format_epic_number(epic: str) -> str:
    """
    Format EPIC number with proper slashes (WB/12/345/678901)
    
    Args:
        epic: Raw EPIC number
        
    Returns:
        Formatted EPIC number
    """
    # Remove existing formatting
    epic = epic.upper().replace('/', '').replace(' ', '')
    
    # Check if it starts with WB or Wb
    if epic.startswith('WB'):
        epic = epic[2:]
    
    # Format: WB/XX/XXX/XXXXXX
    if len(epic) >= 11:
        # Extract components
        part1 = epic[:2]   # e.g., 12
        part2 = epic[2:5]  # e.g., 345
        part3 = epic[5:]   # e.g., 678901
        
        return f"WB/{part1}/{part2}/{part3}"
    
    return f"WB/{epic}"


def decode_cid_character(char: str, cid_map: Dict[str, str]) -> str:
    """
    Decode CID font characters
    
    Args:
        char: Character to decode
        cid_map: CID mapping dictionary
        
    Returns:
        Decoded character
    """
    if char.startswith('(cid:') and char.endswith(')'):
        return cid_map.get(char[1:-1], char)
    return char


def decode_shifted_character(char: str, char_map: Dict[str, str]) -> str:
    """
    Decode shifted characters (D->a, E->b, etc.)
    
    Args:
        char: Character to decode
        char_map: Character mapping dictionary
        
    Returns:
        Decoded character
    """
    return char_map.get(char, char)


def build_url(base_url: str, *parts: str, **params: Any) -> str:
    """
    Build URL with path parts and query parameters
    
    Args:
        base_url: Base URL
        *parts: URL path parts
        **params: Query parameters
        
    Returns:
        Complete URL
    """
    url = base_url
    for part in parts:
        url = urljoin(url + '/', part)
    
    if params:
        query_string = '&'.join(f"{k}={quote(str(v))}" for k, v in params.items())
        url = f"{url}?{query_string}"
    
    return url


def parse_ac_number(ac_str: str) -> Optional[int]:
    """
    Parse AC number from string (e.g., "AC_139" -> 139)
    
    Args:
        ac_str: AC string
        
    Returns:
        AC number or None
    """
    try:
        if ac_str.startswith('AC_'):
            return int(ac_str.split('_')[1])
        return int(ac_str)
    except (ValueError, IndexError):
        return None


def format_voter_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format and clean voter data
    
    Args:
        raw_data: Raw voter data dictionary
        
    Returns:
        Cleaned and formatted data
    """
    formatted = {}
    
    # Copy and clean fields
    for key, value in raw_data.items():
        if isinstance(value, str):
            value = value.strip()
        
        formatted[key] = value
    
    # Format EPIC if present
    if 'epic_no' in formatted and formatted['epic_no']:
        formatted['epic_no'] = format_epic_number(formatted['epic_no'])
    
    # Ensure age is integer
    if 'age' in formatted:
        try:
            formatted['age'] = int(formatted['age'])
        except (ValueError, TypeError):
            formatted['age'] = None
    
    return formatted


class ProgressTracker:
    """
    Simple progress tracker for batch operations
    """
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        
    def update(self, n: int = 1):
        """Update progress by n items"""
        self.current += n
        self._print_progress()
    
    def _print_progress(self):
        """Print progress bar"""
        if self.total == 0:
            percent = 100
        else:
            percent = (self.current / self.total) * 100
        
        bar_length = 50
        filled = int(bar_length * self.current / self.total) if self.total > 0 else bar_length
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f'\r{self.description}: |{bar}| {self.current}/{self.total} ({percent:.1f}%)', end='', flush=True)
        
        if self.current >= self.total:
            print()  # New line when complete
