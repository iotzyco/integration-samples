import httpx
import json
from typing import Optional

client = httpx.Client()


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_response(response: httpx.Response, step_name: str):
    """Print API response"""
    print(f"\n[{step_name}]")
    print(f"Status: {response.status_code}")
    print(f"URL: {response.url}")
    
    try:
        response_json = response.json()
        # Using json.dumps without ensure_ascii to avoid encoding issues
        print(f"Response: {json.dumps(response_json, indent=2)}")
        return response_json
    except Exception as e:
        print(f"Response (text): {response.text}")
        return None


def get_identity_token(base_url: str, client_id: str, client_secret: str, 
                       grant_type: str) -> Optional[str]:
    """
    Step 0: Get token from Identity service (OAuth2 Client Credentials)
    
    Endpoint: POST /connect/token
    """
    print_section("STEP 0: Getting token from Identity")
    
    url = f"{base_url}/connect/token"
    
    # OAuth2 requires form-urlencoded, not JSON
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": grant_type
    }
    
    print(f"Identity request:")
    print(f"  client_id: {client_id}")
    print(f"  grant_type: {grant_type}")
    
    try:
        # OAuth2 token endpoint uses application/x-www-form-urlencoded
        response = client.post(url, data=payload)
        response.raise_for_status()
        
        result = response.json()
        print(f"\nStatus: {response.status_code}")
        
        if "access_token" in result:
            token = result["access_token"]
            token_type = result.get("token_type", "Bearer")
            expires_in = result.get("expires_in", "N/A")
            
            print(f"[OK] Token retrieved successfully")
            print(f"  Token type: {token_type}")
            print(f"  Expires in: {expires_in} seconds")
            print(f"  Token: {token[:50]}...")
            
            return token
        else:
            print(f"[ERROR] Token not found in response: {result}")
            return None
            
    except httpx.HTTPError as e:
        print(f"[ERROR] Error getting token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Server response: {e.response.text}")
        return None


def create_device(base_url: str, user_name: str, vendor_code: str,
                  model_code: str, firmware_version: str, access_token: str,
                  device_serial: Optional[str] = None) -> Optional[dict]:
    """
    Step 1: Create device emulator
    
    Endpoint: POST /api/emulators/v1/devices
    """
    print_section("STEP 1: Creating device emulator")
    
    url = f"{base_url}/api/emulators/v1/devices"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "userName": user_name,
        "vendorCode": vendor_code,
        "modelCode": model_code,
        "firmwareVersion": firmware_version
    }
    
    # Add serial number if provided
    if device_serial:
        payload["deviceSerial"] = device_serial
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return print_response(response, "Device creation")
    except httpx.HTTPError as e:
        print(f"[ERROR] Error creating device: {e}")
        return None


def send_sensor_value(base_url: str, device_id: str, sensor_code: str,
                      value: float, access_token: str) -> Optional[dict]:
    """
    Step 2: Send sensor value to emulator
    
    Endpoint: POST /api/emulators/v1/devices/{deviceId}/sensor
    """
    print_section("STEP 2: Sending sensor value")
    
    url = f"{base_url}/api/emulators/v1/devices/{device_id}/sensor"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "deviceId": device_id,
        "sensorCode": sensor_code,
        "value": value
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return print_response(response, "Sending sensor value")
    except httpx.HTTPError as e:
        print(f"[ERROR] Error sending sensor value: {e}")
        return None
