#!/bin/bash

# Validate downloaded PDFs against remote source (Smart Version)
# Only validates ACs that exist in the download directory
# Checks if PDFs exist, are readable, and reports missing ones

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOWNLOAD_BASE="$REPO_ROOT/data/downloaded_pdfs/ALL"

# Function to check if PDF is readable
is_pdf_readable() {
    local pdf_file="$1"
    
    # Check if file exists
    if [[ ! -f "$pdf_file" ]]; then
        return 1
    fi
    
    # Check if file size is reasonable (> 1KB)
    local file_size=$(stat -c%s "$pdf_file" 2>/dev/null || stat -f%z "$pdf_file" 2>/dev/null || echo 0)
    if [[ $file_size -lt 1024 ]]; then
        return 1
    fi
    
    # Check PDF header
    if ! head -c 4 "$pdf_file" 2>/dev/null | grep -q "%PDF"; then
        return 1
    fi
    
    return 0
}

# Function to validate a single district
validate_district() {
    local dist_num=$1
    local dist_name=$2
    
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Validating District $dist_num: $dist_name${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    
    local download_dir="$DOWNLOAD_BASE/DISTRICT_${dist_num}_${dist_name}"
    
    if [[ ! -d "$download_dir" ]]; then
        echo -e "${RED}✗ Download directory not found: $download_dir${NC}"
        return 1
    fi
    
    # Try with zero-padded district number first, then without
    local metadata_dir="$REPO_ROOT/data/api_metadata/api/DIST_$(printf "%02d" $dist_num)_${dist_name}"
    if [[ ! -d "$metadata_dir" ]]; then
        metadata_dir="$REPO_ROOT/data/api_metadata/api/DIST_${dist_num}_${dist_name}"
    fi
    
    if [[ ! -d "$metadata_dir" ]]; then
        echo -e "${YELLOW}⚠ Metadata directory not found, using download directory as reference${NC}"
        validate_from_downloads "$dist_num" "$dist_name" "$download_dir"
        return $?
    fi
    
    local total_parts=0
    local found_pdfs=0
    local readable_pdfs=0
    local corrupt_pdfs=0
    local missing_pdfs=0
    local missing_list=()
    
    # Get list of ACs that actually exist in download directory
    local downloaded_acs=()
    for ac_dir in "$download_dir"/AC_*; do
        if [[ -d "$ac_dir" ]]; then
            local ac_name=$(basename "$ac_dir")
            downloaded_acs+=("$ac_name")
        fi
    done
    
    if [[ ${#downloaded_acs[@]} -eq 0 ]]; then
        echo -e "${YELLOW}⚠ No ACs found in download directory${NC}"
        return 1
    fi
    
    echo -e "Found ${#downloaded_acs[@]} ACs to validate\n"
    
    # Process each downloaded AC
    for ac_name in "${downloaded_acs[@]}"; do
        local ac_num=$(echo "$ac_name" | grep -oP 'AC_\K\d+')
        local ac_num_int=$((10#$ac_num))
        
        # Try to find metadata with both zero-padded and non-padded AC numbers
        local parts_file=""
        # Try zero-padded first (AC_084_*)
        parts_file=$(find "$metadata_dir" -name "parts.json" -path "*/AC_$(printf "%03d" $ac_num_int)_*/parts.json" 2>/dev/null | head -1)
        # If not found, try non-padded (AC_84_*)
        if [[ -z "$parts_file" ]]; then
            parts_file=$(find "$metadata_dir" -name "parts.json" -path "*/AC_${ac_num}_*/parts.json" 2>/dev/null | head -1)
        fi
        
        if [[ ! -f "$parts_file" ]]; then
            echo -e "${YELLOW}⚠ No metadata found for $ac_name, skipping validation${NC}"
            continue
        fi
        
        echo -e "${BLUE}Checking $ac_name...${NC}"
        
        # Read parts from JSON
        local parts_data=$(cat "$parts_file")
        local num_parts=$(echo "$parts_data" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('parts', [])))" 2>/dev/null || echo 0)
        
        if [[ $num_parts -eq 0 ]]; then
            echo -e "${YELLOW}  ⚠ Could not read parts count, counting actual PDFs${NC}"
            num_parts=$(find "$download_dir/$ac_name" -name "*.pdf" | wc -l)
        fi
        
        total_parts=$((total_parts + num_parts))
        
        local ac_found=0
        local ac_readable=0
        local ac_corrupt=0
        local ac_missing=0
        
        # Check each part
        for ((part=1; part<=num_parts; part++)); do
            # Try both zero-padded and non-padded AC numbers in filename
            local pdf_filename=$(printf "AC%dPART%03d.pdf" "$ac_num_int" "$part")
            local pdf_filename_padded=$(printf "AC%03dPART%03d.pdf" "$ac_num_int" "$part")
            
            # Find the PDF in any PS folder (try both naming conventions)
            local pdf_path=$(find "$download_dir/$ac_name" -name "$pdf_filename" -o -name "$pdf_filename_padded" 2>/dev/null | head -1)
            
            if [[ -z "$pdf_path" ]]; then
                # PDF not found
                missing_pdfs=$((missing_pdfs + 1))
                ac_missing=$((ac_missing + 1))
                missing_list+=("$dist_num|$ac_num_int|$part")
                if [[ $ac_missing -le 5 ]]; then
                    echo -e "${RED}  ✗ Missing: $pdf_filename${NC}"
                fi
            else
                found_pdfs=$((found_pdfs + 1))
                ac_found=$((ac_found + 1))
                
                # Check if PDF is readable
                if is_pdf_readable "$pdf_path"; then
                    readable_pdfs=$((readable_pdfs + 1))
                    ac_readable=$((ac_readable + 1))
                else
                    corrupt_pdfs=$((corrupt_pdfs + 1))
                    ac_corrupt=$((ac_corrupt + 1))
                    missing_list+=("$dist_num|$ac_num_int|$part")
                    if [[ $ac_corrupt -le 5 ]]; then
                        echo -e "${YELLOW}  ⚠ Corrupt/Unreadable: $pdf_filename${NC}"
                    fi
                fi
            fi
        done
        
        # AC Summary
        if [[ $ac_missing -gt 5 ]]; then
            echo -e "${RED}  ... and $((ac_missing - 5)) more missing${NC}"
        fi
        if [[ $ac_corrupt -gt 5 ]]; then
            echo -e "${YELLOW}  ... and $((ac_corrupt - 5)) more corrupt${NC}"
        fi
        
        if [[ $ac_missing -eq 0 && $ac_corrupt -eq 0 ]]; then
            echo -e "${GREEN}  ✓ $ac_name: All $num_parts PDFs present and readable${NC}"
        else
            echo -e "${YELLOW}  ⚠ $ac_name: $ac_readable readable, $ac_corrupt corrupt, $ac_missing missing (Total: $num_parts)${NC}"
        fi
    done
    
    # District Summary
    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}District $dist_num Summary:${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "Total Parts Expected: $total_parts"
    echo -e "${GREEN}✓ Readable PDFs: $readable_pdfs${NC}"
    if [[ $corrupt_pdfs -gt 0 ]]; then
        echo -e "${YELLOW}⚠ Corrupt PDFs: $corrupt_pdfs${NC}"
    fi
    if [[ $missing_pdfs -gt 0 ]]; then
        echo -e "${RED}✗ Missing PDFs: $missing_pdfs${NC}"
    fi
    
    local needs_download=$((corrupt_pdfs + missing_pdfs))
    echo -e "\n${BLUE}Total needing download: $needs_download${NC}"
    
    # Export missing list for download
    if [[ $needs_download -gt 0 ]]; then
        local missing_file="$REPO_ROOT/data/missing_pdfs_dist_${dist_num}.txt"
        printf "%s\n" "${missing_list[@]}" > "$missing_file"
        echo -e "${YELLOW}Missing PDFs list saved to: $missing_file${NC}"
        return 2  # Indicates missing PDFs
    fi
    
    echo -e "${GREEN}✓ District $dist_num validation complete!${NC}\n"
    return 0
}

# Fallback: validate from downloads when no metadata
validate_from_downloads() {
    local dist_num=$1
    local dist_name=$2
    local download_dir=$3
    
    echo -e "${YELLOW}Validating from download directory only...${NC}\n"
    
    local total_pdfs=0
    local readable_pdfs=0
    local corrupt_pdfs=0
    
    for ac_dir in "$download_dir"/AC_*; do
        if [[ ! -d "$ac_dir" ]]; then
            continue
        fi
        
        local ac_name=$(basename "$ac_dir")
        echo -e "${BLUE}Checking $ac_name...${NC}"
        
        local ac_total=0
        local ac_readable=0
        local ac_corrupt=0
        
        while IFS= read -r pdf_file; do
            ac_total=$((ac_total + 1))
            total_pdfs=$((total_pdfs + 1))
            
            if is_pdf_readable "$pdf_file"; then
                ac_readable=$((ac_readable + 1))
                readable_pdfs=$((readable_pdfs + 1))
            else
                ac_corrupt=$((ac_corrupt + 1))
                corrupt_pdfs=$((corrupt_pdfs + 1))
                echo -e "${YELLOW}  ⚠ Corrupt: $(basename "$pdf_file")${NC}"
            fi
        done < <(find "$ac_dir" -name "*.pdf" 2>/dev/null)
        
        if [[ $ac_corrupt -eq 0 ]]; then
            echo -e "${GREEN}  ✓ $ac_name: All $ac_total PDFs readable${NC}"
        else
            echo -e "${YELLOW}  ⚠ $ac_name: $ac_readable readable, $ac_corrupt corrupt (Total: $ac_total)${NC}"
        fi
    done
    
    # Summary
    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}District $dist_num Summary (from downloads):${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "Total PDFs Found: $total_pdfs"
    echo -e "${GREEN}✓ Readable PDFs: $readable_pdfs${NC}"
    if [[ $corrupt_pdfs -gt 0 ]]; then
        echo -e "${YELLOW}⚠ Corrupt PDFs: $corrupt_pdfs${NC}"
        return 2
    fi
    
    echo -e "${GREEN}✓ District $dist_num validation complete!${NC}\n"
    return 0
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "═══════════════════════════════════════════════════"
    echo "  PDF Download Validation Tool (Smart Version)"
    echo "═══════════════════════════════════════════════════"
    echo -e "${NC}\n"
    
    local validation_failed=0
    
    # Validate District 9 (North 24 Parganas)
    if validate_district 9 "North_24_Parganas"; then
        echo -e "${GREEN}✓ District 9 validation passed${NC}"
    else
        validation_failed=$?
    fi
    
    echo -e "\n"
    
    # Validate District 13 (Kolkata South)
    if validate_district 13 "Kolkata_SOUTH"; then
        echo -e "${GREEN}✓ District 13 validation passed${NC}"
    else
        validation_failed=$?
    fi
    
    # Final summary
    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Validation Complete${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    
    if [[ $validation_failed -eq 0 ]]; then
        echo -e "${GREEN}✓ All PDFs validated successfully!${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Some PDFs need attention. Check the output above.${NC}"
        if [[ -f "$REPO_ROOT/data/missing_pdfs_dist_9.txt" || -f "$REPO_ROOT/data/missing_pdfs_dist_13.txt" ]]; then
            echo -e "\n${BLUE}To download missing PDFs, run:${NC}"
            if [[ -f "$REPO_ROOT/data/missing_pdfs_dist_9.txt" ]]; then
                echo -e "  ${YELLOW}./scripts/download_missing.sh 9${NC}"
            fi
            if [[ -f "$REPO_ROOT/data/missing_pdfs_dist_13.txt" ]]; then
                echo -e "  ${YELLOW}./scripts/download_missing.sh 13${NC}"
            fi
        fi
        return 1
    fi
}

# Run main
main "$@"
