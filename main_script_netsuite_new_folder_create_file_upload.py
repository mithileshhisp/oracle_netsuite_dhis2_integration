#pip install requests requests_oauthlib

import requests
from requests_oauthlib import OAuth1
from datetime import datetime,date
import json
import base64

from dotenv import load_dotenv
import os

load_dotenv()  # this loads .env file

# 🔹 Your NetSuite Account ID

# 🔹 Your Account ID
#ACCOUNT_ID = "******"
# 🔹 OAuth Credentials (use yours)

#CLIENT_KEY = "**********"
#CLIENT_SECRET = "***********"
#TOKEN_ID = "************"
#TOKEN_SECRET = "*********"

#signature_method='HMAC-SHA256',

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

url = f"{NETSUITE_BASE_URL}/services/rest/record/v1/vendor"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

uin_code = "IPPF-THA-009"

# ==================== FUNCTION 1: Create Vendor Folder ====================
def create_vendor_folder(vendor_id, uin_code):
    """
    Create folder structure for vendor
    
    Sample Call:
    result = create_vendor_folder(12345, "IPPF-IND-001")
    
    Sample Response:
    {
        "status": "success",
        "data": {
            "activeFolderId": 98765,
            "archiveFolderId": 98766,
            "activeFolderPath": "/Compliance-Documents/Accuity-Certificates/Active/IPPF-IND-001",
            "archiveFolderPath": "/Compliance-Documents/Accuity-Certificates/Archive/IPPF-IND-001"
        }
    }
    """
    payload = {
        "vendorId": vendor_id,
        "uinCode": uin_code
    }
    
    print("=" * 60)
    print("API 1: Creating Vendor Folder")
    print("=" * 60)
    print(f"Request URL: {CREATE_FOLDER_URL}")
    print(f"Request Body: {json.dumps(payload, indent=2)}")
    print("-" * 60)
    
    response = requests.post(
        CREATE_FOLDER_URL,
        auth=auth,
        json=payload,
        headers=headers
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    print("=" * 60)
    
    return response.json()


# ==================== FUNCTION 2: Upload Certificate ====================
def upload_certificate(uin_code, folder_id, pdf_file_path, archive_folder_id=None, archive_enabled=True):
    """
    Upload certificate to vendor folder
    
    Sample Call:
    result = upload_certificate(
        uin_code="IPPF-IND-001",
        folder_id=98765,
        pdf_file_path="Accuity_IPPF-IND-001_2026-03-24.pdf",
        archive_folder_id=98766,
        archive_enabled=True
    )
    
    Sample Response:
    {
        "status": "success",
        "data": {
            "fileId": 56790,
            "fileName": "Accuity_IPPF-IND-001_2026-03-24.pdf",
            "folderId": 98765,
            "oldFileId": 56789,
            "oldFileArchived": true
        }
    }
    """
    
    # Read and encode PDF to base64
    with open(pdf_file_path, "rb") as f:
        pdf_bytes = f.read()
        certificate_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    payload = {
        "uinCode": uin_code,
        "folderId": folder_id,
        "certificateBase64": certificate_base64,
        "archiveEnabled": archive_enabled
    }
    
    # Add optional parameters
    if archive_folder_id:
        payload["archiveFolderId"] = archive_folder_id
    
    # Add issue date if needed (optional)
    # Extract from filename or use current date
    import re
    match = re.search(r'_(\d{4}-\d{2}-\d{2})\.pdf$', pdf_file_path)
    if match:
        payload["issueDate"] = match.group(1)
    
    print("\n" + "=" * 60)
    print("API 2: Uploading Certificate")
    print("=" * 60)
    print(f"Request URL: {UPLOAD_CERT_URL}")
    print(f"PDF File: {pdf_file_path}")
    print(f"PDF Size: {len(pdf_bytes)} bytes")
    print(f"Base64 Length: {len(certificate_base64)} characters")
    #print(f"Request Body Keys: {list(payload.keys())}")
    print("-" * 60)
    
    response = requests.post(
        UPLOAD_CERT_URL,
        auth=auth,
        json=payload,
        headers=headers,
        timeout=60
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    print("=" * 60)
    
    return response.json()

# ==================== COMPLETE WORKFLOW EXAMPLE ====================
def complete_workflow_example():

    print("\n📋 STEP 1: Downlods file from source DHIS2")

    tempEventUid = "HEJ9jJPAS5y"
    tempDeUid = "R6nujxC6zLD"
   
    #pdf_url = "https://links.hispindia.org/ippf_uin/api/events/files?eventUid=AH9WpjR9duL&dataElementUid=R6nujxC6zLD"
    #pdf_url = "https://links.hispindia.org/ippf_uin/api/events/files?eventUid=HEJ9jJPAS5y&dataElementUid=R6nujxC6zLD"
    
    session_get = requests.Session()
    session_get.auth = (DHIS2_GET_USER, DHIS2_GET_PASSWORD)

    file_download_url = (
        f"{DHIS2_GET_API_URL}/events/files"
        f"?eventUid={tempEventUid}"
        f"&dataElementUid={tempDeUid}"
    )
    #pdf_url = "https://links.hispindia.org/ippf_uin/api/events/files?eventUid=HEJ9jJPAS5y&dataElementUid=R6nujxC6zLD"

    file_resource_response = session_get.get(file_download_url)

    #print("status_code:", file_resource_response.status_code)
    #print("Content-Type:", file_resource_response.headers.get("Content-Type"))
    #print("preview_response:", file_resource_response.text[:200])  # preview response

    # Check response
    if file_resource_response.status_code == 200:
        print("PDF downloaded successfully")
    else:
        print("Failed:", file_resource_response.status_code)

    #file_path = "downloaded_file.pdf"

    #custom_file_name = "Accuity_IPPF-THA-009_2026-03-25.pdf"
    # Create custom name
    event_uid = "HEJ9jJPAS5y"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_and_time = datetime.now().strftime("%Y-%m-%d")
    
    '''
    file_path = f"Accuity_{uin_code}_{date_and_time}.pdf"

    with open(file_path, "wb") as f:
        f.write(file_resource_response.content)

    print("Saved to:", file_path)
    '''

    file_path = "Accuity_IPPF-THA-009_2026-04-13.pdf"

    print("-" * 60)

    print("\n📋 STEP 2: Upload Certificate in Oracle NetSuite")
    
    #pdf_file = "IPPF-THA-009_DHIS2.pdf"
    # file path in netsuite 
    # Compliance-Documents > Accuity-Certificates search file name
    cert_result = upload_certificate(
        uin_code=uin_code,
        folder_id=FOLDER_ID,
        pdf_file_path=file_path,
        archive_folder_id=ARCHIVE_FOLDER_ID,
        archive_enabled=True
    )
    
    if cert_result.get('status') == 'success':
        print(f"\n✅ Certificate Uploaded Successfully!")
        print(f"File ID: {cert_result['data']['fileId']}")
        print(f"File Name: {cert_result['data']['fileName']}")
        print(f"Folder: {cert_result['data']['folderPath']}")
        
        if cert_result['data'].get('oldFileId'):
            print(f"Old Certificate Archived: {cert_result['data']['oldFileId']}")
    else:
        print(f"\n❌ Certificate Upload Failed: {cert_result.get('message')}")

    print("-" * 60)

    '''
    vendor_creation_payload = {
        #"entityId": "SUPP2001",
        "companyname": "New Supplier Pvt Ltd",
        "category": {"id": "39"},
        "email": "supplier@test.com",
        "phone": "9876543210",
        "subsidiary": {"id": "33"},
        "custentity_jj_san_country_sup": {"id": "1"},
        "custentity_2663_email_address_notif" : "supplier@test.com",
        "payablesAccount": {"id": "3939"},
        "currency" :  {"id": "71"},
        #"defaultaddress" : "123 MG Road Mumbai 400001 INDIA",
        "addressBook": {
            "items": [
                {
                    "defaultBilling": True,
                    "defaultShipping": True,
                    "addressBookAddress": {
                        "addr1": "123 MG Road",
                        "city": "Mumbai",
                        "state": "MH",
                        "zip": "400001",
                        "country": {"id": "IN"}
                    }
                }
            ]
        },
        "custentity_ippf_uin_number": uin_code
    }

    #print(" post start" )
    print("\n📋 STEP 1: Create Vendor in Oracle NetSuite")
    post_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Post start : { post_start } " )
    print("-" * 60)
    response = requests.post(
        url,
        auth=auth,
        json=vendor_creation_payload,
        headers=headers
    )

    print("1 Status:", response.status_code)
    #print("Response:", response.text)

    #print("2 Status:", response.status_code)

    if response.status_code == 204:
        print("Vendor created successfully.")
    else:
        print("Response:", response.text)

    #print("3 Status:", response.status_code)

    if response.content:
        data = response.json()
        print(data)
    else:
        print("Success - No content returned (204)")

    #print("Location Header:", response.headers) 

    location = response.headers.get("Location")
    print("Location Header:", location)

    if location:
        vendor_id = location.rstrip("/").split("/")[-1]
        print("Vendor Internal ID:", vendor_id)
        print(f"\n✅ Vendor Created Successfully!")
        print(f"   Vendor ID: {vendor_id}")
        print(f"   UIN Code: {uin_code}")

        # Step 2: Create Folder (API 1)
        print("\n📁 STEP 2: Create Vendor Folder Structure")
        print("-" * 60)

        #folder_result = create_vendor_folder(vendor_id, uin_code)
 
        # Path to your PDF file
        pdf_file = "IPPF-THA-009_DHIS2.pdf"
        
        cert_result = upload_certificate(
            uin_code=uin_code,
            folder_id=FOLDER_ID,
            pdf_file_path=file_path,
            archive_folder_id=ARCHIVE_FOLDER_ID,
            archive_enabled=True
        )
        
        if cert_result.get('status') == 'success':
            print(f"\n✅ Certificate Uploaded Successfully!")
            print(f"File ID: {cert_result['data']['fileId']}")
            print(f"File Name: {cert_result['data']['fileName']}")
            print(f"Folder: {cert_result['data']['folderPath']}")
            
            if cert_result['data'].get('oldFileId'):
                print(f"Old Certificate Archived: {cert_result['data']['oldFileId']}")
        else:
            print(f"\n❌ Certificate Upload Failed: {cert_result.get('message')}")


  
        #if folder_result.get('status') == 'success':
            #active_folder_id = folder_result['data']['activeFolderId']
           # archive_folder_id = folder_result['data']['archiveFolderId']
            
            #print(f"\n✅ Folder Created Successfully!")
            #print(f"Active Folder ID: {active_folder_id}")
            #print(f"Active Folder Path: {folder_result['data']['activeFolderPath']}")
            #print(f"Archive Folder ID: {archive_folder_id}")
            #print(f"Archive Folder Path: {folder_result['data']['archiveFolderPath']}")
            
            # Step 3: Upload Certificate (API 2)
            print("\n📄 STEP 3: Upload Certificate")
            print("-" * 60)
            
            # Path to your PDF file
            pdf_file = "IPPF-THA-009_DHIS2.pdf"
            
            cert_result = upload_certificate(
                uin_code=uin_code,
                folder_id=active_folder_id,
                pdf_file_path=pdf_file,
                archive_folder_id=archive_folder_id,
                archive_enabled=True
            )
            
            if cert_result.get('status') == 'success':
                print(f"\n✅ Certificate Uploaded Successfully!")
                print(f"File ID: {cert_result['data']['fileId']}")
                print(f"File Name: {cert_result['data']['fileName']}")
                print(f"Folder: {cert_result['data']['folderPath']}")
                
                if cert_result['data'].get('oldFileId'):
                    print(f"Old Certificate Archived: {cert_result['data']['oldFileId']}")
            else:
                print(f"\n❌ Certificate Upload Failed: {cert_result.get('message')}")
        else:
            print(f"\n❌ Folder Creation Failed: {folder_result.get('message')}")
     
        print("\n" + "✅" * 30)
        print("WORKFLOW COMPLETE")
        '''
    print("WORKFLOW COMPLETE")
    print("✅" * 30)


# ==================== RUN EXAMPLE ====================
if __name__ == "__main__":
    complete_workflow_example()    