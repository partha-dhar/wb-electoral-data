#!/usr/bin/env python3
"""
CLI Script for fetching metadata from ECI Gateway API
"""

import sys
import argparse
import logging
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import load_config, setup_logging, ensure_directories, get_session_with_ssl


def fetch_districts(session, config):
    """Fetch all districts"""
    api_config = config['eci_api']
    url = f"{api_config['base_url']}/getDistrict"
    
    params = {'state_cd': api_config['state_code']}
    
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    return data.get('payload', [])


def fetch_assemblies(session, config):
    """Fetch all assemblies"""
    api_config = config['eci_api']
    url = f"{api_config['base_url']}/getAsmbly"
    
    params = {'state_cd': api_config['state_code']}
    
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    return data.get('payload', [])


def fetch_parts(session, config, ac_number):
    """Fetch parts for an AC"""
    api_config = config['eci_api']
    url = f"{api_config['base_url']}/getPartByAc"
    
    params = {
        'state_cd': api_config['state_code'],
        'ac_no': ac_number
    }
    
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    return data.get('payload', [])


def main():
    parser = argparse.ArgumentParser(
        description='Fetch electoral metadata from ECI Gateway API'
    )
    
    # Add arguments
    parser.add_argument('--districts', action='store_true', help='Fetch all districts')
    parser.add_argument('--assemblies', action='store_true', help='Fetch all assemblies')
    parser.add_argument('--parts', type=int, help='Fetch parts for AC number')
    parser.add_argument('--all', action='store_true', help='Fetch all metadata')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    parser.add_argument('--output', help='Output directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    
    # Override config
    if args.output:
        config['directories']['output_dir'] = args.output
    if args.verbose:
        config['logging']['level'] = 'DEBUG'
    
    # Setup
    ensure_directories(config)
    logger = setup_logging(config)
    
    # Create session
    session = get_session_with_ssl()
    
    # Add headers
    api_config = config['eci_api']
    session.headers.update(api_config.get('headers', {}))
    
    output_dir = Path(config['directories']['output_dir'])
    
    try:
        if args.districts or args.all:
            logger.info("Fetching districts...")
            districts = fetch_districts(session, config)
            
            output_file = output_dir / 'districts.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(districts, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Fetched {len(districts)} districts")
            print(f"  Saved to: {output_file}")
        
        if args.assemblies or args.all:
            logger.info("Fetching assemblies...")
            assemblies = fetch_assemblies(session, config)
            
            output_file = output_dir / 'assemblies.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(assemblies, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Fetched {len(assemblies)} assemblies")
            print(f"  Saved to: {output_file}")
        
        if args.parts:
            logger.info(f"Fetching parts for AC {args.parts}...")
            parts = fetch_parts(session, config, args.parts)
            
            output_file = output_dir / f'AC_{args.parts:03d}_parts.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(parts, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Fetched {len(parts)} parts for AC {args.parts}")
            print(f"  Saved to: {output_file}")
        
        if not (args.districts or args.assemblies or args.parts or args.all):
            parser.print_help()
            return 1
        
        return 0
    
    except Exception as e:
        logger.error(f"Error fetching metadata: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
