# ECI Gateway API Documentation

## Overview

The ECI (Election Commission of India) Gateway API provides access to electoral roll metadata and voter information.

**Base URL**: `https://gateway-voters.eci.gov.in/api/v1/citizen/sir`

**State Code (West Bengal)**: `S25`

## Authentication

⚠️ **Important**: These metadata endpoints work **WITHOUT** bearer token authentication.

## Required Headers

```http
PLATFORM-TYPE: ECIWEB
applicationName: VSP
state: S25
```

## Endpoints

### 1. Get Districts

Fetches all districts for a state.

```http
GET /getDistrict
```

**Parameters:**
- `state_cd` (required): State code (e.g., S25)

**Response:**
```json
{
  "status": "success",
  "payload": [
    {
      "districtNo": 1,
      "distName": "COOCHBEHAR"
    }
  ]
}
```

### 2. Get Assemblies

Fetches all assembly constituencies for a state.

```http
GET /getAsmbly
```

**Parameters:**
- `state_cd` (required): State code (e.g., S25)

**Response:**
```json
{
  "status": "success",
  "payload": [
    {
      "acNo": 1,
      "acName": "MEKHLIGANJ",
      "distNo": 1
    }
  ]
}
```

### 3. Get Parts by Assembly

Fetches all polling parts for an assembly constituency.

```http
GET /getPartByAc
```

**Parameters:**
- `state_cd` (required): State code (e.g., S25)
- `ac_no` (required): Assembly constituency number

**Response:**
```json
{
  "status": "success",
  "payload": [
    {
      "partNo": 1,
      "partName": "Polling Station Name",
      "totalVoters": 650,
      "maleVoters": 325,
      "femaleVoters": 325
    }
  ]
}
```

## Example Usage

### Python with requests

```python
import requests

BASE_URL = "https://gateway-voters.eci.gov.in/api/v1/citizen/sir"

headers = {
    'PLATFORM-TYPE': 'ECIWEB',
    'applicationName': 'VSP',
    'state': 'S25'
}

# Get districts
response = requests.get(
    f"{BASE_URL}/getDistrict",
    params={'state_cd': 'S25'},
    headers=headers
)

districts = response.json()['payload']

# Get assemblies
response = requests.get(
    f"{BASE_URL}/getAsmbly",
    params={'state_cd': 'S25'},
    headers=headers
)

assemblies = response.json()['payload']

# Get parts for AC 139
response = requests.get(
    f"{BASE_URL}/getPartByAc",
    params={'state_cd': 'S25', 'ac_no': 139},
    headers=headers
)

parts = response.json()['payload']
```

### cURL

```bash
# Get districts
curl -X GET \
  'https://gateway-voters.eci.gov.in/api/v1/citizen/sir/getDistrict?state_cd=S25' \
  -H 'PLATFORM-TYPE: ECIWEB' \
  -H 'applicationName: VSP' \
  -H 'state: S25'

# Get assemblies
curl -X GET \
  'https://gateway-voters.eci.gov.in/api/v1/citizen/sir/getAsmbly?state_cd=S25' \
  -H 'PLATFORM-TYPE: ECIWEB' \
  -H 'applicationName: VSP' \
  -H 'state: S25'

# Get parts for AC 139
curl -X GET \
  'https://gateway-voters.eci.gov.in/api/v1/citizen/sir/getPartByAc?state_cd=S25&ac_no=139' \
  -H 'PLATFORM-TYPE: ECIWEB' \
  -H 'applicationName: VSP' \
  -H 'state: S25'
```

## Rate Limiting

- Be respectful with API usage
- Add delays between requests to avoid overwhelming the server
- Recommended: 0.5-1 second delay between requests

## SSL/TLS Notes

Some systems may encounter SSL errors with legacy renegotiation. Use the provided `SSLContextAdapter` in the codebase to handle this.

## West Bengal Data

- **Total Districts**: 21
- **Total Assemblies**: 294
- **Total Polling Parts**: ~61,531

## Error Handling

```python
try:
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    if data.get('status') == 'success':
        return data['payload']
    else:
        # Handle API error
        print(f"API Error: {data.get('message')}")
        
except requests.exceptions.RequestException as e:
    # Handle connection error
    print(f"Connection Error: {e}")
```

## Additional Notes

1. API endpoints may change without notice
2. Always validate data against multiple sources
3. Store metadata locally to reduce API calls
4. The API does not provide detailed voter information (names, addresses)
5. For voter details, PDFs from ceowestbengal.nic.in are required
