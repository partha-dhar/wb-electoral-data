#!/usr/bin/env python3
"""
Universal Voter Data Extraction Script

Extracts voter data from Electoral Roll PDFs for ANY district/AC.
Handles both CID-encoded and plain text PDFs automatically.

Usage:
    python3 extract_voters_universal.py --district 13 --ac 146
    python3 extract_voters_universal.py --district 9 --ac 139
    python3 extract_voters_universal.py --district 13  # All ACs in district
    python3 extract_voters_universal.py --all          # All districts

Output:
    - Saves to: data/electoral_roll.db (SQLite)
    - Or: data/extracted_voters/DISTRICT_N/AC_N.csv (if --csv flag)
"""

import pdfplumber
import sqlite3
import re
import sys
import argparse
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

def decode_text(text):
    """
    Decode CID-encoded text from Electoral Roll PDFs.
    The PDF uses character shifting where:
    - Uppercase letters are shifted by -3
    - Some special characters map differently
    """
    if not text:
        return ""
    
    # Character mapping based on the encoding pattern
    char_map = {
        # Uppercase letters (shifted by -3)
        'D': 'a', 'E': 'b', 'F': 'c', 'G': 'd', 'H': 'e', 'I': 'f', 'J': 'g', 'K': 'h',
        'L': 'i', 'M': 'j', 'N': 'k', 'O': 'l', 'P': 'm', 'Q': 'n', 'R': 'o', 'S': 'p',
        'T': 'q', 'U': 'r', 'V': 's', 'W': 't', 'X': 'u', 'Y': 'v', 'Z': 'w',
        
        # Special characters
        '$': 'A', '%': 'B', '&': 'C', "'": 'D', '(': 'E', ')': 'F', '*': 'G', '+': 'H',
        ',': 'I', '-': 'J', '.': 'K', '/': 'L', '0': 'M', '1': 'N', '2': 'O', '3': 'P',
        '4': 'Q', '5': 'R', '6': 'S', '7': 'T', '8': 'U', '9': 'V', ':': 'W',
        
        # Numbers (in CID format) - keep as-is
        '\\': 'y',
    }
    
    decoded = []
    i = 0
    while i < len(text):
        # Handle (cid:XX) patterns - these are numbers and special chars
        if text[i:i+5].startswith('(cid:') or text[i:i+6].startswith('(cidW'):
            # Find the closing parenthesis
            end = text.find(')', i)
            if end != -1:
                cid_content = text[i+5:end] if text[i:i+5].startswith('(cid:') else text[i+6:end]
                if cid_content.isdigit():
                    # CID numbers map to digits and special chars
                    num = int(cid_content)
                    # Special characters first
                    if num == 18:  # (cid:18) is "/"
                        decoded.append('/')
                    elif num == 17:  # (cid:17) is "."
                        decoded.append('.')
                    elif 19 <= num <= 28:  # (cid:19) to (cid:28) map to 0-9
                        decoded.append(str(num - 19))
                    elif num == 15:  # (cidW15) is space
                        decoded.append(' ')
                    elif num == 16:  # (cidW16) is "/"
                        decoded.append('/')
                    elif num == 29:  # (cidW29) is ":"
                        decoded.append(':')
                    else:
                        decoded.append('')  # Skip unknown CID codes
                i = end + 1
                continue
        
        # Map regular characters
        char = text[i]
        if char in char_map:
            decoded.append(char_map[char])
        elif char.isalnum() or char in ' .,/-':
            decoded.append(char)
        else:
            decoded.append(char)
        
        i += 1
    
    result = ''.join(decoded)
    # Clean up multiple spaces but preserve single spaces
    result = ' '.join(result.split())
    return result

def parse_age_from_parts(parts, start_idx=0):
    """Extract age from line parts"""
    for i in range(start_idx, len(parts)):
        part = parts[i]
        
        # Age is often in format (cid:X)(cid:Y) where X and Y are the two digits
        cid_pattern = re.findall(r'\(cid[W]?:(\d+)\)', part)
        if len(cid_pattern) >= 2:
            digit1 = int(cid_pattern[0])
            digit2 = int(cid_pattern[1])
            # CID:19-28 map to 0-9
            if 19 <= digit1 <= 28:
                digit1 = digit1 - 19
            if 19 <= digit2 <= 28:
                digit2 = digit2 - 19
            age = digit1 * 10 + digit2
            if 18 <= age <= 120:
                return str(age)
        
        # Also try cleaning and parsing normally
        cleaned = re.sub(r'\(cid[W]?:\d+\)', '', part)
        if cleaned.isdigit():
            num = int(cleaned)
            if 18 <= num <= 120:
                return str(num)
    
    return ""

def parse_epic_from_parts(parts, start_idx=0):
    """Extract EPIC number from line parts"""
    for i in range(start_idx, len(parts)):
        part = parts[i]
        # Look for EPIC patterns
        if 'WB' in part or ':%(cid:18)' in part or 'WB(cid:18)' in part or 'WB(cidW' in part:
            epic_decoded = decode_text(part)
            epic_decoded = epic_decoded.strip()
            return epic_decoded
        elif '.1' in part or '.N' in part or 'DKN' in part:
            epic_decoded = decode_text(part)
            epic_decoded = epic_decoded.strip()
            return epic_decoded
    
    return ""

def extract_voter_data_from_pdf(pdf_path):
    """Extract voter information from Electoral Roll PDF (handles CID encoding)"""
    voters = []
    
    with pdfplumber.open(pdf_path) as pdf:
        # Extract metadata from filename
        filename = Path(pdf_path).stem  # e.g., AC146PART001
        ac_match = re.search(r'AC(\d+)', filename)
        part_match = re.search(r'PART(\d+)', filename)
        
        ac_number = ac_match.group(1) if ac_match else ""
        part_number = part_match.group(1) if part_match else ""
        
        # Get AC and PS names from folder structure
        path_parts = Path(pdf_path).parts
        ac_folder = next((p for p in path_parts if p.startswith('AC_')), "")
        ps_folder = next((p for p in path_parts if p.startswith('PS_')), "")
        
        # Extract AC name
        ac_name = ""
        if ac_folder:
            ac_parts = ac_folder.split('_')[2:]
            ac_name = ' '.join(ac_parts)
        
        # Extract PS number and name
        ps_number = ""
        ps_name = ""
        if ps_folder:
            ps_parts = ps_folder.split('_')
            ps_number = ps_parts[1] if len(ps_parts) > 1 else ""
            ps_name = ' '.join(ps_parts[2:]) if len(ps_parts) > 2 else ""
        
        # Process each page
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            current_section = ""
            
            for i, line in enumerate(lines):
                # Skip header lines
                if 'OHFWRU' in line or 'HODWLRQ' in line:
                    continue
                
                # Look for section headers
                if '6HFWLRQ' in line or 'Section' in line or 'section' in decode_text(line).lower():
                    current_section = decode_text(line)
                    continue
                
                # Look for voter lines with relationship markers
                if (')DWKHU' in line or '+XVEDQG' in line or '0RWKHU' in line or 
                    'Father' in line or 'Husband' in line or 'Mother' in line or
                    ')father' in decode_text(line).lower() or 'husband' in decode_text(line).lower()):
                    
                    parts = line.split()
                    
                    if len(parts) < 5:
                        continue
                    
                    # Serial number
                    sl_no = parts[0].replace('(cid:', '').replace('(cidW:', '').replace(')', '')
                    if '(' in sl_no:
                        sl_no = re.sub(r'\(cid[W]?:\d+\)', '', parts[0] + (parts[1] if len(parts) > 1 else ''))
                    
                    # House number  
                    house_no = parts[1] if len(parts) > 1 else ""
                    
                    # Find where the relationship starts
                    rel_start_idx = -1
                    for j, part in enumerate(parts[2:], start=2):
                        if any(marker in part for marker in [')DWKHU', '+XVEDQG', '0RWKHU', 'Father', 'Husband', 'Mother']):
                            rel_start_idx = j
                            break
                    
                    # Voter name is from index 2 to just before relationship
                    if rel_start_idx > 2:
                        voter_name_encoded = ' '.join(parts[2:rel_start_idx])
                    else:
                        voter_name_encoded = parts[2] if len(parts) > 2 else ""
                    voter_name = decode_text(voter_name_encoded)
                    
                    # Find relationship
                    relationship = ""
                    rel_idx = -1
                    for j, part in enumerate(parts):
                        decoded_part = decode_text(part).lower()
                        if ')DWKHU' in part or 'father' in decoded_part:
                            relationship = "Father"
                            rel_idx = j
                            break
                        elif '+XVEDQG' in part or 'husband' in decoded_part:
                            relationship = "Husband"
                            rel_idx = j
                            break
                        elif '0RWKHU' in part or 'mother' in decoded_part:
                            relationship = "Mother"
                            rel_idx = j
                            break
                        elif ':LIH' in part or 'wife' in decoded_part:
                            relationship = "Wife"
                            rel_idx = j
                            break
                    
                    # Relation name
                    relation_name_encoded = ""
                    relation_name = ""
                    if rel_idx != -1 and rel_idx + 1 < len(parts):
                        # Find where sex marker appears
                        sex_idx = -1
                        for j in range(rel_idx + 1, len(parts)):
                            if parts[j] in ['0', ')', 'M', 'F'] and j > rel_idx + 1:
                                sex_idx = j
                                break
                        
                        if sex_idx > rel_idx + 1:
                            relation_name_encoded = ' '.join(parts[rel_idx + 1:sex_idx])
                        else:
                            relation_name_encoded = parts[rel_idx + 1] if rel_idx + 1 < len(parts) else ""
                        relation_name = decode_text(relation_name_encoded)
                    
                    # Sex
                    sex = ""
                    for j, part in enumerate(parts):
                        if part == '0' and j > 0 and len(parts[j-1]) > 2:
                            sex = "M"
                            break
                        elif part == ')' and j > 0 and len(parts[j-1]) > 2:
                            sex = "F"
                            break
                        elif part == 'M':
                            sex = "M"
                            break
                        elif part == 'F':
                            sex = "F"
                            break
                    
                    # Age
                    age = parse_age_from_parts(parts, rel_idx + 2 if rel_idx != -1 else 3)
                    
                    # EPIC number
                    epic_no = parse_epic_from_parts(parts, rel_idx + 2 if rel_idx != -1 else 3)
                    
                    if voter_name and relationship:
                        voter = {
                            'ac_number': ac_number,
                            'ac_name': ac_name,
                            'part_number': part_number,
                            'ps_number': ps_number,
                            'ps_name': ps_name,
                            'section_info': current_section,
                            'sl_no': sl_no,
                            'house_no': house_no,
                            'voter_name': voter_name,
                            'voter_name_encoded': voter_name_encoded,
                            'relationship': relationship,
                            'relation_name': relation_name,
                            'relation_name_encoded': relation_name_encoded,
                            'sex': sex,
                            'age': age,
                            'epic_no': epic_no,
                            'pdf_filename': Path(pdf_path).name,
                            'page_number': page_num
                        }
                        voters.append(voter)
    
    return voters

def save_voters_to_db(voters, conn):
    """Save voter records to database"""
    cursor = conn.cursor()
    
    for voter in voters:
        cursor.execute('''
            INSERT INTO voters (
                ac_number, ac_name, part_number, ps_number, ps_name,
                section_info, sl_no, house_no, voter_name, voter_name_encoded,
                relationship, relation_name, relation_name_encoded, sex, age,
                epic_no, pdf_filename, page_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            voter['ac_number'], voter['ac_name'], voter['part_number'],
            voter['ps_number'], voter['ps_name'], voter['section_info'],
            voter['sl_no'], voter['house_no'], voter['voter_name'],
            voter['voter_name_encoded'], voter['relationship'],
            voter['relation_name'], voter['relation_name_encoded'],
            voter['sex'], voter['age'], voter['epic_no'],
            voter['pdf_filename'], voter['page_number']
        ))
    
    conn.commit()

def save_voters_to_csv(voters, csv_path):
    """Save voters to CSV file"""
    import csv
    
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        if voters:
            fieldnames = list(voters[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(voters)

def get_db_connection(db_path="data/electoral_roll.db"):
    """Get database connection"""
    return sqlite3.connect(db_path)

def find_district_dirs(district_num=None):
    """Find district directories"""
    base_dir = Path("data/downloaded_pdfs/ALL")
    
    if district_num:
        dirs = list(base_dir.glob(f"DISTRICT_{district_num}_*"))
        return dirs
    else:
        return sorted(base_dir.glob("DISTRICT_*"))

def find_ac_dirs(district_dir, ac_num=None):
    """Find AC directories in a district"""
    district_dir = Path(district_dir)
    
    if ac_num:
        # Check both zero-padded and non-padded formats
        dirs = list(district_dir.glob(f"AC_{ac_num}_*"))
        if not dirs:
            dirs = list(district_dir.glob(f"AC_{int(ac_num):03d}_*"))
        return dirs
    else:
        return sorted(district_dir.glob("AC_*"))

def process_ac(ac_dir, conn=None, output_csv=False):
    """Process a single AC directory"""
    ac_dir = Path(ac_dir)
    
    # Find all PDFs (check both flat and PS subdirectory structure)
    pdf_files = sorted(ac_dir.glob("*.pdf"))
    if not pdf_files:
        pdf_files = sorted(ac_dir.glob("PS_*/*.pdf"))
    
    if not pdf_files:
        print(f"No PDFs found in {ac_dir.name}")
        return 0, 0
    
    total_voters = 0
    errors = 0
    all_voters = []
    
    # Process each PDF with progress bar
    for pdf_path in tqdm(pdf_files, desc=f"Extracting {ac_dir.name}"):
        try:
            voters = extract_voter_data_from_pdf(pdf_path)
            if voters:
                if conn:
                    save_voters_to_db(voters, conn)
                if output_csv:
                    all_voters.extend(voters)
                total_voters += len(voters)
        except Exception as e:
            errors += 1
            print(f"\nError processing {pdf_path.name}: {e}")
    
    # Save CSV if requested
    if output_csv and all_voters:
        ac_num = all_voters[0]['ac_number']
        district_name = ac_dir.parent.name
        csv_path = Path(f"data/extracted_voters/{district_name}/AC_{ac_num}.csv")
        save_voters_to_csv(all_voters, csv_path)
        print(f"Saved CSV: {csv_path}")
    
    return total_voters, errors

def main():
    parser = argparse.ArgumentParser(
        description="Universal voter data extraction for West Bengal Electoral Rolls",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract single AC
  python3 extract_voters_universal.py --district 13 --ac 146
  
  # Extract all ACs in a district
  python3 extract_voters_universal.py --district 13
  
  # Extract all districts
  python3 extract_voters_universal.py --all
  
  # Save to CSV instead of database
  python3 extract_voters_universal.py --district 13 --ac 146 --csv
        """
    )
    
    parser.add_argument('--district', type=int, help='District number (e.g., 9, 13)')
    parser.add_argument('--ac', type=int, help='AC number (e.g., 139, 146)')
    parser.add_argument('--all', action='store_true', help='Process all districts')
    parser.add_argument('--csv', action='store_true', help='Save to CSV instead of database')
    parser.add_argument('--db', default='data/electoral_roll.db', help='Database path')
    
    args = parser.parse_args()
    
    if not (args.district or args.all):
        parser.print_help()
        sys.exit(1)
    
    # Setup database connection (unless CSV-only mode)
    conn = None if args.csv else get_db_connection(args.db)
    
    total_voters = 0
    total_errors = 0
    
    # Determine what to process
    if args.all:
        district_dirs = find_district_dirs()
        print(f"\nProcessing {len(district_dirs)} districts\n")
    elif args.district:
        district_dirs = find_district_dirs(args.district)
        if not district_dirs:
            print(f"Error: District {args.district} not found")
            sys.exit(1)
    
    # Process each district
    for district_dir in district_dirs:
        print(f"\n{'='*80}")
        print(f"Processing: {district_dir.name}")
        print(f"{'='*80}\n")
        
        # Find ACs in district
        if args.ac:
            ac_dirs = find_ac_dirs(district_dir, args.ac)
            if not ac_dirs:
                print(f"Warning: AC {args.ac} not found in {district_dir.name}")
                continue
        else:
            ac_dirs = find_ac_dirs(district_dir)
        
        # Process each AC
        for ac_dir in ac_dirs:
            voters, errors = process_ac(ac_dir, conn, args.csv)
            total_voters += voters
            total_errors += errors
    
    if conn:
        conn.close()
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*80}")
    print(f"Total voters extracted: {total_voters:,}")
    print(f"Total errors: {total_errors}")
    
    if not args.csv:
        # Show database summary
        conn = get_db_connection(args.db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total, ac_number, ac_name FROM voters GROUP BY ac_number, ac_name ORDER BY ac_number")
        results = cursor.fetchall()
        
        print(f"\nDatabase Summary ({args.db}):")
        print(f"{'='*80}")
        for count, ac, name in results:
            print(f"AC {ac} ({name}): {count:,} voters")
        print(f"{'='*80}\n")
        
        conn.close()

if __name__ == "__main__":
    main()
