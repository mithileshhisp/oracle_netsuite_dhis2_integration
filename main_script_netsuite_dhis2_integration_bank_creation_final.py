#https://4533524-sb1.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=1244&deploy=1

import requests
import json
import base64
import hmac
import hashlib
import time
import logging
from requests_oauthlib import OAuth1
from urllib.parse import quote

from dotenv import load_dotenv
import os

load_dotenv()


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONFIGURATION ==========
NETSUITE_ACCOUNT_ID = "4533524-sb1"

RESTLET_URL = f"https://{NETSUITE_ACCOUNT_ID}.restlets.api.netsuite.com/app/site/hosting/restlet.nl"
UPLOAD_CERT_URL = "https://4533524-sb1.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=1243&deploy=1"

UPLOAD_CERT_URL = "https://4533524-sb1.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=1244&deploy=1"

# Replace with your actual script and deploy IDs
SCRIPT_ID = "1244"
DEPLOY_ID = "1"


DHIS2_GET_API_URL = os.getenv("DHIS2_GET_API_URL")
DHIS2_GET_USER = os.getenv("DHIS2_GET_USER")
DHIS2_GET_PASSWORD = os.getenv("DHIS2_GET_PASSWORD")

CLIENT_KEY = os.getenv("CLIENT_KEY")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKEN_ID = os.getenv("TOKEN_ID")
TOKEN_SECRET = os.getenv("TOKEN_SECRET")

NETSUITE_BASE_URL = os.getenv("NETSUITE_BASE_URL")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
SIGNATURE_METHOD = os.getenv("SIGNATURE_METHOD")

CREATE_FOLDER_URL = os.getenv("CREATE_FOLDER_URL")
UPLOAD_CERT_URL = os.getenv("UPLOAD_CERT_URL")

FOLDER_ID = os.getenv("FOLDER_ID")
ARCHIVE_FOLDER_ID = os.getenv("ARCHIVE_FOLDER_ID")


#print("CLIENT_KEY:", CLIENT_KEY)

auth = OAuth1(
    CLIENT_KEY,
    CLIENT_SECRET,
    TOKEN_ID,
    TOKEN_SECRET,
    signature_method=SIGNATURE_METHOD,
    realm=ACCOUNT_ID
)

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

'''
def get_oauth_header(url, http_method, consumer_key, consumer_secret, token_id, token_secret):
    timestamp = str(int(time.time()))
    nonce = base64.b64encode(str(timestamp).encode()).decode()
   
    signature_params = {
        'oauth_consumer_key': consumer_key,
        'oauth_nonce': nonce,
        'oauth_signature_method': 'HMAC-SHA256',
        'oauth_timestamp': timestamp,
        'oauth_token': token_id,
        'oauth_version': '1.0'
    }
   
    sorted_params = sorted(signature_params.items())
    param_string = '&'.join([f"{quote(k)}={quote(v)}" for k, v in sorted_params])
    signature_base = f"{http_method}&{quote(url, safe='')}&{quote(param_string, safe='')}"
    signing_key = f"{quote(consumer_secret)}&{quote(token_secret)}"
   
    signature = hmac.new(
        signing_key.encode(),
        signature_base.encode(),
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature).decode()
   
    oauth_params = signature_params.copy()
    oauth_params['oauth_signature'] = signature
   
    auth_header = 'OAuth ' + ', '.join([f'{k}="{v}"' for k, v in oauth_params.items()])
    return auth_header
'''

def inactive_bank_details():

    full_url = f"{RESTLET_URL}?script={SCRIPT_ID}&deploy={DEPLOY_ID}"
    
    print(f"Delete URL: {full_url}")
    
    # Inactivate by Record ID
    #curl -X DELETE \
    #'https://4533524-sb1.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=1244&deploy=1' \
    #-H 'Content-Type: application/json' \
    #-d '{"recordId": "13524"}'

    delete_payload = {
        'action': 'inactivate',
        "recordId": '13526',
        "vendorId": '42630' ,
        #'isActive': True # for activate the bank
        'isActive': False # for deActivate the bank
    }

    print(f"delete_payload: {delete_payload}")
    
    try:
        response = requests.post(full_url, auth=auth, headers=headers, data=json.dumps(delete_payload), timeout=60)
       
        logger.info(f"Response Status: {response.status_code}")

        print(f"Response Status: {response.status_code}")

        result = response.json()

        print("FULL RESPONSE:", result)
       
       
        return result
       
    except requests.exceptions.Timeout:
        logger.error("Request timeout after 60 seconds")
        return None
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return None


def create_bank_details(vendor_id, bank_type, file_format_id, **optional_fields):
    """
    Create bank details for a vendor in NetSuite
    
    Required Parameters:
    - vendor_id: Internal ID of the vendor
    - bank_type: "Primary" or "Secondary"
    - file_format_id: Internal ID of Payment File Format
    
    Optional Parameters (pass as keyword arguments):
    - subsidiaryId, accountNumber, accountName, bankNumber, bankName, etc.
    """
    
    full_url = f"{RESTLET_URL}?script={SCRIPT_ID}&deploy={DEPLOY_ID}"
    
    print(f"Post URL: {full_url}")
    
    # Build payload with mandatory fields

        #"vendorId": vendor_id,
        #"bankType": bank_type,
        #"fileFormatId": file_format_id,

    '''
    identifier (RECOMMENDED)
    payload = {
        'vendorId': '42630',
        'bankType': 'Secondary',
        'fileFormatId': '40',
        'bankNameIdentifier': 'PNB_SAVINGS_001',  # ← Unique identifier
        'accountName': 'Rajeev Ragta TEST',
        'bankNumber': '555555',
        'bankName': 'PNB',
        'accountNumber': '55555'
    }
    '''

    payload = {
        "vendorId": "42630",
        "bankType": "Secondary",
        "isActive": True,
        "fileFormatId": "174",
        "bankNameIdentifier" : "IDFC Saving Bank Account 12123456",
        "accountName":"Mithilesh IDFC",
        "bankNumber": "555576767",
        "subsidiaryId":"33",
        "bankName": "IDFC Saving Bank Account",
        "accountNumber" : "5555565656",
        "branchNumber" : "4444444545454",
        "branchName" : "Delhi",
        "iban": "333333374747",
        "swift": "RRRRRRR7777777656565"
    }
    

    '''
    payload for inactive the bank details -- 
    payload = {
        'recordId': '13525',
        'vendorId': '42630'  # Verifies record belongs to this vendor
        'isinactive': True,
    }
    '''
    # Add optional fields

    #payload.update(optional_fields)
    
    # Log request (mask sensitive data)
    '''
    log_payload = payload.copy()
    if 'accountNumber' in log_payload:
        log_payload['accountNumber'] = mask_sensitive(log_payload['accountNumber'])
    if 'iban' in log_payload:
        log_payload['iban'] = mask_sensitive(log_payload['iban'])
  
    logger.info(f"Sending request to NetSuite: {json.dumps(log_payload, indent=2)}")
    '''

    # Generate OAuth header
    '''
    auth_header = get_oauth_header(
        full_url, 'POST', CONSUMER_KEY, CONSUMER_SECRET, TOKEN_ID, TOKEN_SECRET
    )
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': auth_header
    }
    '''
    clean_payload = {k: v for k, v in payload.items() if v is not None}
    print(f"Post payload: {clean_payload}")

    #print("AUTH OBJECT:", auth)
    #print("CK:", CLIENT_KEY)
    #print("CS:", CLIENT_SECRET)
    #print("TK:", TOKEN_ID)
    #print("TS:", TOKEN_SECRET)
    #print("HEADERS:", headers)

    try:
        response = requests.post(full_url, auth=auth, headers=headers, data=json.dumps(payload), timeout=60)
       
        logger.info(f"Response Status: {response.status_code}")

        print(f"Response Status: {response.status_code}")

        result = response.json()

        print("FULL RESPONSE:", result)
       
        # Log request ID for tracking
        if 'metadata' in result and 'requestId' in result['metadata']:
            logger.info(f"Request ID: {result['metadata']['requestId']}")
       
        if result.get('success'):
            logger.info(f"✅ Bank details created successfully! Record ID: {result['data']['recordId']}")
            logger.info(f"Processing Time: {result['metadata']['processingTimeMs']}ms")
        else:
            logger.error(f"❌ Failed: {result.get('message')}")
            if 'missingFields' in result:
                logger.error(f"Missing fields: {result['missingFields']}")
       
        return result
       
    except requests.exceptions.Timeout:
        logger.error("Request timeout after 60 seconds")
        return None
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return None

def get_bank_details(vendor_id, bank_type="Primary"):
    """Retrieve bank details for a vendor"""
   
    full_url = f"{RESTLET_URL}?script={SCRIPT_ID}&deploy={DEPLOY_ID}&vendorId={vendor_id}&bankType={bank_type}"
   
    #full_url = https://4533524-sb1.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=customscript_bank_details_api&deploy=customdeploy_bank_details_api&vendorId=41930&bankType=Primary"
    
    # "https://4533524-sb1.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=1244&deploy=1&vendorId=41930&bankType=Primary"
    logger.info(f"Fetching bank details for Vendor ID: {vendor_id}, Type: {bank_type}")
   
    '''
    auth_header = get_oauth_header(
        full_url, 'GET', CONSUMER_KEY, CONSUMER_SECRET, TOKEN_ID, TOKEN_SECRET
    )
    
    headers = {'Authorization': auth_header}
    '''
    print(f"Get Bank Details URL: {full_url}")
    #https://4533524-sb1.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=1244&deploy=1&vendorId=41930&bankType=Primary
    try:
        response = requests.get(full_url, auth=auth, headers=headers, verify=True, timeout=30)
        result = response.json()
        #print("FULL RESPONSE:", result)
        if result.get('success'):
            logger.info(f"✅ Found {result['data']['count']} bank detail record(s)")
            if 'requestId' in result.get('metadata', {}):
                logger.info(f"Request ID: {result['metadata']['requestId']}")
        else:
            logger.error(f"❌ Failed: {result.get('message')}")
       
        return result
       
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return None

def mask_sensitive(value):
    """Mask sensitive data for logging"""
    if not value:
        return None
    if len(value) <= 4:
        return '****'
    return value[:4] + '****' + value[-4:]

# ========== EXAMPLE USAGE ==========
if __name__ == "__main__":
   

    print("=" * 60)
    print("EXAMPLE 1: Create Bank Details (Minimal Required Fields)")
    print("=" * 60)
   
    # Minimal payload with ONLY mandatory fields
    '''
    result = create_bank_details(
        vendor_id=41930,      # Replace with actual vendor ID
        bank_type="Primary",
        file_format_id=456     # Replace with actual file format ID
    )

    ''' 
    result = inactive_bank_details(
        #recordId=13525
    )

    '''
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Create Bank Details (With Optional Fields)")
    print("=" * 60)
  
    result = create_bank_details(
        vendor_id=42630,
        bank_type="Primary",
        file_format_id=174
    )
    '''

    print("\n" + "=" * 60)
    print("EXAMPLE 3: Get Bank Details")
    print("=" * 60)
   
    result = get_bank_details(43031, "Primary")
   
    if result and result.get('success'):
        for record in result['data']['records']:
            print(f"\nRecord ID: {record['recordId']}")
            print(f"Bank Name: {record['bankName']}")
            print(f"Bank name: {record['name']}")
            
            print(f"Account Number: {record['accountNumber']}")
            print(f"Account Name: {record['accountName']}")
            print(f"Bank Type: {record['bankType']}")
            print(f"File Format Id: {record['fileFormatId']}")
            print(f"iban: {record['iban']}")
            print(f"swift: {record['swift']}")
            print(f"isActive: {record['isActive']}")
            print(f"subsidiaryId: {record['subsidiaryId']}")
            print(f"address1: {record['address1']}")
            print(f"custpage_eft_custrecord_2663_entity_branch_no: {record['custpage_eft_custrecord_2663_entity_branch_no']}")
            #print(f"country: {record['country']}")


#Sample output results:
'''


# create bank details
result = create_bank_details(
    vendor_id=41930,
    bank_type="Primary",
    file_format_id=174,
    accountNumber="1234567890",
    accountName="ABC Company Ltd",
    bankName="Chase Bank",
    iban="GB29NWBK60161331926819",
    swift="CHASUS33",
    city="New York",
    country="1"
)





[BankDetailsAPI - API Call Started] {
  "requestId": "REQ_1744722000000_a7b3c9",
  "endpoint": "POST",
  "timestamp": "2026-04-15T10:30:00.000Z"
}

[BankDetailsAPI - Request Parsed Successfully] {
  "requestId": "REQ_1744722000000_a7b3c9",
  "parsedData": {
    "vendorId": 12345,
    "bankType": "Primary",
    "fileFormatId": 456,
    "hasAccountNumber": true,
    "hasIban": true
  }
}

[BankDetailsAPI - Vendor Verified Successfully] {
  "vendorId": 12345,
  "vendorName": "ABC Corp",
  "vendorEmail": "vendor@example.com"
}

[BankDetailsAPI - Record Saved Successfully] {
  "recordId": 987654,
  "timings": {
    "duplicateCheckMs": 45,
    "saveOperationMs": 234,
    "totalProcessingMs": 345
  }
}



-- bank response
{
    "vendorId": 41930,
    "bankType": "Primary",
    "fileFormatId": 456,
    "accountNumber": "1234567890",
    "accountName": "ABC Company Ltd",
    "bankNumber": "021000021",
    "bankName": "Chase Bank",
    "branchNumber": "123",
    "branchName": "Downtown Branch",
    "accountSuffix": "001",
    "accountType": "Checking",
    "iban": "GB29NWBK60161331926819",
    "swift": "CHASUS33",
    "bic": "CHASUS33XXX",
    "address1": "123 Main Street",
    "address2": "Suite 100",
    "city": "New York",
    "state": "NY",
    "zip": "10001",
    "country": "1",
    "customerCode": "CUST001",
    "edi": true,
    "babyBonus": false,
    "chargeBearer": "SHA",
    "bankFeeCode": "FEE001",
    "subsidiaryId": 1
}    





'''