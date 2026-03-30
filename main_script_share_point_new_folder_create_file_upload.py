# ✅ 2. Install Required Libraries
#pip install requests msal



import requests
from msal import ConfidentialClientApplication

site_id = "your_site_id"
drive_id = "your_drive_id"
#✅ 3. Get Access Token (OAuth)

CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret" 
TENANT_ID = "your_tenant_id"

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

result = app.acquire_token_for_client(scopes=SCOPE)

if "access_token" in result:
    access_token = result["access_token"]
else:
    raise Exception("Failed to get token", result)


print("access_token:", access_token)


# ✅ 4. Get SharePoint Site ID

site_url = "yourcompany.sharepoint.com"
site_path = "sites/yoursite"

url = f"https://graph.microsoft.com/v1.0/sites/{site_url}:/{site_path}"

headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(url, headers=headers)
site_id = response.json()["id"]


print("Site ID:", site_id)

# ✅ 5. Get Document Library (Drive ID)

url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"

response = requests.get(url, headers=headers)
drives = response.json()["value"]

drive_id = drives[0]["id"]  # usually default document library


print("Drive ID:", drive_id)


#✅ 6. Create Folder in SharePoint

folder_name = "IPPF-THA-009"
#folder_name = "MyFolder"

headers = {
    "Authorization": f"Bearer {access_token}"
}

url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"

data = {
    "name": folder_name,
    "folder": {},
    "@microsoft.graph.conflictBehavior": "rename"
}

response = requests.post(url, headers=headers, json=data)

print("folder creation response:" ,response.json())

#✅ 7. Upload File into Folder
file_path = "test.pdf"
file_name = "test.pdf"
#folder_name = "MyFolder"
folder_name = "IPPF-THA-009"

upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{folder_name}/{file_name}:/content"

with open(file_path, "rb") as f:
    response = requests.put(upload_url, headers=headers, data=f)

print(response.json())

######################################################

#🧠 Smart Way in Python (Auto Token Handling)

import time
from msal import ConfidentialClientApplication

CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"
TENANT_ID = "your-tenant-id"

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

token_cache = {
    "access_token": None,
    "expires_at": 0
}

def get_access_token():
    if token_cache["access_token"] and time.time() < token_cache["expires_at"]:
        return token_cache["access_token"]

    result = app.acquire_token_for_client(scopes=SCOPE)

    if "access_token" in result:
        token_cache["access_token"] = result["access_token"]
        token_cache["expires_at"] = time.time() + result["expires_in"] - 60
        return token_cache["access_token"]
    else:
        raise Exception("Token failed", result)
    
#######################################################################################
# 
# 
# ✅ 1. Create Parent Folder
parent_folder = "ParentFolder"

url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"

data = {
    "name": parent_folder,
    "folder": {},
    "@microsoft.graph.conflictBehavior": "rename"
}

response = requests.post(url, headers=headers, json=data)
print("Parent:", response.json())

#✅ 2. Create Child Folder inside Parent

child_folder = "ChildFolder"

url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{parent_folder}:/children"

data = {
    "name": child_folder,
    "folder": {},
    "@microsoft.graph.conflictBehavior": "rename"
}

response = requests.post(url, headers=headers, json=data)
print("Child:", response.json())

#✅ 3. Upload File into Child Folder
file_path = "test.pdf"
file_name = "test.pdf"

upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{parent_folder}/{child_folder}/{file_name}:/content"

with open(file_path, "rb") as f:
    response = requests.put(upload_url, headers=headers, data=f)

print("Upload:", response.json())

# 🔥 Shortcut (Even Better) You can skip folder creation check and just upload:
upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/ParentFolder/ChildFolder/test.pdf:/content"

# 🧠 Pro Version (Auto Create If Not Exists)
def create_folder(path):
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{path}"
    
    data = {
        "folder": {},
        "@microsoft.graph.conflictBehavior": "replace"
    }

    return requests.put(url, headers=headers, json=data).json()


# Create nested folders in one go
create_folder("ParentFolder")
create_folder("ParentFolder/ChildFolder")




#####

from msal import ConfidentialClientApplication
import time

CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"
TENANT_ID = "your-tenant-id"

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

token_cache = {
    "access_token": None,
    "expires_at": 0
}


def get_access_token():
    if token_cache["access_token"] and time.time() < token_cache["expires_at"]:
        return token_cache["access_token"]

    print("🔄 Generating new token...")

    result = app.acquire_token_for_client(scopes=SCOPE)

    if "access_token" in result:
        token_cache["access_token"] = result["access_token"]
        token_cache["expires_at"] = time.time() + result["expires_in"] - 60
        return token_cache["access_token"]
    else:
        raise Exception(result)
    

def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }


## 2. Add retry on expiry ✅
def safe_request(method, url, **kwargs):
    response = requests.request(method, url, headers=get_headers(), **kwargs)

    if response.status_code == 401:
        print("🔄 Token expired, refreshing...")
        token_cache["access_token"] = None
        response = requests.request(method, url, headers=get_headers(), **kwargs)

    return response