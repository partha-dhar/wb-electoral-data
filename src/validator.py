"""
Data Validator Module
Validates extracted voter data against ECI Gateway API
"""

import logging
import requests
from typing import Dict, List, Optional, Any
import time
from difflib import SequenceMatcher

from .utils import get_session_with_ssl


class DataValidator:
    """
    Validates voter data against official ECI Gateway API
    """
    
    def __init__(self, config: Dict):
        """
        Initialize data validator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = get_session_with_ssl()
        
        # API settings
        api_config = config.get('eci_api', {})
        self.base_url = api_config.get('base_url', '')
        self.state_code = api_config.get('state_code', 'S25')
        self.timeout = api_config.get('timeout', 30)
        self.retry_attempts = api_config.get('retry_attempts', 3)
        self.retry_delay = api_config.get('retry_delay', 2.0)
        
        # Setup headers
        headers = api_config.get('headers', {})
        self.session.headers.update(headers)
        
        # Validation settings
        validation_config = config.get('validation', {})
        self.match_threshold = validation_config.get('match_threshold', 0.95)
        self.compare_fields = validation_config.get('compare_fields', ['epic_no', 'name', 'age'])
    
    def validate_voter(self, voter: Dict[str, Any], 
                      ac_number: int, part_number: int) -> Dict[str, Any]:
        """
        Validate a single voter against API
        
        Args:
            voter: Voter dictionary
            ac_number: Assembly Constituency number
            part_number: Part number
            
        Returns:
            Validation result dictionary
        """
        result = {
            'valid': False,
            'match_score': 0.0,
            'api_data': None,
            'differences': [],
            'error': None
        }
        
        # Get EPIC number
        epic = voter.get('epic_no')
        if not epic:
            result['error'] = "No EPIC number to validate"
            return result
        
        try:
            # Fetch voter data from API
            api_data = self._fetch_voter_from_api(epic, ac_number, part_number)
            
            if not api_data:
                result['error'] = "Voter not found in API"
                return result
            
            result['api_data'] = api_data
            
            # Compare fields
            match_score = self._calculate_match_score(voter, api_data)
            result['match_score'] = match_score
            
            # Check if match exceeds threshold
            if match_score >= self.match_threshold:
                result['valid'] = True
            
            # Find differences
            result['differences'] = self._find_differences(voter, api_data)
            
        except Exception as e:
            self.logger.error(f"Error validating voter {epic}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _fetch_voter_from_api(self, epic: str, ac_number: int, 
                              part_number: int) -> Optional[Dict[str, Any]]:
        """
        Fetch voter data from ECI API
        
        Args:
            epic: EPIC number
            ac_number: AC number
            part_number: Part number
            
        Returns:
            Voter data from API or None
        """
        # Construct API endpoint
        # This is based on the ECI Gateway API structure
        endpoint = f"{self.base_url}/getVoterDetails"
        
        params = {
            'epic_no': epic,
            'state_code': self.state_code,
            'ac_no': ac_number,
            'part_no': part_number
        }
        
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.get(
                    endpoint,
                    params=params,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract voter data from response
                    if data.get('status') == 'success':
                        return data.get('payload', {})
                    else:
                        self.logger.warning(f"API returned error: {data.get('message')}")
                        return None
                
                elif response.status_code == 404:
                    return None
                
                else:
                    self.logger.warning(f"API returned status {response.status_code}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
            
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
        
        return None
    
    def _calculate_match_score(self, local_voter: Dict[str, Any], 
                               api_voter: Dict[str, Any]) -> float:
        """
        Calculate similarity score between local and API data
        
        Args:
            local_voter: Locally extracted voter data
            api_voter: API voter data
            
        Returns:
            Match score between 0.0 and 1.0
        """
        scores = []
        
        for field in self.compare_fields:
            local_value = str(local_voter.get(field, '')).strip().upper()
            api_value = str(api_voter.get(field, '')).strip().upper()
            
            if not local_value or not api_value:
                continue
            
            # Calculate similarity
            if field in ['age', 'epic_no']:
                # Exact match for numeric/ID fields
                score = 1.0 if local_value == api_value else 0.0
            else:
                # Fuzzy match for text fields (names, addresses)
                score = SequenceMatcher(None, local_value, api_value).ratio()
            
            scores.append(score)
        
        # Return average score
        return sum(scores) / len(scores) if scores else 0.0
    
    def _find_differences(self, local_voter: Dict[str, Any], 
                         api_voter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find differences between local and API data
        
        Args:
            local_voter: Locally extracted voter data
            api_voter: API voter data
            
        Returns:
            List of differences
        """
        differences = []
        
        for field in self.compare_fields:
            local_value = local_voter.get(field)
            api_value = api_voter.get(field)
            
            if local_value != api_value:
                differences.append({
                    'field': field,
                    'local': local_value,
                    'api': api_value
                })
        
        return differences
    
    def validate_batch(self, voters: List[Dict[str, Any]], 
                      ac_number: int, part_number: int,
                      sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate a batch of voters
        
        Args:
            voters: List of voter dictionaries
            ac_number: AC number
            part_number: Part number
            sample_size: Number of voters to validate (None = all)
            
        Returns:
            Validation report
        """
        # Use sample size from config if not specified
        if sample_size is None:
            sample_size = self.config.get('validation', {}).get('sample_size', 100)
        
        # Sample voters if list is too large
        voters_to_validate = voters[:sample_size] if len(voters) > sample_size else voters
        
        self.logger.info(
            f"Validating {len(voters_to_validate)} voters "
            f"(AC {ac_number}, Part {part_number})"
        )
        
        report = {
            'total_voters': len(voters),
            'validated': 0,
            'valid': 0,
            'invalid': 0,
            'errors': 0,
            'avg_match_score': 0.0,
            'results': []
        }
        
        match_scores = []
        
        for voter in voters_to_validate:
            result = self.validate_voter(voter, ac_number, part_number)
            
            report['validated'] += 1
            
            if result['error']:
                report['errors'] += 1
            elif result['valid']:
                report['valid'] += 1
                match_scores.append(result['match_score'])
            else:
                report['invalid'] += 1
            
            report['results'].append({
                'voter': voter,
                'result': result
            })
            
            # Add delay to avoid rate limiting
            time.sleep(0.1)
        
        # Calculate average match score
        if match_scores:
            report['avg_match_score'] = sum(match_scores) / len(match_scores)
        
        # Calculate validation rate
        report['validation_rate'] = (report['valid'] / report['validated']) if report['validated'] > 0 else 0
        
        self.logger.info(
            f"Validation complete: {report['valid']}/{report['validated']} valid "
            f"({report['validation_rate']:.1%})"
        )
        
        return report
    
    def fetch_part_data(self, ac_number: int, part_number: int) -> Optional[Dict[str, Any]]:
        """
        Fetch complete part data from API
        
        Args:
            ac_number: AC number
            part_number: Part number
            
        Returns:
            Part data from API or None
        """
        endpoint = f"{self.base_url}/getPartByAc"
        
        params = {
            'state_cd': self.state_code,
            'ac_no': ac_number,
            'part_no': part_number
        }
        
        try:
            response = self.session.get(endpoint, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('payload', {})
            else:
                self.logger.error(f"Failed to fetch part data: {response.status_code}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error fetching part data: {e}")
            return None
    
    def compare_counts(self, local_count: int, ac_number: int, 
                      part_number: int) -> Dict[str, Any]:
        """
        Compare voter counts between local and API
        
        Args:
            local_count: Number of voters extracted locally
            ac_number: AC number
            part_number: Part number
            
        Returns:
            Comparison result
        """
        result = {
            'local_count': local_count,
            'api_count': None,
            'match': False,
            'difference': None
        }
        
        # Fetch part data from API
        part_data = self.fetch_part_data(ac_number, part_number)
        
        if part_data:
            api_count = part_data.get('total_voters', 0)
            result['api_count'] = api_count
            result['difference'] = local_count - api_count
            result['match'] = (local_count == api_count)
        
        return result
