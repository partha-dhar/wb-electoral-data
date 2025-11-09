"""
PDF Downloader Module
Downloads electoral roll PDFs from ceowestbengal.nic.in
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
import time
import base64

from .utils import (
    get_session_with_ssl,
    sanitize_filename,
    calculate_file_hash,
    ProgressTracker
)


class PDFDownloader:
    """
    Downloads electoral roll PDFs from CEO West Bengal website
    """
    
    def __init__(self, config: Dict):
        """
        Initialize PDF downloader
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = get_session_with_ssl()
        
        # Setup directories
        self.pdf_dir = Path(config['directories']['pdf_dir'])
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        
        # Download settings
        download_config = config.get('download', {})
        self.concurrent = download_config.get('concurrent_downloads', 5)
        self.retry_attempts = download_config.get('retry_attempts', 3)
        self.retry_delay = download_config.get('retry_delay', 1.0)
        self.chunk_size = download_config.get('chunk_size', 8192)
        
        # Setup headers
        self.session.headers.update({
            'User-Agent': download_config.get('user_agent', 'Mozilla/5.0')
        })
    
    def download_pdf(self, url: str, output_path: Path, resume: bool = True) -> bool:
        """
        Download a single PDF file
        
        Args:
            url: URL of the PDF
            output_path: Where to save the PDF
            resume: Enable resume capability
            
        Returns:
            True if successful, False otherwise
        """
        # Check if file already exists
        if output_path.exists() and output_path.stat().st_size > 0:
            self.logger.info(f"File already exists: {output_path.name}")
            return True
        
        # Create parent directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        for attempt in range(self.retry_attempts):
            try:
                # Request file
                response = self.session.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                # Check if it's actually a PDF
                content_type = response.headers.get('Content-Type', '')
                if 'pdf' not in content_type.lower():
                    self.logger.warning(f"URL does not return PDF: {url}")
                    return False
                
                # Download file
                total_size = int(response.headers.get('content-length', 0))
                
                with open(output_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                
                self.logger.info(f"Downloaded: {output_path.name} ({downloaded} bytes)")
                return True
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"Failed to download {url} after {self.retry_attempts} attempts")
                    return False
        
        return False
    
    def download_ac_pdfs(self, ac_number: int, ac_name: str, part_urls: List[str]) -> Dict[str, any]:
        """
        Download all PDFs for an Assembly Constituency
        
        Args:
            ac_number: AC number (e.g., 139)
            ac_name: AC name (e.g., "BELGACHIA EAST")
            part_urls: List of PDF URLs for each part
            
        Returns:
            Dictionary with download statistics
        """
        # Create AC directory
        ac_dir = self.pdf_dir / f"AC_{ac_number:03d}_{sanitize_filename(ac_name)}"
        ac_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Downloading {len(part_urls)} PDFs for AC {ac_number} - {ac_name}")
        
        results = {
            'total': len(part_urls),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'files': []
        }
        
        # Progress tracker
        progress = ProgressTracker(len(part_urls), f"AC {ac_number}")
        
        # Download with thread pool
        with ThreadPoolExecutor(max_workers=self.concurrent) as executor:
            futures = {}
            
            for idx, url in enumerate(part_urls, start=1):
                # Generate filename
                filename = f"part_{idx:03d}.pdf"
                output_path = ac_dir / filename
                
                # Submit download task
                future = executor.submit(self.download_pdf, url, output_path)
                futures[future] = (idx, url, output_path)
            
            # Collect results
            for future in as_completed(futures):
                idx, url, output_path = futures[future]
                
                try:
                    success = future.result()
                    if success:
                        results['successful'] += 1
                        results['files'].append(str(output_path))
                    else:
                        results['failed'] += 1
                except Exception as e:
                    self.logger.error(f"Error downloading part {idx}: {e}")
                    results['failed'] += 1
                
                progress.update()
        
        self.logger.info(
            f"Download complete for AC {ac_number}: "
            f"{results['successful']} successful, {results['failed']} failed"
        )
        
        return results
    
    def build_pdf_url(self, ac_number: int, part_number: int, 
                     base_params: Optional[Dict] = None) -> str:
        """
        Build PDF URL for a specific AC and part
        
        Args:
            ac_number: AC number
            part_number: Part number
            base_params: Base parameters for URL construction
            
        Returns:
            Complete PDF URL
        """
        # This method should be customized based on actual website structure
        # Example implementation:
        
        if base_params is None:
            base_params = {}
        
        # Encode parameters (similar to your working download script)
        params_str = f"ac={ac_number}&part={part_number}"
        for key, value in base_params.items():
            params_str += f"&{key}={value}"
        
        encoded_params = base64.b64encode(params_str.encode()).decode()
        
        base_url = self.config['source']['base_url']
        pdf_url = f"{base_url}/PDFServlet?{encoded_params}"
        
        return pdf_url
    
    def fetch_ac_list(self) -> List[Tuple[int, str]]:
        """
        Fetch list of Assembly Constituencies from website
        
        Returns:
            List of tuples (ac_number, ac_name)
        """
        # This should scrape the website to get AC list
        # Placeholder implementation
        
        self.logger.info("Fetching AC list from website...")
        
        try:
            # TODO: Implement actual scraping based on website structure
            # For now, return empty list
            return []
        except Exception as e:
            self.logger.error(f"Failed to fetch AC list: {e}")
            return []
    
    def download_district(self, district_number: int, 
                         ac_list: Optional[List[int]] = None) -> Dict[str, any]:
        """
        Download all PDFs for a district
        
        Args:
            district_number: District number
            ac_list: Optional list of AC numbers to download
            
        Returns:
            Dictionary with download statistics
        """
        self.logger.info(f"Downloading district {district_number}")
        
        # TODO: Implement district-level download
        # This requires fetching AC list for the district
        # and calling download_ac_pdfs for each
        
        results = {
            'district': district_number,
            'acs_processed': 0,
            'total_pdfs': 0,
            'successful': 0,
            'failed': 0
        }
        
        return results
    
    def download_all(self) -> Dict[str, any]:
        """
        Download all PDFs for West Bengal
        
        Returns:
            Dictionary with download statistics
        """
        self.logger.info("Starting download of all West Bengal electoral rolls")
        
        # Fetch list of all ACs
        ac_list = self.fetch_ac_list()
        
        if not ac_list:
            self.logger.warning("No ACs found to download")
            return {'error': 'No ACs found'}
        
        results = {
            'total_acs': len(ac_list),
            'completed_acs': 0,
            'total_pdfs': 0,
            'successful': 0,
            'failed': 0
        }
        
        # Process each AC
        for ac_number, ac_name in ac_list:
            # TODO: Get part URLs for this AC
            part_urls = []  # Fetch from website
            
            if part_urls:
                ac_results = self.download_ac_pdfs(ac_number, ac_name, part_urls)
                results['completed_acs'] += 1
                results['total_pdfs'] += ac_results['total']
                results['successful'] += ac_results['successful']
                results['failed'] += ac_results['failed']
        
        self.logger.info(
            f"Download complete: {results['successful']}/{results['total_pdfs']} PDFs downloaded"
        )
        
        return results
