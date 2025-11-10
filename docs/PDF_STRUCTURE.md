# Electoral Roll PDF Download Structure

## Directory Structure

All downloaded PDFs are organized in: `data/downloaded_pdfs/ALL/`

### Hierarchy

```
data/downloaded_pdfs/ALL/
├── DISTRICT_{distNo}_{distName}/
│   ├── AC_{acNo}_{acName}/
│   │   ├── PS_{partNo:03d}_{psName}/
│   │   │   └── AC{acNo}PART{partNo:03d}.pdf
│   │   ├── PS_{partNo:03d}_{psName}/
│   │   │   └── AC{acNo}PART{partNo:03d}.pdf
│   │   └── ...
│   ├── AC_{acNo}_{acName}/
│   │   └── ...
│   └── ...
├── DISTRICT_{distNo}_{distName}/
│   └── ...
└── ...
```

### Example

```
data/downloaded_pdfs/ALL/
├── DISTRICT_13_Kolkata_SOUTH/
│   ├── AC_146_CHOWRINGHEE/
│   │   ├── PS_001_ST._XAVIERS_COLLEGE,_ROOM_NO.-1/
│   │   │   └── AC146PART001.pdf
│   │   ├── PS_002_ST._XAVIERS_COLLEGE,_ROOM_NO.-2/
│   │   │   └── AC146PART002.pdf
│   │   ├── PS_003_ST._XAVIERS_COLLEGE,_ROOM_NO.-3/
│   │   │   └── AC146PART003.pdf
│   │   └── ... (172 PS folders total)
│   ├── AC_147_KABITIRTHA/
│   │   ├── PS_001_.../
│   │   │   └── AC147PART001.pdf
│   │   └── ... (215 PS folders total)
│   ├── AC_148_ALIPORE/ (164 PS folders)
│   ├── AC_149_RASHBEHARI_AVENUE/ (151 PS folders)
│   ├── AC_150_TOLLYGUNGE/ (198 PS folders)
│   ├── AC_151_DHAKURIA/ (223 PS folders)
│   └── AC_152_BALLYGUNGE/ (243 PS folders)
│
└── DISTRICT_9_North_24_Parganas/
    ├── AC_136_KAMARHATI/
    │   ├── PS_001_.../
    │   │   └── AC136PART001.pdf
    │   └── ...
    └── ... (28 ACs total, 6567 PDFs)
```

## Naming Conventions

### District Folders
- Format: `DISTRICT_{distNo}_{distName}`
- `distNo`: 2-digit district number (e.g., 13)
- `distName`: District name with spaces replaced by underscores

### Assembly Constituency (AC) Folders
- Format: `AC_{acNo}_{acName}`
- `acNo`: 3-digit AC number (e.g., 146)
- `acName`: AC name with spaces replaced by underscores

### Polling Station (PS) Folders
- Format: `PS_{partNo:03d}_{psName}`
- `partNo`: 3-digit zero-padded part/PS number (e.g., 001, 002, 172)
- `psName`: Polling station name with special characters replaced by underscores
  - Characters replaced: `/ \ : * ? " < > |`
  - Commas preserved in folder names

### PDF Files
- Format: `AC{acNo}PART{partNo:03d}.pdf`
- Example: `AC146PART001.pdf`, `AC147PART215.pdf`
- Each PDF is placed inside its corresponding PS folder

## Download Script

The universal download script maintains this structure automatically:

```bash
# Download entire district
./scripts/download_electoral_rolls.sh --district 13

# Download specific AC
./scripts/download_electoral_rolls.sh --district 13 --ac 146

# List available districts
./scripts/download_electoral_rolls.sh --list-districts

# List ACs in a district
./scripts/download_electoral_rolls.sh --list-acs 13
```

## Benefits of This Structure

1. **Hierarchical Organization**: Clear district → AC → PS hierarchy
2. **Easy Navigation**: Find specific polling stations by part number
3. **Metadata Preservation**: PS folder names preserve polling station information
4. **Scalability**: Can accommodate any number of districts and ACs
5. **Consistency**: Same structure across all districts
6. **Future-Proof**: Easy to add new districts or update existing ones

## Statistics (Current)

- **Total Districts**: 2
  - District 13 (Kolkata South): 7 ACs, 1,366 PDFs
  - District 9 (North 24 Parganas): 28 ACs, 6,567 PDFs
- **Total PDFs**: 7,933
- **Total PS Folders**: Matches total PDFs (one PS folder per part)

## Notes

- All PDFs are stored in `ALL/` folder, not scattered in multiple locations
- Old flat structures (without PS folders) have been reorganized
- Empty placeholder folders outside `ALL/` have been removed
- The `.gitkeep` file in `data/downloaded_pdfs/` preserves the directory in git while gitignoring PDF files
