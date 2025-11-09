# Setup Guide

Complete setup instructions for the West Bengal Electoral Data Extraction Tool.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Development Setup](#development-setup)
- [Troubleshooting](#troubleshooting)
- [Testing](#testing)

---

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows 10+
- **Python**: 3.8 or higher
- **RAM**: Minimum 4GB (8GB recommended for large batch processing)
- **Disk Space**: At least 10GB free space for PDFs and extracted data

### Required Software

1. **Python 3.8+**
   ```bash
   # Check Python version
   python3 --version
   
   # If not installed:
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3 python3-pip python3-venv
   
   # macOS (using Homebrew)
   brew install python@3.9
   
   # Windows
   # Download from https://www.python.org/downloads/
   ```

2. **Git** (for cloning the repository)
   ```bash
   # Check Git version
   git --version
   
   # If not installed:
   # Ubuntu/Debian
   sudo apt-get install git
   
   # macOS
   brew install git
   
   # Windows
   # Download from https://git-scm.com/downloads
   ```

3. **SQLite3** (usually pre-installed)
   ```bash
   # Check SQLite version
   sqlite3 --version
   
   # If not installed:
   # Ubuntu/Debian
   sudo apt-get install sqlite3
   
   # macOS (pre-installed, or via Homebrew)
   brew install sqlite
   ```

---

## Installation

### Method 1: Automated Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/wb-electoral-data.git
   cd wb-electoral-data
   ```

2. **Run the automated setup script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   The script will:
   - Create a Python virtual environment
   - Install all dependencies
   - Create necessary directories
   - Set up the configuration file
   - Make CLI scripts executable

3. **Activate the virtual environment**
   ```bash
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

### Method 2: Manual Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/partha-dhar/wb-electoral-data.git
   cd wb-electoral-data
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Install the package in development mode**
   ```bash
   pip install -e .
   ```

5. **Create necessary directories**
   ```bash
   mkdir -p pdfs data output api logs
   ```

6. **Set up configuration**
   ```bash
   cp config/config.example.yaml config/config.yaml
   ```

7. **Make scripts executable** (Linux/macOS only)
   ```bash
   chmod +x scripts/*.py
   ```

---

## Configuration

### Basic Configuration

Edit `config/config.yaml` to customize the tool:

```yaml
# PDF Download Settings
download:
  base_url: "https://ceowestbengal.nic.in"
  output_dir: "pdfs"
  concurrent_downloads: 5
  retry_attempts: 3
  timeout: 30

# Extraction Settings
extraction:
  min_age: 18
  max_age: 120
  validate_epic: true

# Storage Settings
storage:
  db_path: "data/voters.db"
  json_output: "output/voters.json"
  compression: true

# API Settings
api:
  base_url: "https://electoralsearch.eci.gov.in"
  timeout: 30
  rate_limit: 10  # requests per minute

# Logging Settings
logging:
  level: "INFO"
  file: "logs/app.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Advanced Configuration

For detailed configuration options, see:
- `config/config.example.yaml` - All available settings with comments
- `docs/API.md` - API endpoint configuration
- `README.md` - Configuration section

---

## Quick Start

### 1. Fetch Metadata (Districts, Assemblies, Polling Parts)

```bash
# Fetch all districts
python scripts/fetch_metadata.py --type districts

# Fetch assemblies for a specific district
python scripts/fetch_metadata.py --type assemblies --district-code 19

# Fetch polling parts for an assembly
python scripts/fetch_metadata.py --type parts --ac-number 139
```

### 2. Download PDFs

```bash
# Download PDFs for a specific assembly
python scripts/download_pdfs.py --ac-number 139 --output-dir pdfs/AC_139

# Download with custom settings
python scripts/download_pdfs.py \
  --ac-number 139 \
  --output-dir pdfs/AC_139 \
  --concurrent 10 \
  --retry 5
```

### 3. Extract Voter Data

```bash
# Extract from a single PDF
python scripts/extract_voters.py \
  --input pdfs/AC_139/part_001.pdf \
  --output data/voters.db

# Batch extract from all PDFs in a directory
python scripts/extract_voters.py \
  --input pdfs/AC_139 \
  --output data/voters.db \
  --batch
```

### 4. Validate Data (Optional)

```bash
# Validate extracted data against ECI API
python scripts/validate_data.py \
  --input data/voters.db \
  --output output/validation_report.json
```

---

## Usage Examples

### Example 1: Complete Workflow for One Assembly

```bash
# Activate virtual environment
source venv/bin/activate

# Fetch metadata
python scripts/fetch_metadata.py --type parts --ac-number 139

# Download PDFs
python scripts/download_pdfs.py --ac-number 139 --output-dir pdfs/AC_139

# Extract voters
python scripts/extract_voters.py \
  --input pdfs/AC_139 \
  --output data/ac_139_voters.db \
  --batch

# Export to JSON
python -c "
from src.storage import StorageManager
storage = StorageManager('config/config.yaml')
storage.export_to_json('data/ac_139_voters.db', 'output/ac_139_voters.json')
"

# Export to CSV
python -c "
from src.storage import StorageManager
storage = StorageManager('config/config.yaml')
storage.export_to_csv('data/ac_139_voters.db', 'output/ac_139_voters.csv')
"
```

### Example 2: Using the Web Interface

```bash
# Start the web server
cd web
python app.py

# Open browser to http://localhost:5000
# Use the web interface to:
# - Browse voters
# - Search by name/EPIC
# - Validate data
# - Export to CSV/Excel
```

### Example 3: Programmatic Usage

```python
from src.downloader import PDFDownloader
from src.extractor import PDFExtractor
from src.parser import VoterParser
from src.storage import StorageManager
import yaml

# Load configuration
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Download PDFs
downloader = PDFDownloader(config)
pdf_urls = [...]  # List of PDF URLs
downloaded = downloader.download_batch(pdf_urls, "pdfs/AC_139")

# Extract text from PDFs
extractor = PDFExtractor(config)
text = extractor.extract_text("pdfs/AC_139/part_001.pdf")

# Parse voter data
parser = VoterParser(config)
voters = parser.parse_voters(text)

# Save to database
storage = StorageManager(config)
storage.save_voters(voters, "data/voters.db", ac_number=139)

# Export to JSON
storage.export_to_json("data/voters.db", "output/voters.json")
```

---

## Development Setup

### Setting Up Development Environment

1. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov black flake8 mypy pylint
   ```

2. **Install pre-commit hooks** (optional)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

3. **Configure IDE** (VS Code example)
   
   Create `.vscode/settings.json`:
   ```json
   {
     "python.pythonPath": "venv/bin/python",
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "python.formatting.provider": "black",
     "editor.formatOnSave": true
   }
   ```

### Code Style

This project follows PEP 8 with Black formatting:

```bash
# Format code
black src/ scripts/ web/

# Check linting
flake8 src/ scripts/ web/

# Type checking
mypy src/ scripts/ web/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Format code (`black .`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## Troubleshooting

### Common Issues

#### 1. SSL Certificate Errors

**Problem**: `SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]`

**Solution**:
```bash
# Install certifi
pip install --upgrade certifi

# Or disable SSL verification (not recommended for production)
# Edit config/config.yaml:
download:
  verify_ssl: false
```

#### 2. CID Font Decoding Issues

**Problem**: Garbled text in extracted data (e.g., `*RXWDP%DQHUMHH`)

**Solution**: The tool automatically handles CID font decoding. If issues persist:
- Check PDF version (some older PDFs may use different encoding)
- Try alternative extraction method in `src/extractor.py`
- See `docs/PDF_FORMAT.md` for detailed decoding information

#### 3. Memory Issues During Batch Processing

**Problem**: `MemoryError` when processing large batches

**Solution**:
```bash
# Reduce concurrent downloads
python scripts/download_pdfs.py --concurrent 3

# Process PDFs in smaller batches
python scripts/extract_voters.py --input pdfs/batch1 --batch
python scripts/extract_voters.py --input pdfs/batch2 --batch
```

#### 4. Database Locked Errors

**Problem**: `sqlite3.OperationalError: database is locked`

**Solution**:
```bash
# Close other programs accessing the database
# Or increase SQLite timeout in config:
storage:
  timeout: 30
```

#### 5. Rate Limiting on API Calls

**Problem**: API returns 429 (Too Many Requests)

**Solution**:
```yaml
# Edit config/config.yaml
api:
  rate_limit: 5  # Reduce requests per minute
  retry_attempts: 5
  backoff_factor: 2  # Exponential backoff
```

#### 6. Python Version Mismatch

**Problem**: `SyntaxError` or module import errors

**Solution**:
```bash
# Check Python version
python3 --version

# Ensure using Python 3.8+
# Create virtual environment with specific version
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Debug Mode

Enable debug logging for detailed information:

```yaml
# config/config.yaml
logging:
  level: "DEBUG"
  file: "logs/debug.log"
```

View logs:
```bash
tail -f logs/debug.log
```

### Getting Help

- **Documentation**: Check `docs/` folder
- **Issues**: Open an issue on GitHub
- **Discussions**: GitHub Discussions tab
- **API Reference**: `docs/API.md`

---

## Testing

### Unit Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::test_parse_voter_name
```

### Integration Tests

```bash
# Test complete workflow
pytest tests/test_integration.py

# Test with real PDFs (requires sample PDFs)
pytest tests/test_integration.py --use-real-pdfs
```

### Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# View in browser
open htmlcov/index.html
```

### Performance Testing

```bash
# Benchmark extraction speed
python scripts/extract_voters.py \
  --input pdfs/sample \
  --benchmark \
  --output /tmp/benchmark.db
```

---

## Next Steps

After setup, you can:

1. **Explore the codebase**
   - Read `README.md` for project overview
   - Check `docs/` for detailed documentation
   - Review `src/` modules for implementation details

2. **Run examples**
   - Follow usage examples above
   - Try the web interface
   - Experiment with different configurations

3. **Contribute**
   - Fix bugs
   - Add features
   - Improve documentation
   - Write tests

4. **Deploy**
   - Set up production database (PostgreSQL)
   - Configure reverse proxy (Nginx)
   - Enable HTTPS
   - Set up monitoring

---

## Additional Resources

- **README.md**: Project overview and quick start
- **docs/API.md**: ECI Gateway API documentation
- **docs/PDF_FORMAT.md**: PDF structure and parsing details
- **ANALYTICS.md**: Data statistics and insights
- **LICENSE**: MIT License with data privacy notice

For more help, visit the [GitHub repository](https://github.com/partha-dhar/wb-electoral-data).
