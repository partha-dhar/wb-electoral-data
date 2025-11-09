#!/usr/bin/env python3
"""
CLI Script for validating extracted voter data against ECI API
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validator import DataValidator
from src.storage import DataStorage
from src.utils import load_config, setup_logging, ensure_directories


def main():
    parser = argparse.ArgumentParser(
        description='Validate extracted voter data against ECI Gateway API'
    )
    
    # Add arguments
    parser.add_argument('--ac', type=int, required=True, help='AC number')
    parser.add_argument('--part', type=int, help='Part number (optional, validates all parts if not specified)')
    parser.add_argument('--file', type=str, help='Specific data file to validate')
    parser.add_argument('--sample', type=int, help='Sample size for validation')
    parser.add_argument('--report', action='store_true', help='Generate validation report')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    
    # Override config
    if args.sample:
        config['validation']['sample_size'] = args.sample
    if args.verbose:
        config['logging']['level'] = 'DEBUG'
    
    # Setup
    ensure_directories(config)
    logger = setup_logging(config)
    
    # Initialize components
    validator = DataValidator(config)
    storage = DataStorage(config)
    
    try:
        # Load data file(s)
        output_dir = Path(config['directories']['output_dir'])
        
        if args.file:
            # Validate specific file
            data_file = Path(args.file)
            if not data_file.exists():
                print(f"Error: File not found: {data_file}")
                return 1
            
            data = storage.load_voters(data_file)
            voters = data['voters']
            metadata = data['metadata']
            
            ac_number = metadata['ac_number']
            part_number = metadata['part_number']
            
            logger.info(f"Validating AC {ac_number}, Part {part_number}")
            
            # Validate
            report = validator.validate_batch(voters, ac_number, part_number, args.sample)
            
            # Print results
            print("\n" + "="*60)
            print(f"VALIDATION REPORT - AC {ac_number}, Part {part_number}")
            print("="*60)
            print(f"Total voters: {report['total_voters']}")
            print(f"Validated: {report['validated']}")
            print(f"Valid: {report['valid']}")
            print(f"Invalid: {report['invalid']}")
            print(f"Errors: {report['errors']}")
            print(f"Validation rate: {report['validation_rate']:.1%}")
            print(f"Average match score: {report['avg_match_score']:.2f}")
            print("="*60)
            
            # Save report if requested
            if args.report:
                report_path = storage.save_validation_report(report, ac_number, part_number)
                print(f"\nReport saved to: {report_path}")
        
        elif args.part:
            # Validate specific part
            pattern = f"AC_{args.ac:03d}_Part_{args.part:03d}.json"
            data_files = list(output_dir.glob(pattern))
            
            if not data_files:
                print(f"Error: No data file found matching {pattern}")
                return 1
            
            data_file = data_files[0]
            data = storage.load_voters(data_file)
            voters = data['voters']
            
            logger.info(f"Validating AC {args.ac}, Part {args.part}")
            
            # Validate
            report = validator.validate_batch(voters, args.ac, args.part, args.sample)
            
            # Compare counts
            count_comparison = validator.compare_counts(len(voters), args.ac, args.part)
            
            # Print results
            print("\n" + "="*60)
            print(f"VALIDATION REPORT - AC {args.ac}, Part {args.part}")
            print("="*60)
            print(f"Local voters: {count_comparison['local_count']}")
            print(f"API voters: {count_comparison['api_count']}")
            print(f"Difference: {count_comparison['difference']}")
            print(f"Count match: {'✓' if count_comparison['match'] else '✗'}")
            print()
            print(f"Validated: {report['validated']} voters")
            print(f"Valid: {report['valid']}")
            print(f"Invalid: {report['invalid']}")
            print(f"Errors: {report['errors']}")
            print(f"Validation rate: {report['validation_rate']:.1%}")
            print(f"Average match score: {report['avg_match_score']:.2f}")
            print("="*60)
            
            # Save report if requested
            if args.report:
                report['count_comparison'] = count_comparison
                report_path = storage.save_validation_report(report, args.ac, args.part)
                print(f"\nReport saved to: {report_path}")
        
        else:
            # Validate all parts for AC
            pattern = f"AC_{args.ac:03d}_Part_*.json"
            data_files = sorted(output_dir.glob(pattern))
            
            if not data_files:
                print(f"Error: No data files found for AC {args.ac}")
                return 1
            
            print(f"Found {len(data_files)} part files for AC {args.ac}")
            
            all_reports = []
            
            for data_file in data_files:
                data = storage.load_voters(data_file)
                voters = data['voters']
                metadata = data['metadata']
                part_number = metadata['part_number']
                
                print(f"\nValidating Part {part_number}...", end=' ')
                
                report = validator.validate_batch(voters, args.ac, part_number, args.sample)
                all_reports.append(report)
                
                print(f"✓ ({report['valid']}/{report['validated']} valid)")
            
            # Aggregate results
            total_validated = sum(r['validated'] for r in all_reports)
            total_valid = sum(r['valid'] for r in all_reports)
            total_invalid = sum(r['invalid'] for r in all_reports)
            total_errors = sum(r['errors'] for r in all_reports)
            
            avg_validation_rate = sum(r['validation_rate'] for r in all_reports) / len(all_reports)
            avg_match_score = sum(r['avg_match_score'] for r in all_reports) / len(all_reports)
            
            # Print summary
            print("\n" + "="*60)
            print(f"VALIDATION SUMMARY - AC {args.ac}")
            print("="*60)
            print(f"Parts validated: {len(all_reports)}")
            print(f"Total voters validated: {total_validated}")
            print(f"Valid: {total_valid}")
            print(f"Invalid: {total_invalid}")
            print(f"Errors: {total_errors}")
            print(f"Average validation rate: {avg_validation_rate:.1%}")
            print(f"Average match score: {avg_match_score:.2f}")
            print("="*60)
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error during validation: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
