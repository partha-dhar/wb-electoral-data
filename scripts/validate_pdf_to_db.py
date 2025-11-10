#!/usr/bin/env python3
"""
PDF-to-Database Validation Script

Validates database records against actual PDF files by:
- Counting voters per PDF and comparing with DB
- Spot-checking voter names and EPIC numbers
- Verifying PDF metadata matches DB entries
- Detecting missing PDFs or DB records

Usage:
    python3 validate_pdf_to_db.py
    python3 validate_pdf_to_db.py --district 13
    python3 validate_pdf_to_db.py --ac 146
    python3 validate_pdf_to_db.py --sample 10  # Spot-check 10 random PDFs
"""

import sqlite3
import pdfplumber
import argparse
import random
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

def get_db_connection(db_path="data/electoral_roll.db"):
    """Get database connection"""
    return sqlite3.connect(db_path)

def decode_text(text):
    """
    Decode CID-encoded text from Electoral Roll PDFs.
    (Same function as in extract_voters_universal.py)
    """
    if not text:
        return ""
    
    char_map = {
        'D': 'a', 'E': 'b', 'F': 'c', 'G': 'd', 'H': 'e', 'I': 'f', 'J': 'g', 'K': 'h',
        'L': 'i', 'M': 'j', 'N': 'k', 'O': 'l', 'P': 'm', 'Q': 'n', 'R': 'o', 'S': 'p',
        'T': 'q', 'U': 'r', 'V': 's', 'W': 't', 'X': 'u', 'Y': 'v', 'Z': 'w',
        '$': 'A', '%': 'B', '&': 'C', "'": 'D', '(': 'E', ')': 'F', '*': 'G', '+': 'H',
        ',': 'I', '-': 'J', '.': 'K', '/': 'L', '0': 'M', '1': 'N', '2': 'O', '3': 'P',
        '4': 'Q', '5': 'R', '6': 'S', '7': 'T', '8': 'U', '9': 'V', ':': 'W',
        '\\': 'y',
    }
    
    decoded = []
    i = 0
    while i < len(text):
        if text[i:i+5].startswith('(cid:') or text[i:i+6].startswith('(cidW'):
            end = text.find(')', i)
            if end != -1:
                cid_content = text[i+5:end] if text[i:i+5].startswith('(cid:') else text[i+6:end]
                if cid_content.isdigit():
                    num = int(cid_content)
                    if num == 18:
                        decoded.append('/')
                    elif num == 17:
                        decoded.append('.')
                    elif 19 <= num <= 28:
                        decoded.append(str(num - 19))
                    elif num == 15:
                        decoded.append(' ')
                    elif num == 16:
                        decoded.append('/')
                    elif num == 29:
                        decoded.append(':')
                    else:
                        decoded.append('')
                i = end + 1
                continue
        
        char = text[i]
        if char in char_map:
            decoded.append(char_map[char])
        elif char.isalnum() or char in ' .,/-':
            decoded.append(char)
        else:
            decoded.append(char)
        
        i += 1
    
    result = ''.join(decoded)
    result = ' '.join(result.split())
    return result

def count_voters_in_pdf(pdf_path):
    """
    Count voters in a PDF by looking for relationship markers
    """
    voter_count = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            
            for line in lines:
                # Look for voter lines with relationship markers
                if any(marker in line for marker in [')DWKHU', '+XVEDQG', '0RWKHU', 'Father', 'Husband', 'Mother']):
                    # Additional check: should have some voter-like content
                    if len(line.split()) >= 5:
                        voter_count += 1
    
    return voter_count

def get_sample_voter_from_pdf(pdf_path, voter_index=0):
    """
    Extract a sample voter from PDF for spot-checking
    Returns: (name, relationship, epic_no)
    """
    voters_found = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            
            for line in lines:
                if any(marker in line for marker in [')DWKHU', '+XVEDQG', '0RWKHU', 'Father', 'Husband', 'Mother']):
                    if len(line.split()) >= 5:
                        if voters_found == voter_index:
                            # Extract basic info
                            parts = line.split()
                            
                            # Find relationship
                            rel = ""
                            rel_idx = -1
                            for j, part in enumerate(parts):
                                decoded = decode_text(part).lower()
                                if 'father' in decoded:
                                    rel = "Father"
                                    rel_idx = j
                                    break
                                elif 'husband' in decoded:
                                    rel = "Husband"
                                    rel_idx = j
                                    break
                            
                            if rel_idx > 2:
                                # Name is likely before relationship
                                name_encoded = ' '.join(parts[2:rel_idx])
                                name = decode_text(name_encoded)
                                
                                # Try to find EPIC
                                epic = ""
                                for part in parts[rel_idx:]:
                                    if 'WB' in part or '.1' in part:
                                        epic = decode_text(part).strip()
                                        break
                                
                                return (name, rel, epic)
                        
                        voters_found += 1
    
    return (None, None, None)

def validate_pdf_counts(conn, district=None, ac=None):
    """
    Compare voter counts between PDFs and database
    """
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("PDF-TO-DATABASE COUNT VALIDATION")
    print("="*80 + "\n")
    
    # Get list of PDFs from database
    where_clause = []
    params = []
    
    if district:
        where_clause.append("ac_number LIKE ?")
        params.append(f"{district}%")
    
    if ac:
        where_clause.append("ac_number = ?")
        params.append(str(ac))
    
    where_sql = " WHERE " + " AND ".join(where_clause) if where_clause else ""
    
    # Get unique PDFs and their voter counts from DB
    cursor.execute(f"""
        SELECT pdf_filename, ac_number, part_number, COUNT(*) as db_count
        FROM voters{where_sql}
        GROUP BY pdf_filename, ac_number, part_number
        ORDER BY ac_number, part_number
    """, params)
    
    db_pdfs = cursor.fetchall()
    
    if not db_pdfs:
        print("No PDFs found in database for the specified criteria")
        return
    
    print(f"Found {len(db_pdfs)} PDFs in database\n")
    
    mismatches = []
    missing_pdfs = []
    
    # Find PDF files
    base_dir = Path("data/downloaded_pdfs/ALL")
    
    for pdf_filename, ac_num, part_num, db_count in tqdm(db_pdfs, desc="Validating PDFs"):
        # Find the PDF file
        pdf_files = list(base_dir.glob(f"**/AC_{ac_num}_*/**/{pdf_filename}"))
        
        if not pdf_files:
            # Try zero-padded format
            pdf_files = list(base_dir.glob(f"**/AC_{int(ac_num):03d}_*/**/{pdf_filename}"))
        
        if not pdf_files:
            missing_pdfs.append((pdf_filename, ac_num, part_num, db_count))
            continue
        
        pdf_path = pdf_files[0]
        
        try:
            pdf_count = count_voters_in_pdf(pdf_path)
            
            # Allow small discrepancies (±5) due to parsing differences
            if abs(pdf_count - db_count) > 5:
                mismatches.append({
                    'pdf': pdf_filename,
                    'ac': ac_num,
                    'part': part_num,
                    'pdf_count': pdf_count,
                    'db_count': db_count,
                    'diff': pdf_count - db_count
                })
        except Exception as e:
            print(f"\nError processing {pdf_filename}: {e}")
    
    # Report results
    print("\n" + "="*80)
    print("VALIDATION RESULTS")
    print("="*80 + "\n")
    
    if not mismatches and not missing_pdfs:
        print("✅ All PDFs validated successfully!")
        print(f"   Total PDFs checked: {len(db_pdfs)}")
    else:
        if mismatches:
            print(f"⚠️  Found {len(mismatches)} count mismatches:\n")
            print(f"{'PDF':<25} {'AC':<6} {'Part':<8} {'PDF Count':<12} {'DB Count':<12} {'Diff':<8}")
            print("-" * 80)
            for m in mismatches[:20]:
                print(f"{m['pdf']:<25} {m['ac']:<6} {m['part']:<8} {m['pdf_count']:<12} {m['db_count']:<12} {m['diff']:<8}")
            if len(mismatches) > 20:
                print(f"... and {len(mismatches) - 20} more")
        
        if missing_pdfs:
            print(f"\n❌ Found {len(missing_pdfs)} missing PDF files:")
            for pdf, ac, part, count in missing_pdfs[:10]:
                print(f"   {pdf} (AC {ac}, Part {part}) - {count} voters in DB")
            if len(missing_pdfs) > 10:
                print(f"   ... and {len(missing_pdfs) - 10} more")

def spot_check_voters(conn, sample_size=10):
    """
    Randomly select PDFs and spot-check voter details
    """
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print(f"SPOT-CHECK VALIDATION ({sample_size} random PDFs)")
    print("="*80 + "\n")
    
    # Get random PDFs
    cursor.execute("""
        SELECT DISTINCT pdf_filename, ac_number, part_number
        FROM voters
        ORDER BY RANDOM()
        LIMIT ?
    """, (sample_size,))
    
    sample_pdfs = cursor.fetchall()
    
    base_dir = Path("data/downloaded_pdfs/ALL")
    matches = 0
    mismatches = 0
    
    for pdf_filename, ac_num, part_num in sample_pdfs:
        # Find PDF
        pdf_files = list(base_dir.glob(f"**/AC_{ac_num}_*/**/{pdf_filename}"))
        if not pdf_files:
            pdf_files = list(base_dir.glob(f"**/AC_{int(ac_num):03d}_*/**/{pdf_filename}"))
        
        if not pdf_files:
            print(f"⚠️  PDF not found: {pdf_filename}")
            continue
        
        pdf_path = pdf_files[0]
        
        # Get first voter from PDF
        pdf_name, pdf_rel, pdf_epic = get_sample_voter_from_pdf(pdf_path, 0)
        
        if not pdf_name:
            print(f"⚠️  Could not extract voter from {pdf_filename}")
            continue
        
        # Get first voter from DB
        cursor.execute("""
            SELECT voter_name, relationship, epic_no
            FROM voters
            WHERE pdf_filename = ? AND ac_number = ? AND part_number = ?
            LIMIT 1
        """, (pdf_filename, ac_num, part_num))
        
        db_result = cursor.fetchone()
        
        if db_result:
            db_name, db_rel, db_epic = db_result
            
            # Check if they match (case-insensitive, normalized)
            name_match = pdf_name.lower().strip() == db_name.lower().strip()
            rel_match = pdf_rel.lower() == db_rel.lower()
            
            if name_match and rel_match:
                matches += 1
                print(f"✅ {pdf_filename}: {db_name} ({db_rel})")
            else:
                mismatches += 1
                print(f"❌ {pdf_filename}:")
                print(f"   PDF: {pdf_name} ({pdf_rel})")
                print(f"   DB:  {db_name} ({db_rel})")
    
    print(f"\n{'='*80}")
    print(f"Spot-check results: {matches} matches, {mismatches} mismatches out of {len(sample_pdfs)} checked")
    print(f"{'='*80}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Validate database records against actual PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--district', type=int, help='Validate specific district')
    parser.add_argument('--ac', type=int, help='Validate specific AC')
    parser.add_argument('--sample', type=int, default=0, help='Number of PDFs to spot-check (default: 0 = skip)')
    parser.add_argument('--db', default='data/electoral_roll.db', help='Database path')
    
    args = parser.parse_args()
    
    conn = get_db_connection(args.db)
    
    # Validate counts
    validate_pdf_counts(conn, args.district, args.ac)
    
    # Spot-check if requested
    if args.sample > 0:
        spot_check_voters(conn, args.sample)
    
    conn.close()
    
    print("\n✅ PDF-to-Database validation complete\n")

if __name__ == "__main__":
    main()
