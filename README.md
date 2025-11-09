# West Bengal Electoral Data Extraction Tool

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Electoral Roll](https://img.shields.io/badge/Electoral%20Roll-2002-green.svg)](https://ceowestbengal.nic.in)
[![SIR 2025](https://img.shields.io/badge/SIR-2025-orange.svg)](https://eci.gov.in)

A comprehensive, production-ready toolkit for downloading, extracting, parsing, and validating **West Bengal electoral roll data** from the **2002 base electoral roll** for **Special Intensive Revision (SIR) 2025** targeting the **Bidhansabha Legislative Assembly Election 2026**.

## 🔍 Keywords

`west bengal electoral roll` • `voter list extraction` • `election data scraping` • `pdf data extraction` • `india election data` • `electoral roll parser` • `voter registration data` • `assembly constituency data` • `polling booth data` • `epic number validation` • `eci gateway api` • `bidhansabha election 2026` • `sir 2025` • `python election tools` • `web scraping india` • `cid font decoding` • `bengal voter data` • `legislative assembly election`

## 🎯 Overview

This project provides **automated tools** for processing West Bengal electoral data:
- 📥 **Download** electoral roll PDFs from [CEO West Bengal](https://ceowestbengal.nic.in)
- 📄 **Extract** voter information from PDFs (handling CID font encoding)
- 🔍 **Parse** and structure voter data (Name, Age, EPIC, Address, Gender, etc.)
- ✅ **Validate** data against official [ECI Gateway API](https://electoralsearch.eci.gov.in)
- 💾 **Store** data in structured formats (SQLite, JSON, YAML, CSV, Excel)
- 🌐 **Web interface** for browsing, searching, and validation

### Why This Tool?

The official CEO West Bengal website presents several challenges for data access:

1. **CAPTCHA Barriers** 🔒
   - Official website requires CAPTCHA for each PDF download
   - This tool bypasses CAPTCHA by directly accessing PDF URLs
   - Enables automated batch downloading of hundreds of PDFs

2. **Unsearchable PDFs** 🚫
   - PDFs on the official website contain garbled/encoded text
   - Standard Ctrl+F search doesn't work on these PDFs
   - Text appears as: `*RXWDP%DQHUMHH` instead of `JOHN DOE`

3. **CID Font Decoding** 🔤
   - This tool implements comprehensive CID (Character Identifier) font mapping
   - Converts garbled characters to readable text automatically
   - Makes data searchable, sortable, and analyzable

4. **Data Validation** ✅
   - Cross-verifies extracted voter data against official ECI Gateway API
   - Ensures data accuracy and completeness
   - Validates EPIC numbers, names, and demographic information
   - Uses fuzzy matching (95% threshold) for name comparison
   - See `src/validator.py` for implementation details

5. **Structured Data Export** 💾
   - Converts unstructured PDF data into structured formats
   - Exports to SQLite, JSON, CSV, Excel for easy analysis
   - Maintains data integrity throughout the pipeline

**In short**: This tool makes publicly available electoral data actually usable for research, analysis, and transparency initiatives.

### Data Source Context

- **Base Electoral Roll**: 2002 (All extracted data is from 2002 base electoral roll)
- **Revision Type**: Special Intensive Revision (SIR) 2025
- **Target Election**: Bidhansabha (Legislative Assembly) Election 2026
- **Coverage**: 21 Districts, 294 Assembly Constituencies, 61,531+ Polling Parts
- **Official Sources**: CEO West Bengal & Election Commission of India (ECI)

## 📊 Project Statistics

### Achievements
- ✅ **229,487 voters** extracted from AC_139 (Belgachia East)
- ✅ **61,531 polling parts** cataloged across West Bengal
- ✅ **294 assembly constituencies** mapped
- ✅ **21 districts** covered
- ✅ **99.99% extraction accuracy** with robust error handling
- ✅ **100% API success rate** for metadata collection
- ✅ **~5,100 voters/minute** extraction speed

For detailed analytics, see **[ANALYTICS.md](ANALYTICS.md)**

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[SETUP_GUIDE.md](SETUP_GUIDE.md)** | Complete setup instructions, prerequisites, troubleshooting |
| **[ANALYTICS.md](ANALYTICS.md)** | Detailed statistics, performance metrics, data quality analysis |
| **[API.md](docs/API.md)** | ECI Gateway API reference and usage guide |
| **[PDF_FORMAT.md](docs/PDF_FORMAT.md)** | PDF structure, CID font decoding, extraction techniques |
| **[REPOSITORY_SUMMARY.md](REPOSITORY_SUMMARY.md)** | Technical overview, architecture, and codebase structure |
| **[LICENSE](LICENSE)** | MIT License with data privacy notice |

## 📈 Analytics Summary

### Extraction Results (AC_139 - Belgachia East)

| Metric | Value | Coverage |
|--------|-------|----------|
| **PDFs Downloaded** | 353 | 100% |
| **Voters Extracted** | 229,487 | - |
| **Age Data** | 229,464 | 99.99% |
| **EPIC Numbers** | 190,195 | 82.87% |
| **Gender Data** | 229,487 | 100% |
| **Address Data** | 228,900 | 99.74% |
| **Extraction Accuracy** | - | 99.99% |

### West Bengal Coverage

| Category | Count | Status |
|----------|-------|--------|
| **Districts** | 21 | ✅ All cataloged |
| **Assembly Constituencies** | 294 | ✅ All mapped |
| **Polling Parts** | 61,531+ | ✅ Complete metadata |
| **Voters (AC_139 only)** | 229,487 | ✅ Extracted & validated |

### Performance Metrics

- ⚡ **Extraction Speed**: ~5,100 voters/minute
- 💯 **API Success Rate**: 100% (316 API calls)
- 🎯 **Data Integrity**: 0% corruption, full validation
- 🔧 **Processing Time**: ~7.6 seconds per PDF

### Scaling Projections

Based on AC_139 statistics:
- **Full West Bengal**: ~67 million voters (estimated)
- **Total Storage**: ~200 GB for complete dataset
- **Processing Time**: ~220 hours for all 294 assemblies

*For complete analytics including data quality analysis, demographic insights, and technical metrics, see **[ANALYTICS.md](ANALYTICS.md)***

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  CEO WB Website │────▶│ PDF Download │────▶│ Text Extract│
└─────────────────┘     └──────────────┘     └─────────────┘
                                                      │
                                                      ▼
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   ECI Gateway   │◀────│  Validation  │◀────│   Parsing   │
│      API        │     │    Layer     │     │             │
└─────────────────┘     └──────────────┘     └─────────────┘
                                                      │
                                                      ▼
                                              ┌─────────────┐
                                              │ JSON/YAML   │
                                              │  Storage    │
                                              └─────────────┘
```

## 📦 Features

- **Smart PDF Downloading**: Batch download with resume capability
- **CID Font Decoding**: Handles special character encoding in PDFs
- **Robust Parsing**: Extracts 19+ fields per voter record
- **API Validation**: Cross-verify with official ECI data
- **Web Dashboard**: Interactive interface for data exploration
- **Modular Design**: Easy to extend and customize

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/partha-dhar/wb-electoral-data.git
cd wb-electoral-data

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy example config
cp config/config.example.yaml config/config.yaml

# Edit configuration (optional)
nano config/config.yaml
```

### Usage

#### 1. Download PDFs

```bash
# Download all PDFs for a specific Assembly Constituency
python scripts/download_pdfs.py --ac 139

# Download for entire district
python scripts/download_pdfs.py --district 10

# Download all West Bengal
python scripts/download_pdfs.py --all
```

#### 2. Extract Voter Data

```bash
# Extract from specific AC
python scripts/extract_voters.py --ac 139

# Batch extract all downloaded PDFs
python scripts/extract_voters.py --batch
```

#### 3. Validate Data

```bash
# Validate extracted data against ECI API
python scripts/validate_data.py --ac 139

# Generate validation report
python scripts/validate_data.py --ac 139 --report
```

#### 4. Verify with API (New!)

```bash
# Verify extracted voters using ECI's individual voter API
# Note: API has incomplete data, used only for verification
python scripts/verify_with_api.py --ac 139

# Custom delay between API calls (default: 0.5s)
python scripts/verify_with_api.py --ac 139 --delay 1.0

# View verification statistics
python scripts/verify_with_api.py --ac 139 --batch-size 50
```

**Why API Verification?**
- The ECI API endpoint (`get-eroll-data-2003`) returns individual voter data
- **No Bearer token required** - Works with basic headers only!
- Used for **verification purposes** as API data is incomplete (missing names)
- **Primary method remains PDF extraction** for complete data
- Verification results stored in SQLite database
- Rate limited: 50 requests/second (we use 2/second to be safe)

#### 5. Web Interface

```bash
# Start web server
python web/app.py

# Access at http://localhost:5000
```

## 📁 Project Structure

```
wb-electoral-data/
├── src/
│   ├── __init__.py
│   ├── downloader.py      # PDF downloading logic
│   ├── extractor.py       # Text extraction with CID decoding
│   ├── parser.py          # Voter data parsing
│   ├── validator.py       # ECI API validation
│   ├── storage.py         # JSON/YAML storage & SQLite DB
│   └── utils.py           # Helper functions
├── scripts/
│   ├── download_pdfs.py   # CLI for downloading
│   ├── extract_voters.py  # CLI for extraction
│   ├── validate_data.py   # CLI for validation
│   ├── verify_with_api.py # API verification (NEW!)
│   └── fetch_metadata.py  # Fetch district/AC metadata
├── web/
│   ├── app.py             # Flask web application
│   ├── templates/         # HTML templates
│   └── static/            # CSS, JS, images
├── config/
│   ├── config.yaml        # Main configuration
│   └── config.example.yaml
├── docs/
│   ├── API.md             # API documentation
│   ├── PDF_FORMAT.md      # PDF structure details
│   └── DEVELOPMENT.md     # Development guide
├── tests/
│   ├── test_downloader.py
│   ├── test_extractor.py
│   └── test_parser.py
├── .gitignore
├── requirements.txt
├── setup.py
├── LICENSE
└── README.md
```

## 🔧 Configuration

Edit `config/config.yaml`:

```yaml
# Data directories (excluded from git)
data_dir: ./data
pdf_dir: ./data/pdfs
output_dir: ./data/output

# API settings
eci_api:
  base_url: https://gateway-voters.eci.gov.in/api/v1/citizen/sir
  state_code: S25
  timeout: 30

# Download settings
download:
  concurrent: 5
  retry_attempts: 3
  delay: 1.0
```

## 📊 Data Format

### Output JSON Structure

```json
{
  "metadata": {
    "ac_number": 139,
    "ac_name": "BELGACHIA EAST",
    "part_number": 1,
    "extraction_date": "2025-11-10",
    "total_voters": 650
  },
  "voters": [
    {
      "serial_no": 1,
      "name": "JOHN DOE",
      "relative_name": "ROBERT DOE",
      "relation_type": "Father",
      "house_no": "123/A",
      "age": 45,
      "gender": "M",
      "epic_no": "WB/12/345/678901"
    }
  ]
}
```

## 🌐 Web Interface

The web interface provides:
- **Browse**: Navigate districts → assemblies → parts
- **Search**: Find voters by name, EPIC, or address
- **Validate**: Check against official ECI API
- **Export**: Download data in JSON/CSV/Excel
- **Statistics**: Visualize voter demographics

## 🔒 Data Privacy & Compliance

⚠️ **Important**: This tool processes publicly available electoral roll data from official government sources.

**Usage Guidelines**:
- ✅ Educational and research purposes
- ✅ Electoral analysis and demographic studies
- ✅ Transparency and accountability initiatives
- ❌ Commercial exploitation without authorization
- ❌ Voter privacy violations
- ❌ Unauthorized data selling or sharing

**Compliance**:
- Follow Election Commission of India (ECI) guidelines
- Respect data protection regulations
- Use data responsibly and ethically
- Maintain data accuracy and integrity

## 🤝 Contributing

Contributions are welcome! We appreciate help with:
- 🐛 Bug fixes and error handling improvements
- 📚 Documentation enhancements
- ✨ New features and functionality
- 🧪 Test coverage and quality assurance
- 🌐 Internationalization and localization

**Before contributing**, please:
1. Read **[SETUP_GUIDE.md](SETUP_GUIDE.md)** for development setup
2. Check existing issues and pull requests
3. Follow the coding standards (PEP 8, Black formatting)
4. Add tests for new features
5. Update documentation accordingly

**Contribution Process**:
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request with detailed description

## 🛠️ Technology Stack

| Category | Technologies |
|----------|-------------|
| **Language** | Python 3.8+ |
| **PDF Processing** | pdfplumber, PyPDF2 |
| **Web Framework** | Flask, Jinja2 |
| **Database** | SQLite3, pandas |
| **HTTP Client** | requests, urllib3 |
| **Data Formats** | JSON, YAML, CSV, Excel |
| **Testing** | pytest, unittest |
| **Deployment** | Docker-ready, WSGI compatible |

## 🎓 Use Cases

This toolkit is valuable for:

1. **Electoral Research**: Analyze voter demographics and distribution patterns
2. **Academic Studies**: Research on electoral behavior and political geography
3. **Civic Tech Projects**: Build transparency and accountability tools
4. **Data Journalism**: Investigate electoral trends and anomalies
5. **Government Analytics**: Support policy planning and resource allocation
6. **NGO Initiatives**: Monitor electoral processes and voter registration drives

## 🚀 Deployment Options

### Local Development
```bash
# Quick start with setup script
./setup.sh
source venv/bin/activate
python web/app.py
```

### Production Deployment
- **Web Server**: Nginx + Gunicorn
- **Database**: PostgreSQL (for larger datasets)
- **Caching**: Redis
- **Monitoring**: Prometheus + Grafana
- **Containerization**: Docker + Docker Compose

See **[SETUP_GUIDE.md](SETUP_GUIDE.md)** for detailed deployment instructions.

## 📝 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

**Additional Terms**:
- Data sourced from public government websites (CEO West Bengal, ECI)
- Use responsibly and comply with local regulations
- Attribution required for derivative works
- No warranty provided - use at your own risk

## 🙏 Acknowledgments

- **Election Commission of India (ECI)** - For providing electoral data and API access
- **CEO West Bengal** - For maintaining the electoral roll website and PDF archives
- **Python Community** - For excellent libraries (pdfplumber, Flask, pandas)
- **Contributors** - Everyone who helps improve this toolkit
- **Open Source Community** - For inspiration and best practices

## 📧 Contact & Support

### Get Help
- 📖 **Documentation**: Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for setup issues
- 🐛 **Bug Reports**: Open an issue on GitHub with detailed description
- 💡 **Feature Requests**: Submit an issue with "enhancement" label
- 💬 **Discussions**: Use GitHub Discussions for questions and ideas

### Stay Updated
- ⭐ **Star this repository** to get updates
- 👁️ **Watch releases** for new versions
- 🍴 **Fork** to create your own customizations

## 🔗 Related Resources

### Official Sources
- [CEO West Bengal](https://ceowestbengal.nic.in) - Electoral Roll Website
- [ECI Gateway](https://electoralsearch.eci.gov.in) - Official Voter Search API
- [Election Commission of India](https://eci.gov.in) - National Electoral Body

### Documentation
- [Setup Guide](SETUP_GUIDE.md) - Installation and configuration
- [Analytics Report](ANALYTICS.md) - Data statistics and insights
- [API Documentation](docs/API.md) - ECI Gateway API reference
- [PDF Format Guide](docs/PDF_FORMAT.md) - PDF structure and decoding
- [Repository Summary](REPOSITORY_SUMMARY.md) - Technical overview

### Related Projects
- Electoral roll analysis tools for other Indian states
- Voter registration verification systems
- Political boundary mapping tools
- Demographic analysis frameworks

## 🏷️ Tags

`#WestBengal` `#ElectoralRoll` `#VoterData` `#IndiaElections` `#OpenData` `#CivicTech` `#ElectionData` `#Python` `#DataExtraction` `#PDFParsing` `#APIIntegration` `#BidhansabhaElection2026` `#SIR2025` `#ElectionCommissionOfIndia` `#DemocracyData` `#TransparencyTools` `#ElectoralAnalysis` `#LegislativeAssembly`

---

<div align="center">

**West Bengal Electoral Data Extraction Tool**

*Empowering transparency and research through open electoral data*

**[Documentation](SETUP_GUIDE.md)** • **[Analytics](ANALYTICS.md)** • **[API Reference](docs/API.md)** • **[License](LICENSE)**

</div>

---

**Disclaimer**: This tool processes publicly available electoral roll data for educational, research, and transparency purposes. Users must comply with Election Commission of India guidelines and local data protection regulations. The authors are not responsible for misuse of this tool or the data it processes. Always verify data accuracy from official sources.
