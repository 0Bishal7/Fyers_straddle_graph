import os
import json
import pyotp
import base64
import requests
from urllib.parse import urlparse, parse_qs
from fyers_apiv3 import fyersModel
from .models import FyersToken

# Credentials (Move sensitive data to environment variables)
SECRET_KEY = os.getenv("FYERS_SECRET_KEY", "CXP8VF2G7S")
REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI", "https://127.0.0.1/")
CLIENT_ID = os.getenv("FYERS_CLIENT_ID", "EEOUGTFHE5-100")
FY_ID = os.getenv("FYERS_ID", "YA45110")
TOTP_SECRET = os.getenv("FYERS_TOTP_SECRET", "26R6SB7XRTSJTSNRLMCNC4HF6ZGUNS2I")
PIN = os.getenv("FYERS_PIN", "7550")

# Function to encode a string in base64
def get_encoded_string(string):
    return base64.b64encode(str(string).encode("ascii")).decode("ascii")

# Function to fetch access token
def get_fyers_access_token():
    """Fetches a new Fyers access token and saves it to the database."""
    
    # Step 1: Send OTP request
    URL_SEND_LOGIN_OTP = "https://api-t2.fyers.in/vagator/v2/send_login_otp_v2"
    res = requests.post(url=URL_SEND_LOGIN_OTP, json={"fy_id": get_encoded_string(FY_ID), "app_id": "2"}).json()
    
    if "request_key" not in res:
        raise Exception("Failed to send OTP")

    # Step 2: Verify OTP
    totp = pyotp.TOTP(TOTP_SECRET).now()
    URL_VERIFY_OTP = "https://api-t2.fyers.in/vagator/v2/verify_otp"
    res2 = requests.post(url=URL_VERIFY_OTP, json={"request_key": res["request_key"], "otp": totp}).json()
    
    if "request_key" not in res2:
        raise Exception("Failed to verify OTP")

    # Step 3: Verify PIN
    ses = requests.Session()
    URL_VERIFY_PIN = "https://api-t2.fyers.in/vagator/v2/verify_pin_v2"
    payload2 = {"request_key": res2["request_key"], "identity_type": "pin", "identifier": get_encoded_string(PIN)}
    res3 = ses.post(url=URL_VERIFY_PIN, json=payload2).json()
    
    if "data" not in res3 or "access_token" not in res3["data"]:
        raise Exception("Failed to verify PIN")

    ses.headers.update({'authorization': f"Bearer {res3['data']['access_token']}"})

    # Step 4: Get Auth Code
    TOKEN_URL = "https://api-t1.fyers.in/api/v3/token"
    payload3 = {
        "fyers_id": FY_ID,
        "app_id": CLIENT_ID[:-4],
        "redirect_uri": REDIRECT_URI,
        "appType": "100",
        "code_challenge": "",
        "state": "None",
        "scope": "",
        "nonce": "",
        "response_type": "code",
        "create_cookie": True
    }
    res4 = ses.post(url=TOKEN_URL, json=payload3).json()
    
    if "Url" not in res4:
        raise Exception("Failed to generate auth code URL")

    # Extract auth_code from URL
    parsed = urlparse(res4['Url'])
    auth_code = parse_qs(parsed.query)['auth_code'][0]

    # Step 5: Generate Access Token
    session = fyersModel.SessionModel(
        client_id=CLIENT_ID,
        secret_key=SECRET_KEY,
        redirect_uri=REDIRECT_URI,
        response_type="code",
        grant_type="authorization_code"
    )
    session.set_token(auth_code)
    response = session.generate_token()
    
    if "access_token" not in response:
        raise Exception("Failed to generate access token")

    access_token = response['access_token']

    # Save or update in database
    FyersToken.objects.update_or_create(id=1, defaults={'access_token': access_token})

    return access_token
