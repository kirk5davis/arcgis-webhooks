import time
import logging
import concurrent.futures
from django.core.mail import EmailMessage
from arcgis.gis import GIS
from arcgis_webhooks.settings import ARCGIS_ENTERPRISE_URL, ARCGIS_ENTERPRISE_ADMIN, ARCGIS_ENTERPRISE_ADMIN_PW, DEFAULT_NOTIFICATION_RECIPIENTS, DEFAULT_NOTIFICATION_SENDER, ACCEPTED_GOVERNMENT_USER_DOMAIN_SUBSTRINGS

logger = logging.getLogger(__name__)


def _check_for_agency_group_access(gis_obj, input_email_domain):
    """returns a group to which a new user should be added based on an input email domain.
        Example: 'watech.wa.gov', agency domain returned would be 'watech'.
        A group with the tag 'agency-group' and 'watech' would need to exist for this funtion
        to return anything."""
    for sub_string in ACCEPTED_GOVERNMENT_USER_DOMAIN_SUBSTRINGS:
        input_email_domain = input_email_domain.replace(sub_string, "")
    agency_domain = input_email_domain
    possible_agency_groups = gis_obj.groups.search("agency_group")
    for group in possible_agency_groups:
        if agency_domain in group.tags:
            return group
    return None


def _email_check(input_payload):
    gis = GIS(ARCGIS_ENTERPRISE_URL, ARCGIS_ENTERPRISE_ADMIN, ARCGIS_ENTERPRISE_ADMIN_PW)
    new_userid = next(i for i in input_payload['events'])['id']
    new_user_email = gis.users.get(username=new_userid).email
    email_domain = new_user_email.split("@")[-1]
    if any(sub_string in email_domain for sub_string in ACCEPTED_GOVERNMENT_USER_DOMAIN_SUBSTRINGS):
        # government email exists, check for agency group and update user
        status = "SUCCESSFUL"
        html_content = f"""
                        <h2><b>{status}</b> new user added to GeoPortal 2.0</h2> 
                        <p>User: {new_userid} - {new_user_email}</p><p>Processed: {time.ctime()}</p>
                    """
        agency_group = _check_for_agency_group_access(gis, email_domain)
        if agency_group:
            agency_group.add_users(usernames=[new_userid])
            html_content += f"""
                        <p><b>Additional actions taken:</b> <ul><li>Added user to agency group -- {agency_group.title}</li></ul></p>
                    """
        else:
            html_content += f"""
                        <p><b>Additional actions taken:</b> None, Agency group not yet created for <b>{email_domain}</b></p>
                    """
    else:
        # non-government email, quarantine the user
        # found under portal admin https://geoportal2.watech.wa.gov/portal/sharing/rest/portals/0123456789ABCDEF/roles
        quarantined_role_id = "4tp5IdAF1x1grmVB"
        quarantined_group = gis.groups.get("f63dbf4254744dbaa38268343d7ba572")
        training_resources_group = gis.groups.get("4424d80fd12e45d2b0def73c5fbac816")

        # adjust the user's settings  
        new_user = gis.users.get(new_userid)
        new_user.update_role(quarantined_role_id)
        quarantined_group.add_users(usernames=[new_userid])
        training_resources_group.remove_users(usernames=[new_userid])

        status = "QUARANTINED"
        html_content = f"""
                        <h2><b>{status}</b> new user added to GeoPortal 2.0</h2> 
                        <p>User: {new_userid} - {new_user_email}</p><p>Processed: {time.ctime()}</p>
                    """
        
    email_subject = f"[GP2-Notification] Check new user process: {status}"
    msg = EmailMessage(email_subject, html_content, DEFAULT_NOTIFICATION_SENDER, DEFAULT_NOTIFICATION_RECIPIENTS)
    msg.content_subtype = 'html'
    msg.send()
    return f"{time.ctime()} -- Completed email check of new users: {new_userid} - {new_user_email} - Status: {status}\n"


def check_email(input_task):
    """Checks if username is a State government email address"""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(_email_check, input_task.data)
        return_value = future.result()
    return return_value
    