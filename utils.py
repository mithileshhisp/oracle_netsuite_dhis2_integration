# utils.py

import requests
from requests_oauthlib import OAuth1
import logging

import certifi  ## for post data in hmis production certificate issue


import json
import smtplib
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders
from urllib.parse import quote

## for nepali date
#import nepali_datetime
from datetime import datetime, timedelta, date

#from datetime import timedelta

from dotenv import load_dotenv
import os
import glob
import base64
from dotenv import load_dotenv


load_dotenv()  # this loads .env file

FROM_EMAIL_ADDR = os.getenv("FROM_EMAIL_ADDR")
FROM_EMAIL_PASSWORD = os.getenv("FROM_EMAIL_PASSWORD")



# 🔹 Your NetSuite Account ID

# 🔹 Your Account ID
#ACCOUNT_ID = "******"
# 🔹 OAuth Credentials (use yours)


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

NETSUITE_ACCOUNT_ID = "4533524-sb1"

RESTLET_URL = f"https://{NETSUITE_ACCOUNT_ID}.restlets.api.netsuite.com/app/site/hosting/restlet.nl"


# Replace with your actual script and deploy IDs
SCRIPT_ID = "1244"
DEPLOY_ID = "1"

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
from constants import LOG_FILE
#from app import QueueLogHandler

DHIS2_API_URL = os.getenv("DHIS2_API_URL")

from constants import LOG_FILE_TEI_ATTRIBUTE_VALUE_ERROR_LOG

# ADD THIS PART (UI streaming) for print in HTML Page in response
#Add a global log queue
import queue
log_queue = queue.Queue()
#Add a Queue logging handler
#import logging

'''
class QueueLogHandler(logging.Handler):
    def emit(self, record):
        log_queue.put(self.format(record))
'''

import logging
import queue

log_queue = queue.Queue()

class QueueHandler(logging.Handler):
    def emit(self, record):
        log_queue.put(self.format(record))


def configure_logging():

    #Optional (Advanced, but useful)
    '''
    import sys
    sys.stdout.write = lambda msg: logging.info(msg)
    logging.info(f"[job:{job_id}] step 1")
    '''

    LOG_DIR = "logs"
    #os.makedirs(LOG_DIR, exist_ok=True)

    os.makedirs(LOG_DIR, exist_ok=True)
    assert LOG_DIR != "/" and LOG_DIR != "" #### Never delete outside log folder.

    # Create unique log filename
    #log_filename = f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    log_filename = LOG_FILE
    #log_filename = f"{LOG_FILE}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    log_path = os.path.join(LOG_DIR, log_filename)

    #logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    logging.basicConfig(filename=log_path, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    '''
    logging.basicConfig(filename=log_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            QueueLogHandler()   # 👈 THIS is the key
        ]
    )
    '''
    # ✅ ADD THIS (UI streaming)
    '''
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if not any(isinstance(h, QueueLogHandler) for h in root_logger.handlers):
        queue_handler = QueueLogHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        queue_handler.setFormatter(formatter)
        root_logger.addHandler(queue_handler)
    '''

def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error(message)

#################################
## for Oracle NetSuite dhis2 integration DHIS2 Integration ######



def get_option_code_attr_value_map( options_get_url, session_get, OPTION_META_ATTRIBUTE ):
    
    option_code_attr_value_map = {}
    
    #Option code attributeValue
    #https://links.hispindia.org/ippf_uin/api/options?fields=id,name,code,attributeValues&filter=attributeValues.attribute.id:eq:ZoJYwqgoGI6&paging=false
    option_details_url = (
        f"{options_get_url}.json"
        f"?fields=id,name,code,attributeValues"
        f"&filter=attributeValues.attribute.id:eq:{OPTION_META_ATTRIBUTE}&paging=false"
    )

    #print(option_details_url)
    #print(f" event_search_url : {event_get_url}" )
    #response = requests.get(event_search_url, auth=HTTPBasicAuth(dhis2_username, dhis2_password))
    option_response = session_get.get(option_details_url)
    
    if option_response.status_code == 200:
        option_response_data = option_response.json()
        
        if option_response_data:
            '''
            for option in option_response_data.get("options", []):
                code = option.get("code")

            for attr in option.get("attributeValues", []):
                if attr.get("attribute", {}).get("id") == OPTION_META_ATTRIBUTE:
                    option_code_attr_value_map[code] = attr.get("value")
            '''


            
            option_code_attr_value_map = {
            option["code"]: attr["value"]
            for option in option_response_data.get("options", [])
                for attr in option.get("attributeValues", [])
                    if attr.get("attribute", {}).get("id") == OPTION_META_ATTRIBUTE
            }   

            return option_code_attr_value_map
    
    else:
        return []


def get_orgunit_details(orgunit_post_url, session_post ):
    
    org_map = {}
    #UIN code search
    #https://links.hispindia.org/ippf_co/api/organisationUnits.json?fields=id,name,code,level,children[id,name,attributeVattributeValues[attribute[id],value]alues]&filter=level:eq:2&paging=false
    
    orgunit_details_url = (
        f"{orgunit_post_url}.json"
        f"?fields=id,name,code,level,children[id,name,attributeValues[attribute[id],value]]"
        f"&filter=level:eq:2&paging=false"
    )

    #print(orgunit_details_url)
    #print(f" event_search_url : {event_get_url}" )
    #response = requests.get(event_search_url, auth=HTTPBasicAuth(dhis2_username, dhis2_password))
    response = session_post.get(orgunit_details_url)
    
    if response.status_code == 200:
        orgunit_response_data = response.json()
       
        for org in orgunit_response_data.get("organisationUnits", []):
            code = org.get("code")

            # Skip if no code (like KYC Affiliates in your JSON)
            if not code:
                continue

            org_map[code] = {
                "orgUnitUID": org.get("id"),
                "children": [
                    {
                        "name": child.get("name"),
                        "id": child.get("id"),
                        "attributeValues": child.get("attributeValues", [])
                    }
                    for child in org.get("children", [])
                ]
            }

        return org_map
    else:
        return []
    

def get_org_and_child_uid(org_map, region_code, child_name):

    parent = org_map.get(region_code)
    
    if not parent:
        return None, None

    org_uid = parent.get("orgUnitUID")

    for child in parent.get("children", []):
        if child.get("name") == child_name:
            return org_uid, child.get("id")

    return org_uid, None  # parent found but child not found

def get_org_and_child_attribute_value_temp(org_map, region_code, child_name, attribute_id):

    parent = org_map.get(region_code)
    
    if not parent:
        return None, None, None

    org_uid = parent.get("orgUnitUID")

    for child in parent.get("children", []):
        if child.get("name") == child_name:
            
            # search inside attributeValues
            for attr in child.get("attributeValues", []):
                if attr.get("attribute", {}).get("id") == attribute_id:
                    return org_uid, child.get("id"), attr.get("value")

            # child found but attribute not found
            return org_uid, None, None

    # parent found but child not found
    return org_uid, None, None

def get_org_and_child_attribute_value(org_map, region_code, attribute_id):

    parent = org_map.get(region_code)
    
    if not parent:
        return None, None, None

    org_uid = parent.get("orgUnitUID")

    for child in parent.get("children", []):
        for attr in child.get("attributeValues", []):
            if attr.get("attribute", {}).get("id") == attribute_id:
                return org_uid, child.get("id"), attr.get("value")

    # If we finish checking ALL children and nothing found
    return org_uid, None, None


def get_single_orgunit_details(orgunit_post_url, session_post, orguit_uid):
    
    #https://links.hispindia.org/ippf_co/api/organisationUnits/vXS042miHoG.json
    orgunit_get_url = f"{orgunit_post_url}/{orguit_uid}.json?fields=*"

    #print(orgunit_get_url)
    #print(f" event_search_url : {event_get_url}" )
    #response = requests.get(event_search_url, auth=HTTPBasicAuth(dhis2_username, dhis2_password))
    response = session_post.get(orgunit_get_url)
    
    if response.status_code == 200:
        orgunit_response_data = response.json()
        #print(response)
        #print(orgunit_response_data)
        return orgunit_response_data 
    else:
        return []
    
def check_orgunit_exists_in_org_grp(org_unit_grp_get_url, session_get, org_unit_grp_id, org_unit_id ):
    #https://links.hispindia.org/ippf_uin/api/organisationUnitGroups/yyfCrWDmoKf.json?fields=id,name,organisationUnits[id,name]
        
    orgunit_grp_get_url = f"{org_unit_grp_get_url}/{org_unit_grp_id}.jsonfields=id,name,organisationUnits[id,name]"
    
    response = session_get.get(orgunit_grp_get_url)
    if response.status_code == 200:

        org_unit_grp_response_data = response.json()

        org_unit_grp_members = org_unit_grp_response_data.get("organisationUnits", [])
      
        for org_unit in org_unit_grp_members:
            if org_unit.get("id") == org_unit_id:
                return 1
        return 2


def check_orgunit_exists(org_unit_grp_get_url, session_get, org_unit_grp_id, org_unit_id):
    #https://links.hispindia.org/ippf_uin/api/organisationUnitGroups/yyfCrWDmoKf.json?fields=id,name,organisationUnits[id,name]
    #https://links.hispindia.org/ippf_uin/api/organisationUnitGroups/yyfCrWDmoKf.jsonfields=id,name,organisationUnits[id,name]
    orgunit_grp_get_url = f"{org_unit_grp_get_url}/{org_unit_grp_id}.json?fields=id,name,organisationUnits[id,name]"
    #print(orgunit_grp_get_url)
    response = session_get.get(orgunit_grp_get_url)
    if response.status_code == 200:
        org_unit_grp_response_data = response.json()
        #org_unit_grp_members = org_unit_grp_response_data.get("organisationUnits", [])
        return 1 if any(
            org_unit.get("id") == org_unit_id 
            for org_unit in org_unit_grp_response_data.get("organisationUnits", [])
        ) else 2

def push_orgunit_in_dhis2(orgunit_post_url, session_post, orgUnit_post_payload, region_code, legal_name, uin_code, tei, tei_get_url, session_get, attribute_id ):
    #
    try:
        #orgunit_post_url = f"{orgunit_post_url}"
        response = session_post.post(orgunit_post_url, data=json.dumps(orgUnit_post_payload), headers={"Content-Type": "application/json"})
        response.raise_for_status()
        
        print(f"Orgunit created successfully for Region : {region_code}, orgunit_name : {legal_name}, uin_code : {uin_code}")
        logging.info(f"Orgunit created successfully for Region : {region_code}, orgunit_name : {legal_name}, uin_code : {uin_code}")
        
        update_tei_attributeValue_in_dhis2( attribute_id, tei, tei_get_url, session_get )
    except requests.RequestException as e:
        resp_msg=response.text
        ind=resp_msg.find('conflict')
        
        print(f"Failed to create Orgunit. for Region : {region_code}. Error: {response.text}")
        logging.error(f"Failed to create Orgunit for Region : {region_code}. orgunit name : {legal_name} . Status code: {response.status_code} . error details: {response.json()} .Error: {response.text}")



def update_orgunit_in_dhis2(orgunit_post_url, session_post, orgUnit_post_payload, orguit_uid, region_code, legal_name, uin_code, tei, tei_get_url, session_get, attribute_id ):
    #
    try:
        orgunit_update_url = f"{orgunit_post_url}/{orguit_uid}"
        response = session_post.put(orgunit_update_url, data=json.dumps(orgUnit_post_payload), headers={"Content-Type": "application/json"})
        response.raise_for_status()
        
        print(f"Orgunit updated successfully for Region : {region_code}, orgunit_name : {legal_name}, orguit_uid : {orguit_uid}, uin_code : {uin_code}")
        logging.info(f"Orgunit updated successfully for Region : {region_code}, orgunit_name : {legal_name}, orguit_uid : {orguit_uid}, uin_code : {uin_code}")
        update_tei_attributeValue_in_dhis2( attribute_id, tei, tei_get_url, session_get )
    except requests.RequestException as e:
        resp_msg=response.text
        ind=resp_msg.find('conflict')
        
        print(f"Failed to update Orgunit. for Region : {region_code}.  orguit_uid : {orguit_uid}. Error: {response.text}")
        logging.error(f"Failed to update Orgunit for Region : {region_code}. orgunit name : {legal_name} , orguit_uid : {orguit_uid} . Status code: {response.status_code} . error details: {response.json()} .Error: {response.text}")




def get_tei_details(tei_get_url, session_get, ORGUNIT_UID, PROGRAM_UID, SEARCH_TEI_ATTRIBUTE_UID, SEARCH_VALUE, UIN_SYNC_NETSUITE_DHIS2_ATTRIBUTE_UID, LEGAL_NAME_ATTRIBUTE_UID ):
    
    #UIN code search
    #https://links.hispindia.org/ippf_uin/api/trackedEntityInstances.json?ou=Eo4s43hL1Vi&ouMode=DESCENDANTS&program=w6sqrDv2VK8&filter=qZcVhl6kfpc:neq:%27%27&skipPaging=true
    #https://links.hispindia.org/ippf_uin/api/trackedEntityInstances.json?ou=Eo4s43hL1Vi&ouMode=DESCENDANTS&program=w6sqrDv2VK8&filter=qZcVhl6kfpc:neq:%27%27&filter=pbRJfByMgk3:neq:true
    #https://links.hispindia.org/ippf_uin/api/trackedEntityInstances.json?ou=Eo4s43hL1Vi&ouMode=DESCENDANTS&program=w6sqrDv2VK8&filter=qZcVhl6kfpc:neq:%27%27
    #https://links.hispindia.org/ippf_uin/api/trackedEntityInstances.json?ou=iR2btIxN87s&ouMode=DESCENDANTS&program=GJbgrJjzCrr&filter=pkLdNynZWat:neq:%27%27
    #https://links.hispindia.org/ippf_uin/api/trackedEntityInstances.json?ou=iR2btIxN87s&ouMode=DESCENDANTS&program=GJbgrJjzCrr&filter=IzbdGgEgQ3T:eq:In%20Progress
    #tei_search_url = f"{tei_get_url}?ou={ORGUNIT_UID}&ouMode=DESCENDANTS&program={PROGRAM_UID}&filter=HKw3ToP2354:eq:{beneficiary_mapping_reg_id}"
    final_tei_list = []
    tei_search_url = (
        f"{tei_get_url}.json"
        f"?ou={ORGUNIT_UID}&ouMode=DESCENDANTS"
        f"&program={PROGRAM_UID}"
        f"&filter={SEARCH_TEI_ATTRIBUTE_UID}:neq:{SEARCH_VALUE}&skipPaging=true"
    )

    #print(tei_search_url)
    #print(f" event_search_url : {event_get_url}" )
    #response = requests.get(event_search_url, auth=HTTPBasicAuth(dhis2_username, dhis2_password))
    response = session_get.get(tei_search_url)
    
    if response.status_code != 200:
        return []
    
    if response.status_code == 200:
        tei_response_data = response.json()
        #print(response)
        #print(tei_response_data)
       
        #print(f"tei_response_data trackedEntityInstance : {tei_response_data.get('trackedEntityInstance')}" )
        teiattributesValue = tei_response_data.get('attributes',[])
        teis = tei_response_data.get('trackedEntityInstances', [])


        if teis:
            for tei in teis:
                # Convert attributes list into dictionary
                attributes_dict = {
                    #attr["displayName"]: attr.get("value", "")
                    attr["attribute"]: attr.get("value", "")
                    for attr in tei.get("attributes", [])
                }
                if (
                    not attributes_dict.get(UIN_SYNC_NETSUITE_DHIS2_ATTRIBUTE_UID) and 
                    attributes_dict.get(LEGAL_NAME_ATTRIBUTE_UID) and 
                    attributes_dict.get(SEARCH_TEI_ATTRIBUTE_UID)
                ):
                    #print("---- TEI ----")
                    #print("UIN_SYNC:", attributes_dict.get(UIN_SYNC_BPR_DHIS2_ATTRIBUTE_UID))
                    #print("LEGAL_NAME:", attributes_dict.get(LEGAL_NAME_ATTRIBUTE_UID))
                    #print("SEARCH_ATTR:", attributes_dict.get(SEARCH_TEI_ATTRIBUTE_UID))
                    final_tei_list.append(tei)
                #print(f"teiattributesValue : {teiattributesValue}" )
        
        return final_tei_list 
    else:
        return []


def get_tei_latest_event_details(event_get_url, session_get, tei_uid, PROGRAM_UID, PROGRAM_STAGE_COMP_CHECK_UID ):

    #https://links.hispindia.org/ippf_uin/api/events.json?trackedEntityInstance=Fjdh85rHIQi&program=w6sqrDv2VK8&programStage=jKxGLMkHnHy&order=eventDate:desc&fields=event,orgUnit,eventDate,dataValues[dataElement,value]&skipPaging=true&&filter=gDI26Sq88pk
    #https://links.hispindia.org/ippf_uin/api/events.json?trackedEntityInstance=Fjdh85rHIQi&program=w6sqrDv2VK8&programStage=jKxGLMkHnHy&order=eventDate:desc&fields=event,orgUnit,eventDate,dataValues&skipPaging=true&&filter=gDI26Sq88pk
    
    latest_event = None

    tei_events_url = (
        f"{event_get_url}.json"
        f"?trackedEntityInstance={tei_uid}"
        f"&program={PROGRAM_UID}"
        f"&programStage={PROGRAM_STAGE_COMP_CHECK_UID}"
        f"&order=eventDate:desc"
        f"&fields=event,orgUnit,eventDate,dataValues[dataElement,value]&skipPaging=true"
    )

    #print(tei_events_url)
    #print( f"tei_events_url for TEI { tei_uid } : { tei_events_url }")
    event_response = session_get.get(tei_events_url)

    if event_response.status_code != 200:
        return None
    
    all_events_data = event_response.json()

    if all_events_data:

        events = all_events_data.get("events", [])

        for temp_event in events:
            if temp_event.get("dataValues") and len(temp_event["dataValues"]) > 0:   # non-empty list evaluates to True and If dataValues key might not exist
                latest_event = temp_event
                break   # stop at first match (because already descending)

        if latest_event:
            print("Latest Event ID:", latest_event["event"])
            print("Event Date:", latest_event["eventDate"])
            return latest_event   # return first matching event

        else:
            #print("No event found with dataValues. tei :" , tei_uid)
            print( f"No event found with dataValues. tei . { tei_uid } and program {PROGRAM_UID} and stage { PROGRAM_STAGE_COMP_CHECK_UID }" )
            return None

    return None   # if no matching event found


def get_tei_event_details(tei_get_url, session_get, tei_uid, PROGRAM_STAGE_UID):

  #https://links.hispindia.org/ippf_uin/api/trackedEntityInstances/g2e5lEB62la.json?fields=enrollments[events[event,program,programStage,orgUnit,dataValues[dataElement,value]]]
    
    tei_events_url = (
        f"{tei_get_url}/{tei_uid}.json"
        f"?fields=enrollments[events[event,program,programStage,orgUnit,dataValues[dataElement,value]]]"
    )

    #print(tei_events_url)
    response = session_get.get(tei_events_url)

    if response.status_code != 200:
        return None

    data = response.json()

    # Loop through all enrollments
    for enrollment in data.get("enrollments", []):
        for event in enrollment.get("events", []):
            #print("tei_event:", event)
            #print("tei_event_programstage:", event.get("programStage"))
            if event.get("programStage") == PROGRAM_STAGE_UID:
                return event   # return first matching event

    return None   # if no matching event found

def update_tei_attributeValue_in_dhis2( attribute_id, tei, tei_get_url, session_get ):
    #
    try:
        
        if tei:
            new_attribute_value = "true"     
            tei_uid = tei["trackedEntityInstance"]
            org_unit = tei["orgUnit"]
            
            '''
            tempTeiAttributeValues = []
            teiAttributeValue = {
                "attribute": attribute_id,
                "value": new_attribute_value
            }
           
            tempTeiAttributeValues.insert(0, teiAttributeValue)
            tei_updateAttributeValue_payload = {
                "orgUnit": org_unit,
                "attributes": tempTeiAttributeValues
            }
            '''

            existing_attributes = tei.get("attributes", [])

            updated = False
            for attr in existing_attributes:
                if attr["attribute"] == attribute_id:
                    attr["value"] = new_attribute_value
                    updated = True

            if not updated:
                existing_attributes.append({
                    "attribute": attribute_id,
                    "value": new_attribute_value
                })

            tei_updateAttributeValue_payload = {
                "orgUnit": org_unit,
                "attributes": existing_attributes
            }

            tei_attributeValue_update_url = f"{tei_get_url}/{tei_uid}"

            #event_update_url = f"{dhis2_api_url}events/{eventUID}/{dataElementUid}"
            response = session_get.put(tei_attributeValue_update_url, json=tei_updateAttributeValue_payload )
            
            response.raise_for_status()

            if response.status_code == 200:
                conflictsDetails   = response.json().get("response", {}).get("conflicts")
        
                print(f"TEI updated successfully. updated tei : {tei_uid}. attribute : {attribute_id} .value : {new_attribute_value}")
                logging.info(f"TEI updated successfully. updated tei : {tei_uid}. attribute :  {attribute_id} .value : {new_attribute_value}")
                #logging.info(f"Event created successfully . BenVisitID : {BenVisitID} . BeneficiaryRegID : {BeneficiaryRegID}. Event count: {event_count}. Event uid: {event_uid}" )
                #logging.info("MySQL connection closed")

            else:
                print(f"Failed to update TEI attributeValue. Error: {response.text}")
                logging.error(f"Failed to update TEI attributeValue.conflictsDetails : {conflictsDetails} .Status code: {response.status_code} .error details: {response.json()} .Error: {response.text}")

    except requests.RequestException as e:
        resp_msg=response.text
        ind=resp_msg.find('conflict')
        #print(f'####################################################### FAILED #######################################################', flush=True)
        #print(f'RECORD NO.: {record_count}                    current benID: {row["BeneficiaryRegID"]}', flush=True)
        #print(f"Failed to create events. Error: {resp_msg[ind-1:]}", flush=True)
        #print(f"Failed to create events. Error: {response.text}")
        #logging.error(f"Failed to create events .event_uid : {event_uid} . row : {row} . Status code: {response.status_code} . error details: {response.json()} .Error: {response.text}")

        with open(LOG_FILE_TEI_ATTRIBUTE_VALUE_ERROR_LOG, 'a') as fail_record:
            fail_record.write(f'\ncurrent tei_uid: {tei_uid}. \n Error Message: {resp_msg[ind-1:]}\n')
            fail_record.write("----------------------------------------------------------------------------------------\n")

        print(f" Failed to update TEI attributeValue. Error: {response.text}")
        logging.error(f"Failed to update TEI attributeValue . tei_uid : {tei_uid} . Status code: {response.status_code} . error details: {response.json()} .Error: {response.text}")

def update_eventDataValue_in_dhis2( tei_uid, event_get_url, session_get, event_data_value, eventUID, dataElementUid, program_uid):

    #print( f" updateEventDataValue . { updateEventDataValue }" )
    event_update_url = f"{event_get_url}events/{eventUID}/{dataElementUid}"
    #print( f"event_update_url . { event_update_url }" )

    updateEventDataValue = {
        "event": eventUID,
        "program": program_uid,
        "dataValues": [
            { "dataElement":dataElementUid, "value": event_data_value }
        ]                 
    }

    response = session_get.put(event_update_url, json=updateEventDataValue )
    
    if response.status_code == 200:
        conflictsDetails   = response.json().get("response", {}).get("conflicts")
        #description   = response.json().get("response", {}).get("description")
        impCount = response.json().get("response", {}).get("importCount").get("imported")
        updateCount = response.json().get("response", {}).get("importCount").get("updated")
        ignoreCount = response.json().get("response", {}).get("importCount").get("ignored")
       
        print(f"Events updated successfully. tei_uid : {tei_uid}. updated event : {eventUID}. impCount : {impCount} .updateCount : {updateCount} .ignoreCount : {ignoreCount}")
        logging.info(f"Events updated successfully. tei_uid : {tei_uid}. updated event : {eventUID}. impCount : {impCount} .updateCount : {updateCount} .ignoreCount : {ignoreCount}")
       
    else:
        print(f"Failed to update events. Error: {response.text}")
        logging.error(f"Failed to update events. tei_uid : {tei_uid} .conflictsDetails : {conflictsDetails} .Status code: {response.status_code} .error details: {response.json()} .Error: {response.text}")



# ==================== FUNCTION 2: Upload Certificate ====================
def upload_certificate(uin_code, folder_id, pdf_file_path, archive_folder_id=None, archive_enabled=True):

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


def get_bank_details(vendor_id, bank_type):
    """Retrieve bank details for a vendor"""
   
    full_url = f"{RESTLET_URL}?script={SCRIPT_ID}&deploy={DEPLOY_ID}&vendorId={vendor_id}&bankType={bank_type}"
   
    #full_url = https://4533524-sb1.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=customscript_bank_details_api&deploy=customdeploy_bank_details_api&vendorId=41930&bankType=Primary"
    
    # "https://4533524-sb1.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=1244&deploy=1&vendorId=41930&bankType=Primary"
    logging.info(f"Fetching bank details for Vendor ID: {vendor_id}, Type: {bank_type}")
   
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
            logging.info(f"✅ Found {result['data']['count']} bank detail record(s)")
            if 'requestId' in result.get('metadata', {}):
                logging.info(f"Request ID: {result['metadata']['requestId']}")
        else:
            logging.error(f"❌ Failed: {result.get('message')}")
       
        return result
       
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return None

def create_bank_details(vendor_internal_id,primary_bank_payload):
    
    primary_bank_payload["vendorId"] = vendor_internal_id

    full_url = f"{RESTLET_URL}?script={SCRIPT_ID}&deploy={DEPLOY_ID}"
    try:
        response = requests.post(full_url, auth=auth, headers=headers, data=json.dumps(primary_bank_payload), timeout=60)
       
        logging.info(f"Response Status: {response.status_code}")

        print(f"Response Status: {response.status_code}")

        result = response.json()

        print("FULL RESPONSE:", result)
       
        # Log request ID for tracking
        if 'metadata' in result and 'requestId' in result['metadata']:
            logging.info(f"Request ID: {result['metadata']['requestId']}")
       
        if result.get('success'):
            logging.info(f"Bank details created successfully! With Record ID: {result['data']['recordId']}")
            logging.info(f"Processing Time: {result['metadata']['processingTimeMs']}ms")
        else:
            logging.error(f"Failed: {result.get('message')}")
            if 'missingFields' in result:
                logging.error(f"Missing fields: {result['missingFields']}")
       
        return result
       
    except requests.exceptions.Timeout:
        logging.error("Request timeout after 60 seconds")
        return None
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return None


def create_vendor_in_netsuite_and_update_dhis2(primary_bank_payload,
    netsuite_payload, tei_uid, legal_name, tei_get_url, 
    session_get, attribute_id, event_get_url, latest_event_uin_control_uid, 
    dataElementUid,PROGRAM_UID,uin_code, file_upload_de_uid,tei ):
    
    url = f"{NETSUITE_BASE_URL}/services/rest/record/v1/vendor"
    #print(" post start" )
    print("\n📋 STEP 1: Create Vendor in Oracle NetSuite")

    logging.info(f"STEP 1: Create Vendor in Oracle NetSuite")

    post_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Post start : { post_start } " )
    logging.info("-" * 50)
    print("-" * 50)
    response = requests.post(
        url,
        auth=auth,
        json=netsuite_payload,
        headers={"Content-Type": "application/json",
                "Accept": "application/json"}
    )

    print("1 Status:", response.status_code)
    #print("Response:", response.text)

    #print("2 Status:", response.status_code)

    if response.status_code == 204:
        print("Vendor created successfully.")
        logging.info(f"Vendor created successfully. for legal_name: {legal_name} tei_uid:  {tei_uid} ")
    else:
        print("Response:", response.text)
        logging.error("Response Error: ", response.text)
    #print("3 Status:", response.status_code)

    if response.content:
        data = response.json()
        print(data)
    else:
        print("Success - No content returned (204)")

    #print("Location Header:", response.headers) 

    location = response.headers.get("Location")
    print("Location Header:", location)
    logging.info(f"Vendor URL Location Header:. {location}")

    if location:
        vendor_id = location.rstrip("/").split("/")[-1]
        print("Vendor Internal ID:", vendor_id)
        logging.info(f"Vendor Internal ID :. {vendor_id}")

        post_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Vendor Post end :  {post_end} " )
        logging.info("-" * 50)
        print("-" * 50)

        get_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Get Created vendor details : {get_start} ")
        logging.info(f"Get Created vendor details : {get_start} ")

        print("-" * 50)
        logging.info("-" * 50)
        created_supplier_response = requests.get(
            location,
            auth=auth,
            headers={"Accept": "application/json"}
        )

        if created_supplier_response.status_code == 200:
            get_response_data = created_supplier_response.json()

            entity_id_full = get_response_data.get("entityId")
            supplier_code = entity_id_full.split(" ")[0] if entity_id_full else None

            print("Full entityId:", entity_id_full)
            print("Supplier Code:", supplier_code)

            logging.info(f"Full entityId: . {entity_id_full}, Supplier Code: {supplier_code} ")

            vendor_internal_id = get_response_data.get("id")
            uin_number = get_response_data.get("custentity_ippf_uin_number")
            email = get_response_data.get("email")
            payables_account_id = get_response_data.get("payablesAccount", {}).get("id")

            print("vendor_internal_id:", vendor_internal_id)
            print("uin_number:", uin_number)
            print("email:", email)
            print("payables_account_id:", payables_account_id)


            print("\n" + "=" * 60)
            print("EXAMPLE 2: Create Bank Details (With Optional Fields)")
            logging.info("EXAMPLE 2: Create Bank Details (With Optional Fields)")
            logging.info("=" * 60)
            print("=" * 60)
        
            result = create_bank_details(
                vendor_internal_id,primary_bank_payload
            )

        logging.info("\n" + "=" * 60)
        logging.info("EXAMPLE 3: Get Bank Details")
        logging.info("=" * 60)
        print("\n" + "=" * 60)
        print("EXAMPLE 3: Get Bank Details")
        print("=" * 60)
    
        result = get_bank_details(vendor_internal_id, "Primary")

        #https://links.hispindia.org/ippf_uin/api/events/files?eventUid=MilMyjFj70Z&dataElementUid=R6nujxC6zLD

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
                #print(f"vendorName: {record['vendorName']}")
                #print(f"country: {record['country']}")
                
        else:
            print("Error:", created_supplier_response.text)
            logging.error("Get Response Error for new vendor creation: ", created_supplier_response.text)
        
        
        logging.info("\n" + "STEP 1: Downlods file from source DHIS2")
        print("\n📋 STEP 1: Downlods file from source DHIS2")

        #pdf_url = #https://links.hispindia.org/ippf_uin/api/events/files?eventUid=MilMyjFj70Z&dataElementUid=R6nujxC6zLD

        session_get = requests.Session()
        session_get.auth = (DHIS2_GET_USER, DHIS2_GET_PASSWORD)

        file_download_url = (
            f"{DHIS2_GET_API_URL}/events/files"
            f"?eventUid={latest_event_uin_control_uid}"
            f"&dataElementUid={file_upload_de_uid}"
        )

        file_resource_response = session_get.get(file_download_url)

        #print("status_code:", file_resource_response.status_code)
        #print("Content-Type:", file_resource_response.headers.get("Content-Type"))
        #print("preview_response:", file_resource_response.text[:200])  # preview response

        # Check response
        if file_resource_response.status_code == 200:
            print("PDF downloaded successfully")
        
            #file_path = "downloaded_file.pdf"

            #custom_file_name = "Accuity_IPPF-THA-009_2026-03-25.pdf"
            
            # Create custom name
            date_and_time_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            date_and_time = datetime.now().strftime("%Y-%m-%d")
            
            file_path = f"Accuity_{uin_code}_{date_and_time}.pdf"

            with open(file_path, "wb") as f:
                f.write(file_resource_response.content)

            print("Saved to:", file_path)
            logging.info(f"Saved to: {file_path}")
            print("-" * 60)
            logging.info("-" * 60)

            print("\n📋 STEP 2: Upload Certificate in Oracle NetSuite")
            logging.info(f"STEP 2: Upload Certificate in Oracle NetSuite")
        
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
                logging.info(f"Certificate Uploaded Successfully!")
                print(f"File ID: {cert_result['data']['fileId']}")
                logging.info(f"File ID: {cert_result['data']['fileId']}")
                print(f"File Name: {cert_result['data']['fileName']}")
                print(f"Folder: {cert_result['data']['folderPath']}")
                
                if cert_result['data'].get('oldFileId'):
                    print(f"Old Certificate Archived: {cert_result['data']['oldFileId']}")
                    logging.info(f"Old Certificate Archived: {cert_result['data']['oldFileId']}")
            else:
                print(f"\n❌ Certificate Upload Failed: {cert_result.get('message')}")
                logging.error(f"\n❌ Certificate Upload Failed: {cert_result.get('message')}")

            print("-" * 60)
            logging.info("-" * 60)

            #update_eventDataValue_in_dhis2( tei_uid, event_get_url, session_get, supplier_code, latest_event_uin_control_uid, dataElementUid, PROGRAM_UID )
            #update_tei_attributeValue_in_dhis2( attribute_id, tei_uid, tei_get_url, session_get )

        else:
            print("❌ Failed to Downlods file from source DHIS2:", file_resource_response.status_code)
            print("❌ Failed: to report download from source dhis2", file_resource_response.text)
            logging.error("❌ Failed: to report download from source dhis2", file_resource_response.text)


        #update_eventDataValue_in_dhis2( tei_uid, event_get_url, session_get, supplier_code, latest_event_uin_control_uid, dataElementUid, PROGRAM_UID )
        update_tei_attributeValue_in_dhis2( attribute_id, tei, tei_get_url, session_get )


        get_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("-" * 50)
        print(f"Get end : {get_end}" )
        print("-" * 50)


# ================= CONFIG =================
HEADERS_JSON = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


# ================= HELPER =================
def safe_json(response):
    try:
        return response.json()
    except Exception:
        return {}


# ================= DHIS2 =================
def update_tei_attribute_value(
    attribute_id,
    tei,
    tei_base_url,
    session,
    new_value
):
    try:
        tei_uid = tei["trackedEntityInstance"]
        org_unit = tei["orgUnit"]

        existing_attributes = tei.get("attributes", [])

        updated = False
        for attr in existing_attributes:
            if attr["attribute"] == attribute_id:
                attr["value"] = new_value
                updated = True
                break

        if not updated:
            existing_attributes.append({
                "attribute": attribute_id,
                "value": new_value
            })

        payload = {
            "trackedEntityInstance": tei_uid,
            "orgUnit": org_unit,
            "attributes": existing_attributes
        }

        url = f"{tei_base_url}/{tei_uid}"

        response = session.put(url, json=payload)
        response.raise_for_status()

        print(f"✅ TEI updated | TEI: {tei_uid}, Attribute: {attribute_id}, Value: {new_value}")
        logging.info(f"TEI updated | TEI: {tei_uid}, Attribute: {attribute_id}, Value: {new_value}")

    except requests.RequestException as e:
        msg = getattr(e.response, "text", str(e))
        logging.error(f"TEI update failed | TEI: {tei_uid} | Error: {msg}")
        print(f"TEI update failed | TEI: {tei_uid} | Error: {msg}")


def update_event_data_value(
    tei_uid,
    event_base_url,
    session,
    event_uid,
    program_uid,
    data_element_uid,
    value
):
    try:
        url = f"{event_base_url}/events/{event_uid}"

        payload = {
            "event": event_uid,
            "program": program_uid,
            "dataValues": [
                {
                    "dataElement": data_element_uid,
                    "value": value
                }
            ]
        }

        response = session.put(url, json=payload)
        response.raise_for_status()

        data = safe_json(response)
        import_count = data.get("response", {}).get("importCount", {})

        logging.info(
            f"Event updated | TEI: {tei_uid}, Event: {event_uid}, "
            f"Imported: {import_count.get('imported')}, "
            f"Updated: {import_count.get('updated')}"
        )

    except requests.RequestException as e:
        msg = getattr(e.response, "text", str(e))
        
        print(f"Event update failed | TEI: {tei_uid}, Event: {event_uid} | Error: {msg}")
        logging.error(
            f"Event update failed | TEI: {tei_uid}, Event: {event_uid} | Error: {msg}"
        )


# ================= NETSUITE =================
def create_vendor_netsuite(netsuite_url, payload):
    try:
        response = requests.post(
            netsuite_url,
            auth=auth,
            json=payload,
            headers=HEADERS_JSON
        )

        if response.status_code not in (200, 201, 204):
            logging.error(f"Vendor creation failed: {response.text}")
            return None

        location = response.headers.get("Location")
        
        print("Location Header:", location)
        logging.info(f"Vendor URL Location Header:. {location}")

        if not location:
            logging.error(f"Location header missing")
            return None

        vendor_id = location.rstrip("/").split("/")[-1]

        logging.info(f"Vendor created | ID: {vendor_id}")

        return location

    except requests.RequestException as e:
        logging.error(f"NetSuite error: {str(e)}")
        return None


def get_vendor_details(location):
    try:
        response = requests.get(location, auth=auth, headers=HEADERS_JSON)
        response.raise_for_status()

        data = response.json()

        entity_id = data.get("entityId")
        entity_id_full = data.get("entityId")

        #supplier_code = entity_id_full.split(" ")[0] if entity_id_full else None

        supplier_code = entity_id.split(" ")[0] if entity_id else None
        
        print("Full entityId:", entity_id_full)
        print("Supplier Code:", supplier_code)

        logging.info(f"Full entityId: . {entity_id_full}, Supplier Code: {supplier_code} ")

        return {
            "supplier_code": supplier_code,
            "vendor_id": data.get("id"),
            "email": data.get("email")
        }

    except requests.RequestException as e:
        logging.error(f"Fetch vendor failed: {str(e)}")
        return None


# ================= MAIN FLOW =================
def create_vendor_and_sync_dhis2(
    netsuite_payload,
    tei,
    tei_uid,
    config,session_get
):
    print("\n📋 STEP 1: Create Vendor in NetSuite")
    logging.info("STEP 1: Create Vendor")

    location = create_vendor_netsuite(
        config["NETSUITE_URL"],
        netsuite_payload
    )

    if not location:
        return

    print("📥 STEP 2: Fetch Vendor Details")
    logging.info("STEP 2: Fetch Vendor Details")
    vendor_data = get_vendor_details(location)

    if not vendor_data:
        return

    supplier_code = vendor_data["supplier_code"]

    print("🔄 STEP 3: Update DHIS2")

    # Update Event
    update_event_data_value(
        tei_uid=tei_uid,
        event_base_url=config["DHIS2_EVENT_URL"],
        session=session_get,
        event_uid=config["EVENT_UID"],
        program_uid=config["PROGRAM_UID"],
        data_element_uid=config["DATA_ELEMENT_UID"],
        value=supplier_code
    )

    # Update TEI
    update_tei_attribute_value(
        attribute_id=config["ATTRIBUTE_ID"],
        tei=tei,
        tei_base_url=config["DHIS2_TEI_URL"],
        session=session_get,
        new_value="true"
    )

    print("✅ Flow completed successfully\n")
