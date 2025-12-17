import random
import json
import os
from typing import Optional
from dotenv import load_dotenv
from emulator_api import client, get_identity_token, create_device, send_sensor_value, print_section

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

# Service addresses
IDENTITY_API_BASE_URL = os.getenv("IDENTITY_API_BASE_URL", "https://http-identity.umecdev.deviot.cloud")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.umecdev.deviot.cloud")

# Authorization credentials for Emulators API (OAuth2 Client Credentials)
IDENTITY_CLIENT_ID = os.getenv("IDENTITY_CLIENT_ID")
IDENTITY_CLIENT_SECRET = os.getenv("IDENTITY_CLIENT_SECRET")
IDENTITY_GRANT_TYPE = os.getenv("IDENTITY_GRANT_TYPE", "client_credentials")

# Authorization credentials for Mobile API (user)
USER_NAME = os.getenv("USER_NAME")
PASSWORD = os.getenv("PASSWORD")

# Device parameters
VENDOR_CODE = os.getenv("VENDOR_CODE", "umec")
MODEL_CODE = os.getenv("MODEL_CODE", "powermaster")
FIRMWARE_VERSION = os.getenv("FIRMWARE_VERSION", "0.01")
DEVICE_SERIAL = os.getenv("DEVICE_SERIAL")  # Device serial number (optional, if None - not sent)

# Sensor parameters for testing
SENSOR_CODE = os.getenv("SENSOR_CODE", "throttle_line01")
SENSOR_VALUE = int(os.getenv("SENSOR_VALUE", "8"))

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_response(response, step_name: str):
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


# ============================================================================
# API FUNCTIONS
# ============================================================================

def sign_in(base_url: str, user_name: str, password: str) -> Optional[dict]:
    """
    Step 3: User authentication
    
    Endpoint: POST /api/customer/v1/signin
    """
    print_section("STEP 3: User authentication")
    
    url = f"{base_url}/api/customer/v1/signin"
    payload = {
        "userName": user_name,
        "password": password
    }
    
    print(f"Request: {json.dumps({'userName': user_name, 'password': '***'}, indent=2)}")
    
    try:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return print_response(response, "Authentication")
    except Exception as e:
        print(f"[ERROR] Authentication error: {e}")
        return None


def get_unit_details(base_url: str, unit_id: int, access_token: str) -> Optional[dict]:
    """
    Step 4: Get unit details
    
    Endpoint: GET /api/customer/v1/units/{unitId}
    """
    print_section("STEP 4: Getting unit details")
    
    url = f"{base_url}/api/customer/v1/units/{unit_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print(f"Unit ID: {unit_id}")
    
    try:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return print_response(response, "Unit details")
    except Exception as e:
        print(f"[ERROR] Error getting unit details: {e}")
        return None


def set_unit_parameters(base_url: str, unit_id: int, access_token: str, 
                        brightness_value: int) -> Optional[dict]:
    """
    Step 5: Set unit parameters
    
    Endpoint: PUT /api/customer/v1/units/{unitId}/parameters
    """
    print_section("STEP 5: Setting unit parameters")
    
    url = f"{base_url}/api/customer/v1/units/{unit_id}/parameters"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "unitId": unit_id,
        "parameters": [
            {
                "code": "brightness",
                "value": str(brightness_value)
            }
        ]
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        response = client.put(url, json=payload, headers=headers)
        response.raise_for_status()
        return print_response(response, "Setting parameters")
    except Exception as e:
        print(f"[ERROR] Error setting parameters: {e}")
        return None


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():    
    # ========================================================================
    # STEP 0: Get token from Identity for Emulators API
    # ========================================================================
    emulator_token = get_identity_token(
        IDENTITY_API_BASE_URL,
        IDENTITY_CLIENT_ID,
        IDENTITY_CLIENT_SECRET,
        IDENTITY_GRANT_TYPE
    )
    
    if not emulator_token:
        print("\n[ERROR] Failed to get token from Identity. Stopping.")
        return
    
    print(f"\n[OK] Token for Emulators API obtained")
    
    # ========================================================================
    # STEP 1: Create emulator
    # ========================================================================
    create_result = create_device(
        API_BASE_URL,
        USER_NAME,
        VENDOR_CODE,
        MODEL_CODE,
        FIRMWARE_VERSION,
        emulator_token,
        DEVICE_SERIAL
    )
    
    if not create_result:
        print("\n[ERROR] Failed to create device. Stopping.")
        return
    
    device_id = create_result.get("deviceId")
    unit_ids = create_result.get("unitIds", [])
    
    if not device_id:
        print("\n[ERROR] deviceId not received. Stopping.")
        return
    
    if not unit_ids or len(unit_ids) == 0:
        print("\n[ERROR] unitIds not received. Stopping.")
        return
    
    unit_id = unit_ids[0]  # Take first unit
    print(f"\n[OK] Device emulator created: deviceId={device_id}, unitId={unit_id}")
    
    # ========================================================================
    # STEP 2: Send sensor value
    # ========================================================================
    sensor_result = send_sensor_value(
        API_BASE_URL,
        device_id,
        SENSOR_CODE,
        SENSOR_VALUE,
        emulator_token
    )
    
    if sensor_result is not None:
        print(f"\n[OK] Sensor value sent")
    else:
        print(f"\n[WARNING] Failed to send sensor value (continuing)")
    
    # ========================================================================
    # STEP 3: User authentication in Mobile API
    # ========================================================================
    signin_result = sign_in(
        API_BASE_URL,
        USER_NAME,
        PASSWORD
    )
    
    if not signin_result:
        print("\n[ERROR] Authentication failed. Stopping.")
        return
    
    access_token = signin_result.get("accessToken")
    
    if not access_token:
        print("\n[ERROR] Access token not received. Stopping.")
        return
    
    print(f"\n[OK] Authentication successful")
    
    # ========================================================================
    # STEP 4: Get unit details
    # ========================================================================
    unit_details = get_unit_details(
        API_BASE_URL,
        unit_id,
        access_token
    )
    
    # Get serial number from unit details
    device_serial_from_api = None
    if unit_details:
        device_serial_from_api = unit_details.get("deviceSerial")
        print(f"\n[OK] Unit details obtained")
    else:
        print(f"\n[WARNING] Failed to get unit details (continuing)")
    
    # ========================================================================
    # STEP 5: Set parameters
    # ========================================================================
    random_brightness = random.randint(0, 100)
    
    params_result = set_unit_parameters(
        API_BASE_URL,
        unit_id,
        access_token,
        random_brightness
    )
    
    if params_result is not None:
        print(f"\n[OK] Unit parameters set")
    else:
        print(f"\n[WARNING] Failed to set parameters")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print_section("EXECUTION SUMMARY")
    print(f"[OK] Device emulator created:")
    print(f"   Device ID: {device_id}")
    print(f"   Unit ID: {unit_id}")
    if device_serial_from_api:
        print(f"   Device Serial: {device_serial_from_api}")
    print(f"[OK] User authenticated: {USER_NAME}")
    print(f"[OK] Brightness set: {random_brightness}")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close HTTP client
        client.close()


