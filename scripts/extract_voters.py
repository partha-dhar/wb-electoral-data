#!/usr/bin/env python3
"""
CLI Script for extracting voter data from PDFs
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractor import TextExtractor
from src.parser import VoterParser
from src.storage import DataStorage
from src.utils import load_config, setup_logging, ensure_directories, ProgressTracker


def extract_single_pdf(pdf_path: Path, config: dict) -> dict:
    """Extract voters from a single PDF"""
    logger = logging.getLogger(__name__)
    
    # Initialize components
    extractor = TextExtractor(config)
    parser = VoterParser(config)
    
    logger.info(f"Processing {pdf_path.name}")
    
    # Extract text
    lines = extractor.extract_text_from_pdf(pdf_path)
    
    # Parse voters
    voters = parser.parse_pdf_lines(lines)
    
    # Get metadata
    metadata = parser.parse_part_metadata(lines)
    
    return {
        'voters': voters,
        'metadata': metadata,
        'total_lines': len(lines)
    }


def extract_ac_directory(ac_dir: Path, config: dict) -> list:
    """Extract voters from all PDFs in AC directory"""
    logger = logging.getLogger(__name__)
    
    # Find all PDF files
    pdf_files = sorted(ac_dir.glob('*.pdf'))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {ac_dir}")
        return []
    
    logger.info(f"Found {len(pdf_files)} PDFs in {ac_dir.name}")
    
    # Initialize components
    storage = DataStorage(config)
    
    progress = ProgressTracker(len(pdf_files), f"Extracting {ac_dir.name}")
    
    results = []
    total_voters = 0
    
    for pdf_file in pdf_files:
        try:
            result = extract_single_pdf(pdf_file, config)
            voters = result['voters']
            metadata = result['metadata']
            
            # Save voters
            if voters:
                ac_number = metadata.get('ac_number', 0)
                part_number = metadata.get('part_number', 0)
                
                if ac_number and part_number:
                    output_path = storage.save_voters(voters, ac_number, part_number, metadata)
                    result['output_path'] = str(output_path)
                
                total_voters += len(voters)
            
            results.append({
                'pdf': pdf_file.name,
                'voters': len(voters),
                'success': True
            })
        
        except Exception as e:
            logger.error(f"Error processing {pdf_file.name}: {e}")
            results.append({
                'pdf': pdf_file.name,
                'voters': 0,
                'success': False,
                'error': str(e)
            })
        
        progress.update()
    
    logger.info(f"Extracted {total_voters} total voters from {ac_dir.name}")
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Extract voter data from electoral roll PDFs'
    )
    
    # Add arguments
    parser.add_argument('--pdf', type=str, help='Single PDF file to process')
    parser.add_argument('--ac', type=int, help='AC number to process')
    parser.add_argument('--dir', type=str, help='Directory containing PDFs')
    parser.add_argument('--batch', action='store_true', help='Process all PDFs in pdf_dir')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    parser.add_argument('--output', help='Output directory (overrides config)')
    parser.add_argument('--format', choices=['json', 'yaml'], help='Output format')
    parser.add_argument('--stats', action='store_true', help='Generate statistics')
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
        config['directories']['output_dir'] = args.output
    if args.format:
        config['storage']['format'] = args.format
    if args.verbose:
        config['logging']['level'] = 'DEBUG'
    
    # Setup
    ensure_directories(config)
    logger = setup_logging(config)
    
    try:
        # Process based on arguments
        if args.pdf:
            # Single PDF
            pdf_path = Path(args.pdf)
            if not pdf_path.exists():
                print(f"Error: PDF file not found: {pdf_path}")
                return 1
            
            result = extract_single_pdf(pdf_path, config)
            
            # Save output
            storage = DataStorage(config)
            metadata = result['metadata']
            output_path = storage.save_voters(
                result['voters'],
                metadata.get('ac_number', 0),
                metadata.get('part_number', 0),
                metadata
            )
            
            print(f"\nExtracted {len(result['voters'])} voters")
            print(f"Saved to: {output_path}")
        
        elif args.ac:
            # AC directory
            pdf_dir = Path(config['directories']['pdf_dir'])
            ac_dirs = list(pdf_dir.glob(f"AC_{args.ac:03d}_*"))
            
            if not ac_dirs:
                print(f"Error: AC {args.ac} directory not found in {pdf_dir}")
                return 1
            
            results = extract_ac_directory(ac_dirs[0], config)
            
            # Print summary
            successful = sum(1 for r in results if r['success'])
            total_voters = sum(r['voters'] for r in results)
            
            print("\n" + "="*60)
            print(f"AC {args.ac} EXTRACTION COMPLETE")
            print("="*60)
            print(f"PDFs processed: {successful}/{len(results)}")
            print(f"Total voters extracted: {total_voters}")
            print("="*60)
        
        elif args.dir:
            # Custom directory
            dir_path = Path(args.dir)
            if not dir_path.exists():
                print(f"Error: Directory not found: {dir_path}")
                return 1
            
            results = extract_ac_directory(dir_path, config)
        
        elif args.batch:
            # Batch process all
            pdf_dir = Path(config['directories']['pdf_dir'])
            ac_dirs = [d for d in pdf_dir.iterdir() if d.is_dir() and d.name.startswith('AC_')]
            
            if not ac_dirs:
                print(f"Error: No AC directories found in {pdf_dir}")
                return 1
            
            print(f"Found {len(ac_dirs)} AC directories")
            
            all_results = []
            for ac_dir in sorted(ac_dirs):
                print(f"\nProcessing {ac_dir.name}...")
                results = extract_ac_directory(ac_dir, config)
                all_results.extend(results)
            
            # Print overall summary
            successful = sum(1 for r in all_results if r['success'])
            total_voters = sum(r['voters'] for r in all_results)
            
            print("\n" + "="*60)
            print("BATCH EXTRACTION COMPLETE")
            print("="*60)
            print(f"ACs processed: {len(ac_dirs)}")
            print(f"PDFs processed: {successful}/{len(all_results)}")
            print(f"Total voters extracted: {total_voters}")
            print("="*60)
        
        else:
            parser.print_help()
            return 1
        
        # Generate statistics if requested
        if args.stats:
            from src.parser import VoterParser
            parser_obj = VoterParser(config)
            storage = DataStorage(config)
            
            # Load all voters and generate stats
            # TODO: Implement statistics generation
            print("\nStatistics generation not yet implemented")
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Extraction interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error during extraction: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
