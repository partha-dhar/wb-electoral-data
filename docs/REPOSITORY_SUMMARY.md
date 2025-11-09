# West Bengal Electoral Data - Repository Summary

## 📁 Repository Structure

```
wb-electoral-data/
├── README.md                  # Main documentation
├── LICENSE                    # MIT License
├── requirements.txt           # Python dependencies
├── setup.py                   # Package setup
├── .gitignore                 # Git ignore rules
│
├── config/
│   └── config.example.yaml    # Configuration template
│
├── src/                       # Core Python modules
│   ├── __init__.py
│   ├── downloader.py         # PDF downloading
│   ├── extractor.py          # Text extraction (CID decoding)
│   ├── parser.py             # Voter data parsing
│   ├── validator.py          # ECI API validation
│   ├── storage.py            # JSON/YAML storage
│   └── utils.py              # Helper functions
│
├── scripts/                   # CLI scripts
│   ├── download_pdfs.py      # Download PDFs
│   ├── extract_voters.py     # Extract voter data
│   ├── validate_data.py      # Validate against API
│   └── fetch_metadata.py     # Fetch metadata from API
│
├── web/                       # Web interface
│   ├── app.py                # Flask application
│   ├── templates/
│   │   └── index.html        # Main web UI
│   └── static/               # CSS, JS (future)
│
└── docs/                      # Documentation
    ├── API.md                # ECI API documentation
    └── PDF_FORMAT.md         # PDF structure guide
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/partha-dhar/wb-electoral-data.git
cd wb-electoral-data

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy config
cp config/config.example.yaml config/config.yaml
```

### 2. Fetch Metadata

```bash
# Fetch all districts and assemblies
python scripts/fetch_metadata.py --all

# Fetch parts for specific AC
python scripts/fetch_metadata.py --parts 139
```

### 3. Download PDFs

```bash
# Download for specific AC
python scripts/download_pdfs.py --ac 139

# Download entire district
python scripts/download_pdfs.py --district 10

# Download all West Bengal
python scripts/download_pdfs.py --all
```

### 4. Extract Voter Data

```bash
# Extract from single PDF
python scripts/extract_voters.py --pdf data/pdfs/AC_139/part_001.pdf

# Extract entire AC
python scripts/extract_voters.py --ac 139

# Batch extract all
python scripts/extract_voters.py --batch
```

### 5. Validate Data

```bash
# Validate specific part
python scripts/validate_data.py --ac 139 --part 1

# Validate all parts for AC
python scripts/validate_data.py --ac 139

# Generate validation report
python scripts/validate_data.py --ac 139 --part 1 --report
```

### 6. Web Interface

```bash
# Start web server
python web/app.py

# Access at http://localhost:5000
```

## 🔑 Key Features

### 1. Smart PDF Downloading
- Batch download with concurrency control
- Resume capability for interrupted downloads
- SSL handling for legacy servers
- Progress tracking

### 2. CID Font Decoding
- Handles special PDF character encoding
- Decodes (cid:19) → 0, (cid:20) → 1, etc.
- Character shifting (D→a, E→b, etc.)
- Special character mapping

### 3. Robust Parsing
- Extracts 19+ fields per voter
- Validates age, gender, EPIC format
- Handles various PDF layouts
- Error recovery

### 4. API Validation
- Cross-verifies with ECI Gateway API
- Fuzzy matching for names
- Exact matching for IDs/numbers
- Match score calculation
- Count comparison

### 5. Flexible Storage
- JSON or YAML output
- Organized by district/AC
- Metadata preservation
- Export to CSV/Excel
- Compression support

### 6. Web Dashboard
- Browse by district/AC/part
- Search by name or EPIC
- Validate against API
- View statistics
- Export data

## 📊 Data Flow

```
CEO WB Website
      ↓
[Download PDFs] ← scripts/download_pdfs.py
      ↓
[Extract Text] ← src/extractor.py (CID decoding)
      ↓
[Parse Voters] ← src/parser.py
      ↓
[Store JSON/YAML] ← src/storage.py
      ↓
[Validate with ECI API] ← src/validator.py
      ↓
[Web Interface] ← web/app.py
```

## 🔧 Configuration

Key settings in `config/config.yaml`:

```yaml
# Data directories (excluded from git)
directories:
  data_dir: ./data
  pdf_dir: ./data/pdfs
  output_dir: ./data/output

# ECI API
eci_api:
  base_url: https://gateway-voters.eci.gov.in/api/v1/citizen/sir
  state_code: S25

# Download settings
download:
  concurrent_downloads: 5
  retry_attempts: 3

# Extraction settings
extraction:
  min_age: 18
  max_age: 120

# Validation settings
validation:
  match_threshold: 0.95
  sample_size: 100

# Storage settings
storage:
  format: json  # or yaml
  compression: false
```

## 📝 Module Overview

### src/downloader.py
- `PDFDownloader`: Download PDFs from CEO WB website
- Methods: `download_pdf()`, `download_ac_pdfs()`, `download_all()`

### src/extractor.py
- `TextExtractor`: Extract text from PDFs with CID decoding
- Methods: `extract_text_from_pdf()`, `decode_text()`, `extract_with_layout()`

### src/parser.py
- `VoterParser`: Parse voter information from text
- Methods: `parse_voter_record()`, `parse_pdf_lines()`, `extract_statistics()`

### src/validator.py
- `DataValidator`: Validate against ECI API
- Methods: `validate_voter()`, `validate_batch()`, `compare_counts()`

### src/storage.py
- `DataStorage`: Store data in JSON/YAML
- Methods: `save_voters()`, `load_voters()`, `export_to_csv()`, `create_index()`

### src/utils.py
- Helper functions: `load_config()`, `setup_logging()`, `format_epic_number()`
- `SSLContextAdapter`: Handle legacy SSL servers
- `ProgressTracker`: Track batch operation progress

## 🌐 Web API Endpoints

```
GET  /api/districts                           # List all districts
GET  /api/assemblies?district={no}            # List assemblies
GET  /api/parts/{ac_number}                   # List parts for AC
GET  /api/voters/{ac_number}/{part_number}    # Get voter data
GET  /api/search?q={query}&ac={ac_number}     # Search voters
GET  /api/validate/{ac_number}/{part_number}  # Validate data
GET  /api/export/{ac_number}/{part_number}    # Export data
GET  /api/stats                               # Overall statistics
```

## 🔐 Data Privacy

⚠️ **Important Considerations:**

1. This tool processes **publicly available** electoral roll data
2. Use only for **legitimate purposes**
3. Respect voter **privacy** and data protection rights
4. Do NOT use for **commercial purposes** without authorization
5. Follow **Election Commission of India** guidelines
6. The data directory is **excluded from git** by default

## 🧪 Testing

```bash
# Test metadata fetching
python scripts/fetch_metadata.py --districts

# Test single PDF extraction
python scripts/extract_voters.py --pdf sample.pdf

# Test validation
python scripts/validate_data.py --ac 139 --part 1 --sample 5

# Test web interface
python web/app.py
```

## 📦 Dependencies

Core:
- `requests` - HTTP requests
- `pdfplumber` - PDF text extraction
- `beautifulsoup4` - HTML parsing
- `pyyaml` - YAML support
- `flask` - Web framework

Optional:
- `pandas` - Data analysis
- `openpyxl` - Excel export

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- Election Commission of India
- CEO West Bengal
- Open source community

## 📧 Support

- Issues: GitHub Issues
- Documentation: See docs/ folder
- Examples: Check scripts/ folder

---

**Created**: November 2025  
**Version**: 1.0.0  
**Python**: 3.8+  

**Ready for GitHub! 🚀**
