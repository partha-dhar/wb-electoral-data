#!/usr/bin/env python3
"""
Universal Database Validation Script

Validates voter data in the database for:
- Data completeness
- Duplicate detection
- Data quality checks
- Statistics generation

Usage:
    python3 validate_database.py
    python3 validate_database.py --district 13
    python3 validate_database.py --ac 146
    python3 validate_database.py --dedupe  # Remove exact duplicates
"""

import sqlite3
import argparse
from pathlib import Path
from collections import Counter

def get_db_connection(db_path="data/electoral_roll.db"):
    """Get database connection"""
    return sqlite3.connect(db_path)

def validate_completeness(conn, district=None, ac=None):
    """Check data completeness"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("DATA COMPLETENESS VALIDATION")
    print("="*80 + "\n")
    
    # Overall statistics
    where_clause = []
    params = []
    
    if district:
        # Find ACs in this district from the data
        cursor.execute("SELECT DISTINCT ac_number FROM voters WHERE ac_number LIKE ?", (f"{district}%",))
        acs_in_district = [row[0] for row in cursor.fetchall()]
        if acs_in_district:
            where_clause.append(f"ac_number IN ({','.join('?' * len(acs_in_district))})")
            params.extend(acs_in_district)
    
    if ac:
        where_clause.append("ac_number = ?")
        params.append(str(ac))
    
    where_sql = " WHERE " + " AND ".join(where_clause) if where_clause else ""
    
    # Total voters
    cursor.execute(f"SELECT COUNT(*) FROM voters{where_sql}", params)
    total_voters = cursor.fetchone()[0]
    print(f"Total Voters: {total_voters:,}")
    
    # Voters with EPIC
    cursor.execute(f"SELECT COUNT(*) FROM voters{where_sql} AND epic_no != '' AND epic_no IS NOT NULL", params)
    with_epic = cursor.fetchone()[0]
    epic_pct = (with_epic / total_voters * 100) if total_voters > 0 else 0
    print(f"With EPIC Number: {with_epic:,} ({epic_pct:.1f}%)")
    
    # Voters with age
    cursor.execute(f"SELECT COUNT(*) FROM voters{where_sql} AND age != '' AND age IS NOT NULL", params)
    with_age = cursor.fetchone()[0]
    age_pct = (with_age / total_voters * 100) if total_voters > 0 else 0
    print(f"With Age: {with_age:,} ({age_pct:.1f}%)")
    
    # Voters with names
    cursor.execute(f"SELECT COUNT(*) FROM voters{where_sql} AND voter_name != '' AND voter_name IS NOT NULL", params)
    with_name = cursor.fetchone()[0]
    name_pct = (with_name / total_voters * 100) if total_voters > 0 else 0
    print(f"With Voter Name: {with_name:,} ({name_pct:.1f}%)")
    
    # Gender distribution
    cursor.execute(f"SELECT sex, COUNT(*) FROM voters{where_sql} GROUP BY sex", params)
    gender_dist = cursor.fetchall()
    print(f"\nGender Distribution:")
    for sex, count in gender_dist:
        sex_label = sex if sex else "Unknown"
        pct = (count / total_voters * 100) if total_voters > 0 else 0
        print(f"  {sex_label}: {count:,} ({pct:.1f}%)")
    
    # AC-wise summary
    print(f"\nAC-wise Summary:")
    cursor.execute(f"""
        SELECT ac_number, ac_name, COUNT(*) as voter_count
        FROM voters{where_sql}
        GROUP BY ac_number, ac_name
        ORDER BY ac_number
    """, params)
    
    ac_results = cursor.fetchall()
    print(f"{'AC Number':<15} {'AC Name':<40} {'Voters':<15}")
    print("-" * 70)
    for ac_num, ac_name, count in ac_results:
        print(f"{ac_num:<15} {ac_name:<40} {count:<15,}")

def detect_duplicates(conn, district=None, ac=None):
    """Detect duplicate voter records"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("DUPLICATE DETECTION")
    print("="*80 + "\n")
    
    where_clause = []
    params = []
    
    if district:
        cursor.execute("SELECT DISTINCT ac_number FROM voters WHERE ac_number LIKE ?", (f"{district}%",))
        acs_in_district = [row[0] for row in cursor.fetchall()]
        if acs_in_district:
            where_clause.append(f"ac_number IN ({','.join('?' * len(acs_in_district))})")
            params.extend(acs_in_district)
    
    if ac:
        where_clause.append("ac_number = ?")
        params.append(str(ac))
    
    where_sql = " WHERE " + " AND ".join(where_clause) if where_clause else ""
    
    # Exact duplicates (same name, AC, part, sl_no)
    cursor.execute(f"""
        SELECT ac_number, ac_name, part_number, voter_name, COUNT(*) as dup_count
        FROM voters{where_sql}
        GROUP BY ac_number, part_number, sl_no, voter_name
        HAVING COUNT(*) > 1
        ORDER BY dup_count DESC
        LIMIT 20
    """, params)
    
    exact_dupes = cursor.fetchall()
    
    if exact_dupes:
        print(f"⚠️  Found {len(exact_dupes)} groups of exact duplicates:")
        print(f"\n{'AC':<10} {'Part':<10} {'Name':<40} {'Count':<10}")
        print("-" * 70)
        for ac, ac_name, part, name, count in exact_dupes[:10]:
            print(f"{ac:<10} {part:<10} {name:<40} {count:<10}")
        if len(exact_dupes) > 10:
            print(f"... and {len(exact_dupes) - 10} more")
    else:
        print("✅ No exact duplicates found")
    
    # Potential duplicates (same name, EPIC)
    cursor.execute(f"""
        SELECT voter_name, epic_no, COUNT(*) as dup_count
        FROM voters{where_sql}
        WHERE epic_no != '' AND epic_no IS NOT NULL
        GROUP BY epic_no
        HAVING COUNT(*) > 1
        ORDER BY dup_count DESC
        LIMIT 20
    """, params)
    
    epic_dupes = cursor.fetchall()
    
    if epic_dupes:
        print(f"\n⚠️  Found {len(epic_dupes)} duplicate EPIC numbers:")
        print(f"\n{'Name':<40} {'EPIC':<20} {'Count':<10}")
        print("-" * 70)
        for name, epic, count in epic_dupes[:10]:
            print(f"{name:<40} {epic:<20} {count:<10}")
        if len(epic_dupes) > 10:
            print(f"... and {len(epic_dupes) - 10} more")
    else:
        print("\n✅ No duplicate EPIC numbers found")

def remove_exact_duplicates(conn):
    """Remove exact duplicate records (keep one copy)"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("REMOVING EXACT DUPLICATES")
    print("="*80 + "\n")
    
    # Find duplicates
    cursor.execute("""
        SELECT MIN(rowid) as keep_id, ac_number, part_number, sl_no, voter_name, COUNT(*) as dup_count
        FROM voters
        GROUP BY ac_number, part_number, sl_no, voter_name
        HAVING COUNT(*) > 1
    """)
    
    duplicates = cursor.fetchall()
    
    if not duplicates:
        print("✅ No duplicates to remove")
        return
    
    print(f"Found {len(duplicates)} groups of duplicates")
    
    removed = 0
    for keep_id, ac, part, sl_no, name, dup_count in duplicates:
        # Delete all except the one we want to keep
        cursor.execute("""
            DELETE FROM voters
            WHERE ac_number = ? AND part_number = ? AND sl_no = ? AND voter_name = ?
            AND rowid != ?
        """, (ac, part, sl_no, name, keep_id))
        
        removed += cursor.rowcount
    
    conn.commit()
    
    print(f"✅ Removed {removed} duplicate records")
    print(f"✅ Kept {len(duplicates)} unique records")

def data_quality_checks(conn, district=None, ac=None):
    """Perform data quality checks"""
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("DATA QUALITY CHECKS")
    print("="*80 + "\n")
    
    where_clause = []
    params = []
    
    if district:
        cursor.execute("SELECT DISTINCT ac_number FROM voters WHERE ac_number LIKE ?", (f"{district}%",))
        acs_in_district = [row[0] for row in cursor.fetchall()]
        if acs_in_district:
            where_clause.append(f"ac_number IN ({','.join('?' * len(acs_in_district))})")
            params.extend(acs_in_district)
    
    if ac:
        where_clause.append("ac_number = ?")
        params.append(str(ac))
    
    where_sql = " WHERE " + " AND ".join(where_clause) if where_clause else ""
    
    issues = []
    
    # Check for missing names
    cursor.execute(f"SELECT COUNT(*) FROM voters{where_sql} AND (voter_name = '' OR voter_name IS NULL)", params)
    missing_names = cursor.fetchone()[0]
    if missing_names > 0:
        issues.append(f"⚠️  {missing_names:,} voters with missing names")
    
    # Check for invalid ages
    cursor.execute(f"""
        SELECT COUNT(*) FROM voters{where_sql}
        AND age != '' AND age IS NOT NULL
        AND (CAST(age AS INTEGER) < 18 OR CAST(age AS INTEGER) > 120)
    """, params)
    invalid_ages = cursor.fetchone()[0]
    if invalid_ages > 0:
        issues.append(f"⚠️  {invalid_ages:,} voters with invalid ages (< 18 or > 120)")
    
    # Check for malformed EPIC numbers
    cursor.execute(f"""
        SELECT COUNT(*) FROM voters{where_sql}
        AND epic_no != '' AND epic_no IS NOT NULL
        AND LENGTH(epic_no) < 10
    """, params)
    malformed_epic = cursor.fetchone()[0]
    if malformed_epic > 0:
        issues.append(f"⚠️  {malformed_epic:,} voters with malformed EPIC numbers (< 10 chars)")
    
    if issues:
        print("Data Quality Issues:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ No data quality issues detected")
    
    # Age distribution
    print(f"\nAge Distribution:")
    cursor.execute(f"""
        SELECT 
            CASE 
                WHEN CAST(age AS INTEGER) BETWEEN 18 AND 25 THEN '18-25'
                WHEN CAST(age AS INTEGER) BETWEEN 26 AND 35 THEN '26-35'
                WHEN CAST(age AS INTEGER) BETWEEN 36 AND 45 THEN '36-45'
                WHEN CAST(age AS INTEGER) BETWEEN 46 AND 60 THEN '46-60'
                WHEN CAST(age AS INTEGER) > 60 THEN '60+'
                ELSE 'Unknown'
            END as age_group,
            COUNT(*) as count
        FROM voters{where_sql}
        GROUP BY age_group
        ORDER BY age_group
    """, params)
    
    age_dist = cursor.fetchall()
    for age_group, count in age_dist:
        print(f"  {age_group}: {count:,}")

def generate_report(conn, output_file="docs/DATABASE_VALIDATION.md"):
    """Generate comprehensive validation report"""
    cursor = conn.cursor()
    
    # Get overall statistics
    cursor.execute("SELECT COUNT(*) FROM voters")
    total_voters = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT ac_number) FROM voters")
    total_acs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM voters WHERE epic_no != '' AND epic_no IS NOT NULL")
    with_epic = cursor.fetchone()[0]
    
    # AC-wise data
    cursor.execute("""
        SELECT ac_number, ac_name, COUNT(*) as voter_count,
               SUM(CASE WHEN epic_no != '' THEN 1 ELSE 0 END) as with_epic,
               SUM(CASE WHEN age != '' THEN 1 ELSE 0 END) as with_age
        FROM voters
        GROUP BY ac_number, ac_name
        ORDER BY ac_number
    """)
    
    ac_data = cursor.fetchall()
    
    # Write report
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write("# Database Validation Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Overall Statistics\n\n")
        f.write(f"- **Total Voters:** {total_voters:,}\n")
        f.write(f"- **Total ACs:** {total_acs}\n")
        f.write(f"- **Voters with EPIC:** {with_epic:,} ({with_epic/total_voters*100:.1f}%)\n\n")
        
        f.write("## AC-wise Summary\n\n")
        f.write("| AC Number | AC Name | Total Voters | With EPIC | With Age | EPIC % |\n")
        f.write("|-----------|---------|--------------|-----------|----------|--------|\n")
        
        for ac_num, ac_name, voters, epic, age in ac_data:
            epic_pct = (epic / voters * 100) if voters > 0 else 0
            f.write(f"| {ac_num} | {ac_name} | {voters:,} | {epic:,} | {age:,} | {epic_pct:.1f}% |\n")
    
    print(f"\n✅ Validation report saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Validate and check voter database",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--district', type=int, help='Validate specific district')
    parser.add_argument('--ac', type=int, help='Validate specific AC')
    parser.add_argument('--dedupe', action='store_true', help='Remove exact duplicates')
    parser.add_argument('--report', action='store_true', help='Generate validation report')
    parser.add_argument('--db', default='data/electoral_roll.db', help='Database path')
    
    args = parser.parse_args()
    
    conn = get_db_connection(args.db)
    
    # Run validations
    validate_completeness(conn, args.district, args.ac)
    detect_duplicates(conn, args.district, args.ac)
    data_quality_checks(conn, args.district, args.ac)
    
    # Remove duplicates if requested
    if args.dedupe:
        remove_exact_duplicates(conn)
        print("\n✅ Re-running validation after deduplication...\n")
        detect_duplicates(conn, args.district, args.ac)
    
    # Generate report if requested
    if args.report:
        generate_report(conn)
    
    conn.close()
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    from datetime import datetime
    main()
