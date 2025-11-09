# API Verification Quick Reference

## 🎉 What We've Added

A complete voter data verification system using the newly discovered ECI API endpoint!

### Key Features:
- ✅ Verifies extracted PDF data against official ECI API
- ✅ **No authentication required** - works without Bearer token
- ✅ Handles legacy SSL automatically
- ✅ Rate-limited to respect server constraints (2 req/sec)
- ✅ Stores verification results in SQLite database
- ✅ Comprehensive statistics and reporting

## 🚀 Quick Start

### 1. Verify Voters for an AC

```bash
python scripts/verify_with_api.py --ac 139
```

This will:
- Fetch all voters for AC 139 from your database
- Check each voter against the ECI API
- Store verification results (verified/not_found/mismatch)
- Generate comprehensive statistics

### 2. Custom Options

```bash
# Slower rate (1 request/second for safety)
python scripts/verify_with_api.py --ac 139 --delay 1.0

# Larger batch size (faster commits)
python scripts/verify_with_api.py --ac 139 --batch-size 200

# Debug mode
python scripts/verify_with_api.py --ac 139 --log-level DEBUG

# Custom database path
python scripts/verify_with_api.py --ac 139 --db-path /path/to/voters.db
```

## 📊 What Gets Verified

The API returns:
- ✅ EPIC Number (e.g., "WB/20/139/000214")
- ✅ Age (e.g., "47")
- ✅ AC Name (e.g., "BELGACHIA EAST")
- ✅ Part Name (e.g., "St.Marrys Orphanage")
- ⚠️ Names are **empty/missing** (API limitation)
- ⚠️ Gender often **empty**

## 🔍 Verification Logic

1. **Verified**: EPIC number matches exactly, age matches (±1 year tolerance)
2. **Not Found**: API returns no record for this serial number
3. **Mismatch**: API returns data but EPIC/age doesn't match

## 📈 Output Example

```
================================================================================
VERIFICATION SUMMARY
================================================================================
Assembly Constituency: AC 139
Total Voters: 229,487
✓ Verified: 185,432 (80.82%)
✗ Not Found: 35,821 (15.61%)
⚠ Mismatched: 8,234 (3.57%)
⚠ Errors: 0
================================================================================
```

## 💾 Database Schema

Verification adds these columns to `voters` table:

```sql
verified BOOLEAN DEFAULT NULL          -- TRUE/FALSE/NULL
verification_date TIMESTAMP             -- When verified
api_data TEXT                          -- JSON response from API
```

## 🔬 Test the API

Before running full verification, test the API:

```bash
python3 test_api.py
```

This will:
- Make a single API request
- Show response structure
- Verify SSL configuration works
- Display available data fields

## ⚠️ Important Notes

### Rate Limiting
- **API Limit**: 50 requests/second burst capacity
- **Our Default**: 2 requests/second (conservative)
- **Recommendation**: Use default for large batches, increase for small tests

### Data Limitations
- **API has incomplete data** (names missing)
- **PDF extraction remains primary method**
- **Use API for verification only, not data extraction**

### SSL Issues
- ECI server uses legacy SSL renegotiation
- Our script handles this automatically with `LegacySSLAdapter`
- You may see SSL warnings - this is expected and handled

## 🔐 Authentication

**Great News**: The API works **WITHOUT** authentication!

Required headers (all public):
```python
{
    "Accept": "application/json",
    "Content-Type": "application/json",
    "CurrentRole": "citizen",
    "PLATFORM-TYPE": "ECIWEB",
    "applicationName": "VSP",
    "channelidobo": "VSP"
}
```

No Bearer token, no API key, no registration needed!

## 📚 API Details

**Endpoint**: `https://gateway-s2-blo.eci.gov.in/api/v1/elastic-sir/get-eroll-data-2003`

**Method**: POST

**Payload**:
```json
{
  "oldStateCd": "S25",
  "oldAcNo": "139",
  "oldPartNo": "1",
  "oldPartSerialNo": "1"
}
```

**Response**:
```json
{
  "status": "Success",
  "statusCode": 200,
  "message": "Record Found Successfully",
  "payload": [{
    "epicNumber": "WB/20/139/000214",
    "age": "47",
    "oldAcName": "BELGACHIA EAST",
    // ... other fields
  }]
}
```

## 🛠️ Troubleshooting

### Issue: SSL Error
**Solution**: Script handles this automatically. If still failing, check urllib3 version.

### Issue: Empty Responses
**Cause**: API has incomplete data for some records.
**Solution**: This is normal. Verification marks these as "not_found".

### Issue: Slow Performance
**Cause**: Default delay is 0.5s per request.
**Solution**: 
- Don't reduce delay below 0.2s (risk rate limiting)
- For 229,487 voters at 0.5s = ~32 hours
- Consider running overnight or in batches

### Issue: Database Locked
**Cause**: Multiple processes accessing database.
**Solution**: Run only one verification process at a time.

## 📖 Further Reading

- **README.md**: Overview and usage guide
- **ANALYTICS.md**: API discovery details and statistics
- **docs/API.md**: Complete API documentation
- **src/storage.py**: Database implementation

## 🎯 Next Steps

1. ✅ **Done**: API discovery and testing
2. ✅ **Done**: Implementation and documentation
3. ⏳ **TODO**: Run verification on AC_139
4. ⏳ **TODO**: Generate verification statistics
5. ⏳ **TODO**: Compare PDF vs API data quality
6. ⏳ **TODO**: Document findings in ANALYTICS.md

## 💡 Pro Tips

1. **Test First**: Run `test_api.py` before large verification jobs
2. **Start Small**: Verify a single part before full AC
3. **Monitor Progress**: Use INFO log level for progress tracking
4. **Check Stats**: Review verification statistics after completion
5. **Compare Data**: Use verification to validate PDF extraction quality

---

**Need Help?**
- Check documentation in `README.md` and `ANALYTICS.md`
- Review script help: `python scripts/verify_with_api.py --help`
- Examine test script: `test_api.py` for API examples

**Report Issues**:
- GitHub Issues: https://github.com/partha-dhar/wb-electoral-data/issues
