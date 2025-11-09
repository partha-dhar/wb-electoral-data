#!/usr/bin/env python3
"""
Verify extracted voter data against ECI API.

This script validates voters extracted from PDFs by cross-checking with the official
ECI API endpoint. It updates the database with verification status.

Since the API has incomplete data (empty names), we use it only for verification
purposes while keeping PDF extraction as the primary data source.
"""

import sys
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib3

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage import Database
from src.utils import setup_logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class LegacySSLAdapter(HTTPAdapter):
    """Custom SSL adapter to handle ECI's legacy SSL configuration."""
    
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.load_default_certs()
        ctx.check_hostname = False
        ctx.verify_mode = 0  # ssl.CERT_NONE
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        kwargs['ssl_context'] = ctx
        kwargs['assert_hostname'] = False
        return super().init_poolmanager(*args, **kwargs)


class APIVerifier:
    """Verifies voter data against ECI API."""
    
    API_URL = "https://gateway-s2-blo.eci.gov.in/api/v1/elastic-sir/get-eroll-data-2003"
    
    def __init__(self, db: Database, delay: float = 0.5):
        """
        Initialize the verifier.
        
        Args:
            db: Database instance
            delay: Delay between API calls (seconds) to respect rate limits
        """
        self.db = db
        self.delay = delay
        self.logger = logging.getLogger(__name__)
        
        # Create session with legacy SSL support
        self.session = requests.Session()
        self.session.mount('https://', LegacySSLAdapter())
        
        # Headers required by ECI API (NO Bearer token needed!)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "CurrentRole": "citizen",
            "PLATFORM-TYPE": "ECIWEB",
            "applicationName": "VSP",
            "channelidobo": "VSP"
        }
        
        self.stats = {
            'total': 0,
            'verified': 0,
            'not_found': 0,
            'mismatch': 0,
            'errors': 0
        }
    
    def verify_voter(
        self,
        state_code: str,
        ac_no: int,
        part_no: int,
        serial_no: int,
        epic_number: Optional[str] = None,
        age: Optional[int] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Verify a single voter against the API.
        
        Args:
            state_code: State code (e.g., "S25" for West Bengal)
            ac_no: Assembly constituency number
            part_no: Part number
            serial_no: Serial number within the part
            epic_number: Expected EPIC number (for validation)
            age: Expected age (for validation)
        
        Returns:
            Tuple of (verified: bool, api_data: Dict or None)
        """
        payload = {
            "oldStateCd": state_code,
            "oldAcNo": str(ac_no),
            "oldPartNo": str(part_no),
            "oldPartSerialNo": str(serial_no)
        }
        
        try:
            response = self.session.post(
                self.API_URL,
                headers=self.headers,
                json=payload,
                timeout=10,
                verify=False
            )
            
            if response.status_code != 200:
                self.logger.warning(
                    f"API returned {response.status_code} for "
                    f"AC{ac_no}/Part{part_no}/Serial{serial_no}"
                )
                return False, None
            
            data = response.json()
            
            if data.get('status') != 'Success':
                self.logger.warning(f"API status not success: {data.get('message')}")
                return False, None
            
            payload_data = data.get('payload', [])
            if not payload_data:
                self.logger.debug(f"No data found for Serial {serial_no}")
                return False, None
            
            voter_data = payload_data[0]
            
            # Verify EPIC number if provided
            if epic_number:
                api_epic = voter_data.get('epicNumber', '').strip()
                if api_epic and api_epic != epic_number:
                    self.logger.warning(
                        f"EPIC mismatch: Expected {epic_number}, got {api_epic}"
                    )
                    return False, voter_data
            
            # Verify age if provided (allow ±1 year difference)
            if age:
                api_age_str = voter_data.get('age', '').strip()
                if api_age_str:
                    try:
                        api_age = int(api_age_str)
                        if abs(api_age - age) > 1:
                            self.logger.warning(
                                f"Age mismatch: Expected {age}, got {api_age}"
                            )
                    except ValueError:
                        pass
            
            return True, voter_data
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout verifying Serial {serial_no}")
            return False, None
        except Exception as e:
            self.logger.error(f"Error verifying Serial {serial_no}: {e}")
            return False, None
    
    def verify_assembly_constituency(
        self,
        ac_no: int,
        state_code: str = "S25",
        batch_size: int = 100
    ) -> Dict:
        """
        Verify all voters from an assembly constituency.
        
        Args:
            ac_no: Assembly constituency number
            state_code: State code (default: S25 for West Bengal)
            batch_size: Number of voters to process before committing
        
        Returns:
            Statistics dictionary
        """
        self.logger.info(f"Starting verification for AC {ac_no}")
        
        # Get all voters for this AC
        voters = self.db.get_voters_by_ac(ac_no)
        
        if not voters:
            self.logger.warning(f"No voters found in database for AC {ac_no}")
            return self.stats
        
        self.logger.info(f"Found {len(voters)} voters to verify")
        self.stats['total'] = len(voters)
        
        batch_count = 0
        
        for idx, voter in enumerate(voters, 1):
            try:
                # Extract voter details
                voter_id = voter[0]
                epic_number = voter[1]
                part_no = voter[2]
                serial_no = voter[3]
                age = voter[4] if len(voter) > 4 else None
                
                # Verify with API
                verified, api_data = self.verify_voter(
                    state_code=state_code,
                    ac_no=ac_no,
                    part_no=part_no,
                    serial_no=serial_no,
                    epic_number=epic_number,
                    age=age
                )
                
                # Update database with verification status
                if verified:
                    self.db.mark_voter_verified(voter_id, True, api_data)
                    self.stats['verified'] += 1
                elif api_data is None:
                    self.db.mark_voter_verified(voter_id, False, None)
                    self.stats['not_found'] += 1
                else:
                    self.db.mark_voter_verified(voter_id, False, api_data)
                    self.stats['mismatch'] += 1
                
                batch_count += 1
                
                # Commit in batches
                if batch_count >= batch_size:
                    self.db.conn.commit()
                    batch_count = 0
                    self.logger.info(
                        f"Progress: {idx}/{len(voters)} "
                        f"({(idx/len(voters)*100):.1f}%) - "
                        f"Verified: {self.stats['verified']}, "
                        f"Not Found: {self.stats['not_found']}, "
                        f"Mismatch: {self.stats['mismatch']}"
                    )
                
                # Respect rate limits (50 req/sec, we'll do 2 req/sec to be safe)
                time.sleep(self.delay)
                
            except Exception as e:
                self.logger.error(f"Error processing voter {voter_id}: {e}")
                self.stats['errors'] += 1
        
        # Final commit
        self.db.conn.commit()
        
        self.logger.info("=" * 80)
        self.logger.info("VERIFICATION COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"Total voters:    {self.stats['total']}")
        self.logger.info(f"Verified:        {self.stats['verified']} "
                        f"({self.stats['verified']/self.stats['total']*100:.1f}%)")
        self.logger.info(f"Not found:       {self.stats['not_found']} "
                        f"({self.stats['not_found']/self.stats['total']*100:.1f}%)")
        self.logger.info(f"Mismatched:      {self.stats['mismatch']} "
                        f"({self.stats['mismatch']/self.stats['total']*100:.1f}%)")
        self.logger.info(f"Errors:          {self.stats['errors']}")
        
        return self.stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Verify extracted voter data against ECI API'
    )
    parser.add_argument(
        '--ac',
        type=int,
        required=True,
        help='Assembly constituency number to verify'
    )
    parser.add_argument(
        '--state-code',
        default='S25',
        help='State code (default: S25 for West Bengal)'
    )
    parser.add_argument(
        '--db-path',
        default='data/voters.db',
        help='Path to SQLite database'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between API calls in seconds (default: 0.5)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of voters to process before committing (default: 100)'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("West Bengal Electoral Data Verifier")
    logger.info("=" * 80)
    logger.info(f"Assembly Constituency: {args.ac}")
    logger.info(f"State Code: {args.state_code}")
    logger.info(f"Database: {args.db_path}")
    logger.info(f"API Delay: {args.delay}s")
    logger.info(f"Batch Size: {args.batch_size}")
    logger.info("=" * 80)
    
    # Initialize database
    db = Database(args.db_path)
    
    # Add verification columns if they don't exist
    try:
        db.cursor.execute("""
            ALTER TABLE voters 
            ADD COLUMN verified BOOLEAN DEFAULT NULL
        """)
        db.cursor.execute("""
            ALTER TABLE voters 
            ADD COLUMN verification_date TIMESTAMP DEFAULT NULL
        """)
        db.cursor.execute("""
            ALTER TABLE voters 
            ADD COLUMN api_data TEXT DEFAULT NULL
        """)
        db.conn.commit()
        logger.info("Added verification columns to database")
    except Exception:
        # Columns already exist
        pass
    
    # Initialize verifier
    verifier = APIVerifier(db, delay=args.delay)
    
    # Run verification
    try:
        stats = verifier.verify_assembly_constituency(
            ac_no=args.ac,
            state_code=args.state_code,
            batch_size=args.batch_size
        )
        
        # Print final summary
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"Assembly Constituency: AC {args.ac}")
        print(f"Total Voters: {stats['total']:,}")
        print(f"✓ Verified: {stats['verified']:,} ({stats['verified']/stats['total']*100:.2f}%)")
        print(f"✗ Not Found: {stats['not_found']:,} ({stats['not_found']/stats['total']*100:.2f}%)")
        print(f"⚠ Mismatched: {stats['mismatch']:,} ({stats['mismatch']/stats['total']*100:.2f}%)")
        print(f"⚠ Errors: {stats['errors']:,}")
        print("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("\nVerification interrupted by user")
        db.conn.commit()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
