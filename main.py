## install
#pip install python-dotenv
#pip install psycopg2-binary
#pip install clickhouse-connect
#pip install --upgrade certifi
#pip install --upgrade requests certifi urllib3 ## for post data in hmis production certificate issue

import urllib3 ## for disable warning of Certificate
urllib3.disable_warnings() ## for disable warning of Certificate

import ssl
#import requests

from concurrent.futures import ThreadPoolExecutor
import requests
import certifi  ## for post data in hmis production certificate issue
import json
from datetime import datetime,date
#import nepali_datetime
# main.py
from dotenv import load_dotenv
import os
import time

load_dotenv()

from utils import (
    configure_logging,get_tei_details,get_tei_latest_event_details,
    log_info,log_error,get_option_code_attr_value_map,check_orgunit_exists
)

#print("OpenSSL version:", ssl.OPENSSL_VERSION)
#print("Certifi CA bundle:", requests.certs.where())

DHIS2_GET_API_URL = os.getenv("DHIS2_GET_API_URL")
DHIS2_GET_USER = os.getenv("DHIS2_GET_USER")
DHIS2_GET_PASSWORD = os.getenv("DHIS2_GET_PASSWORD")

DHIS2_POST_API_URL = os.getenv("DHIS2_POST_API_URL")
DHIS2_POST_USER = os.getenv("DHIS2_POST_USER")
DHIS2_POST_PASSWORD = os.getenv("DHIS2_POST_PASSWORD")


PROGRAM_UID = os.getenv("PROGRAM_UID")
PROGRAM_STAGE_COMP_CHECK_UID = os.getenv("PROGRAM_STAGE_COMP_CHECK_UID")
PROGRAM_STAGE_UIN_CONT_UID = os.getenv("PROGRAM_STAGE_UIN_CONT_UID")


SEARCH_TEI_ATTRIBUTE_UID = os.getenv("SEARCH_TEI_ATTRIBUTE_UID")

UIN_SYNC_NETSUITE_DHIS2_ATTRIBUTE_UID = os.getenv("UIN_SYNC_NETSUITE_DHIS2_ATTRIBUTE_UID")
REGION_NAME_ATTRIBUTE_UID = os.getenv("REGION_NAME_ATTRIBUTE_UID")
LEGAL_NAME_ATTRIBUTE_UID = os.getenv("LEGAL_NAME_ATTRIBUTE_UID")

DEFAULT_ADDRESS_ATTRIBUTE_UID = os.getenv("DEFAULT_ADDRESS_ATTRIBUTE_UID")
EMAIL_ATTRIBUTE_UID = os.getenv("EMAIL_ATTRIBUTE_UID")
PHONE_ATTRIBUTE_UID = os.getenv("PHONE_ATTRIBUTE_UID")

ORG_UNIT_GRP_UID = os.getenv("ORG_UNIT_GRP_UID")

SEARCH_VALUE = os.getenv("SEARCH_VALUE")
ORGUNIT_UID = os.getenv("ORGUNIT_UID")

ORG_UNIT_META_ATTRIBUTE = os.getenv("ORG_UNIT_META_ATTRIBUTE")

OPTION_META_ATTRIBUTE = os.getenv("OPTION_META_ATTRIBUTE")

orgunit_post_url = f"{DHIS2_POST_API_URL}organisationUnits"

options_get_url = f"{DHIS2_GET_API_URL}options"

org_unit_grp_get_url = f"{DHIS2_GET_API_URL}organisationUnitGroups"

tei_get_url = f"{DHIS2_GET_API_URL}trackedEntityInstances"
event_get_url = f"{DHIS2_GET_API_URL}events"

dataValueSet_endPoint = f"{DHIS2_POST_API_URL}dataValueSets"

namespace_url = f"{DHIS2_GET_API_URL}dataStore/accuityResponse/"
ACCUITY_FLOW_URL = os.getenv("ACCUITY_FLOW_URL_NEW")

#print( f" DHIS2_GET_USER. { DHIS2_GET_USER }, DHIS2_GET_PASSWORD  { DHIS2_GET_PASSWORD} " )

#DHIS2_AUTH_POST = ("hispdev", "Devhisp@1")
#session_post = requests.Session()
#session_post.auth = DHIS2_AUTH_POST

# Create a session object for persistent connection
#session_get = requests.Session()
#session_get.auth = DHIS2_AUTH_GET

raw_auth = os.getenv("DHIS2_AUTH")

if raw_auth is None:
    raise ValueError("DHIS2_AUTH is missing in .env")

if ":" not in raw_auth:
    raise ValueError("DHIS2_AUTH must be in user:password format")

user, pwd = raw_auth.split(":", 1)
#session_get.auth = (user, pwd)
'''
session_get = requests.Session()
session_get.auth = (DHIS2_GET_USER, DHIS2_GET_PASSWORD)

session_post = requests.Session()
session_post.auth = (DHIS2_POST_USER, DHIS2_POST_PASSWORD)
'''

#session_get.verify = False

RPA_DELAY = 10

def main_with_logger():

    configure_logging()

    current_time_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print( f"Oracle NetSuite dhis2 integration process start . { current_time_start }" )
    log_info(f"Oracle NetSuite dhis2 integration process start  . { current_time_start }")

    session_get = requests.Session()
    session_get.auth = (DHIS2_GET_USER, DHIS2_GET_PASSWORD)

    session_post = requests.Session()
    session_post.auth = (DHIS2_POST_USER, DHIS2_POST_PASSWORD)

    #session = requests.Session()
    #session_post.verify = certifi.where()

    #orgunit_list_map = get_orgunit_details( orgunit_post_url, session_post )

    option_code_attr_value_map = get_option_code_attr_value_map( options_get_url, session_get, OPTION_META_ATTRIBUTE )

    print(option_code_attr_value_map)
    
    tei_list = get_tei_details( tei_get_url, session_get, ORGUNIT_UID, PROGRAM_UID, SEARCH_TEI_ATTRIBUTE_UID, SEARCH_VALUE, UIN_SYNC_NETSUITE_DHIS2_ATTRIBUTE_UID, LEGAL_NAME_ATTRIBUTE_UID )
    
    print(f"trackedEntityInstances list Size {len(tei_list) }")
    log_info(f"trackedEntityInstances list Size {len(tei_list) } ")

    if tei_list:

        for tei in tei_list:
            tei_uid = tei["trackedEntityInstance"]
            org_unit = tei["orgUnit"]

            # Convert attributes list into dictionary
            attributes_dict = {
                #attr["displayName"]: attr.get("value", "")
                attr["attribute"]: attr.get("value", "")
                for attr in tei.get("attributes", [])
            }

            print("Source TEI UID:", tei_uid)
            print("Source Org Unit:", org_unit)
            #print("Legal Name:", attributes_dict.get("Legal Name"))
            #print("Source UIN Code: ", attributes_dict.get(SEARCH_TEI_ATTRIBUTE_UID))
            #print("Source Region: ", attributes_dict.get(REGION_NAME_ATTRIBUTE_UID))
            #print("Source Legal Name: ", attributes_dict.get(LEGAL_NAME_ATTRIBUTE_UID))
            
            #if not attributes_dict.get(UIN_SYNC_BPR_DHIS2_ATTRIBUTE_UID) and attributes_dict.get(LEGAL_NAME_ATTRIBUTE_UID) and attributes_dict.get(SEARCH_TEI_ATTRIBUTE_UID):
            if (
                not attributes_dict.get(UIN_SYNC_NETSUITE_DHIS2_ATTRIBUTE_UID) and 
                attributes_dict.get(LEGAL_NAME_ATTRIBUTE_UID) and 
                attributes_dict.get(SEARCH_TEI_ATTRIBUTE_UID)
            ):
                
                uin_code = attributes_dict.get(SEARCH_TEI_ATTRIBUTE_UID)
                region_code = attributes_dict.get(REGION_NAME_ATTRIBUTE_UID)
                legal_name = attributes_dict.get(LEGAL_NAME_ATTRIBUTE_UID)
                defaultAddress = attributes_dict.get(DEFAULT_ADDRESS_ATTRIBUTE_UID)
                
                sanctionCountry = check_orgunit_exists(org_unit_grp_get_url, session_get, ORG_UNIT_GRP_UID, org_unit)
                
                #sanctionCountry = attributes_dict.get("Wtvi1AZElXY")
                email = attributes_dict.get(EMAIL_ATTRIBUTE_UID)
                phone = attributes_dict.get(PHONE_ATTRIBUTE_UID)

                print("Source UIN Code :", uin_code)
                print("Source Region:", region_code)
                print("Source Legal Name:", legal_name)
                print("defaultAddress:", defaultAddress)
                print("sanctionCountry:", sanctionCountry)
                print("email:", email)
                print("phone:", phone)

                tei_latest_event_comp_check = get_tei_latest_event_details( event_get_url, session_get, tei_uid, PROGRAM_UID, PROGRAM_STAGE_COMP_CHECK_UID )
                tei_latest_event_uin_control = get_tei_latest_event_details( event_get_url, session_get, tei_uid, PROGRAM_UID, PROGRAM_STAGE_UIN_CONT_UID )

                if tei_latest_event_comp_check and tei_latest_event_uin_control:

                    event_datavalues_dict_comp_check = {
                        dataValue["dataElement"]: dataValue["value"]
                        for dataValue in tei_latest_event_comp_check.get("dataValues", [])
                    }

                    tei_latest_event_uin_control_check = {
                        dataValue["dataElement"]: dataValue["value"]
                        for dataValue in tei_latest_event_uin_control.get("dataValues", [])
                    }

                    if event_datavalues_dict_comp_check.get("gDI26Sq88pk") and tei_latest_event_uin_control_check.get("TbN2rRfJxGs"):
                        supplier_category = event_datavalues_dict_comp_check.get("gDI26Sq88pk")
                        print("supplier_category :", supplier_category)
                        print("supplier_category code :", option_code_attr_value_map[supplier_category])

                        supplier_currency = tei_latest_event_uin_control_check.get("TbN2rRfJxGs")
                        print("supplier_currency :", supplier_currency)
                       

            print("-" * 50)
            log_info("-" * 50)

        #print( f"dataValueSet_payload . { dataValueSet_payload }" )
        #push_dataValueSet_in_dhis2( dataValueSet_endPoint, session_post, dataValueSet_payload )
    
if __name__ == "__main__":

    #main()
    main_with_logger()
    current_time_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print( f"Oracle NetSuite dhis2 integration process finished . { current_time_end }" )
    log_info(f"Oracle NetSuite dhis2 integration process finished . { current_time_end }")

    try:
        #sendEmail()
        print( f"Oracle NetSuite dhis2 integration process finished . { current_time_end }" )
    except Exception as e:
        log_error(f"Email failed: {e}")
