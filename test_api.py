#!/usr/bin/env python3
"""Test the new ECI API endpoint for fetching individual voter data."""

import requests
import json
import sys
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Custom SSL context that allows legacy renegotiation
class LegacySSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.load_default_certs()
        ctx.check_hostname = False
        ctx.verify_mode = 0  # ssl.CERT_NONE
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        kwargs['ssl_context'] = ctx
        kwargs['assert_hostname'] = False
        return super().init_poolmanager(*args, **kwargs)

# API endpoint
url = "https://gateway-s2-blo.eci.gov.in/api/v1/elastic-sir/get-eroll-data-2003"

# Headers (without Bearer token)
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "CurrentRole": "citizen",
    "PLATFORM-TYPE": "ECIWEB",
    "applicationName": "VSP",
    "channelidobo": "VSP"
}

# Payload - AC 139 (BELGACHIA EAST), Part 1, Serial 1
payload = {
    "oldStateCd": "S25",
    "oldAcNo": "139",
    "oldPartNo": "1",
    "oldPartSerialNo": "1"
}

print("=" * 80)
print("Testing ECI API: get-eroll-data-2003")
print("=" * 80)
print(f"\nURL: {url}")
print(f"\nHeaders (without Bearer token):")
for key, value in headers.items():
    print(f"  {key}: {value}")
print(f"\nPayload:")
print(f"  {json.dumps(payload, indent=2)}")
print("\n" + "=" * 80)

try:
    # Create session with legacy SSL support
    session = requests.Session()
    session.mount('https://', LegacySSLAdapter())
    
    # Make request
    response = session.post(
        url,
        headers=headers,
        json=payload,
        timeout=10,
        verify=False  # Disable SSL verification due to legacy SSL issues
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    print(f"\nResponse Body:")
    if response.text:
        try:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # If successful, show data structure
            if response.status_code == 200:
                print("\n" + "=" * 80)
                print("SUCCESS! Data structure:")
                print("=" * 80)
                if isinstance(data, dict):
                    print(f"Response keys: {list(data.keys())}")
                elif isinstance(data, list):
                    print(f"Response is a list with {len(data)} items")
                    if data:
                        print(f"First item keys: {list(data[0].keys())}")
        except ValueError:
            print(response.text)
    else:
        print("(Empty response)")
    
except requests.exceptions.SSLError as e:
    print(f"\n❌ SSL Error: {e}")
    print("The server requires legacy SSL renegotiation.")
except requests.exceptions.Timeout:
    print(f"\n❌ Timeout: Request took longer than 10 seconds")
except requests.exceptions.RequestException as e:
    print(f"\n❌ Request Error: {e}")
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
