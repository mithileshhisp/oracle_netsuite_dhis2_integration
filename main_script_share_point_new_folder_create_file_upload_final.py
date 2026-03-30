#pip install requests msal

import requests
from msal import ConfidentialClientApplication
import time

from datetime import datetime,date
import json
import base64

from dotenv import load_dotenv
import os

load_dotenv()  # this loads .env file

SHARE_POINT_SITE_ID = os.getenv("SHARE_POINT_SITE_ID")
SHARE_POINT_DRIVE_ID = os.getenv("SHARE_POINT_DRIVE_ID")

SHARE_POINT_CLIENT_ID = os.getenv("SHARE_POINT_CLIENT_ID")
SHARE_POINT_CLIENT_SECRET = os.getenv("SHARE_POINT_CLIENT_SECRET")
SHARE_POINT_TENANT_ID = os.getenv("SHARE_POINT_TENANT_ID")

SHARE_POINT_ACCESS_TOKEN = os.getenv("SHARE_POINT_ACCESS_TOKEN")

uin_code = "IPPF-THA-009"

#✅ 1. Get/ Create Access Token (OAuth)

'''
AUTHORITY = f"https://login.microsoftonline.com/{SHARE_POINT_TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

app = ConfidentialClientApplication(
    SHARE_POINT_CLIENT_ID,
    authority=AUTHORITY,
    client_credential=SHARE_POINT_CLIENT_SECRET
)

result = app.acquire_token_for_client(scopes=SCOPE)

if "access_token" in result:
    access_token = result["access_token"]
else:
    raise Exception("Failed to get token", result)


print("access_token:", access_token)

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

'''

# ================= CONFIG =================
#ACCESS_TOKEN = SHARE_POINT_ACCESS_TOKEN
drive_id = SHARE_POINT_DRIVE_ID


AUTHORITY = f"https://login.microsoftonline.com/{SHARE_POINT_TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

app = ConfidentialClientApplication(
    SHARE_POINT_CLIENT_ID,
    authority=AUTHORITY,
    client_credential=SHARE_POINT_CLIENT_SECRET
)

token_cache = {
    "access_token": None,
    "expires_at": 0 
}

def get_access_token():
    if token_cache["access_token"] and time.time() < token_cache["expires_at"]:
        print("🔄 Token found in Cache")
        return token_cache["access_token"]

    print("🔄 Generating new token...")

    result = app.acquire_token_for_client(scopes=SCOPE)

    if "access_token" in result:
        token_cache["access_token"] = result["access_token"]
        token_cache["expires_at"] = time.time() + result["expires_in"] - 60
        print("🔄 New token Created")
        return token_cache["access_token"]
    else:
        raise Exception(result)

def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
}


# ================= CHECK FOLDER EXISTS =================
def folder_exists(path):
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{path}"
    
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        return False
    else:
        print("Error checking folder:", response.text)
        return False


# ================= CREATE FOLDER =================
def create_folder(path):
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{path}:"
    
    data = {
        "folder": {},
        "@microsoft.graph.conflictBehavior": "fail"
    }

    response = requests.put(url, headers=get_headers(), json=data)
    return response.json()


# ================= ENSURE FOLDER =================
def ensure_folder(path):
    if not folder_exists(path):
        print(f"📁 Creating folder: {path}")
        return create_folder(path)
    else:
        print(f"✅ Folder already exists: {path}")
        return {"status": "exists", "path": path}


# ================= UPLOAD FILE =================
def upload_file(folder_path, file_path):
    file_name = file_path.split("/")[-1]

    upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{folder_path}/{file_name}:/content"

    with open(file_path, "rb") as f:
        response = requests.put(upload_url, headers=get_headers(), data=f)

    if response.status_code in [200, 201]:
        print(f"✅ File uploaded: {file_name}")
        return response.json()
    else:
        print("❌ Upload failed:", response.text)
        return None


# ================= COMPLETE WORKFLOW =================
def complete_workflow_share_point():
    
    # Parent folder (Year)
    parent_folder = datetime.now().strftime("%Y")
    
    # Child folder (UIN or any dynamic value)
    child_folder = uin_code

    parent_path = parent_folder
    child_path = f"{parent_folder}/{child_folder}"

    print("-" * 60)
    print("📋 STEP 1: Parent Folder Creation")
    print("✅ STEP 1 (a): Ensure Parent Folder")
    ensure_folder(parent_path)

    print("-" * 60)
    print("📋 STEP 2: Child Folder Creation")
    print("✅ STEP 2 (a): Ensure Child Folder")
    ensure_folder(child_path)

    print("-" * 60)
    print("📋 STEP 3: Upload File")

    #file_path = "test.pdf"  # change to your file path
    year_month_date = datetime.now().strftime("%Y-%m-%d")

    file_path = f"Accuity_{uin_code}_{year_month_date}.pdf"
    upload_file(child_path, file_path)
    #print("✅ Upload File Completed")

    print("WORKFLOW COMPLETE")
    print("✅" * 30)


# ================= RUN =================
if __name__ == "__main__":
    complete_workflow_share_point()