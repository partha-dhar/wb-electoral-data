#!/bin/bash
# Universal Electoral Roll PDF Downloader
# Downloads PDFs for any district/AC using metadata from data/api_metadata/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
METADATA_BASE="$REPO_ROOT/data/api_metadata/api"
DOWNLOAD_BASE="$REPO_ROOT/data/downloaded_pdfs/ALL"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Show usage
usage() {
    cat << EOF
${BLUE}Electoral Roll PDF Downloader${NC}
Downloads PDFs using metadata from data/api_metadata/

${YELLOW}Usage:${NC}
  $0 --district DIST_NUM [--ac AC_NUM]
  $0 --list-districts
  $0 --list-acs DIST_NUM

${YELLOW}Options:${NC}
  --district NUM      District number (e.g., 13 for Kolkata South)
  --ac NUM            Specific Assembly Constituency (downloads all if omitted)
  --list-districts    Show all available districts
  --list-acs NUM      Show all ACs in a district
  -h, --help          Show this help

${YELLOW}Examples:${NC}
  $0 --list-districts                    # Show all districts
  $0 --list-acs 13                       # Show ACs in Kolkata South
  $0 --district 13                       # Download all Kolkata South
  $0 --district 13 --ac 146              # Download only AC 146
  $0 --district 3                        # Download all Darjeeling

EOF
}

# List available districts
list_districts() {
    echo -e "${BLUE}Available Districts:${NC}"
    echo ""
    
    for dist_dir in "$METADATA_BASE"/DIST_*/; do
        if [ -d "$dist_dir" ]; then
            dist_name=$(basename "$dist_dir")
            dist_num=$(echo "$dist_name" | grep -oP 'DIST_\K\d+')
            dist_display=$(echo "$dist_name" | sed 's/DIST_[0-9]*_//')
            
            # Count ACs
            ac_count=$(find "$dist_dir" -type d -name "AC_*" | wc -l)
            
            # Get total parts from district_info if available
            dist_info="$dist_dir/district_info.json"
            if [ -f "$dist_info" ]; then
                total_parts=$(python3 -c "import json; print(json.load(open('$dist_info'))['total_parts'])" 2>/dev/null || echo "?")
            else
                total_parts="?"
            fi
            
            echo -e "  ${GREEN}District $dist_num${NC}: $dist_display"
            echo -e "    ACs: $ac_count | Total Parts: $total_parts"
            echo ""
        fi
    done
}

# List ACs in a district
list_acs() {
    local dist_num=$1
    local dist_dir=$(find "$METADATA_BASE" -type d -name "DIST_${dist_num}_*" | head -1)
    
    if [ -z "$dist_dir" ]; then
        echo -e "${RED}✗ District $dist_num not found${NC}"
        return 1
    fi
    
    local dist_name=$(basename "$dist_dir" | sed 's/DIST_[0-9]*_//')
    echo -e "${BLUE}District $dist_num: $dist_name${NC}"
    echo ""
    
    for ac_dir in "$dist_dir"/AC_*/; do
        if [ -d "$ac_dir" ]; then
            local ac_name=$(basename "$ac_dir")
            local ac_num=$(echo "$ac_name" | grep -oP 'AC_\K\d+')
            local ac_display=$(echo "$ac_name" | sed 's/AC_[0-9]*_//')
            
            # Count parts from parts.json
            local parts_file="$ac_dir/parts.json"
            if [ -f "$parts_file" ]; then
                local part_count=$(python3 -c "import json; print(json.load(open('$parts_file'))['total_parts'])" 2>/dev/null || echo "?")
            else
                local part_count="?"
            fi
            
            echo -e "  ${GREEN}AC $ac_num${NC}: $ac_display (${CYAN}$part_count parts${NC})"
        fi
    done
}

# Download PDFs for a single AC
download_ac() {
    local dist_num=$1
    local ac_num=$2
    
    # Find district directory
    local dist_dir=$(find "$METADATA_BASE" -type d -name "DIST_${dist_num}_*" | head -1)
    if [ -z "$dist_dir" ]; then
        echo -e "${RED}✗ District $dist_num not found${NC}"
        return 1
    fi
    
    # Find AC directory
    local ac_dir=$(find "$dist_dir" -type d -name "AC_${ac_num}_*" | head -1)
    if [ -z "$ac_dir" ]; then
        echo -e "${RED}✗ AC $ac_num not found in district $dist_num${NC}"
        return 1
    fi
    
    local ac_name=$(basename "$ac_dir")
    local dist_name=$(basename "$dist_dir")
    
    # Remove DIST_XX_ prefix from dist_name for clean folder names
    dist_name=$(echo "$dist_name" | sed 's/^DIST_[0-9]*_//')
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Downloading AC $ac_num: $(echo $ac_name | sed 's/AC_[0-9]*_//')${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Check parts.json
    local parts_file="$ac_dir/parts.json"
    if [ ! -f "$parts_file" ]; then
        echo -e "${RED}✗ Parts file not found: $parts_file${NC}"
        return 1
    fi
    
    # Create output directory with proper structure
    local output_dir="$DOWNLOAD_BASE/DISTRICT_${dist_num}_${dist_name}/$ac_name"
    mkdir -p "$output_dir"
    
    # Download using Python with scraping approach
    local temp_script="$REPO_ROOT/.tmp_download_ac_${ac_num}.py"
    cat > "$temp_script" << 'PYTHON_EOF'
#!/usr/bin/env python3
import sys
import re
import ssl
import base64
import json
import requests
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

def safe_filename(name):
    """Create safe folder name."""
    return name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_').strip()

def download_pdf(session, ps_info, ps_folder, metadata):
    pdf_filename = ps_info['pdf_filename']
    output_path = ps_folder / pdf_filename
    
    if output_path.exists():
        return {'status': 'skip', 'part': ps_info['ps_num'], 'file': pdf_filename}
    
    try:
        # Encode filename and construct URL
        encoded_filename = base64.b64encode(pdf_filename.encode()).decode()
        url = f"https://ceowestbengal.wb.gov.in/RollPDF/GetDraft?acId={ps_info['ac_id']}&key={encoded_filename}"
        
        response = session.get(url, timeout=60, verify=False)
        response.raise_for_status()
        
        # Check if it's actually a PDF
        if 'pdf' not in response.headers.get('Content-Type', '').lower():
            return {'status': 'error', 'part': ps_info['ps_num'], 'error': 'Not a PDF'}
        
        # Save PDF
        output_path.write_bytes(response.content)
        return {'status': 'success', 'part': ps_info['ps_num'], 'size': len(response.content)}
    except Exception as e:
        return {'status': 'error', 'part': ps_info['ps_num'], 'error': str(e)}

def scrape_polling_stations(session, ac_num):
    """Scrape polling station list to get PDF download info."""
    url = f"https://ceowestbengal.wb.gov.in/Roll_ps/{ac_num}"
    response = session.get(url, timeout=30, verify=False)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    polling_stations = []
    
    table = soup.find('table')
    if table:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                ps_num = cells[0].get_text(strip=True)
                ps_name = cells[1].get_text(strip=True)
                pdf_link = cells[2].find('a')
                
                if pdf_link and ps_num:
                    onclick = pdf_link.get('onclick', '')
                    match = re.search(r"openWithImageCaptcha\('(\d+)',\s*'([^']+)'\)", onclick)
                    if match:
                        polling_stations.append({
                            'ps_num': ps_num,
                            'ps_name': ps_name,
                            'ac_id': match.group(1),
                            'pdf_filename': match.group(2)
                        })
    
    return polling_stations

def main():
    output_dir = Path(sys.argv[1])
    ac_num = int(sys.argv[2])
    metadata_file = Path(sys.argv[3])
    
    # Load metadata for PS names
    with open(metadata_file) as f:
        metadata = json.load(f)
    
    # Create PS name mapping
    ps_names = {}
    for part in metadata['parts']:
        part_num = part['partNumber']
        ps_names[part_num] = safe_filename(part['partName'])
    
    # Setup session
    session = requests.Session()
    session.mount('https://', SSLAdapter())
    
    # Step 1: Scrape polling station list
    print("Fetching polling station list...")
    try:
        polling_stations = scrape_polling_stations(session, ac_num)
        total = len(polling_stations)
        print(f"Total parts: {total}")
    except Exception as e:
        print(f"Error fetching polling stations: {e}")
        return 1
    
    if total == 0:
        print("No polling stations found!")
        return 1
    
    # Step 2: Download PDFs into PS folders
    success = 0
    skipped = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for ps in polling_stations:
            part_num = int(ps['pdf_filename'].split('PART')[1].replace('.pdf', ''))
            ps_name = ps_names.get(part_num, f"PART_{part_num}")
            ps_folder_name = f"PS_{part_num:03d}_{ps_name}"
            ps_folder = output_dir / ps_folder_name
            ps_folder.mkdir(parents=True, exist_ok=True)
            
            futures[executor.submit(download_pdf, session, ps, ps_folder, metadata)] = ps
        
        with tqdm(total=total, unit='pdf') as pbar:
            for future in as_completed(futures):
                result = future.result()
                if result['status'] == 'success':
                    success += 1
                elif result['status'] == 'skip':
                    skipped += 1
                else:
                    failed += 1
                pbar.update(1)
    
    print(f"\n✓ Success: {success} | Skipped: {skipped} | Failed: {failed}")
    # Return success if there were no new failures
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
PYTHON_EOF
    
    chmod +x "$temp_script"
    
    # Run download with metadata file for PS names
    python3 "$temp_script" "$output_dir" "$ac_num" "$parts_file"
    local exit_code=$?
    
    # Cleanup
    rm -f "$temp_script"
    
    return $exit_code
}

# Download entire district
download_district() {
    local dist_num=$1
    
    local dist_dir=$(find "$METADATA_BASE" -type d -name "DIST_${dist_num}_*" | head -1)
    if [ -z "$dist_dir" ]; then
        echo -e "${RED}✗ District $dist_num not found${NC}"
        return 1
    fi
    
    local dist_display=$(basename "$dist_dir" | sed 's/DIST_[0-9]*_//')
    
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Electoral Roll PDF Download              ║${NC}"
    echo -e "${BLUE}║  District $dist_num: $dist_display${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""
    
    local success_count=0
    local fail_count=0
    
    # Get all AC directories
    local ac_dirs=($(find "$dist_dir" -type d -name "AC_*" | sort))
    
    for ac_dir in "${ac_dirs[@]}"; do
        local ac_num=$(basename "$ac_dir" | grep -oP 'AC_\K\d+')
        
        if download_ac "$dist_num" "$ac_num"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
        echo ""
    done
    
    # Summary
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Download Summary:${NC}"
    echo -e "  Successful ACs: ${GREEN}$success_count${NC}"
    echo -e "  Failed ACs: ${RED}$fail_count${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    return $([ $fail_count -eq 0 ] && echo 0 || echo 1)
}

# Main
main() {
    cd "$REPO_ROOT"
    
    # Check for Python dependencies
    if ! python3 -c "import requests, tqdm, bs4" 2>/dev/null; then
        echo -e "${YELLOW}Installing required Python packages...${NC}"
        pip3 install requests tqdm beautifulsoup4 --quiet
    fi
    
    # Parse arguments
    case "${1:-}" in
        --list-districts)
            list_districts
            ;;
        --list-acs)
            if [ -z "$2" ]; then
                echo -e "${RED}✗ Please provide district number${NC}"
                usage
                exit 1
            fi
            list_acs "$2"
            ;;
        --district)
            if [ -z "$2" ]; then
                echo -e "${RED}✗ Please provide district number${NC}"
                usage
                exit 1
            fi
            
            if [ "${3:-}" == "--ac" ] && [ -n "${4:-}" ]; then
                # Download specific AC
                download_ac "$2" "$4"
            else
                # Download entire district
                download_district "$2"
            fi
            ;;
        -h|--help|"")
            usage
            ;;
        *)
            echo -e "${RED}✗ Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
}

main "$@"
