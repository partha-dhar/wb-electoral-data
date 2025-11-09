#!/usr/bin/env python3
"""
CLI Script for downloading electoral roll PDFs
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.downloader import PDFDownloader
from src.utils import load_config, setup_logging, ensure_directories


def main():
    parser = argparse.ArgumentParser(
        description='Download electoral roll PDFs from CEO West Bengal'
    )
    
    # Add arguments
    parser.add_argument('--ac', type=int, help='Assembly Constituency number')
    parser.add_argument('--district', type=int, help='District number')
    parser.add_argument('--all', action='store_true', help='Download all West Bengal')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    parser.add_argument('--output', help='Output directory (overrides config)')
    parser.add_argument('--concurrent', type=int, help='Concurrent downloads')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    
    # Override config with CLI args
    if args.output:
        config['directories']['pdf_dir'] = args.output
    if args.concurrent:
        config['download']['concurrent_downloads'] = args.concurrent
    if args.verbose:
        config['logging']['level'] = 'DEBUG'
    
    # Setup
    ensure_directories(config)
    logger = setup_logging(config)
    
    # Initialize downloader
    downloader = PDFDownloader(config)
    
    try:
        # Perform download based on arguments
        if args.all:
            logger.info("Downloading all West Bengal electoral rolls")
            results = downloader.download_all()
        
        elif args.district:
            logger.info(f"Downloading district {args.district}")
            results = downloader.download_district(args.district)
        
        elif args.ac:
            logger.info(f"Downloading AC {args.ac}")
            # TODO: Implement AC-specific download
            # For now, show message
            print(f"AC download not yet implemented. Please specify district or use --all")
            print(f"\nTo download a specific AC, you need to provide:")
            print(f"  - AC name")
            print(f"  - List of part URLs")
            return 1
        
        else:
            parser.print_help()
            return 1
        
        # Print results
        print("\n" + "="*60)
        print("DOWNLOAD COMPLETE")
        print("="*60)
        if 'error' in results:
            print(f"Error: {results['error']}")
        else:
            print(f"Total PDFs: {results.get('total_pdfs', 0)}")
            print(f"Successful: {results.get('successful', 0)}")
            print(f"Failed: {results.get('failed', 0)}")
        print("="*60)
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Download interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error during download: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
