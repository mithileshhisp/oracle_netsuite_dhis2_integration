# utils.py

import requests
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
load_dotenv()

FROM_EMAIL_ADDR = os.getenv("FROM_EMAIL_ADDR")
FROM_EMAIL_PASSWORD = os.getenv("FROM_EMAIL_PASSWORD")

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
    print(orgunit_grp_get_url)
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
        f"&filter={SEARCH_TEI_ATTRIBUTE_UID}:neq:{SEARCH_VALUE}"
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
            print("No event found with dataValues.")
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


