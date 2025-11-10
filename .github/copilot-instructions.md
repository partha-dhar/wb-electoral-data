# GitHub Copilot Instructions for WB Electoral Data Project

## 🎯 Project Overview
This project downloads, validates, and extracts voter data from West Bengal electoral rolls PDFs. All operations must be scalable, reusable, and maintainable across all districts, ACs, and parts.

---

## � CRITICAL: Directory Path & Terminal Management

### Absolute Directory Paths
**ALWAYS use correct directory paths:**

```bash
# Base Directory (User workspace)
BASE_DIR="$HOME/Desktop/sir26"                        # ~/Desktop/sir26/

# Git Repository (Where code lives)
REPO_DIR="$HOME/Desktop/sir26/wb-electoral-data"      # ~/Desktop/sir26/wb-electoral-data/

# CRITICAL: Before running ANY command, verify you're in the correct directory!
```

### Terminal Usage Rules
**ALWAYS follow these terminal guidelines:**

1. **Before EVERY terminal command, check/navigate to correct directory:**
   ```bash
   cd ~/Desktop/sir26/wb-electoral-data  # For git operations, scripts
   cd ~/Desktop/sir26                     # For outer workspace operations
   ```

2. **NEVER interrupt long-running processes** (downloads, extractions, builds)
   - Use NEW terminal for monitoring/other commands
   - Let extraction/download complete in background
   - Use `nohup` or background processes for overnight tasks

3. **For long-running tasks, use background execution:**
   ```bash
   # ✅ GOOD - Run in background with logging
   nohup python3 scripts/extract_voters.py --district 13 > /tmp/extraction.log 2>&1 &
   
   # ✅ GOOD - Use separate terminal for monitoring
   # Terminal 1: Run extraction
   # Terminal 2: Monitor progress (tail -f /tmp/extraction.log)
   
   # ❌ BAD - Block terminal and risk interruption
   python3 scripts/long_running_task.py
   ```

4. **Always verify directory before operations:**
   ```bash
   # At start of every terminal session:
   pwd                                  # Check current directory
   cd ~/Desktop/sir26/wb-electoral-data # Navigate to repo
   git status                           # Verify git repo
   ```

### Directory Structure
```
~/Desktop/sir26/                              # Base workspace
├── .github/
│   └── copilot-instructions.md              # THIS FILE (outer copy)
├── wb-electoral-data/                        # Git repository
│   ├── .github/
│   │   └── copilot-instructions.md          # THIS FILE (repo copy)
│   ├── .git/                                # Git metadata
│   ├── data/                                # Data directory
│   │   ├── downloaded_pdfs/                 # Downloaded PDFs
│   │   ├── api_metadata/                    # API metadata
│   │   └── electoral_roll.db                # SQLite database
│   ├── scripts/                             # Universal scripts
│   ├── docs/                                # Documentation
│   └── README.md
├── archive/                                  # Old/reference code
└── [other workspace files]
```

---

## 📋 INSTRUCTION FILE SYNCHRONIZATION

### Dual Instruction Files
**TWO identical instruction files MUST always be kept in sync:**

1. **Outer File**: `~/Desktop/sir26/.github/copilot-instructions.md`
2. **Repo File**: `~/Desktop/sir26/wb-electoral-data/.github/copilot-instructions.md`

### Update Protocol
**WHENEVER user provides new instructions:**

1. ✅ Update BOTH instruction files with identical content
2. ✅ Add new sections/rules to both files simultaneously
3. ✅ Use same content, formatting, examples in both
4. ✅ Verify synchronization after updates:
   ```bash
   diff ~/Desktop/sir26/.github/copilot-instructions.md \
        ~/Desktop/sir26/wb-electoral-data/.github/copilot-instructions.md
   # Should show NO differences
   ```

### Why Two Files?
- **Outer file** (`sir26/.github/`): Available across entire workspace
- **Repo file** (`wb-electoral-data/.github/`): Tracked in git, versioned
- **Both must match**: Ensures consistency regardless of context

---

## �📁 Directory Structure & Organization

### Documentation Rules
- **ALL documentation files MUST be placed in `./docs/`**
- **NEVER create documentation in the root directory**
- Use clear, descriptive filenames: `VALIDATION_REPORT.md`, `API_GUIDE.md`, etc.
- Keep documentation up-to-date with code changes

### Data Structure Rules
- **Voter data MUST NEVER be committed to git**
- **Only counts, statistics, and validation results go into documentation**
- Downloaded PDFs: `data/downloaded_pdfs/ALL/DISTRICT_{N}_{Name}/AC_{N}_{Name}/PS_{N}_{Name}/`
- API Metadata: `data/api_metadata/api/DIST_{NN}_{Name}/AC_{NNN}_{Name}/parts.json`
- Temporary/working files: Create outside git repo (e.g., `/tmp/`)

### Analytics & Validation
- Real counts go to: `docs/ANALYTICS.md`
- Validation results go to: `docs/VALIDATION_REPORT.md`
- No raw voter data (names, addresses, IDs) in git
- Only aggregated statistics: PDF counts, AC counts, completion percentages

---

## 🛠️ Scripting Best Practices

### Universal Script Design
**ALWAYS create scripts that work for ANY district/AC/part:**

```bash
# ✅ GOOD - Universal script with parameters
./scripts/download_electoral_rolls.sh --district 9
./scripts/download_electoral_rolls.sh --district 13 --ac 150
./scripts/validate_downloads.sh  # Validates ALL districts

# ❌ BAD - Hard-coded, single-use scripts
./scripts/download_district_9.sh
./scripts/validate_kolkata_south.sh
```

### Script Requirements
1. **Accept command-line arguments** for district, AC, part numbers
2. **Provide `--help` flag** with usage examples
3. **Handle both zero-padded and non-padded formats** (AC_084 vs AC_84)
4. **Validate inputs** before processing
5. **Show progress** for long-running operations
6. **Generate detailed reports** with statistics
7. **Exit gracefully** with appropriate error codes

### Naming Convention Handling
**CRITICAL: Handle multiple naming conventions in all scripts:**

```bash
# Metadata uses zero-padded formats
DIST_09_North_24_Parganas/AC_084_BAGDAHA/parts.json

# Downloads may use non-padded formats
DISTRICT_9_North_24_Parganas/AC_84_BAGDAHA/

# PDFs may use either format
AC084PART001.pdf  # or  AC84PART001.pdf

# Always check BOTH formats:
pdf_file=$(find . -name "AC${ac}PART${part}.pdf" -o -name "AC$(printf "%03d" $ac)PART${part}.pdf")
```

---

## 🧹 Code Maintenance

### Before Creating New Code
1. **Check for reusable code** in existing scripts
2. **Search for similar functionality** before implementing from scratch
3. **Extend existing scripts** rather than creating duplicates
4. **Follow established patterns** in the codebase

### Cleanup Rules
**ALWAYS remove old/obsolete code:**

```bash
# When creating new version of a script:
# 1. Test new version thoroughly
# 2. Remove old version: validate_downloads_old.sh
# 3. Update documentation references
# 4. Commit with clear message: "Replace old validation with smart multi-format version"
```

### File Cleanup Checklist
Before finalizing any feature:
- [ ] Remove `*.old`, `*.tmp`, `*.bak`, `*_old.*` files
- [ ] Remove obsolete scripts that have been replaced
- [ ] Remove test files from root directory
- [ ] Move documentation from root to `docs/`
- [ ] Update README.md with new script usage
- [ ] Check for duplicate functionality

---

## 📊 Validation & Quality Assurance

### Validation Requirements
**ALWAYS validate against remote metadata:**

1. **Cross-check with API**: Compare local PDFs against `parts.json` metadata
2. **Check file integrity**: Size > 1KB, valid PDF header (`%PDF`)
3. **Verify completeness**: All parts from metadata are downloaded
4. **Test readability**: Ensure PDFs can be opened
5. **Generate reports**: Detail missing/corrupt files with AC and part numbers

### Validation Report Format
```markdown
## District {N} ({Name})
- Total ACs: {count}
- Total PDFs: {downloaded}/{expected} ({percentage}%)
- Missing: {count} PDFs
- Corrupt: {count} PDFs

### AC {N} ({Name})
- Status: ✅ Complete | ⚠️ Incomplete | ❌ Failed
- PDFs: {downloaded}/{expected}
- Missing Parts: [{list}] (if any)
```

---

## 🔒 Data Privacy & Security

### Sensitive Data Rules
**NEVER commit the following to git:**
- ❌ Voter names
- ❌ Addresses
- ❌ EPIC numbers (Voter ID)
- ❌ Phone numbers
- ❌ Any personally identifiable information (PII)

**Allowed in git:**
- ✅ PDF counts and statistics
- ✅ AC/PS numbers and names
- ✅ Validation results (counts only)
- ✅ API metadata (part numbers, AC details)
- ✅ Scripts and documentation

### .gitignore Rules
Ensure these patterns are in `.gitignore`:
```
# Voter data
data/extracted_voters/
data/voter_database/
*.db
*.sqlite
*_voters.csv
*_voter_data.json

# Large PDF files
data/downloaded_pdfs/**/*.pdf

# Temporary files
/tmp/
*.tmp
*.log
```

---

## 📝 Documentation Standards

### README.md Structure
Maintain these sections:
1. **Project Overview** - What the project does
2. **Current Status** - Latest validation results, completion percentage
3. **Quick Start** - Installation and basic usage
4. **Usage Examples** - Common commands for each script
5. **Documentation** - Table of all docs with descriptions
6. **Project Structure** - Directory organization
7. **Development** - Contributing guidelines

### Documentation Table Format
```markdown
| Document | Description |
|----------|-------------|
| **[VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md)** | PDF download validation report (100% complete - 7,936 PDFs) |
| **[API.md](docs/API.md)** | West Bengal CEO API documentation and endpoints |
```

### Commit Message Guidelines
```bash
# Good commit messages
feat: Add universal download script for any district/AC
fix: Handle zero-padded AC numbers in validation
docs: Update validation report with District 9 results
refactor: Remove old validation script, use smart version
chore: Clean up obsolete files and move docs to docs/

# Bad commit messages
update
fix bug
changes
wip
```

---

## 🔍 Problem-Solving Approach

### When Encountering Issues
1. **Investigate first** - Don't assume, verify with actual data
2. **Check naming conventions** - Zero-padded vs non-padded?
3. **Validate assumptions** - Does metadata actually exist?
4. **Search codebase** - Has this been solved before?
5. **Create general solution** - Make it work for all cases, not just one

### Example: Metadata "Missing" Issue
```
❌ Problem: "AC 84-99 metadata not found"
🔍 Investigation: Checked actual files - metadata EXISTS
💡 Root Cause: Script looks for AC_84_ but files are AC_084_
✅ Solution: Check both formats, use find with pattern matching
📚 Lesson: Always handle multiple naming conventions
```

---

## 🚀 Deployment & Testing

### Before Committing Code
1. **Test with multiple districts/ACs** - Not just one case
2. **Verify edge cases** - First AC, last AC, gaps in sequence
3. **Check error handling** - Invalid inputs, missing files, network errors
4. **Run validation** - Ensure no regressions
5. **Update documentation** - README, usage examples, validation reports
6. **Clean up** - Remove old files, test data, temporary files

### Testing Checklist
- [ ] Script works with District 9 (28 ACs)
- [ ] Script works with District 13 (7 ACs)
- [ ] Script handles missing parts gracefully
- [ ] Script provides clear error messages
- [ ] Script generates accurate reports
- [ ] Documentation is updated
- [ ] Old code is removed
- [ ] No sensitive data in commit

---

## 🎨 Code Style

### Shell Scripts (Bash)
```bash
#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Clear function names
validate_pdf_file() {
    local pdf_path="$1"
    # Implementation
}

# Use absolute paths
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Descriptive variable names
ac_number=150
district_name="Kolkata_SOUTH"

# Comments for complex logic
# Handle both zero-padded (AC_084) and non-padded (AC_84) formats
```

### Python Scripts
```python
#!/usr/bin/env python3
"""
Script description and purpose.
"""
import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Script purpose")
    parser.add_argument("--district", type=int, required=True)
    args = parser.parse_args()
    
    # Implementation

if __name__ == "__main__":
    main()
```

---

## 📋 Key Lessons from This Project

### 1. Naming Convention Challenges
- **Issue**: West Bengal CEO Office uses inconsistent formats (DIST_09 vs DISTRICT_9)
- **Solution**: Always check multiple formats using find patterns
- **Pattern**: `find . -name "AC_${ac}_*" -o -name "AC_$(printf "%03d" $ac)_*"`

### 2. Validation Strategy
- **Always validate against source** (API metadata, not assumptions)
- **Check file existence AND integrity** (size, PDF header)
- **Generate detailed reports** (which AC, which part is missing)
- **Only download missing files** (skip existing, valid PDFs)

### 3. Script Design
- **One universal script > Many single-purpose scripts**
- **Parameters > Hard-coded values**
- **Clear error messages > Silent failures**
- **Progress indicators > Black box operations**

### 4. Documentation
- **Centralize in docs/** (not scattered in root)
- **Update with every change** (validation results, new scripts)
- **Show examples** (usage, output, common scenarios)
- **Document issues and solutions** (for future reference)

### 5. Data Management
- **Never commit voter data** (privacy and repo size)
- **Only commit counts/statistics** (analytics, validation)
- **Use .gitignore properly** (PDFs, databases, extracted data)
- **Organize by hierarchy** (District > AC > PS > PDF)

---

## 🎯 Project Goals & Principles

### Core Principles
1. **Scalability**: Works for 1 AC or 1000 ACs
2. **Reusability**: Same script for all districts
3. **Maintainability**: Clear code, good documentation
4. **Data Privacy**: No PII in git, ever
5. **Efficiency**: Download once, validate always

### Success Metrics
- ✅ 100% validation coverage
- ✅ Zero hard-coded scripts
- ✅ All documentation in docs/
- ✅ No voter data in git
- ✅ Clean, organized codebase

---

## 🔄 Workflow Summary

### Standard Development Flow
```
1. Plan → Check for existing solutions
2. Develop → Create universal, parameterized scripts
3. Test → Multiple districts, edge cases
4. Validate → Run validation scripts
5. Document → Update README, create/update docs in docs/
6. Clean → Remove old files, test data
7. Commit → Clear message, no sensitive data
```

### Standard Validation Flow
```
1. Download PDFs → Use universal download script
2. Validate → Run validation against API metadata
3. Fix Issues → Download missing, investigate corrupt
4. Re-validate → Confirm 100% completion
5. Document → Update VALIDATION_REPORT.md
6. Update README → Current status, new commands
```

---

## 📚 References

### Key Documentation Files
- `docs/VALIDATION_REPORT.md` - Current validation status
- `docs/API.md` - West Bengal CEO API details
- `docs/PDF_STRUCTURE.md` - Directory organization
- `docs/SETUP_GUIDE.md` - Initial setup instructions

### Key Scripts
- `scripts/download_electoral_rolls.sh` - Universal downloader
- `scripts/validate_downloads.sh` - Smart validation with multi-format support
- `scripts/extract_voters.py` - PDF data extraction
- `scripts/verify_with_api.py` - API cross-verification

---

## ⚠️ Critical Reminders

### ALWAYS
- ✅ Place docs in `./docs/`
- ✅ Create universal scripts (work for any district/AC)
- ✅ Handle multiple naming conventions
- ✅ Validate against remote metadata
- ✅ Update documentation with changes
- ✅ Remove old code after testing new version
- ✅ Check for reusable code before writing new

### NEVER
- ❌ Commit voter data (names, addresses, IDs)
- ❌ Hard-code district/AC numbers in scripts
- ❌ Leave old/obsolete scripts in repo
- ❌ Create docs in root directory
- ❌ Assume naming conventions (always check both formats)
- ❌ Skip validation after changes

---

## 🎉 Project Achievements

### Completed Milestones
- ✅ Downloaded 7,936 PDFs across 35 ACs (Districts 9 & 13)
- ✅ 100% validation completion (0 missing, 0 corrupt)
- ✅ Created universal download script
- ✅ Created smart validation with multi-format support
- ✅ Solved naming convention challenges
- ✅ Comprehensive documentation (12 files)
- ✅ Clean, organized codebase

### Ready for Next Phase
- 🚀 Voter data extraction from validated PDFs (AC_139 completed, need to validate the database)
- 🚀 Database creation and indexing
- 🚀 API verification and cross-checking
- 🚀 Analytics and reporting

---

## 📦 Archive Management

### Archive Folder Review
The `~/Desktop/sir26/archive/` folder contains development artifacts from initial project creation. **A complete backup ZIP has been created.**

### What Was Extracted from Archive
**ALL useful code has been integrated into main repo:**

1. **CID Decoding Logic** ✅
   - Source: `archive/old_scripts/extract_voter_data_final.py`
   - Integrated into: `scripts/extract_voters_universal.py`
   - Character mappings, CID codes fully documented

2. **PDF Validation Approach** ✅
   - Created: `scripts/validate_pdf_to_db.py`
   - Validates DB records against actual PDFs
   - Counts voters, spot-checks names/EPICs

3. **Monitoring Scripts** ✅
   - Updated: `scripts/monitor_extraction.sh`
   - Based on archive monitoring utilities

### Archive Cleanup Protocol
**ALWAYS follow these steps when managing archive:**

1. **Before Deleting Archive:**
   ```bash
   # Create timestamped backup
   cd ~/Desktop/sir26
   zip -r archive_backup_$(date +%Y%m%d).zip archive/
   
   # Verify ZIP created
   ls -lh archive_backup_*.zip
   ```

2. **Review Archive Contents:**
   - Check for useful code not yet extracted
   - Look for documentation/notes worth preserving
   - Identify any unique solutions to problems

3. **Extract Useful Code:**
   - Integrate into appropriate universal scripts
   - Document source in code comments
   - Add to `docs/ARCHIVE_REVIEW.md`

4. **After Extraction:**
   ```bash
   # Safe to remove archive folder
   rm -rf ~/Desktop/sir26/archive/
   
   # Keep ZIP backup for reference
   mv archive_backup_*.zip ~/Desktop/sir26/backups/
   ```

### Archive Contents Summary
See `docs/ARCHIVE_REVIEW.md` for complete list of:
- Scripts extracted and integrated
- Documentation preserved
- Development artifacts archived
- Lessons learned from iterative development

**Status:** Archive reviewed November 10, 2025. All useful code extracted. Safe to delete folder (backup ZIP created).

---

**Last Updated**: November 10, 2025  
**Project Status**: Validation Phase Complete (100%) - Ready for Extraction  
**Total PDFs**: 7,936 across 35 ACs in 2 districts
