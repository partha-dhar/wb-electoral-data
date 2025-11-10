# Kolkata South (District 13) - Electoral Roll Download Guide

## Overview

This guide covers downloading and processing electoral roll data for **Kolkata South** district (District 13) from the CEO West Bengal website.

**Official URL**: https://ceowestbengal.wb.gov.in/Roll_ac/13

## District Information

- **District Number**: 13
- **District Name**: Kolkata SOUTH
- **Total Assembly Constituencies**: 7
- **Total Polling Parts**: 1,366

## Assembly Constituencies

| AC No | AC Name | Total Parts |
|-------|---------|-------------|
| 146 | CHOWRINGHEE | 172 |
| 147 | KABITIRTHA | 215 |
| 148 | ALIPORE | 164 |
| 149 | RASHBEHARI AVENUE | 151 |
| 150 | TOLLYGUNGE | 198 |
| 151 | DHAKURIA | 223 |
| 152 | BALLYGUNGE | 243 |

## Quick Start

### 1. Download PDFs

#### Download All Kolkata South (1,366 PDFs)
```bash
cd wb-electoral-data
python3 scripts/download_kolkata_south.py
```

#### Download Specific AC
```bash
# Download only AC 146 (CHOWRINGHEE)
python3 scripts/download_kolkata_south.py --ac 146

# Download only AC 152 (BALLYGUNGE)
python3 scripts/download_kolkata_south.py --ac 152
```

#### Download Range of ACs
```bash
# Download AC 146-148
python3 scripts/download_kolkata_south.py --start-ac 146 --end-ac 148

# Download AC 150-152
python3 scripts/download_kolkata_south.py --start-ac 150 --end-ac 152
```

#### Advanced Options
```bash
# Custom output directory
python3 scripts/download_kolkata_south.py --output /path/to/output

# Increase concurrent downloads (faster, more load)
python3 scripts/download_kolkata_south.py --concurrent 10

# Reduce concurrent downloads (slower, less load)
python3 scripts/download_kolkata_south.py --concurrent 2
```

### 2. Extract Voter Data

After downloading PDFs, extract voter information:

```bash
# Extract from specific AC
python3 scripts/extract_voters.py --ac 146 --db-path data/electoral_roll.db

# Extract from all downloaded PDFs
python3 scripts/extract_voters.py --input data/downloaded_pdfs/DISTRICT_Kolkata_SOUTH
```

### 3. Verify with API

Cross-verify extracted data against ECI API:

```bash
# Verify AC 146
python3 scripts/verify_with_api.py --ac 146 --db-path data/electoral_roll.db

# Verify with custom delay between requests
python3 scripts/verify_with_api.py --ac 146 --delay 1.0
```

## Directory Structure

After download, the structure will be:

```
data/downloaded_pdfs/
└── DISTRICT_Kolkata_SOUTH/
    ├── AC_146_CHOWRINGHEE/
    │   ├── PS_001_ST. XAVIERS COLLEGE, ROOM NO.-1/
    │   │   └── AC146PART001.pdf
    │   ├── PS_002_ST. XAVIERS COLLEGE, ROOM NO.-2/
    │   │   └── AC146PART002.pdf
    │   └── ... (172 parts)
    ├── AC_147_KABITIRTHA/
    │   └── ... (215 parts)
    ├── AC_148_ALIPORE/
    │   └── ... (164 parts)
    ├── AC_149_RASHBEHARI_AVENUE/
    │   └── ... (151 parts)
    ├── AC_150_TOLLYGUNGE/
    │   └── ... (198 parts)
    ├── AC_151_DHAKURIA/
    │   └── ... (223 parts)
    └── AC_152_BALLYGUNGE/
        └── ... (243 parts)
```

## Metadata

API metadata for Kolkata South is already available at:
```
data/api_metadata/api/DIST_13_Kolkata_SOUTH/
├── AC_146_CHOWRINGHEE/
│   └── parts.json
├── AC_147_KABITIRTHA/
│   └── parts.json
├── AC_148_ALIPORE/
│   └── parts.json
├── AC_149_RASHBEHARI_AVENUE/
│   └── parts.json
├── AC_150_TOLLYGUNGE/
│   └── parts.json
├── AC_151_DHAKURIA/
│   └── parts.json
├── AC_152_BALLYGUNGE/
│   └── parts.json
├── assemblies.json
└── district_info.json
```

## Expected Statistics

Based on similar districts, expected statistics for Kolkata South:

- **Total Voters**: ~1.2-1.5 million (estimated across all 7 ACs)
- **Average Voters per Part**: ~800-1,000
- **Total PDFs**: 1,366
- **Estimated Size**: ~3-5 GB for all PDFs
- **Download Time**: 
  - 5 concurrent: ~30-45 minutes
  - 10 concurrent: ~15-25 minutes
  - 2 concurrent: ~60-90 minutes

## Troubleshooting

### PDF Download Fails

If PDF downloads fail, check:
1. Internet connection
2. CEO West Bengal website is accessible
3. PDF URL structure (may need adjustment)

Try testing with a single AC first:
```bash
python3 scripts/download_kolkata_south.py --ac 146 --concurrent 2
```

### Extraction Errors

If extraction fails:
1. Verify PDFs downloaded correctly (check file sizes)
2. Check CID font mappings in `src/extractor.py`
3. Run with verbose logging:
```bash
python3 scripts/extract_voters.py --ac 146 --verbose
```

### API Verification Issues

If API verification fails:
1. Check internet connection
2. ECI Gateway API may have rate limits
3. Use larger delay: `--delay 2.0`

## Next Steps

After completing Kolkata South:

1. **Analyze Data**:
   ```bash
   python3 -m src.analytics --ac 146
   ```

2. **Generate Reports**:
   ```bash
   python3 -m src.analytics --district 13 --report
   ```

3. **Start Web Interface**:
   ```bash
   cd web
   python3 app.py
   ```
   Then open: http://localhost:5000

## Related Documentation

- [Setup Guide](SETUP_GUIDE.md)
- [API Verification Guide](API_VERIFICATION_GUIDE.md)
- [Analytics Guide](ANALYTICS.md)
- [API Documentation](API.md)

## Notes

- **Data Privacy**: All downloaded data is excluded from Git via `.gitignore`
- **Storage**: Ensure sufficient disk space (~5 GB for full district)
- **Time**: Full district download takes 30-45 minutes with default settings
- **Updates**: Check CEO West Bengal website for latest data revisions

---

**Last Updated**: November 10, 2025  
**Data Source**: CEO West Bengal (https://ceowestbengal.wb.gov.in)  
**Electoral Roll**: 2002 Base, SIR 2025
