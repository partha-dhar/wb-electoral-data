# PDF Format Documentation

## Electoral Roll PDF Structure

West Bengal electoral roll PDFs follow a specific format that requires special handling for text extraction.

## Character Encoding Issues

### CID Font Encoding

PDFs use CID (Character Identifier) fonts which encode characters differently:

```
(cid:17) → .  (period)
(cid:18) → /  (slash)
(cid:19) → 0
(cid:20) → 1
(cid:21) → 2
...
(cid:28) → 9
```

### Shifted Characters

Some characters are shifted by -3 in ASCII:

```
D → a
E → b
F → c
G → d
H → e
...
Z → w
```

### Special Characters

```
$ → A
% → B
& → C
* → G
: → W
```

## Example Raw Text

```
*RXWDP%DQHUMHH
Dge: 5(cid:20)
Epic: Wb(cid:20)(cid:19)(cid:18)(cid:20)(cid:22)(cid:25)(cid:18)(cid:25)(cid:27)(cid:20)(cid:24)(cid:25)(cid:25)
```

## Decoded Text

```
JOHN DOE
Age: 45
Epic: WB/12/345/678901
```

## PDF Layout

### Page Header
- Assembly Constituency Number and Name
- Part Number
- Section Name
- Polling Station Details

### Voter Records

Each voter record typically contains:

```
Serial No: 1
Name: VOTER NAME
Relation: Father/Mother/Husband: RELATIVE NAME
House No: XX/XX
Age: XX
Gender: M/F
EPIC No: WB/XX/XXX/XXXXXX
```

## Field Extraction Patterns

### Name
- Usually on first line after serial number
- All uppercase
- May contain special characters

### Relation
- Pattern: `(Father|Mother|Husband):\s*NAME`
- Case insensitive

### Age
- Pattern: `Age:\s*(\d+)`
- Range: 18-120

### EPIC Number
- Pattern: `WB[/\d]+` or variations
- Format: WB/12/345/678901
- May be encoded with CID characters

### House Number
- Pattern: Various formats (5/1, 5-1, 5, etc.)
- May include letters

### Gender
- Pattern: `Gender:\s*([MF])`
- M = Male, F = Female

## Text Extraction Tips

1. **Use pdfplumber**: Best library for handling CID fonts
2. **Decode in layers**: First CID, then shifted chars
3. **Line-by-line**: Process text line by line
4. **Context-aware**: Use surrounding text to validate fields
5. **Error handling**: Some PDFs may have corrupted data

## Common Issues

### Issue 1: Garbled Text
```
*RKQ'RH → JOHN DOE
```
**Solution**: Apply character mapping

### Issue 2: Missing Slashes in EPIC
```
Wb1234567890 → WB/12/345/678901
```
**Solution**: Parse and reformat

### Issue 3: Age Outside Range
```
Age: 5(cid:20) → Age: 52
```
**Solution**: Decode CID characters first

### Issue 4: Merged Fields
```
House:5/1Age:52Gender:M
```
**Solution**: Use regex with flexible spacing

## Validation

After extraction, validate each field:

```python
def validate_voter(voter):
    # Name required
    if not voter.get('name'):
        return False
    
    # Age in range
    age = voter.get('age')
    if age and not (18 <= age <= 120):
        return False
    
    # Gender valid
    gender = voter.get('gender')
    if gender and gender not in ['M', 'F']:
        return False
    
    # EPIC format
    epic = voter.get('epic_no')
    if epic and not epic.startswith('WB/'):
        return False
    
    return True
```

## Sample Code

```python
import pdfplumber
import re

def decode_cid(text):
    """Decode CID characters"""
    cid_map = {
        'cid:17': '.', 'cid:18': '/',
        'cid:19': '0', 'cid:20': '1',
        # ... more mappings
    }
    
    for cid, char in cid_map.items():
        text = text.replace(f'({cid})', char)
    
    return text

def decode_shifted(text):
    """Decode shifted characters"""
    char_map = {
        'D': 'a', 'E': 'b', 'F': 'c',
        # ... more mappings
    }
    
    return ''.join(char_map.get(c, c) for c in text)

def extract_voter(lines, start_idx):
    """Extract single voter record"""
    voter = {}
    
    # Extract serial and name
    match = re.match(r'^(\d+)\s+(.+)$', lines[start_idx])
    if match:
        voter['serial_no'] = int(match.group(1))
        voter['name'] = decode_shifted(decode_cid(match.group(2)))
    
    # Extract other fields...
    
    return voter

# Main extraction
with pdfplumber.open('part_001.pdf') as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        lines = text.split('\n')
        
        for line in lines:
            decoded = decode_shifted(decode_cid(line))
            # Process decoded line...
```

## Tips for Success

1. **Test on sample PDFs first**: Understand the exact format
2. **Log decode errors**: Track which characters aren't mapping
3. **Validate continuously**: Check each field after extraction
4. **Handle variations**: Different parts may have slight format differences
5. **Cross-reference with API**: Validate voter counts against official data

## Future Improvements

- Machine learning for character recognition
- Layout-based extraction using coordinates
- Automated format detection
- Multi-language support
- Table extraction for structured data
